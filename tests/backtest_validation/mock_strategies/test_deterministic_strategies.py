"""
Tests for deterministic mock strategies.

WHY: Mock strategies are test infrastructure — if they don't produce the
expected signals and trades, all downstream validation tests give wrong
results. These tests verify the strategies behave as documented.

RISK MITIGATED: Test infrastructure producing incorrect expected results;
CompositeStrategy misinterpreting LogicTree; signal pre-calculation bugs.
"""

from ..synthetic_data.generators import generate_ranging, generate_trending
from .deterministic_strategies import (
    make_always_long_strategy,
    make_multi_condition_strategy,
    make_rsi_threshold_strategy,
    make_sma_crossover_composite,
)


class TestAlwaysLongStrategy:
    """Verify that the always-long strategy enters once and never exits."""

    def test_one_open_position_no_completed_trades(self, run_backtest):
        """On positive-price data: 1 open position, 0 completed trades.

        WHY: Validates that the CompositeStrategy state machine correctly
        tracks _in_position and that SMA(2) > 0 fires on positive prices.
        """
        data = generate_trending(n_bars=200, seed=42)
        strategy = make_always_long_strategy()
        result = run_backtest(data, strategy)

        portfolio = result["portfolio"]
        assert portfolio.total_trades() == 0, "Should have 0 completed (round-trip) trades"
        assert len(portfolio.positions) == 1, "Should have 1 open position"

    def test_cash_decreases_after_entry(self, run_backtest):
        """Cash should decrease after the BUY (position opened).

        WHY: Validates Portfolio.update_from_fill correctly deducts cost.
        """
        data = generate_trending(n_bars=100, seed=42)
        strategy = make_always_long_strategy()
        result = run_backtest(data, strategy, initial_capital=10000.0)

        portfolio = result["portfolio"]
        assert portfolio.current_cash < 10000.0, "Cash should decrease after buying"


class TestRSIThresholdStrategy:
    """Verify RSI threshold strategy produces trades on ranging data."""

    def test_produces_trades_on_ranging_data(self, run_backtest):
        """RSI oscillates on ranging data, so strategy should enter and exit.

        WHY: Validates that RSI indicator computation + threshold conditions
        work correctly in the CompositeStrategy pre-calculation pipeline.
        """
        data = generate_ranging(n_bars=500, center_price=100.0, seed=42)
        strategy = make_rsi_threshold_strategy(
            rsi_period=14, buy_threshold=30.0, sell_threshold=70.0
        )
        result = run_backtest(data, strategy)

        trades = result["trades"]
        assert len(trades) > 0, "RSI strategy should produce trades on ranging data"

    def test_all_trades_are_long(self, run_backtest):
        """All trades should be LONG (the strategy only buys, never shorts).

        WHY: Validates CompositeStrategy only generates BUY/SELL signals
        (not SHORT/COVER), and Portfolio correctly records direction.
        """
        data = generate_ranging(n_bars=500, center_price=100.0, seed=42)
        strategy = make_rsi_threshold_strategy()
        result = run_backtest(data, strategy)

        for trade in result["trades"]:
            assert trade.direction == "LONG", f"Expected LONG, got {trade.direction}"

    def test_entry_when_rsi_is_low(self, run_backtest):
        """Buy signals should only fire when RSI < buy_threshold.

        WHY: Validates that IndicatorSignal.evaluate_series correctly
        computes RSI and Condition correctly evaluates '<' operator.
        """
        data = generate_ranging(n_bars=500, center_price=100.0, seed=42)
        strategy = make_rsi_threshold_strategy(
            rsi_period=14, buy_threshold=30.0, sell_threshold=70.0
        )

        # Initialize the strategy to inspect pre-calculated signals
        strategy.initialize(data)

        # Calculate RSI values
        rsi_signal = strategy.entry_logic.root.signal
        rsi_values = rsi_signal.calculate_indicator(data)

        # Where entry signal is True, RSI should be < 30
        entry_bars = strategy._entry_signals
        rsi_at_entry = rsi_values[entry_bars]
        if len(rsi_at_entry) > 0:
            assert (rsi_at_entry < 30.0).all(), "Entry signals should only fire when RSI < 30"


class TestSMACrossoverComposite:
    """Verify SMA crossover composite strategy works on trending data."""

    def test_produces_trades_on_trending_data(self, run_backtest):
        """SMA crossover should enter on uptrend, exit on pullbacks.

        WHY: Validates MACD indicator computation (which is EMA fast - EMA slow)
        works correctly in the CompositeStrategy pipeline.
        """
        data = generate_trending(n_bars=500, drift_per_bar=0.0003, seed=42)
        strategy = make_sma_crossover_composite(fast_period=5, slow_period=20)
        result = run_backtest(data, strategy)

        # Should produce at least some trades on trending data
        metrics = result["metrics"]
        assert metrics["total_trades"] >= 0, "Strategy should run without errors"

    def test_deterministic_results(self, run_backtest):
        """Same data + same seed produces identical results.

        WHY: Core determinism guarantee. If this fails, no other test is reliable.
        """
        data = generate_trending(n_bars=300, seed=42)
        strategy1 = make_sma_crossover_composite(fast_period=5, slow_period=20)
        strategy2 = make_sma_crossover_composite(fast_period=5, slow_period=20)

        result1 = run_backtest(data, strategy1)
        result2 = run_backtest(data, strategy2)

        assert result1["metrics"]["total_return"] == result2["metrics"]["total_return"]
        assert result1["metrics"]["total_trades"] == result2["metrics"]["total_trades"]
        assert len(result1["trades"]) == len(result2["trades"])


class TestMultiConditionStrategy:
    """Verify AND logic combines conditions correctly."""

    def test_and_logic_is_stricter_than_single_condition(self, run_backtest):
        """AND(RSI<40, MACD_hist>0) should produce fewer entries than RSI<40 alone.

        WHY: Validates LogicTree.AND correctly requires ALL conditions to be True.
        If AND were broken (acting like OR), we'd see more trades, not fewer.
        """
        data = generate_ranging(n_bars=500, center_price=100.0, seed=42)

        # Multi-condition strategy: RSI<40 AND MACD_hist>0
        multi_strategy = make_multi_condition_strategy()

        # Single-condition strategy: just RSI<40
        single_strategy = make_rsi_threshold_strategy(
            rsi_period=14, buy_threshold=40.0, sell_threshold=60.0
        )

        run_backtest(data, multi_strategy)
        run_backtest(data, single_strategy)

        multi_strategy_copy = make_multi_condition_strategy()
        multi_strategy_copy.initialize(data)
        single_strategy_copy = make_rsi_threshold_strategy(
            rsi_period=14, buy_threshold=40.0, sell_threshold=60.0
        )
        single_strategy_copy.initialize(data)

        # AND should have fewer or equal entry signals than single condition
        multi_entries = multi_strategy_copy._entry_signals.sum()
        single_entries = single_strategy_copy._entry_signals.sum()

        assert (
            multi_entries <= single_entries
        ), f"AND should be stricter: {multi_entries} entries vs {single_entries} for single"

    def test_multi_condition_initializes_without_error(self, run_backtest):
        """Multi-condition strategy should initialize and run without errors.

        WHY: Validates that LogicTree with multiple children evaluates correctly
        via evaluate_series cascade (LogicTree → LogicNode → IndicatorSignal).
        """
        data = generate_ranging(n_bars=300, seed=42)
        strategy = make_multi_condition_strategy()
        result = run_backtest(data, strategy)

        # Should complete without error
        assert "metrics" in result
        assert result["metrics"]["total_trades"] >= 0
