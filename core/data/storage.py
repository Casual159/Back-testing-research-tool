"""
PostgreSQL storage module for OHLCV candle data
Handles database connection, schema creation, and data operations
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgresStorage:
    """PostgreSQL storage for OHLCV candle data"""

    def __init__(self, config: Dict[str, any]):
        """
        Initialize PostgreSQL connection

        Args:
            config: Dictionary with keys: host, port, database, user, password
        """
        self.config = config
        self.conn = None
        self.cursor = None

    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL

        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to PostgreSQL at {self.config['host']}:{self.config['port']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Disconnected from PostgreSQL")

    def create_tables(self):
        """Create candles table if it doesn't exist"""
        if not self.conn:
            self.connect()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS candles (
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            open_time TIMESTAMP NOT NULL,
            open DECIMAL(20, 8) NOT NULL,
            high DECIMAL(20, 8) NOT NULL,
            low DECIMAL(20, 8) NOT NULL,
            close DECIMAL(20, 8) NOT NULL,
            volume DECIMAL(20, 8) NOT NULL,
            close_time TIMESTAMP NOT NULL,
            quote_volume DECIMAL(20, 8),
            trades INTEGER,
            PRIMARY KEY (symbol, timeframe, open_time)
        );
        """

        create_index_query = """
        CREATE INDEX IF NOT EXISTS idx_candles_lookup
        ON candles(symbol, timeframe, open_time DESC);
        """

        try:
            self.cursor.execute(create_table_query)
            self.cursor.execute(create_index_query)
            self.conn.commit()
            logger.info("Tables and indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            self.conn.rollback()
            raise

    def insert_candles(self, df: pd.DataFrame, symbol: str, timeframe: str) -> int:
        """
        Insert candles into database with deduplication

        Args:
            df: DataFrame with columns: open_time, open, high, low, close, volume,
                close_time, quote_volume, trades
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '1h', '1d')

        Returns:
            Number of rows inserted
        """
        if not self.conn:
            self.connect()

        if df.empty:
            logger.warning("Empty DataFrame, nothing to insert")
            return 0

        # Prepare data for insertion
        data = [
            (
                symbol,
                timeframe,
                row['open_time'],
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume']),
                row['close_time'],
                float(row.get('quote_volume', 0)),
                int(row.get('count', row.get('trades', 0)))  # 'count' from bulk_fetcher, 'trades' from API fetcher
            )
            for _, row in df.iterrows()
        ]

        insert_query = """
        INSERT INTO candles (
            symbol, timeframe, open_time, open, high, low, close,
            volume, close_time, quote_volume, trades
        ) VALUES %s
        ON CONFLICT (symbol, timeframe, open_time) DO NOTHING
        """

        try:
            execute_values(self.cursor, insert_query, data)
            self.conn.commit()
            inserted = self.cursor.rowcount
            logger.info(f"Inserted {inserted} new candles for {symbol} {timeframe}")
            return inserted
        except Exception as e:
            logger.error(f"Failed to insert candles: {e}")
            self.conn.rollback()
            raise

    def query_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime
    ) -> pd.DataFrame:
        """
        Query candles from database

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            start: Start datetime
            end: End datetime

        Returns:
            DataFrame with candle data
        """
        if not self.conn:
            self.connect()

        query = """
        SELECT open_time, open, high, low, close, volume,
               close_time, quote_volume, trades
        FROM candles
        WHERE symbol = %s
          AND timeframe = %s
          AND open_time >= %s
          AND open_time <= %s
        ORDER BY open_time ASC
        """

        try:
            df = pd.read_sql_query(
                query,
                self.conn,
                params=(symbol, timeframe, start, end)
            )
            logger.info(f"Queried {len(df)} candles for {symbol} {timeframe}")
            return df
        except Exception as e:
            logger.error(f"Failed to query candles: {e}")
            raise

    def get_available_data_range(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Get the date range of available data for a symbol/timeframe

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            Tuple of (start_date, end_date) or None if no data
        """
        if not self.conn:
            self.connect()

        query = """
        SELECT MIN(open_time) as start_date, MAX(open_time) as end_date
        FROM candles
        WHERE symbol = %s AND timeframe = %s
        """

        try:
            self.cursor.execute(query, (symbol, timeframe))
            result = self.cursor.fetchone()

            if result and result[0]:
                return (result[0], result[1])
            return None
        except Exception as e:
            logger.error(f"Failed to get data range: {e}")
            raise

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get candles for a symbol/timeframe with optional date range

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            start_time: Optional start datetime (inclusive)
            end_time: Optional end datetime (inclusive)

        Returns:
            DataFrame with candle data ordered by time
        """
        if not self.conn:
            self.connect()

        # Build query with optional date filters
        query = """
        SELECT open_time, open, high, low, close, volume,
               close_time, quote_volume, trades
        FROM candles
        WHERE symbol = %s AND timeframe = %s
        """
        params = [symbol, timeframe]

        if start_time:
            query += " AND open_time >= %s"
            params.append(start_time)

        if end_time:
            query += " AND open_time <= %s"
            params.append(end_time)

        query += " ORDER BY open_time ASC"

        try:
            df = pd.read_sql_query(query, self.conn, params=tuple(params))
            logger.info(f"Retrieved {len(df)} candles for {symbol} {timeframe}")
            return df
        except Exception as e:
            logger.error(f"Failed to get candles: {e}")
            raise

    def delete_candles(self, symbol: str, timeframe: str) -> int:
        """
        Delete all candles for a symbol/timeframe

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            Number of rows deleted
        """
        if not self.conn:
            self.connect()

        query = """
        DELETE FROM candles
        WHERE symbol = %s AND timeframe = %s
        """

        try:
            self.cursor.execute(query, (symbol, timeframe))
            self.conn.commit()
            deleted = self.cursor.rowcount
            logger.info(f"Deleted {deleted} candles for {symbol} {timeframe}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete candles: {e}")
            self.conn.rollback()
            raise

    def get_data_stats(self) -> pd.DataFrame:
        """
        Get statistics about stored data

        Returns:
            DataFrame with stats per symbol/timeframe
        """
        if not self.conn:
            self.connect()

        query = """
        SELECT
            symbol,
            timeframe,
            COUNT(*) as candle_count,
            MIN(open_time) as first_candle,
            MAX(open_time) as last_candle
        FROM candles
        GROUP BY symbol, timeframe
        ORDER BY symbol, timeframe
        """

        try:
            df = pd.read_sql_query(query, self.conn)

            # Print formatted stats
            print("\n" + "="*80)
            print("=" + " DATABASE STATISTICS")
            print("="*80)

            for _, row in df.iterrows():
                print(f"\n{row['symbol']} - {row['timeframe']}")
                print(f"  Candles: {row['candle_count']:,}")
                print(f"  Range: {row['first_candle']} -> {row['last_candle']}")

            print("\n" + "="*80)

            return df
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise

    # =========================================================================
    # MARKET REGIMES METHODS
    # =========================================================================

    def insert_regimes(
        self,
        symbol: str,
        timeframe: str,
        regimes_df: pd.DataFrame,
        classifier_version: str = 'v1.0'
    ) -> int:
        """
        Insert regime data for a symbol/timeframe.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            regimes_df: DataFrame with regime data (must have regime columns)
            classifier_version: Version of classifier used

        Returns:
            Number of rows inserted
        """
        if not self.conn:
            self.connect()

        # Prepare data for insertion
        # Reset index to ensure we have datetime in a column
        df_reset = regimes_df.reset_index()

        data = []
        for _, row in df_reset.iterrows():
            # Get timestamp - could be 'open_time' or 'index' depending on reset_index
            timestamp = row.get('open_time') or row.get('index')

            data.append((
                symbol,
                timeframe,
                timestamp,
                row.get('trend_state'),
                row.get('volatility_state'),
                row.get('momentum_state'),
                row.get('full_regime'),
                row.get('simplified_regime'),
                row.get('regime_confidence'),
                classifier_version
            ))

        # Insert with ON CONFLICT to handle duplicates
        insert_query = """
        INSERT INTO market_regimes (
            symbol, timeframe, open_time,
            trend_state, volatility_state, momentum_state,
            full_regime, simplified_regime, confidence,
            classifier_version
        )
        VALUES %s
        ON CONFLICT (symbol, timeframe, open_time)
        DO UPDATE SET
            trend_state = EXCLUDED.trend_state,
            volatility_state = EXCLUDED.volatility_state,
            momentum_state = EXCLUDED.momentum_state,
            full_regime = EXCLUDED.full_regime,
            simplified_regime = EXCLUDED.simplified_regime,
            confidence = EXCLUDED.confidence,
            classifier_version = EXCLUDED.classifier_version,
            created_at = NOW()
        """

        try:
            execute_values(self.cursor, insert_query, data)
            self.conn.commit()
            logger.info(f"Inserted {len(data)} regime records for {symbol} {timeframe}")
            return len(data)
        except Exception as e:
            logger.error(f"Failed to insert regimes: {e}")
            self.conn.rollback()
            raise

    def get_regimes(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get regime data for a symbol/timeframe.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            DataFrame with regime data indexed by open_time
        """
        if not self.conn:
            self.connect()

        # Build query with optional time filters
        query = """
        SELECT
            open_time,
            trend_state,
            volatility_state,
            momentum_state,
            full_regime,
            simplified_regime,
            confidence,
            classifier_version
        FROM market_regimes
        WHERE symbol = %s AND timeframe = %s
        """
        params = [symbol, timeframe]

        if start_time:
            query += " AND open_time >= %s"
            params.append(start_time)

        if end_time:
            query += " AND open_time <= %s"
            params.append(end_time)

        query += " ORDER BY open_time"

        try:
            df = pd.read_sql_query(query, self.conn, params=params, index_col='open_time')
            logger.info(f"Retrieved {len(df)} regime records for {symbol} {timeframe}")
            return df
        except Exception as e:
            logger.error(f"Failed to get regimes: {e}")
            raise

    def has_regimes(self, symbol: str, timeframe: str) -> bool:
        """
        Check if regime data exists for symbol/timeframe.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            True if regime data exists
        """
        if not self.conn:
            self.connect()

        query = """
        SELECT EXISTS(
            SELECT 1 FROM market_regimes
            WHERE symbol = %s AND timeframe = %s
            LIMIT 1
        )
        """

        try:
            self.cursor.execute(query, (symbol, timeframe))
            result = self.cursor.fetchone()
            return result[0] if result else False
        except Exception as e:
            logger.error(f"Failed to check regimes: {e}")
            raise

    def get_regime_stats(self) -> pd.DataFrame:
        """
        Get statistics about stored regime data.

        Returns:
            DataFrame with regime statistics per symbol/timeframe
        """
        if not self.conn:
            self.connect()

        query = """
        SELECT
            symbol,
            timeframe,
            COUNT(*) as regime_count,
            MIN(open_time) as first_regime,
            MAX(open_time) as last_regime,
            AVG(confidence) as avg_confidence,
            classifier_version
        FROM market_regimes
        GROUP BY symbol, timeframe, classifier_version
        ORDER BY symbol, timeframe
        """

        try:
            df = pd.read_sql_query(query, self.conn)
            logger.info(f"Retrieved regime stats for {len(df)} datasets")
            return df
        except Exception as e:
            logger.error(f"Failed to get regime stats: {e}")
            raise

    def delete_regimes(self, symbol: str, timeframe: str) -> int:
        """
        Delete regime data for a symbol/timeframe.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            Number of rows deleted
        """
        if not self.conn:
            self.connect()

        delete_query = """
        DELETE FROM market_regimes
        WHERE symbol = %s AND timeframe = %s
        """

        try:
            self.cursor.execute(delete_query, (symbol, timeframe))
            deleted = self.cursor.rowcount
            self.conn.commit()
            logger.info(f"Deleted {deleted} regime records for {symbol} {timeframe}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete regimes: {e}")
            self.conn.rollback()
            raise

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
