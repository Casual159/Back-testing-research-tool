"""
Base strategy class for backtesting.

All trading strategies must inherit from Strategy and implement
the calculate_signals() method.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from ..events import MarketEvent, SignalEvent


class Strategy(ABC):
    """
    Abstract base class for trading strategies.

    Strategies receive MarketEvents and generate SignalEvents based on
    their trading logic. Each strategy maintains a buffer of recent
    market data for indicator calculations.

    Attributes:
        parameters: Strategy-specific parameters (e.g., periods, thresholds)
        data_buffer: Recent MarketEvents for calculation
        name: Human-readable strategy name
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialize strategy.

        Args:
            parameters: Dict of strategy parameters
        """
        self.parameters = parameters or {}
        self.data_buffer: List[MarketEvent] = []
        self.name = self.get_name()

    @abstractmethod
    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Generate trading signal from market data.

        This method is called for each new bar. It should analyze the
        market data and return a SignalEvent or None.

        Args:
            market_event: New market data

        Returns:
            SignalEvent (BUY/SELL/HOLD) or None if no signal
        """
        pass

    def add_market_data(self, market_event: MarketEvent):
        """
        Add new market data to buffer.

        Args:
            market_event: New market data to store
        """
        self.data_buffer.append(market_event)

        # Optional: Limit buffer size to prevent memory issues
        # Keep only last N bars needed for calculations
        max_buffer_size = self._get_max_buffer_size()
        if len(self.data_buffer) > max_buffer_size:
            self.data_buffer = self.data_buffer[-max_buffer_size:]

    def _get_max_buffer_size(self) -> int:
        """
        Calculate maximum buffer size needed.

        Override in subclass if you know the exact requirement.
        Default keeps 500 bars (enough for most indicators).

        Returns:
            Maximum number of bars to keep in buffer
        """
        return 500

    def get_name(self) -> str:
        """
        Get strategy name.

        Returns:
            Strategy class name (can be overridden for custom names)
        """
        return self.__class__.__name__

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.parameters

    def has_sufficient_data(self, required_bars: int) -> bool:
        """
        Check if buffer has enough data for calculations.

        Args:
            required_bars: Minimum bars needed

        Returns:
            True if sufficient data available
        """
        return len(self.data_buffer) >= required_bars

    def get_closing_prices(self, lookback: int = None) -> List[float]:
        """
        Extract closing prices from buffer.

        Args:
            lookback: Number of recent prices to return (None = all)

        Returns:
            List of closing prices (most recent last)
        """
        if lookback:
            return [bar.ohlcv['close'] for bar in self.data_buffer[-lookback:]]
        return [bar.ohlcv['close'] for bar in self.data_buffer]

    def get_high_prices(self, lookback: int = None) -> List[float]:
        """Extract high prices from buffer."""
        if lookback:
            return [bar.ohlcv['high'] for bar in self.data_buffer[-lookback:]]
        return [bar.ohlcv['high'] for bar in self.data_buffer]

    def get_low_prices(self, lookback: int = None) -> List[float]:
        """Extract low prices from buffer."""
        if lookback:
            return [bar.ohlcv['low'] for bar in self.data_buffer[-lookback:]]
        return [bar.ohlcv['low'] for bar in self.data_buffer]

    def get_volumes(self, lookback: int = None) -> List[float]:
        """Extract volumes from buffer."""
        if lookback:
            return [bar.ohlcv['volume'] for bar in self.data_buffer[-lookback:]]
        return [bar.ohlcv['volume'] for bar in self.data_buffer]

    def calculate_sma(self, period: int, prices: List[float] = None) -> Optional[float]:
        """
        Calculate Simple Moving Average.

        Args:
            period: Number of periods
            prices: List of prices (None = use closing prices from buffer)

        Returns:
            SMA value or None if insufficient data
        """
        if prices is None:
            prices = self.get_closing_prices()

        if len(prices) < period:
            return None

        return sum(prices[-period:]) / period

    def calculate_ema(self, period: int, prices: List[float] = None) -> Optional[float]:
        """
        Calculate Exponential Moving Average.

        Args:
            period: Number of periods
            prices: List of prices (None = use closing prices from buffer)

        Returns:
            EMA value or None if insufficient data
        """
        if prices is None:
            prices = self.get_closing_prices()

        if len(prices) < period:
            return None

        # Use SMA as initial EMA
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return ema

    def __repr__(self):
        return f"{self.name}({self.parameters})"
