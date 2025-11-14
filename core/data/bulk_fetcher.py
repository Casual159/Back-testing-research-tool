"""
Binance Public Data Bulk Fetcher
Downloads historical data from data.binance.vision (no API limits)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path
import requests
import zipfile
import io
import pandas as pd
from dateutil.relativedelta import relativedelta

from config import DataConfig

logger = logging.getLogger(__name__)


class BinanceBulkFetcher:
    """
    Fetches historical klines data from Binance Public Data repository

    Primary source for historical data (no API limits, fast downloads)
    Data availability: From inception (~2017) to ~2 days ago
    """

    BASE_URL = "https://data.binance.vision/data/spot"

    # Public data has ~2 day lag (today's data available in 2 days)
    PUBLIC_DATA_LAG_DAYS = 2

    def __init__(self):
        """Initialize bulk fetcher"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoAnalyzer/1.0'
        })

    @staticmethod
    def get_public_data_cutoff() -> datetime:
        """
        Get the cutoff date for public data availability

        Returns:
            datetime: Last date for which public data is available (now - 2 days)
        """
        return datetime.now() - timedelta(days=BinanceBulkFetcher.PUBLIC_DATA_LAG_DAYS)

    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch historical klines data from public data repository

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '1h', '1d')
            start_date: Start date for data
            end_date: End date for data (defaults to public data cutoff)

        Returns:
            DataFrame with OHLCV data
        """
        if end_date is None:
            end_date = self.get_public_data_cutoff()
        else:
            # Ensure we don't try to fetch beyond what's available
            cutoff = self.get_public_data_cutoff()
            if end_date > cutoff:
                logger.warning(
                    f"End date {end_date} is beyond public data availability. "
                    f"Using cutoff: {cutoff}"
                )
                end_date = cutoff

        logger.info(
            f"Fetching {symbol} {timeframe} from {start_date.date()} to {end_date.date()} "
            f"via Binance Public Data"
        )

        # Strategy: Use monthly files for long ranges, daily for short ranges
        all_data = []

        days_requested = (end_date - start_date).days

        if days_requested <= 31:
            # Short range: use daily files
            logger.debug(f"Using daily files for {days_requested} days range")
            current = start_date
            while current <= end_date:
                date_str = current.strftime('%Y-%m-%d')
                try:
                    df = self._download_daily_file(symbol, timeframe, date_str)
                    if not df.empty:
                        all_data.append(df)
                        logger.debug(f"Downloaded {date_str}: {len(df)} candles")
                except Exception as e:
                    logger.debug(f"Daily file {date_str} not available: {e}")
                current += timedelta(days=1)
        else:
            # Long range: use monthly files + daily for partial months
            logger.debug(f"Using monthly+daily files for {days_requested} days range")
            # Phase 1: Monthly files (fast, bulk download)
            monthly_data = self._fetch_monthly_range(symbol, timeframe, start_date, end_date)
            if not monthly_data.empty:
                all_data.append(monthly_data)

            # Phase 2: Daily files for partial months
            daily_data = self._fetch_daily_range(symbol, timeframe, start_date, end_date)
            if not daily_data.empty:
                all_data.append(daily_data)

        # Combine and deduplicate
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            # Remove duplicates (monthly and daily might overlap)
            combined = combined.drop_duplicates(subset=['open_time'])
            # Filter to exact date range
            combined = combined[
                (combined['open_time'] >= start_date) &
                (combined['open_time'] <= end_date)
            ]
            combined = combined.sort_values('open_time').reset_index(drop=True)
            logger.info(f"Fetched {len(combined)} candles from public data")
            return combined
        else:
            logger.warning("No data fetched from public repository")
            return pd.DataFrame()

    def _fetch_monthly_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch monthly aggregated files"""
        all_data = []

        # Generate list of months to fetch
        current = datetime(start_date.year, start_date.month, 1)
        end_month = datetime(end_date.year, end_date.month, 1)

        # Fetch all complete months
        while current < end_month:
            year_month = current.strftime('%Y-%m')

            try:
                df = self._download_monthly_file(symbol, timeframe, year_month)
                if not df.empty:
                    all_data.append(df)
                    logger.debug(f"Downloaded {year_month}: {len(df)} candles")
            except Exception as e:
                logger.warning(f"Failed to download {year_month}: {e}")

            current += relativedelta(months=1)

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

    def _fetch_daily_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch daily files for partial months"""
        all_data = []

        # Fetch daily files for incomplete months at start and end of range
        # Start of range: from start_date to end of start month
        start_month_end = datetime(start_date.year, start_date.month, 1) + relativedelta(months=1) - timedelta(days=1)
        if start_date.day > 1 and start_date <= min(end_date, start_month_end):
            current = start_date
            while current <= min(end_date, start_month_end):
                date_str = current.strftime('%Y-%m-%d')
                try:
                    df = self._download_daily_file(symbol, timeframe, date_str)
                    if not df.empty:
                        all_data.append(df)
                        logger.debug(f"Downloaded {date_str}: {len(df)} candles")
                except Exception as e:
                    logger.debug(f"Daily file {date_str} not available: {e}")
                current += timedelta(days=1)

        # End of range: from start of end month to end_date
        end_month_start = datetime(end_date.year, end_date.month, 1)
        if end_date >= end_month_start and start_date < end_month_start:
            current = end_month_start

            while current <= end_date:
                date_str = current.strftime('%Y-%m-%d')

                try:
                    df = self._download_daily_file(symbol, timeframe, date_str)
                    if not df.empty:
                        all_data.append(df)
                        logger.debug(f"Downloaded {date_str}: {len(df)} candles")
                except Exception as e:
                    logger.debug(f"Daily file {date_str} not available: {e}")

                current += timedelta(days=1)

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

    def _download_monthly_file(
        self,
        symbol: str,
        timeframe: str,
        year_month: str
    ) -> pd.DataFrame:
        """
        Download and parse a single monthly file

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '1h')
            year_month: Year-month string (e.g., '2024-10')

        Returns:
            DataFrame with OHLCV data
        """
        url = f"{self.BASE_URL}/monthly/klines/{symbol}/{timeframe}/{symbol}-{timeframe}-{year_month}.zip"
        return self._download_and_parse_zip(url)

    def _download_daily_file(
        self,
        symbol: str,
        timeframe: str,
        date: str
    ) -> pd.DataFrame:
        """
        Download and parse a single daily file

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '1h')
            date: Date string (e.g., '2024-10-15')

        Returns:
            DataFrame with OHLCV data
        """
        url = f"{self.BASE_URL}/daily/klines/{symbol}/{timeframe}/{symbol}-{timeframe}-{date}.zip"
        return self._download_and_parse_zip(url)

    def _download_and_parse_zip(self, url: str) -> pd.DataFrame:
        """
        Download ZIP file and parse CSV contents

        Args:
            url: URL to ZIP file

        Returns:
            DataFrame with OHLCV data
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Extract ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                # Should contain one CSV file
                csv_filename = zf.namelist()[0]
                with zf.open(csv_filename) as csv_file:
                    df = self._parse_csv(csv_file)
                    return df

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # File doesn't exist (normal for recent dates)
                return pd.DataFrame()
            raise
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            raise

    def _parse_csv(self, csv_file) -> pd.DataFrame:
        """
        Parse Binance public data CSV format

        CSV columns:
        open_time, open, high, low, close, volume, close_time,
        quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore

        NOTE: Since 2025-01-01, timestamps are in MICROSECONDS (not milliseconds!)
        """
        df = pd.read_csv(
            csv_file,
            names=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'count',
                'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
            ],
            dtype={
                'open_time': 'int64',
                'open': 'float64',
                'high': 'float64',
                'low': 'float64',
                'close': 'float64',
                'volume': 'float64',
                'close_time': 'int64',
                'quote_volume': 'float64',
                'count': 'int64',
                'taker_buy_volume': 'float64',
                'taker_buy_quote_volume': 'float64',
                'ignore': 'int64'
            }
        )

        # Convert timestamps
        # Check if timestamp is in microseconds (16 digits) or milliseconds (13 digits)
        if df['open_time'].iloc[0] > 1e15:
            # Microseconds (since 2025-01-01)
            df['open_time'] = pd.to_datetime(df['open_time'], unit='us')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='us')
        else:
            # Milliseconds (before 2025-01-01)
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

        # Drop unnecessary columns
        df = df.drop(columns=['close_time', 'ignore'])

        return df

    def check_data_availability(
        self,
        symbol: str,
        timeframe: str,
        date: datetime
    ) -> bool:
        """
        Check if data is available for a specific date

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            date: Date to check

        Returns:
            True if data is available, False otherwise
        """
        cutoff = self.get_public_data_cutoff()
        return date <= cutoff
