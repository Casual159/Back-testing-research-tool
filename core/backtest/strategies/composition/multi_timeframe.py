"""
Multi-Timeframe Data Manager

Handles data alignment across different timeframes for multi-TF strategies.

Example:
    - Primary TF: 1H (strategy execution timeframe)
    - Higher TF: 4H (trend detection)
    - Lower TF: 15M (fine-tune entry)

    For each 1H bar, we need to know:
    - Which 4H bar it belongs to (for trend)
    - Which 15M bars it contains (for entry refinement)
"""
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta


class MultiTimeframeData:
    """
    Manages OHLCV data across multiple timeframes with proper alignment.

    Handles the relationship between different timeframes:
    - 1H bar aligns with specific 4H bar (lower TF -> higher TF)
    - 4H bar contains 4 × 1H bars (higher TF -> lower TF)

    Ensures no look-ahead bias by only using data available at each timestamp.
    """

    # Timeframe hierarchy (in minutes)
    TIMEFRAME_MINUTES = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '2h': 120,
        '4h': 240,
        '6h': 360,
        '12h': 720,
        '1d': 1440,
        '1w': 10080
    }

    def __init__(self, data_dict: Dict[str, pd.DataFrame], primary_timeframe: str):
        """
        Initialize multi-timeframe data manager

        Args:
            data_dict: Dictionary mapping timeframe -> DataFrame
                       e.g., {'1h': df_1h, '4h': df_4h}
            primary_timeframe: Main timeframe for strategy execution
        """
        self.data = data_dict
        self.primary_tf = primary_timeframe
        self.primary_data = data_dict[primary_timeframe]

        # Validate timeframes
        self._validate_timeframes()

        # Pre-calculate alignment mappings for efficiency
        self._alignment_cache = {}
        self._build_alignment_cache()

    def _validate_timeframes(self):
        """Validate that all timeframes are recognized"""
        for tf in self.data.keys():
            if tf not in self.TIMEFRAME_MINUTES:
                raise ValueError(f"Unknown timeframe: {tf}. Valid: {list(self.TIMEFRAME_MINUTES.keys())}")

        # Ensure all dataframes have datetime index
        for tf, df in self.data.items():
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValueError(f"Timeframe {tf} data must have DatetimeIndex")

    def _build_alignment_cache(self):
        """
        Pre-build alignment mappings between timeframes

        For each primary TF timestamp, map to corresponding higher TF timestamps
        """
        primary_minutes = self.TIMEFRAME_MINUTES[self.primary_tf]

        for tf, df in self.data.items():
            if tf == self.primary_tf:
                continue

            tf_minutes = self.TIMEFRAME_MINUTES[tf]

            # Determine relationship
            if tf_minutes > primary_minutes:
                # Higher timeframe - map primary timestamps to higher TF bars
                self._alignment_cache[tf] = self._align_to_higher_tf(df, tf_minutes)
            else:
                # Lower timeframe - map primary timestamps to contained lower TF bars
                self._alignment_cache[tf] = self._align_to_lower_tf(df, tf_minutes)

    def _align_to_higher_tf(self, higher_df: pd.DataFrame, higher_tf_minutes: int) -> Dict[datetime, datetime]:
        """
        Align primary timeframe timestamps to higher timeframe bars

        For each primary timestamp, find which higher TF bar it belongs to.

        Example:
            Primary: 1H, Higher: 4H
            1H timestamp 13:00 -> 4H bar starting at 12:00

        Args:
            higher_df: Higher timeframe DataFrame
            higher_tf_minutes: Minutes in higher timeframe

        Returns:
            Dict mapping primary_timestamp -> higher_tf_timestamp
        """
        alignment = {}
        primary_minutes = self.TIMEFRAME_MINUTES[self.primary_tf]
        ratio = higher_tf_minutes // primary_minutes

        for primary_ts in self.primary_data.index:
            # Round down to nearest higher TF bar start
            # Example: 13:00 with 4H bars -> 12:00
            hours_since_midnight = primary_ts.hour + (primary_ts.minute / 60.0)
            higher_tf_hours = higher_tf_minutes / 60.0
            bar_number = int(hours_since_midnight / higher_tf_hours)
            higher_bar_start_hour = int(bar_number * higher_tf_hours)

            # Create timestamp for higher TF bar
            higher_ts = primary_ts.replace(
                hour=higher_bar_start_hour,
                minute=0,
                second=0,
                microsecond=0
            )

            # Find closest actual timestamp in higher_df (handle missing data)
            if higher_ts in higher_df.index:
                alignment[primary_ts] = higher_ts
            else:
                # Find most recent available bar before or at this time
                available_bars = higher_df.index[higher_df.index <= higher_ts]
                if len(available_bars) > 0:
                    alignment[primary_ts] = available_bars[-1]

        return alignment

    def _align_to_lower_tf(self, lower_df: pd.DataFrame, lower_tf_minutes: int) -> Dict[datetime, List[datetime]]:
        """
        Align primary timeframe timestamps to contained lower timeframe bars

        For each primary timestamp, find which lower TF bars it contains.

        Example:
            Primary: 1H, Lower: 15M
            1H bar 13:00-14:00 contains 15M bars: 13:00, 13:15, 13:30, 13:45

        Args:
            lower_df: Lower timeframe DataFrame
            lower_tf_minutes: Minutes in lower timeframe

        Returns:
            Dict mapping primary_timestamp -> list of lower_tf_timestamps
        """
        alignment = {}
        primary_minutes = self.TIMEFRAME_MINUTES[self.primary_tf]
        ratio = primary_minutes // lower_tf_minutes

        for primary_ts in self.primary_data.index:
            # Find all lower TF bars within this primary bar
            bar_end = primary_ts + timedelta(minutes=primary_minutes)

            # Get all lower TF bars in range [primary_ts, bar_end)
            contained_bars = lower_df.index[
                (lower_df.index >= primary_ts) &
                (lower_df.index < bar_end)
            ].tolist()

            alignment[primary_ts] = contained_bars

        return alignment

    def get_data(self, timeframe: str, primary_timestamp: datetime) -> Optional[pd.Series]:
        """
        Get aligned data for specific timeframe at primary timestamp

        Args:
            timeframe: Timeframe to get data for
            primary_timestamp: Current timestamp in primary timeframe

        Returns:
            Series with OHLCV data for the aligned bar, or None if not available
        """
        if timeframe == self.primary_tf:
            # Same timeframe - direct lookup
            if primary_timestamp in self.primary_data.index:
                return self.primary_data.loc[primary_timestamp]
            return None

        if timeframe not in self._alignment_cache:
            return None

        # Get aligned timestamp(s) from cache
        alignment = self._alignment_cache[timeframe]

        if primary_timestamp not in alignment:
            return None

        aligned_ts = alignment[primary_timestamp]

        if isinstance(aligned_ts, list):
            # Lower timeframe - return list of bars (or aggregate?)
            # For now, return the last (most recent) bar
            if aligned_ts:
                return self.data[timeframe].loc[aligned_ts[-1]]
            return None
        else:
            # Higher timeframe - return single bar
            return self.data[timeframe].loc[aligned_ts]

    def get_dataframe_slice(
        self,
        timeframe: str,
        primary_timestamp: datetime,
        lookback: int = None
    ) -> pd.DataFrame:
        """
        Get DataFrame slice for timeframe up to primary timestamp

        Useful for calculating indicators that need multiple bars.

        Args:
            timeframe: Timeframe to get data for
            primary_timestamp: Current timestamp in primary timeframe
            lookback: Number of bars to look back (None = all available)

        Returns:
            DataFrame slice up to (and including) aligned bar
        """
        df = self.data[timeframe]

        if timeframe == self.primary_tf:
            # Same timeframe
            idx = df.index.get_loc(primary_timestamp)
            if lookback:
                start_idx = max(0, idx - lookback + 1)
                return df.iloc[start_idx:idx + 1]
            return df.iloc[:idx + 1]

        # Different timeframe - use alignment
        if timeframe not in self._alignment_cache:
            return pd.DataFrame()

        alignment = self._alignment_cache[timeframe]
        if primary_timestamp not in alignment:
            return pd.DataFrame()

        aligned_ts = alignment[primary_timestamp]

        if isinstance(aligned_ts, list):
            # Lower timeframe - get up to last contained bar
            if not aligned_ts:
                return pd.DataFrame()
            end_ts = aligned_ts[-1]
        else:
            # Higher timeframe
            end_ts = aligned_ts

        idx = df.index.get_loc(end_ts)
        if lookback:
            start_idx = max(0, idx - lookback + 1)
            return df.iloc[start_idx:idx + 1]
        return df.iloc[:idx + 1]

    def get_all_timeframes(self) -> List[str]:
        """Get list of available timeframes"""
        return list(self.data.keys())

    def get_primary_timeframe(self) -> str:
        """Get primary execution timeframe"""
        return self.primary_tf

    @classmethod
    def from_single_timeframe(
        cls,
        data: pd.DataFrame,
        source_tf: str,
        target_timeframes: List[str]
    ) -> 'MultiTimeframeData':
        """
        Create multi-timeframe data by resampling from single timeframe

        Useful when you only have 1H data but need 4H for trend analysis.

        Args:
            data: Source DataFrame
            source_tf: Source timeframe (e.g., '1h')
            target_timeframes: List of timeframes to create (e.g., ['4h', '1d'])

        Returns:
            MultiTimeframeData instance

        Note: Can only create HIGHER timeframes by aggregation, not lower ones.
        """
        data_dict = {source_tf: data}

        source_minutes = cls.TIMEFRAME_MINUTES[source_tf]

        for target_tf in target_timeframes:
            target_minutes = cls.TIMEFRAME_MINUTES[target_tf]

            if target_minutes <= source_minutes:
                raise ValueError(f"Cannot create lower timeframe {target_tf} from {source_tf}")

            # Resample to higher timeframe
            rule = f'{target_minutes}min'  # e.g., '240min' for 4H
            resampled = data.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()

            data_dict[target_tf] = resampled

        return cls(data_dict, source_tf)
