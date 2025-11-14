"""
RSI Reversal Strategy.

Classic mean-reversion strategy:
- BUY when RSI < oversold_threshold (default: 30)
- SELL when RSI > overbought_threshold (default: 70)

Works best in ranging/sideways markets with high volatility.
"""

from typing import Optional
from ..events import MarketEvent, SignalEvent
from .base import Strategy


class RSIReversal(Strategy):
    """
    RSI Reversal Strategy.

    Generates signals based on RSI overbought/oversold levels:
    - RSI < 30: Oversold → potential BUY
    - RSI > 70: Overbought → potential SELL

    This is a mean-reversion strategy that profits from
    price bouncing back from extremes.

    Parameters:
        rsi_period: Period for RSI calculation (default: 14)
        oversold: RSI level considered oversold (default: 30)
        overbought: RSI level considered overbought (default: 70)

    Example:
        >>> strategy = RSIReversal(rsi_period=14, oversold=25, overbought=75)
        >>> # More aggressive thresholds (25/75)
    """

    def __init__(
        self,
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0
    ):
        """
        Initialize RSI Reversal strategy.

        Args:
            rsi_period: Period for RSI calculation
            oversold: RSI threshold for oversold (buy signal)
            overbought: RSI threshold for overbought (sell signal)

        Raises:
            ValueError: If oversold >= overbought
        """
        if oversold >= overbought:
            raise ValueError(f"oversold ({oversold}) must be < overbought ({overbought})")

        super().__init__({
            'rsi_period': rsi_period,
            'oversold': oversold,
            'overbought': overbought
        })

        self.current_rsi = None

    def _get_max_buffer_size(self) -> int:
        """Only need rsi_period + 1 bars for RSI calculation."""
        return self.parameters['rsi_period'] + 20  # Extra for smoothing

    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Calculate RSI reversal signal.

        Args:
            market_event: New market data

        Returns:
            SignalEvent or None if insufficient data or no signal
        """
        rsi_period = self.parameters['rsi_period']
        oversold = self.parameters['oversold']
        overbought = self.parameters['overbought']

        # Check if we have enough data
        if not self.has_sufficient_data(rsi_period + 1):
            return None

        # Calculate RSI
        rsi = self._calculate_rsi(rsi_period)
        if rsi is None:
            return None

        self.current_rsi = rsi

        # Generate signals based on RSI thresholds
        signal = None

        if rsi < oversold:
            # Oversold → BUY signal
            signal = SignalEvent(
                timestamp=market_event.timestamp,
                symbol=market_event.symbol,
                signal_type='BUY',
                strength=min((oversold - rsi) / oversold, 1.0),  # Stronger if more oversold
                metadata={
                    'rsi': rsi,
                    'threshold': oversold,
                    'condition': 'oversold'
                }
            )

        elif rsi > overbought:
            # Overbought → SELL signal
            signal = SignalEvent(
                timestamp=market_event.timestamp,
                symbol=market_event.symbol,
                signal_type='SELL',
                strength=min((rsi - overbought) / (100 - overbought), 1.0),
                metadata={
                    'rsi': rsi,
                    'threshold': overbought,
                    'condition': 'overbought'
                }
            )

        return signal

    def _calculate_rsi(self, period: int) -> Optional[float]:
        """
        Calculate RSI indicator.

        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss

        Args:
            period: Number of periods for RSI

        Returns:
            RSI value (0-100) or None if insufficient data
        """
        prices = self.get_closing_prices()

        if len(prices) < period + 1:
            return None

        # Calculate price changes
        changes = []
        for i in range(1, len(prices)):
            changes.append(prices[i] - prices[i-1])

        # Need at least 'period' changes
        if len(changes) < period:
            return None

        # Calculate initial average gain and loss
        gains = [max(change, 0) for change in changes[-period:]]
        losses = [abs(min(change, 0)) for change in changes[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Avoid division by zero
        if avg_loss == 0:
            return 100.0

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def get_current_rsi(self) -> Optional[float]:
        """
        Get current RSI value (for debugging/visualization).

        Returns:
            Current RSI or None if not calculated yet
        """
        return self.current_rsi

    def __repr__(self):
        return (f"RSIReversal("
                f"period={self.parameters['rsi_period']}, "
                f"oversold={self.parameters['oversold']}, "
                f"overbought={self.parameters['overbought']})")
