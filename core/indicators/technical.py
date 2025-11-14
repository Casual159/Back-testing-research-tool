"""
Technical indicators module
Implements common trading indicators: RSI, MACD, MA, EMA, Bollinger Bands, ATR
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional


class TechnicalIndicators:
    """Calculate technical indicators for trading analysis"""

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """
        Simple Moving Average

        Args:
            data: Price series (typically close prices)
            period: Number of periods

        Returns:
            Series with SMA values
        """
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average

        Args:
            data: Price series (typically close prices)
            period: Number of periods

        Returns:
            Series with EMA values
        """
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index

        Args:
            data: Price series (typically close prices)
            period: Number of periods (default: 14)

        Returns:
            Series with RSI values (0-100)
        """
        # Calculate price changes
        delta = data.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def macd(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence

        Args:
            data: Price series (typically close prices)
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        # Calculate MACD line
        ema_fast = TechnicalIndicators.ema(data, fast_period)
        ema_slow = TechnicalIndicators.ema(data, slow_period)
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)

        # Calculate histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands

        Args:
            data: Price series (typically close prices)
            period: Moving average period (default: 20)
            std_dev: Number of standard deviations (default: 2.0)

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        # Calculate middle band (SMA)
        middle_band = TechnicalIndicators.sma(data, period)

        # Calculate standard deviation
        rolling_std = data.rolling(window=period).std()

        # Calculate upper and lower bands
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)

        return upper_band, middle_band, lower_band

    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Average True Range

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Number of periods (default: 14)

        Returns:
            Series with ATR values
        """
        # Calculate True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        # True Range is the maximum of the three
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR as moving average of True Range
        atr = tr.rolling(window=period).mean()

        return atr

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default: 14)
            smooth_k: %K smoothing period (default: 3)
            smooth_d: %D smoothing period (default: 3)

        Returns:
            Tuple of (%K, %D)
        """
        # Calculate %K
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low)

        # Smooth %K
        k = k.rolling(window=smooth_k).mean()

        # Calculate %D (moving average of %K)
        d = k.rolling(window=smooth_d).mean()

        return k, d

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume

        Args:
            close: Close prices
            volume: Volume

        Returns:
            Series with OBV values
        """
        # Determine direction
        direction = np.sign(close.diff())

        # Calculate OBV
        obv = (direction * volume).cumsum()

        return obv

    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        Volume Weighted Average Price

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume

        Returns:
            Series with VWAP values
        """
        # Calculate typical price
        typical_price = (high + low + close) / 3

        # Calculate VWAP
        vwap = (typical_price * volume).cumsum() / volume.cumsum()

        return vwap


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all common indicators to a dataframe

    Args:
        df: DataFrame with OHLCV data
            Required columns: open, high, low, close, volume

    Returns:
        DataFrame with added indicator columns
    """
    result = df.copy()

    # Moving Averages
    result['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
    result['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
    result['sma_200'] = TechnicalIndicators.sma(df['close'], 200)

    result['ema_12'] = TechnicalIndicators.ema(df['close'], 12)
    result['ema_26'] = TechnicalIndicators.ema(df['close'], 26)

    # RSI
    result['rsi'] = TechnicalIndicators.rsi(df['close'])

    # MACD
    macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'])
    result['macd'] = macd_line
    result['macd_signal'] = signal_line
    result['macd_histogram'] = histogram

    # Bollinger Bands
    upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'])
    result['bb_upper'] = upper
    result['bb_middle'] = middle
    result['bb_lower'] = lower

    # ATR
    result['atr'] = TechnicalIndicators.atr(df['high'], df['low'], df['close'])

    # Stochastic
    k, d = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
    result['stoch_k'] = k
    result['stoch_d'] = d

    # OBV
    result['obv'] = TechnicalIndicators.obv(df['close'], df['volume'])

    # VWAP
    result['vwap'] = TechnicalIndicators.vwap(
        df['high'], df['low'], df['close'], df['volume']
    )

    return result


def calculate_indicators(
    df: pd.DataFrame,
    indicators: Optional[list] = None
) -> pd.DataFrame:
    """
    Calculate specific indicators

    Args:
        df: DataFrame with OHLCV data
        indicators: List of indicator names to calculate
                   If None, calculates all indicators

    Returns:
        DataFrame with added indicator columns

    Available indicators:
        - 'sma_20', 'sma_50', 'sma_200'
        - 'ema_12', 'ema_26'
        - 'rsi'
        - 'macd'
        - 'bollinger'
        - 'atr'
        - 'stochastic'
        - 'obv'
        - 'vwap'
    """
    if indicators is None:
        return add_all_indicators(df)

    result = df.copy()

    for indicator in indicators:
        if indicator == 'sma_20':
            result['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        elif indicator == 'sma_50':
            result['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
        elif indicator == 'sma_200':
            result['sma_200'] = TechnicalIndicators.sma(df['close'], 200)
        elif indicator == 'ema_12':
            result['ema_12'] = TechnicalIndicators.ema(df['close'], 12)
        elif indicator == 'ema_26':
            result['ema_26'] = TechnicalIndicators.ema(df['close'], 26)
        elif indicator == 'rsi':
            result['rsi'] = TechnicalIndicators.rsi(df['close'])
        elif indicator == 'macd':
            macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'])
            result['macd'] = macd_line
            result['macd_signal'] = signal_line
            result['macd_histogram'] = histogram
        elif indicator == 'bollinger':
            upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'])
            result['bb_upper'] = upper
            result['bb_middle'] = middle
            result['bb_lower'] = lower
        elif indicator == 'atr':
            result['atr'] = TechnicalIndicators.atr(df['high'], df['low'], df['close'])
        elif indicator == 'stochastic':
            k, d = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
            result['stoch_k'] = k
            result['stoch_d'] = d
        elif indicator == 'obv':
            result['obv'] = TechnicalIndicators.obv(df['close'], df['volume'])
        elif indicator == 'vwap':
            result['vwap'] = TechnicalIndicators.vwap(
                df['high'], df['low'], df['close'], df['volume']
            )

    return result
