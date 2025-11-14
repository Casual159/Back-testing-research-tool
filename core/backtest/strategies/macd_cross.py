"""
MACD Signal Line Cross Strategy.

Trend-following momentum strategy:
- BUY when MACD crosses above Signal Line
- SELL when MACD crosses below Signal Line

MACD = EMA(12) - EMA(26)
Signal Line = EMA(9) of MACD
"""

from typing import Optional
from ..events import MarketEvent, SignalEvent
from .base import Strategy


class MACDCross(Strategy):
    """
    MACD Signal Line Crossover Strategy.

    Generates signals based on MACD crossing its signal line:
    - MACD crosses above Signal → BUY (bullish momentum)
    - MACD crosses below Signal → SELL (bearish momentum)

    MACD Calculation:
    - MACD Line = EMA(12) - EMA(26)
    - Signal Line = EMA(9) of MACD
    - Histogram = MACD - Signal

    Parameters:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)

    Example:
        >>> strategy = MACDCross(fast_period=12, slow_period=26, signal_period=9)
        >>> # Standard MACD parameters (12, 26, 9)
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ):
        """
        Initialize MACD Cross strategy.

        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period

        Raises:
            ValueError: If fast_period >= slow_period
        """
        if fast_period >= slow_period:
            raise ValueError(f"fast_period ({fast_period}) must be < slow_period ({slow_period})")

        super().__init__({
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period
        })

        # Track previous values for crossover detection
        self.prev_macd = None
        self.prev_signal = None
        self.current_macd = None
        self.current_signal = None

    def _get_max_buffer_size(self) -> int:
        """Need enough bars for slow EMA + signal EMA."""
        return self.parameters['slow_period'] + self.parameters['signal_period'] + 50

    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Calculate MACD crossover signal.

        Args:
            market_event: New market data

        Returns:
            SignalEvent or None if insufficient data or no crossover
        """
        fast_period = self.parameters['fast_period']
        slow_period = self.parameters['slow_period']
        signal_period = self.parameters['signal_period']

        # Need enough data for MACD calculation
        min_bars = slow_period + signal_period
        if not self.has_sufficient_data(min_bars):
            return None

        # Calculate MACD and Signal Line
        macd, signal_line = self._calculate_macd(fast_period, slow_period, signal_period)

        if macd is None or signal_line is None:
            return None

        self.current_macd = macd
        self.current_signal = signal_line

        # Detect crossover (need previous values)
        signal_event = None

        if self.prev_macd is not None and self.prev_signal is not None:
            # Bullish crossover: MACD crosses above Signal
            if self.prev_macd <= self.prev_signal and macd > signal_line:
                histogram = macd - signal_line
                signal_event = SignalEvent(
                    timestamp=market_event.timestamp,
                    symbol=market_event.symbol,
                    signal_type='BUY',
                    strength=min(abs(histogram) / 10, 1.0),  # Strength based on histogram
                    metadata={
                        'macd': macd,
                        'signal_line': signal_line,
                        'histogram': histogram,
                        'crossover_type': 'bullish'
                    }
                )

            # Bearish crossover: MACD crosses below Signal
            elif self.prev_macd >= self.prev_signal and macd < signal_line:
                histogram = macd - signal_line
                signal_event = SignalEvent(
                    timestamp=market_event.timestamp,
                    symbol=market_event.symbol,
                    signal_type='SELL',
                    strength=min(abs(histogram) / 10, 1.0),
                    metadata={
                        'macd': macd,
                        'signal_line': signal_line,
                        'histogram': histogram,
                        'crossover_type': 'bearish'
                    }
                )

        # Update previous values
        self.prev_macd = macd
        self.prev_signal = signal_line

        return signal_event

    def _calculate_macd(
        self,
        fast_period: int,
        slow_period: int,
        signal_period: int
    ) -> tuple:
        """
        Calculate MACD and Signal Line.

        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period

        Returns:
            Tuple of (macd, signal_line) or (None, None)
        """
        prices = self.get_closing_prices()

        # Calculate EMAs
        fast_ema = self.calculate_ema(fast_period, prices)
        slow_ema = self.calculate_ema(slow_period, prices)

        if fast_ema is None or slow_ema is None:
            return None, None

        # MACD = Fast EMA - Slow EMA
        macd = fast_ema - slow_ema

        # Need historical MACD values for signal line
        if len(prices) < slow_period + signal_period:
            return None, None

        # Calculate MACD for all historical bars
        macd_values = []
        for i in range(slow_period, len(prices) + 1):
            hist_prices = prices[:i]
            fast = self.calculate_ema(fast_period, hist_prices)
            slow = self.calculate_ema(slow_period, hist_prices)
            if fast is not None and slow is not None:
                macd_values.append(fast - slow)

        if len(macd_values) < signal_period:
            return None, None

        # Signal Line = EMA of MACD
        signal_line = self.calculate_ema(signal_period, macd_values)

        return macd, signal_line

    def get_current_macd(self) -> Optional[dict]:
        """
        Get current MACD values (for debugging/visualization).

        Returns:
            Dict with 'macd', 'signal', 'histogram' or None
        """
        if self.current_macd is None or self.current_signal is None:
            return None

        return {
            'macd': self.current_macd,
            'signal': self.current_signal,
            'histogram': self.current_macd - self.current_signal
        }

    def __repr__(self):
        return (f"MACDCross("
                f"fast={self.parameters['fast_period']}, "
                f"slow={self.parameters['slow_period']}, "
                f"signal={self.parameters['signal_period']})")
