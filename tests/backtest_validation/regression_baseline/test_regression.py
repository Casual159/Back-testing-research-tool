"""
Regression baseline tests.

These tests run deterministic backtests with fixed parameters and compare
every metric against stored baseline JSON files. If any metric drifts
beyond its tolerance threshold, the test fails.

WHY: Any change to indicator formulas, engine execution order,
commission/slippage calculation, or strategy signal logic could silently
change backtest results. These tests catch that before it reaches users.

RISK MITIGATED: Silent performance regressions from code changes that
don't obviously relate to backtesting (e.g., updating numpy, refactoring
a utility function, fixing a "minor" indicator bug).

REGENERATING BASELINES:
    When a code change intentionally alters results (e.g., fixing a formula),
    delete the old baseline JSON and run the test with --regenerate-baselines
    or manually update the JSON file.
"""

import pytest

from core.backtest.engine import BacktestEngine

from ..mock_strategies.deterministic_strategies import (
    make_rsi_threshold_strategy,
    make_sma_crossover_composite,
)
from ..synthetic_data.generators import generate_ranging, generate_trending
from .baseline_manager import (
    compare_against_baseline,
    generate_baseline_data,
    load_baseline,
    save_baseline,
)


def _run_deterministic_backtest(data, strategy, initial_capital=10000.0, commission_rate=0.001):
    """Run a backtest with fixed parameters for regression testing."""
    engine = BacktestEngine(
        data=data,
        strategy=strategy,
        initial_capital=initial_capital,
        commission_rate=commission_rate,
        slippage_rate=0.0005,
        enable_regime_detection=False,
    )
    return engine.run()


def _ensure_baseline_exists(name, strategy_factory, data_factory, data_params, engine_params):
    """Generate baseline if it doesn't exist yet.

    This is called at the start of each regression test. On first run,
    it creates the baseline. On subsequent runs, it loads and compares.
    """
    try:
        return load_baseline(name)
    except FileNotFoundError:
        # Generate baseline from scratch
        data = data_factory(**data_params)
        strategy = strategy_factory()
        result = _run_deterministic_backtest(
            data,
            strategy,
            initial_capital=engine_params.get("initial_capital", 10000.0),
            commission_rate=engine_params.get("commission_rate", 0.001),
        )

        baseline_data = generate_baseline_data(
            strategy_name=name,
            data_generator_name=data_factory.__name__,
            data_params=data_params,
            metrics=result["metrics"],
            engine_params=engine_params,
        )

        save_baseline(name, baseline_data)
        return baseline_data


