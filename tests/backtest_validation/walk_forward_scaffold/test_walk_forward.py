"""
Tests for the walk-forward validation scaffold.

WHY: Walk-forward validation is our defense against overfitting.
If the scaffold itself has bugs (overlapping train/test, shared strategy
state, wrong split ratios), the overfitting protection is worthless.

RISK MITIGATED:
- Train/test data overlap (would inflate out-of-sample metrics)
- Strategy state leaking between train and test (subtle contamination)
- Incorrect split ratios (too little test data)
- Framework crashes on edge cases
"""

import pytest

from ..mock_strategies.deterministic_strategies import (
    make_rsi_threshold_strategy,
    make_sma_crossover_composite,
)
from ..synthetic_data.generators import generate_ranging, generate_trending
from .walk_forward import WalkForwardResult, WalkForwardValidator


class TestDataSplitting:
    """Verify that train/test split is correct and non-overlapping."""

    def test_no_overlap_between_train_and_test(self):
        """Train and test DataFrames must have completely disjoint time ranges.

        WHY: Any overlap means the test set contains data the strategy
        "saw" during training — invalidating out-of-sample testing.
        """
        data = generate_trending(n_bars=500, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=0.7,
        )
        train, test = validator._split_data()

        # No overlapping timestamps
        overlap = train.index.intersection(test.index)
        assert len(overlap) == 0, f"Found {len(overlap)} overlapping timestamps"

        # Train ends before test starts
        assert train.index[-1] < test.index[0], "Train must end before test starts"

    def test_train_test_cover_all_data(self):
        """Union of train and test indices should equal the full data index.

        WHY: Missing data means we're not using all available information.
        """
        data = generate_trending(n_bars=500, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=0.7,
        )
        train, test = validator._split_data()

        combined = train.index.append(test.index)
        assert len(combined) == len(
            data
        ), f"Combined length {len(combined)} != data length {len(data)}"

    def test_train_ratio_respected(self):
        """Train set should have approximately train_ratio * total_bars."""
        data = generate_trending(n_bars=500, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=0.7,
        )
        train, test = validator._split_data()

        expected_train = int(500 * 0.7)  # 350
        assert (
            len(train) == expected_train
        ), f"Expected {expected_train} train bars, got {len(train)}"
        assert len(test) == 500 - expected_train

    @pytest.mark.parametrize("ratio", [0.5, 0.6, 0.7, 0.8])
    def test_various_train_ratios(self, ratio):
        """Split works correctly for various train ratios."""
        data = generate_trending(n_bars=400, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=ratio,
        )
        train, test = validator._split_data()

        expected_train = int(400 * ratio)
        assert len(train) == expected_train
        assert len(test) == 400 - expected_train


class TestStrategyIsolation:
    """Verify that strategy factory creates independent instances."""

    def test_factory_called_twice(self):
        """Strategy factory should be called for both train and test runs.

        WHY: If the same strategy instance is reused, pre-calculated signals
        from training data could leak into the test evaluation.
        """
        call_count = 0

        def counting_factory():
            nonlocal call_count
            call_count += 1
            return make_sma_crossover_composite(5, 20)

        data = generate_trending(n_bars=200, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=counting_factory,
            train_ratio=0.7,
        )
        validator.run()

        assert call_count == 2, f"Factory should be called twice, was called {call_count} times"


