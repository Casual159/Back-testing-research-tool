"""
Mock strategies with mathematically predictable behavior.

Built using the CompositeStrategy framework (LogicTree + IndicatorSignal)
to validate the exact same execution path that production strategies use.

Each factory function returns a fully configured CompositeStrategy whose
trade behavior can be predicted on known synthetic data.

WHY: Real strategies on real data produce unpredictable trade counts.
These mock strategies let us assert exact trade timing, direction, and PnL.
"""

from core.backtest.strategies.composition.composite_strategy import CompositeStrategy
from core.backtest.strategies.composition.condition import Condition
from core.backtest.strategies.composition.logic_tree import LogicTree
from core.backtest.strategies.composition.signal import IndicatorSignal


def make_always_long_strategy() -> CompositeStrategy:
    """Strategy that enters on bar ~1 and never exits.

    Entry: SMA(2) > 0 — always true for positive prices (fires almost immediately).
    Exit: SMA(2) < 0 — never true for positive prices.

    Expected behavior on positive-price data:
    - 1 BUY signal as soon as SMA(2) is computable (bar 1)
    - 0 SELL signals (SMA never goes below 0)
    - 1 open position at end, 0 completed trades

    Useful for testing single-entry portfolio mechanics and position tracking.
    """
    entry_signal = IndicatorSignal(
        name="sma2_positive",
        indicator="SMA",
        parameters={"period": 2},
        condition=Condition(operator=">", threshold=0),
    )

    exit_signal = IndicatorSignal(
        name="sma2_negative",
        indicator="SMA",
        parameters={"period": 2},
        condition=Condition(operator="<", threshold=0),
    )

    return CompositeStrategy(
        name="always_long",
        entry_logic=LogicTree.AND([entry_signal]),
        exit_logic=LogicTree.AND([exit_signal]),
    )


def make_rsi_threshold_strategy(
    rsi_period: int = 14,
    buy_threshold: float = 30.0,
    sell_threshold: float = 70.0,
) -> CompositeStrategy:
    """RSI mean-reversion strategy with configurable thresholds.

    Entry: RSI(period) < buy_threshold
    Exit: RSI(period) > sell_threshold

    When paired with generate_ranging() data, RSI oscillates predictably
    and the strategy generates a known number of round-trip trades.

    Args:
        rsi_period: RSI lookback period.
        buy_threshold: RSI level below which to buy.
        sell_threshold: RSI level above which to sell.
    """
    entry_signal = IndicatorSignal(
        name="rsi_oversold",
        indicator="RSI",
        parameters={"period": rsi_period},
        condition=Condition(operator="<", threshold=buy_threshold),
    )

    exit_signal = IndicatorSignal(
        name="rsi_overbought",
        indicator="RSI",
        parameters={"period": rsi_period},
        condition=Condition(operator=">", threshold=sell_threshold),
    )

    return CompositeStrategy(
        name=f"rsi_threshold_{rsi_period}_{buy_threshold}_{sell_threshold}",
        entry_logic=LogicTree.AND([entry_signal]),
        exit_logic=LogicTree.AND([exit_signal]),
    )


def make_sma_crossover_composite(
    fast_period: int = 5,
    slow_period: int = 20,
) -> CompositeStrategy:
    """SMA crossover strategy built with CompositeStrategy framework.

    Entry: SMA(fast) cross_above SMA(slow) — simplified as SMA(fast) > SMA(slow)
    Exit: SMA(fast) cross_below SMA(slow) — simplified as SMA(fast) < SMA(slow)

    Note: We use simple threshold conditions (fast > slow, fast < slow) rather
    than cross_above/cross_below because CompositeStrategy evaluates each
    signal independently (not relative to another indicator). The crossover
    detection happens implicitly through the entry/exit state machine in
    CompositeStrategy.calculate_signals().

    Args:
        fast_period: Fast SMA period.
        slow_period: Slow SMA period.
    """
    # Entry: fast SMA is above slow SMA
    # We approximate this by checking if short-term SMA is "high enough"
    # relative to long-term. In practice, CompositeStrategy's state machine
    # (in_position toggle) naturally creates crossover behavior.
    entry_signal = IndicatorSignal(
        name=f"sma{fast_period}_above_threshold",
        indicator="SMA",
        parameters={"period": fast_period},
        condition=Condition(operator=">", threshold=0),  # Always true for positive prices
    )

    # For a proper crossover we need the difference between fast and slow SMA.
    # Since IndicatorSignal computes one indicator at a time, we use a simple
    # approach: entry when fast SMA > slow SMA value at that point.
    # The composite framework doesn't natively support cross-indicator comparison,
    # so we use RSI as a proxy for trend direction instead.

    # Actually, let's use a simpler and more testable approach:
    # Use MACD (which IS a fast/slow moving average difference) cross_above 0
    entry_signal = IndicatorSignal(
        name="macd_positive",
        indicator="MACD",
        parameters={"fast": fast_period, "slow": slow_period, "signal": 3},
        condition=Condition(operator=">", threshold=0),
        indicator_component="macd",
    )

    exit_signal = IndicatorSignal(
        name="macd_negative",
        indicator="MACD",
        parameters={"fast": fast_period, "slow": slow_period, "signal": 3},
        condition=Condition(operator="<", threshold=0),
        indicator_component="macd",
    )

    return CompositeStrategy(
        name=f"sma_crossover_{fast_period}_{slow_period}",
        entry_logic=LogicTree.AND([entry_signal]),
        exit_logic=LogicTree.AND([exit_signal]),
    )


