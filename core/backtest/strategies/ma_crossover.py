"""
Moving Average Crossover Strategy.

Classic trend-following strategy:
- BUY when fast MA crosses above slow MA (bullish crossover)
- SELL when fast MA crosses below slow MA (bearish crossover)

This is one of the simplest and most popular technical trading strategies.
Works best in trending markets, but generates false signals in ranging markets.
"""

from typing import Optional
from ..events import MarketEvent, SignalEvent
from .base import Strategy


class MovingAverageCrossover(Strategy):
    """
    Moving Average Crossover Strategy.

    Generates signals based on two moving averages:
    - Fast MA (shorter period): More responsive to recent price changes
    - Slow MA (longer period): Smoother, represents longer-term trend

    Signal Logic:
    - BUY: Fast MA crosses above Slow MA (golden cross)
    - SELL: Fast MA crosses below Slow MA (death cross)
    - HOLD: No crossover detected

    Parameters:
        fast_period: Period for fast moving average (default: 20)
        slow_period: Period for slow moving average (default: 50)
        ma_type: Type of MA ('SMA' or 'EMA') (default: 'SMA')

    Example:
        >>> strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
        >>> # Strategy will buy when 20-MA crosses above 50-MA
    """

    # Markdown description for user/AI
    DESCRIPTION = """
Trend-following strategy using two moving averages (fast and slow).

**Best for:** TREND_UP, TREND_DOWN (clear trends)
**Avoid:** RANGE, CHOPPY (whipsaws)

**Entry:** Fast MA crosses above slow MA (golden cross)
**Exit:** Fast MA crosses below slow MA (death cross)

**Risk:** Moderate drawdown during reversals. Requires patience in sideways markets.

**Parameters:**
- `fast_period`: Responsive to recent price (default: 20)
- `slow_period`: Trend baseline (default: 50)
- `ma_type`: 'SMA' or 'EMA' (default: 'SMA')
    """.strip()

    # Structured metadata for AI/filtering
    METADATA = {
        "preferred_regimes": ["TREND_UP", "TREND_DOWN"],
        "avoid_regimes": ["RANGE", "CHOPPY"],
        "risk_level": "moderate",
        "category": "trend-following",
        "entry_type": "market",
        "exit_type": "market",
        "drawdown_tolerance": "medium",
        "avg_trade_duration": "medium",
        "win_rate_range": [0.45, 0.55]
    }

    def __init__(
        self,
        fast_period: int = 20,
        slow_period: int = 50,
        ma_type: str = 'SMA'
    ):
        """
        Initialize MA Crossover strategy.

        Args:
            fast_period: Period for fast MA (must be < slow_period)
            slow_period: Period for slow MA
            ma_type: Type of moving average ('SMA' or 'EMA')

        Raises:
            ValueError: If fast_period >= slow_period
        """
        if fast_period >= slow_period:
            raise ValueError(f"fast_period ({fast_period}) must be < slow_period ({slow_period})")

        super().__init__({
            'fast_period': fast_period,
            'slow_period': slow_period,
            'ma_type': ma_type.upper()
        })

        # Track previous MAs for crossover detection
        self.prev_fast_ma = None
        self.prev_slow_ma = None

    def _get_max_buffer_size(self) -> int:
        """Only need slow_period + 1 bars for calculations."""
        return self.parameters['slow_period'] + 10  # +10 for safety

    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Calculate MA crossover signal.

        Args:
            market_event: New market data

        Returns:
            SignalEvent or None if insufficient data or no crossover
        """
        slow_period = self.parameters['slow_period']
        fast_period = self.parameters['fast_period']
        ma_type = self.parameters['ma_type']

        # Check if we have enough data
        if not self.has_sufficient_data(slow_period):
            return None

        # Calculate current MAs
        prices = self.get_closing_prices()

        if ma_type == 'SMA':
            fast_ma = self.calculate_sma(fast_period, prices)
            slow_ma = self.calculate_sma(slow_period, prices)
        elif ma_type == 'EMA':
            fast_ma = self.calculate_ema(fast_period, prices)
            slow_ma = self.calculate_ema(slow_period, prices)
        else:
            raise ValueError(f"Unknown MA type: {ma_type}")

        if fast_ma is None or slow_ma is None:
            return None

        # Detect crossover (need previous values)
        signal = None

        if self.prev_fast_ma is not None and self.prev_slow_ma is not None:
            # Check for bullish crossover (fast crosses above slow)
            if self.prev_fast_ma <= self.prev_slow_ma and fast_ma > slow_ma:
                signal = SignalEvent(
                    timestamp=market_event.timestamp,
                    symbol=market_event.symbol,
                    signal_type='BUY',
                    strength=1.0,
                    metadata={
                        'fast_ma': fast_ma,
                        'slow_ma': slow_ma,
                        'prev_fast_ma': self.prev_fast_ma,
                        'prev_slow_ma': self.prev_slow_ma,
                        'crossover_type': 'golden_cross'
                    }
                )

            # Check for bearish crossover (fast crosses below slow)
            elif self.prev_fast_ma >= self.prev_slow_ma and fast_ma < slow_ma:
                signal = SignalEvent(
                    timestamp=market_event.timestamp,
                    symbol=market_event.symbol,
                    signal_type='SELL',
                    strength=1.0,
                    metadata={
                        'fast_ma': fast_ma,
                        'slow_ma': slow_ma,
                        'prev_fast_ma': self.prev_fast_ma,
                        'prev_slow_ma': self.prev_slow_ma,
                        'crossover_type': 'death_cross'
                    }
                )

        # Update previous values for next iteration
        self.prev_fast_ma = fast_ma
        self.prev_slow_ma = slow_ma

        return signal

    def get_current_mas(self) -> dict:
        """
        Get current MA values (for debugging/visualization).

        Returns:
            Dict with 'fast_ma' and 'slow_ma' keys, or None if not calculated yet
        """
        if self.prev_fast_ma is None or self.prev_slow_ma is None:
            return None

        return {
            'fast_ma': self.prev_fast_ma,
            'slow_ma': self.prev_slow_ma
        }

    def __repr__(self):
        return (f"MovingAverageCrossover("
                f"fast={self.parameters['fast_period']}, "
                f"slow={self.parameters['slow_period']}, "
                f"type={self.parameters['ma_type']})")
