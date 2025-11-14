"""
Binance data fetcher module
Handles downloading historical OHLCV data from Binance API
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from binance.client import Client
from tqdm import tqdm

from config import DataConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BinanceDataFetcher:
    """Fetches historical OHLCV data from Binance"""

    # Binance timeframe mapping
    TIMEFRAME_MAP = {
        '1m': Client.KLINE_INTERVAL_1MINUTE,
        '3m': Client.KLINE_INTERVAL_3MINUTE,
        '5m': Client.KLINE_INTERVAL_5MINUTE,
        '15m': Client.KLINE_INTERVAL_15MINUTE,
        '30m': Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR,
        '2h': Client.KLINE_INTERVAL_2HOUR,
        '4h': Client.KLINE_INTERVAL_4HOUR,
        '6h': Client.KLINE_INTERVAL_6HOUR,
        '8h': Client.KLINE_INTERVAL_8HOUR,
        '12h': Client.KLINE_INTERVAL_12HOUR,
        '1d': Client.KLINE_INTERVAL_1DAY,
        '3d': Client.KLINE_INTERVAL_3DAY,
        '1w': Client.KLINE_INTERVAL_1WEEK,
        '1M': Client.KLINE_INTERVAL_1MONTH,
    }

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True
    ):
        """
        Initialize Binance client

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default True)
        """
        self.testnet = testnet

        if testnet:
            self.client = Client(
                api_key,
                api_secret,
                testnet=True
            )
            # Set testnet URL
            self.client.API_URL = 'https://testnet.binance.vision/api'
            logger.info("Initialized Binance client (TESTNET)")
        else:
            self.client = Client(api_key, api_secret)
            logger.info("Initialized Binance client (LIVE)")

        self.request_delay = DataConfig.BINANCE_REQUEST_DELAY
        self.max_retries = DataConfig.MAX_RETRIES
        self.max_candles = DataConfig.MAX_CANDLES_PER_REQUEST

    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Binance

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '1h', '1d')
            start_date: Start datetime
            end_date: End datetime (default: now)

        Returns:
            DataFrame with columns: open_time, open, high, low, close, volume,
                                   close_time, quote_volume, trades
        """
        if timeframe not in self.TIMEFRAME_MAP:
            raise ValueError(f"Invalid timeframe: {timeframe}")

        if end_date is None:
            end_date = datetime.now()

        logger.info(f"Fetching {symbol} {timeframe} from {start_date} to {end_date}")

        # Convert to milliseconds
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        # Calculate expected number of candles for progress bar
        expected_candles = self._calculate_expected_candles(
            start_date, end_date, timeframe
        )

        all_candles = []
        current_start = start_ms

        # Progress bar
        with tqdm(total=expected_candles, desc=f"{symbol} {timeframe}") as pbar:
            while current_start < end_ms:
                # Fetch batch with retry logic
                candles = self._fetch_batch_with_retry(
                    symbol,
                    timeframe,
                    current_start,
                    end_ms
                )

                if not candles:
                    break

                all_candles.extend(candles)
                pbar.update(len(candles))

                # Update start time for next batch
                current_start = candles[-1][0] + 1

                # Rate limiting
                time.sleep(self.request_delay)

        # Convert to DataFrame
        df = self._candles_to_dataframe(all_candles)

        logger.info(f"Fetched {len(df)} candles for {symbol} {timeframe}")

        return df

    def _fetch_batch_with_retry(
        self,
        symbol: str,
        timeframe: str,
        start_ms: int,
        end_ms: int
    ) -> list:
        """
        Fetch a single batch of candles with retry logic

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            start_ms: Start timestamp in milliseconds
            end_ms: End timestamp in milliseconds

        Returns:
            List of candle data
        """
        interval = self.TIMEFRAME_MAP[timeframe]

        for attempt in range(self.max_retries):
            try:
                candles = self.client.get_klines(
                    symbol=symbol,
                    interval=interval,
                    startTime=start_ms,
                    endTime=end_ms,
                    limit=self.max_candles
                )
                return candles

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch batch after {self.max_retries} attempts")
                    raise

        return []

    def _candles_to_dataframe(self, candles: list) -> pd.DataFrame:
        """
        Convert raw candle data to DataFrame

        Binance kline format:
        [
            [
                1499040000000,      # 0: Open time
                "0.01634000",       # 1: Open
                "0.80000000",       # 2: High
                "0.01575800",       # 3: Low
                "0.01577100",       # 4: Close
                "148976.11427815",  # 5: Volume
                1499644799999,      # 6: Close time
                "2434.19055334",    # 7: Quote asset volume
                308,                # 8: Number of trades
                "1756.87402397",    # 9: Taker buy base asset volume
                "28.46694368",      # 10: Taker buy quote asset volume
                "17928899.62484339" # 11: Ignore
            ]
        ]

        Args:
            candles: Raw candle data from Binance API

        Returns:
            DataFrame with parsed candle data
        """
        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame(candles, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # Convert timestamps to datetime
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

        # Convert price/volume to float
        for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
            df[col] = df[col].astype(float)

        # Convert trades to int
        df['trades'] = df['trades'].astype(int)

        # Drop unnecessary columns
        df = df.drop(['taker_buy_base', 'taker_buy_quote', 'ignore'], axis=1)

        return df

    def _calculate_expected_candles(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> int:
        """
        Calculate expected number of candles

        Args:
            start_date: Start datetime
            end_date: End datetime
            timeframe: Timeframe

        Returns:
            Estimated number of candles
        """
        delta = end_date - start_date
        total_minutes = delta.total_seconds() / 60

        # Timeframe to minutes mapping
        timeframe_minutes = {
            '1m': 1,
            '3m': 3,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '2h': 120,
            '4h': 240,
            '6h': 360,
            '8h': 480,
            '12h': 720,
            '1d': 1440,
            '3d': 4320,
            '1w': 10080,
            '1M': 43200,  # Approximate
        }

        if timeframe not in timeframe_minutes:
            return 1000  # Default estimate

        return int(total_minutes / timeframe_minutes[timeframe])

    def get_server_time(self) -> datetime:
        """
        Get Binance server time

        Returns:
            Server datetime
        """
        server_time = self.client.get_server_time()
        return datetime.fromtimestamp(server_time['serverTime'] / 1000)

    def test_connection(self) -> bool:
        """
        Test connection to Binance API

        Returns:
            True if successful, False otherwise
        """
        try:
            server_time = self.get_server_time()
            logger.info(f"Connected to Binance. Server time: {server_time}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            return False