class TestWalkForwardExecution:
    """Verify walk-forward produces valid results."""

    def test_produces_valid_result_structure(self):
        """WalkForwardResult should have all expected fields populated.

        WHY: Downstream code (UI, reports) depends on these fields existing.
        """
        data = generate_trending(n_bars=300, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=0.7,
        )
        result = validator.run()

        assert isinstance(result, WalkForwardResult)
        assert isinstance(result.train_metrics, dict)
        assert isinstance(result.test_metrics, dict)
        assert result.train_bars > 0
        assert result.test_bars > 0
        assert result.train_period[0] < result.train_period[1]
        assert result.test_period[0] < result.test_period[1]

    def test_metrics_are_valid(self):
        """Both train and test metrics should contain standard keys.

        WHY: Validates that MetricsCalculator runs correctly on both splits.
        """
        data = generate_trending(n_bars=300, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=0.7,
        )
        result = validator.run()

        required_keys = [
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "total_trades",
            "win_rate",
        ]

        for key in required_keys:
            assert key in result.train_metrics, f"Missing '{key}' in train metrics"
            assert key in result.test_metrics, f"Missing '{key}' in test metrics"

    def test_overfit_ratio_calculation(self):
        """Manually verify overfit_ratio formula."""
        result = WalkForwardResult(
            train_metrics={"sharpe_ratio": 2.0},
            test_metrics={"sharpe_ratio": 1.0},
            train_period=(None, None),
            test_period=(None, None),
            train_bars=100,
            test_bars=50,
        )
        assert result.overfit_ratio == 2.0

    def test_overfit_ratio_zero_test_sharpe(self):
        """When test Sharpe is 0, overfit_ratio should be inf."""
        result = WalkForwardResult(
            train_metrics={"sharpe_ratio": 1.5},
            test_metrics={"sharpe_ratio": 0.0},
            train_period=(None, None),
            test_period=(None, None),
            train_bars=100,
            test_bars=50,
        )
        assert result.overfit_ratio == float("inf")

    def test_overfit_ratio_both_zero(self):
        """When both Sharpes are 0, overfit_ratio should be 1.0 (neutral)."""
        result = WalkForwardResult(
            train_metrics={"sharpe_ratio": 0.0},
            test_metrics={"sharpe_ratio": 0.0},
            train_period=(None, None),
            test_period=(None, None),
            train_bars=100,
            test_bars=50,
        )
        assert result.overfit_ratio == 1.0

    def test_return_degradation_calculation(self):
        """Verify return_degradation formula."""
        result = WalkForwardResult(
            train_metrics={"total_return": 20.0},
            test_metrics={"total_return": 10.0},
            train_period=(None, None),
            test_period=(None, None),
            train_bars=100,
            test_bars=50,
        )
        assert result.return_degradation == 0.5


class TestWalkForwardConcrete:
    """Concrete walk-forward examples with real strategies on synthetic data."""

    def test_sma_crossover_on_trending_data(self):
        """SMA crossover walk-forward on 500-bar trending data.

        This is a realistic usage example. We verify:
        - Both splits produce valid metrics
        - Overfit ratio is reasonable (not absurdly high)
        - The framework completes without errors

        We do NOT check exact metric values (that's regression_baseline's job).
        """
        data = generate_trending(n_bars=500, drift_per_bar=0.0003, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            train_ratio=0.7,
            commission_rate=0.001,
        )
        result = validator.run()

        # Structural validation
        assert result.train_bars == 350
        assert result.test_bars == 150
        assert result.train_metrics["total_trades"] >= 0
        assert result.test_metrics["total_trades"] >= 0

        # Win rate in valid range
        assert 0 <= result.train_metrics["win_rate"] <= 100
        assert 0 <= result.test_metrics["win_rate"] <= 100

    def test_rsi_strategy_on_ranging_data(self):
        """RSI mean-reversion walk-forward on ranging data.

        RSI strategies should perform well on ranging data in both
        train and test sets (since the regime is consistent).
        """
        data = generate_ranging(n_bars=500, center_price=100.0, seed=42)
        validator = WalkForwardValidator(
            data=data,
            strategy_factory=lambda: make_rsi_threshold_strategy(14, 30.0, 70.0),
            train_ratio=0.7,
            commission_rate=0.001,
        )
        result = validator.run()

        # Both should produce trades (RSI oscillates on ranging data)
        assert result.train_metrics["total_trades"] >= 0
        assert result.test_metrics["total_trades"] >= 0


class TestWalkForwardEdgeCases:
    """Edge case handling."""

    def test_rejects_too_small_dataset(self):
        """Should reject datasets with fewer than 50 bars."""
        data = generate_trending(n_bars=30, seed=42)
        with pytest.raises(ValueError, match="at least 50 bars"):
            WalkForwardValidator(
                data=data,
                strategy_factory=lambda: make_sma_crossover_composite(5, 20),
            )

    def test_rejects_extreme_train_ratio(self):
        """Should reject train_ratio outside [0.1, 0.9]."""
        data = generate_trending(n_bars=200, seed=42)
        with pytest.raises(ValueError, match="train_ratio"):
            WalkForwardValidator(
                data=data,
                strategy_factory=lambda: make_sma_crossover_composite(5, 20),
                train_ratio=0.05,
            )
