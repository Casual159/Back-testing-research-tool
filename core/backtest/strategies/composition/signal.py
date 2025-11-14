"""
Indicator Signal - Single indicator with condition

Represents a single trading signal based on an indicator value
and a condition to evaluate.

Supports both single-timeframe and multi-timeframe data.
"""
from typing import Dict, Any, Optional, Union
import pandas as pd
import numpy as np

from .condition import Condition
from indicators.technical import TechnicalIndicators


class IndicatorSignal:
    """
    Single indicator signal with evaluation condition

    Example:
        # RSI below 30
        signal = IndicatorSignal(
            name="RSI_Oversold",
            indicator="RSI",
            parameters={'period': 14},
            condition=Condition("<", 30)
        )

        # MACD crosses above zero
        signal = IndicatorSignal(
            name="MACD_BullishCross",
            indicator="MACD",
            parameters={'fast': 12, 'slow': 26, 'signal': 9},
            condition=Condition("cross_above", 0),
            indicator_component="macd"  # Use MACD line, not signal or histogram
        )
    """

    def __init__(
        self,
        name: str,
        indicator: str,
        parameters: Dict[str, Any],
        condition: Condition,
        timeframe: str = "1h",
        indicator_component: Optional[str] = None
    ):
        """
        Initialize indicator signal

        Args:
            name: Human-readable signal name
            indicator: Indicator type (RSI, MACD, SMA, EMA, BB, ATR)
            parameters: Indicator parameters (e.g., {'period': 14})
            condition: Condition to evaluate
            timeframe: Timeframe for this signal (default: 1h)
            indicator_component: For multi-value indicators (MACD: 'macd', 'signal', 'histogram')
        """
        self.name = name
        self.indicator = indicator.upper()
        self.parameters = parameters
        self.condition = condition
        self.timeframe = timeframe
        self.indicator_component = indicator_component

        # Validate indicator
        valid_indicators = ['RSI', 'MACD', 'SMA', 'EMA', 'BB', 'ATR', 'VWAP']
        if self.indicator not in valid_indicators:
            raise ValueError(f"Unknown indicator: {indicator}. Valid: {valid_indicators}")

    def calculate_indicator(self, data: Union[pd.DataFrame, 'MultiTimeframeData']) -> pd.Series:
        """
        Calculate indicator values for given data

        Supports both single-timeframe DataFrame and MultiTimeframeData.

        Args:
            data: OHLCV DataFrame OR MultiTimeframeData instance

        Returns:
            Series of indicator values
        """
        # Import here to avoid circular dependency
        from .multi_timeframe import MultiTimeframeData

        # Handle multi-timeframe data
        if isinstance(data, MultiTimeframeData):
            # Get data for this signal's timeframe
            # Use primary timeframe's index, but get indicator data from signal's timeframe
            primary_df = data.primary_data
            result_index = primary_df.index

            # Get DataFrame slice for this timeframe
            tf_data = data.data[self.timeframe]

            # Calculate indicator on the timeframe's data
            indicator_values = self._calculate_on_dataframe(tf_data)

            # Now we need to align back to primary timeframe
            # For each primary timestamp, get the corresponding indicator value
            aligned_values = []
            for primary_ts in result_index:
                # Get the aligned data point
                aligned_data = data.get_dataframe_slice(self.timeframe, primary_ts, lookback=1)
                if len(aligned_data) > 0:
                    last_ts = aligned_data.index[-1]
                    if last_ts in indicator_values.index:
                        aligned_values.append(indicator_values.loc[last_ts])
                    else:
                        aligned_values.append(np.nan)
                else:
                    aligned_values.append(np.nan)

            return pd.Series(aligned_values, index=result_index)

        else:
            # Single DataFrame
            return self._calculate_on_dataframe(data)

    def _calculate_on_dataframe(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate indicator on a single DataFrame

        Args:
            data: OHLCV DataFrame

        Returns:
            Series of indicator values
        """
        close = data['close']

        if self.indicator == 'RSI':
            period = self.parameters.get('period', 14)
            return TechnicalIndicators.rsi(close, period=period)

        elif self.indicator == 'MACD':
            fast = self.parameters.get('fast', 12)
            slow = self.parameters.get('slow', 26)
            signal = self.parameters.get('signal', 9)
            macd_line, signal_line, histogram = TechnicalIndicators.macd(
                close, fast_period=fast, slow_period=slow, signal_period=signal
            )

            # Return requested component
            component = self.indicator_component or 'macd'
            if component == 'macd':
                return macd_line
            elif component == 'signal':
                return signal_line
            elif component == 'histogram':
                return histogram
            else:
                raise ValueError(f"MACD component '{component}' not found. Available: macd, signal, histogram")

        elif self.indicator == 'SMA':
            period = self.parameters.get('period', 20)
            return TechnicalIndicators.sma(close, period=period)

        elif self.indicator == 'EMA':
            period = self.parameters.get('period', 20)
            return TechnicalIndicators.ema(close, period=period)

        elif self.indicator == 'BB':
            period = self.parameters.get('period', 20)
            num_std = self.parameters.get('num_std', 2.0)
            upper, middle, lower = TechnicalIndicators.bollinger_bands(close, period=period, std_dev=num_std)

            # Return requested component
            component = self.indicator_component or 'middle'
            if component == 'upper':
                return upper
            elif component == 'middle':
                return middle
            elif component == 'lower':
                return lower
            else:
                raise ValueError(f"BB component '{component}' not found. Available: upper, middle, lower")

        elif self.indicator == 'ATR':
            period = self.parameters.get('period', 14)
            return TechnicalIndicators.atr(data['high'], data['low'], data['close'], period=period)

        elif self.indicator == 'VWAP':
            # VWAP = (Typical Price * Volume) / Cumulative Volume
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            return (typical_price * data['volume']).cumsum() / data['volume'].cumsum()

        else:
            raise ValueError(f"Unsupported indicator: {self.indicator}")

    def evaluate(
        self,
        data: pd.DataFrame,
        index: Optional[int] = None
    ) -> bool:
        """
        Evaluate signal at specific point in time

        Args:
            data: OHLCV DataFrame (must be calculated beforehand)
            index: Index to evaluate at (default: last row)

        Returns:
            True if signal condition is met, False otherwise
        """
        if index is None:
            index = len(data) - 1

        # Calculate indicator
        indicator_values = self.calculate_indicator(data)

        # Get current and previous values
        current_value = indicator_values.iloc[index]
        previous_value = indicator_values.iloc[index - 1] if index > 0 else None

        # Evaluate condition
        return self.condition.evaluate(current_value, previous_value)

    def evaluate_series(self, data: pd.DataFrame) -> pd.Series:
        """
        Evaluate signal for entire series

        Args:
            data: OHLCV DataFrame

        Returns:
            Boolean series indicating where signal is active
        """
        # Calculate indicator
        indicator_values = self.calculate_indicator(data)

        # Evaluate condition for series
        return self.condition.evaluate_series(indicator_values)

    def __str__(self) -> str:
        """String representation"""
        component_str = f".{self.indicator_component}" if self.indicator_component else ""
        params_str = ", ".join(f"{k}={v}" for k, v in self.parameters.items())
        return f"{self.name}: {self.indicator}{component_str}({params_str}) {self.condition}"

    def __repr__(self) -> str:
        return f"IndicatorSignal({self.name}, {self.indicator}, {self.condition})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'indicator': self.indicator,
            'parameters': self.parameters,
            'condition': {
                'operator': self.condition.operator.value,
                'threshold': self.condition.threshold,
                'threshold2': self.condition.threshold2
            },
            'timeframe': self.timeframe,
            'indicator_component': self.indicator_component
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndicatorSignal':
        """Create from dictionary"""
        condition = Condition(
            operator=data['condition']['operator'],
            threshold=data['condition']['threshold'],
            threshold2=data['condition'].get('threshold2')
        )

        return cls(
            name=data['name'],
            indicator=data['indicator'],
            parameters=data['parameters'],
            condition=condition,
            timeframe=data.get('timeframe', '1h'),
            indicator_component=data.get('indicator_component')
        )