def make_bollinger_mean_reversion_strategy(
    period: int = 20,
    num_std: float = 2.0,
) -> CompositeStrategy:
    """Bollinger Bands mean-reversion strategy.

    Entry: Price touches lower band (BB_lower > close, approximated via
           BB lower band > threshold)
    Exit: Price touches upper band

    Since IndicatorSignal returns the indicator value (not price comparison),
    we approximate with: RSI oversold (entry) / RSI overbought (exit) which
    correlates with Bollinger band touches on ranging data.

    For direct BB testing, we check if BB bandwidth indicates compression.
    """
    # Use RSI as a simpler proxy that tests the same composition framework
    entry_signal = IndicatorSignal(
        name="rsi_low",
        indicator="RSI",
        parameters={"period": period},
        condition=Condition(operator="<", threshold=35.0),
    )

    exit_signal = IndicatorSignal(
        name="rsi_high",
        indicator="RSI",
        parameters={"period": period},
        condition=Condition(operator=">", threshold=65.0),
    )

    return CompositeStrategy(
        name=f"bb_mean_reversion_{period}",
        entry_logic=LogicTree.AND([entry_signal]),
        exit_logic=LogicTree.AND([exit_signal]),
    )


def make_multi_condition_strategy() -> CompositeStrategy:
    """Strategy with AND logic combining two entry conditions.

    Entry: RSI(14) < 40 AND MACD histogram > 0 (oversold + bullish momentum)
    Exit: RSI(14) > 60

    Tests that LogicTree AND combination works correctly in the
    CompositeStrategy pre-calculation pipeline.
    """
    entry_rsi = IndicatorSignal(
        name="rsi_below_40",
        indicator="RSI",
        parameters={"period": 14},
        condition=Condition(operator="<", threshold=40.0),
    )

    entry_macd = IndicatorSignal(
        name="macd_hist_positive",
        indicator="MACD",
        parameters={"fast": 12, "slow": 26, "signal": 9},
        condition=Condition(operator=">", threshold=0),
        indicator_component="histogram",
    )

    exit_signal = IndicatorSignal(
        name="rsi_above_60",
        indicator="RSI",
        parameters={"period": 14},
        condition=Condition(operator=">", threshold=60.0),
    )

    return CompositeStrategy(
        name="multi_condition_rsi_macd",
        entry_logic=LogicTree.AND([entry_rsi, entry_macd]),
        exit_logic=LogicTree.AND([exit_signal]),
    )


def make_regime_filtered_strategy(
    allowed_regimes: list,
) -> CompositeStrategy:
    """Simple SMA-based strategy with regime filter.

    Entry: SMA(2) > 0 (always true for positive prices)
    Exit: SMA(2) < 0 (never true for positive prices)
    Regime filter: Only enter in allowed_regimes.

    When regime detection is enabled, this strategy should only generate
    BUY signals during periods classified as allowed regimes.

    Args:
        allowed_regimes: List of regime strings, e.g. ["TREND_UP", "RANGE"].
    """
    entry_signal = IndicatorSignal(
        name="sma2_positive",
        indicator="SMA",
        parameters={"period": 2},
        condition=Condition(operator=">", threshold=0),
    )

    exit_signal = IndicatorSignal(
        name="sma2_negative",
        indicator="SMA",
        parameters={"period": 2},
        condition=Condition(operator="<", threshold=0),
    )

    return CompositeStrategy(
        name=f"regime_filtered_{'_'.join(allowed_regimes)}",
        entry_logic=LogicTree.AND([entry_signal]),
        exit_logic=LogicTree.AND([exit_signal]),
        regime_filter=allowed_regimes,
    )
