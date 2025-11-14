"""
Bollinger Bands Strategy.

Mean-reversion strategy using volatility bands:
- BUY when price touches or crosses below lower band
- SELL when price touches or crosses above upper band

Bollinger Bands = SMA ± (std_dev × num_std)
"""

from typing import Optional
import math
from ..events import MarketEvent, SignalEvent
from .base import Strategy


class BollingerBands(Strategy):
    """
    Bollinger Bands Mean Reversion Strategy.

    Generates signals based on price touching bands:
    - Price touches lower band → oversold → BUY
    - Price touches upper band → overbought → SELL

    Bollinger Bands Calculation:
    - Middle Band = SMA(period)
    - Upper Band = Middle Band + (std_dev × num_std)
    - Lower Band = Middle Band - (std_dev × num_std)

    Parameters:
        period: Period for SMA and std dev (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        touch_threshold: % within band to trigger (default: 0.01 = 1%)

    Example:
        >>> strategy = BollingerBands(period=20, num_std=2.0)
        >>> # Standard BB(20, 2)
    """

    def __init__(
        self,
        period: int = 20,
        num_std: float = 2.0,
        touch_threshold: float = 0.01
    ):
        """
        Initialize Bollinger Bands strategy.

        Args:
            period: Period for SMA and standard deviation
            num_std: Number of standard deviations for bands
            touch_threshold: Distance from band to trigger signal (as %)

        Raises:
            ValueError: If period < 2 or num_std <= 0
        """
        if period < 2:
            raise ValueError(f"period ({period}) must be >= 2")
        if num_std <= 0:
            raise ValueError(f"num_std ({num_std}) must be > 0")

        super().__init__({
            'period': period,
            'num_std': num_std,
            'touch_threshold': touch_threshold
        })

        self.current_bands = None

    def _get_max_buffer_size(self) -> int:
        """Need period + some extra for calculation."""
        return self.parameters['period'] + 10

    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Calculate Bollinger Bands signal.

        Args:
            market_event: New market data

        Returns:
            SignalEvent or None if insufficient data or no signal
        """
        period = self.parameters['period']
        num_std = self.parameters['num_std']
        touch_threshold = self.parameters['touch_threshold']

        # Check if we have enough data
        if not self.has_sufficient_data(period):
            return None

        # Calculate Bollinger Bands
        middle, upper, lower = self._calculate_bands(period, num_std)

        if middle is None:
            return None

        self.current_bands = {
            'middle': middle,
            'upper': upper,
            'lower': lower
        }

        # Get current price
        current_price = market_event.ohlcv['close']

        # Calculate band width (for signal strength)
        band_width = upper - lower
        price_position = (current_price - lower) / band_width  # 0 = lower, 1 = upper

        signal = None

        # Check if price touches lower band (oversold)
        lower_distance = (current_price - lower) / lower
        if lower_distance <= touch_threshold:
            # Price at or below lower band → BUY
            strength = max(0, 1 - price_position)  # Stronger if closer to/below lower band
            signal = SignalEvent(
                timestamp=market_event.timestamp,
                symbol=market_event.symbol,
                signal_type='BUY',
                strength=min(strength, 1.0),
                metadata={
                    'price': current_price,
                    'lower_band': lower,
                    'middle_band': middle,
                    'upper_band': upper,
                    'price_position': price_position,
                    'condition': 'lower_band_touch'
                }
            )

        # Check if price touches upper band (overbought)
        upper_distance = (upper - current_price) / upper
        if upper_distance <= touch_threshold:
            # Price at or above upper band → SELL
            strength = max(0, price_position)  # Stronger if closer to/above upper band
            signal = SignalEvent(
                timestamp=market_event.timestamp,
                symbol=market_event.symbol,
                signal_type='SELL',
                strength=min(strength, 1.0),
                metadata={
                    'price': current_price,
                    'lower_band': lower,
                    'middle_band': middle,
                    'upper_band': upper,
                    'price_position': price_position,
                    'condition': 'upper_band_touch'
                }
            )

        return signal

    def _calculate_bands(self, period: int, num_std: float) -> tuple:
        """
        Calculate Bollinger Bands.

        Args:
            period: Period for SMA and std dev
            num_std: Number of standard deviations

        Returns:
            Tuple of (middle_band, upper_band, lower_band) or (None, None, None)
        """
        prices = self.get_closing_prices()

        if len(prices) < period:
            return None, None, None

        # Calculate SMA (middle band)
        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period

        # Calculate standard deviation
        variance = sum((p - middle) ** 2 for p in recent_prices) / period
        std_dev = math.sqrt(variance)

        # Calculate upper and lower bands
        upper = middle + (std_dev * num_std)
        lower = middle - (std_dev * num_std)

        return middle, upper, lower

    def get_current_bands(self) -> Optional[dict]:
        """
        Get current Bollinger Bands values (for debugging/visualization).

        Returns:
            Dict with 'middle', 'upper', 'lower' or None
        """
        return self.current_bands

    def __repr__(self):
        return (f"BollingerBands("
                f"period={self.parameters['period']}, "
                f"std={self.parameters['num_std']})")