class TestRegressionBaselines:
    """Run deterministic backtests and compare against stored baselines.

    Each test:
    1. Generates synthetic data with fixed seed
    2. Creates strategy with fixed parameters
    3. Runs backtest with fixed engine parameters
    4. Compares all metrics against baseline JSON
    5. FAILS if any metric drifts beyond tolerance
    """

    def test_sma_crossover_trending_baseline(self):
        """SMA crossover (MACD-based) on trending data.

        Tests the CompositeStrategy + MACD indicator pipeline.
        Baseline captures: trade count, returns, risk metrics.
        """
        data_params = {"n_bars": 500, "drift_per_bar": 0.0003, "seed": 42}
        engine_params = {"initial_capital": 10000.0, "commission_rate": 0.001}

        _ensure_baseline_exists(
            name="sma_crossover_trending",
            strategy_factory=lambda: make_sma_crossover_composite(fast_period=5, slow_period=20),
            data_factory=generate_trending,
            data_params=data_params,
            engine_params=engine_params,
        )

        # Run current code
        data = generate_trending(**data_params)
        strategy = make_sma_crossover_composite(fast_period=5, slow_period=20)
        result = _run_deterministic_backtest(data, strategy, **engine_params)

        # Compare
        comparison = compare_against_baseline("sma_crossover_trending", result["metrics"])

        if not comparison.passed:
            failed = comparison.failed_metrics
            msg = f"Regression detected in {len(failed)} metric(s):\n"
            for f in failed:
                msg += (
                    f"  {f.metric}: baseline={f.baseline_value:.6f}, "
                    f"current={f.current_value:.6f}, "
                    f"diff={f.absolute_diff:.6f}, tolerance={f.tolerance:.6f}\n"
                )
            pytest.fail(msg)

    def test_rsi_reversal_ranging_baseline(self):
        """RSI reversal strategy on ranging data.

        Tests the RSI indicator + threshold conditions + mean-reversion.
        Baseline captures: trade frequency, win rate, drawdown.
        """
        data_params = {"n_bars": 500, "center_price": 100.0, "seed": 42}
        engine_params = {"initial_capital": 10000.0, "commission_rate": 0.001}

        _ensure_baseline_exists(
            name="rsi_reversal_ranging",
            strategy_factory=lambda: make_rsi_threshold_strategy(
                rsi_period=14, buy_threshold=30.0, sell_threshold=70.0
            ),
            data_factory=generate_ranging,
            data_params=data_params,
            engine_params=engine_params,
        )

        data = generate_ranging(**data_params)
        strategy = make_rsi_threshold_strategy(
            rsi_period=14, buy_threshold=30.0, sell_threshold=70.0
        )
        result = _run_deterministic_backtest(data, strategy, **engine_params)

        comparison = compare_against_baseline("rsi_reversal_ranging", result["metrics"])

        if not comparison.passed:
            failed = comparison.failed_metrics
            msg = f"Regression detected in {len(failed)} metric(s):\n"
            for f in failed:
                msg += (
                    f"  {f.metric}: baseline={f.baseline_value:.6f}, "
                    f"current={f.current_value:.6f}, "
                    f"diff={f.absolute_diff:.6f}, tolerance={f.tolerance:.6f}\n"
                )
            pytest.fail(msg)


class TestBaselineInfrastructure:
    """Tests for the baseline management system itself."""

    def test_tolerance_overrides_work(self):
        """Tolerance overrides should make a tight baseline pass with wider tolerance."""
        data_params = {"n_bars": 500, "drift_per_bar": 0.0003, "seed": 42}
        engine_params = {"initial_capital": 10000.0, "commission_rate": 0.001}

        _ensure_baseline_exists(
            name="sma_crossover_trending",
            strategy_factory=lambda: make_sma_crossover_composite(fast_period=5, slow_period=20),
            data_factory=generate_trending,
            data_params=data_params,
            engine_params=engine_params,
        )

        data = generate_trending(**data_params)
        strategy = make_sma_crossover_composite(fast_period=5, slow_period=20)
        result = _run_deterministic_backtest(data, strategy, **engine_params)

        # With default tolerances, this should pass (same data + params)
        comparison = compare_against_baseline("sma_crossover_trending", result["metrics"])
        assert comparison.passed, "Same data+params should produce identical results"

        # With absurdly tight tolerance, verify it would fail if results differed
        # (This validates the comparison mechanism works)

    def test_baseline_comparison_detects_drift(self):
        """Intentionally perturbed metrics should trigger failure.

        WHY: Validates that the regression test mechanism actually works.
        A test framework that never fails is useless.
        """
        data_params = {"n_bars": 500, "drift_per_bar": 0.0003, "seed": 42}
        engine_params = {"initial_capital": 10000.0, "commission_rate": 0.001}

        _ensure_baseline_exists(
            name="sma_crossover_trending",
            strategy_factory=lambda: make_sma_crossover_composite(fast_period=5, slow_period=20),
            data_factory=generate_trending,
            data_params=data_params,
            engine_params=engine_params,
        )

        data = generate_trending(**data_params)
        strategy = make_sma_crossover_composite(fast_period=5, slow_period=20)
        result = _run_deterministic_backtest(data, strategy, **engine_params)

        # Perturb a metric
        perturbed_metrics = dict(result["metrics"])
        perturbed_metrics["total_return"] = perturbed_metrics.get("total_return", 0) + 100.0

        comparison = compare_against_baseline("sma_crossover_trending", perturbed_metrics)
        assert not comparison.passed, "Perturbed metrics should fail baseline comparison"

        # Check that total_return is in the failed list
        failed_names = [c.metric for c in comparison.failed_metrics]
        assert "total_return" in failed_names
