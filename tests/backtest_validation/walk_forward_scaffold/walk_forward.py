"""
Walk-forward validation scaffold.

Implements a minimal but functional train/test split framework for
out-of-sample validation of backtesting strategies.

WHY: In-sample performance (training on the same data you test on) is
meaningless for predicting live performance. Walk-forward validation
splits data into non-overlapping train/test windows and measures
how well in-sample performance generalizes.

DESIGN: Uses a strategy_factory callable (not a strategy instance) to
create fresh strategy objects for each split. This prevents state
contamination between train and test runs — validated by
bias_detection/test_lookahead_bias.py::TestStateContamination.

EXTENSION POINTS (for future implementation):
    - Multiple rolling windows (anchored or sliding)
    - Parameter optimization on train set
    - Combinatorial purged cross-validation (Lopez de Prado)
    - Monte Carlo permutation tests
"""

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from core.backtest.engine import BacktestEngine


@dataclass
class WalkForwardResult:
    """Results from a single walk-forward validation fold.

    Attributes:
        train_metrics: Performance metrics on training data.
        test_metrics: Performance metrics on test (out-of-sample) data.
        train_period: (start, end) datetimes of training window.
        test_period: (start, end) datetimes of test window.
        train_bars: Number of bars in training set.
        test_bars: Number of bars in test set.
    """

    train_metrics: dict
    test_metrics: dict
    train_period: tuple
    test_period: tuple
    train_bars: int
    test_bars: int

    @property
    def overfit_ratio(self) -> float:
        """Ratio of train Sharpe to test Sharpe.

        Interpretation:
            ~1.0: Good generalization (in-sample ≈ out-of-sample)
            >2.0: Likely overfitting (in-sample >> out-of-sample)
            <0.5: Strategy behaves differently on test data

        Returns float('inf') if test Sharpe is zero (can't divide).
        """
        train_sharpe = self.train_metrics.get("sharpe_ratio", 0)
        test_sharpe = self.test_metrics.get("sharpe_ratio", 0)

        if abs(test_sharpe) < 1e-10:
            return float("inf") if abs(train_sharpe) > 1e-10 else 1.0

        return abs(train_sharpe / test_sharpe)

    @property
    def return_degradation(self) -> float:
        """How much total return degrades from train to test.

        Formula: test_return / train_return
        Values < 1.0 indicate degradation.
        """
        train_ret = self.train_metrics.get("total_return", 0)
        test_ret = self.test_metrics.get("total_return", 0)

        if abs(train_ret) < 1e-10:
            return 1.0

        return test_ret / train_ret


class WalkForwardValidator:
    """Minimal walk-forward validation with a single train/test split.

    Usage:
        validator = WalkForwardValidator(
            data=my_ohlcv_data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=0.7,
        )
        result = validator.run()
        print(f"Overfit ratio: {result.overfit_ratio:.2f}")

    Args:
        data: Full OHLCV DataFrame with DatetimeIndex.
        strategy_factory: Callable that returns a FRESH Strategy instance.
                         Must be a factory (not an instance) to prevent
                         state leakage between train and test runs.
        train_ratio: Fraction of data for training (default: 70%).
        initial_capital: Starting capital for each backtest.
        commission_rate: Commission rate per trade.
        slippage_rate: Slippage rate per trade.
        enable_regime_detection: Whether to enable regime detection.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        strategy_factory: Callable,
        train_ratio: float = 0.7,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        enable_regime_detection: bool = False,
    ):
        if not 0.1 <= train_ratio <= 0.9:
            raise ValueError(f"train_ratio must be between 0.1 and 0.9, got {train_ratio}")

        if len(data) < 50:
            raise ValueError(f"Need at least 50 bars, got {len(data)}")

        self.data = data
        self.strategy_factory = strategy_factory
        self.train_ratio = train_ratio
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.enable_regime_detection = enable_regime_detection

    def _split_data(self) -> tuple:
        """Split data into train and test sets at train_ratio boundary.

        Returns:
            (train_df, test_df) — non-overlapping DataFrames.
        """
        split_idx = int(len(self.data) * self.train_ratio)
        train = self.data.iloc[:split_idx].copy()
        test = self.data.iloc[split_idx:].copy()
        return train, test

    def _run_backtest(self, data: pd.DataFrame) -> dict:
        """Run a backtest on the given data with a FRESH strategy.

        Creates a new strategy instance via factory to prevent state leak.
        """
        strategy = self.strategy_factory()

        engine = BacktestEngine(
            data=data,
            strategy=strategy,
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate,
            enable_regime_detection=self.enable_regime_detection,
        )

        return engine.run()

    def run(self) -> WalkForwardResult:
        """Execute walk-forward validation.

        1. Split data at train_ratio boundary.
        2. Run backtest on train data with fresh strategy.
        3. Run backtest on test data with fresh strategy.
        4. Return comparison results.
        """
        train_data, test_data = self._split_data()

        train_result = self._run_backtest(train_data)
        test_result = self._run_backtest(test_data)

        return WalkForwardResult(
            train_metrics=train_result["metrics"],
            test_metrics=test_result["metrics"],
            train_period=(train_data.index[0], train_data.index[-1]),
            test_period=(test_data.index[0], test_data.index[-1]),
            train_bars=len(train_data),
            test_bars=len(test_data),
        )
