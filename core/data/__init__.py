"""
Data Layer for Backtesting Research Tool

Provides data fetching and storage capabilities:
- BinanceBulkFetcher: Downloads historical data from Binance Public Data
- BinanceDataFetcher: Downloads data via Binance API (for recent data)
- PostgresStorage: Database storage and retrieval
"""

from .bulk_fetcher import BinanceBulkFetcher
from .fetcher import BinanceDataFetcher
from .storage import PostgresStorage

__all__ = [
    'BinanceBulkFetcher',
    'BinanceDataFetcher',
    'PostgresStorage',
]
