"""
Configuration module for CryptoAnalyzer
Loads environment variables and provides centralized config access
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


class Config:
    """Main configuration class"""

    # Binance API
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'

    # Testnet credentials
    BINANCE_TESTNET_API_KEY = os.getenv('BINANCE_TESTNET_API_KEY')
    BINANCE_TESTNET_API_SECRET = os.getenv('BINANCE_TESTNET_API_SECRET')

    # Live credentials
    BINANCE_LIVE_API_KEY = os.getenv('BINANCE_LIVE_API_KEY')
    BINANCE_LIVE_API_SECRET = os.getenv('BINANCE_LIVE_API_SECRET')

    # Active credentials (based on BINANCE_TESTNET flag)
    @classmethod
    @property
    def BINANCE_API_KEY(cls):
        return cls.BINANCE_TESTNET_API_KEY if cls.BINANCE_TESTNET else cls.BINANCE_LIVE_API_KEY

    @classmethod
    @property
    def BINANCE_API_SECRET(cls):
        return cls.BINANCE_TESTNET_API_SECRET if cls.BINANCE_TESTNET else cls.BINANCE_LIVE_API_SECRET

    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

    # PostgreSQL
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'trading_bot')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

    # Trading Settings
    TEST_MODE = os.getenv('TEST_MODE', 'true').lower() == 'true'
    INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', 100))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 0.2))

    # Additional trading parameters
    DEFAULT_SYMBOL = 'BTCUSDT'
    DEFAULT_TIMEFRAME = '1h'

    @classmethod
    def validate(cls):
        """Validate that all required config values are set"""
        if cls.BINANCE_TESTNET:
            required = ['BINANCE_TESTNET_API_KEY', 'BINANCE_TESTNET_API_SECRET']
            mode = "testnet"
        else:
            required = ['BINANCE_LIVE_API_KEY', 'BINANCE_LIVE_API_SECRET']
            mode = "live"

        missing = [key for key in required if not getattr(cls, key)]

        if missing:
            raise ValueError(f"Missing required {mode} config values: {', '.join(missing)}")

        return True

    @classmethod
    def get_binance_config(cls):
        """Get Binance API configuration with automatic testnet/live switching"""
        api_key = cls.BINANCE_TESTNET_API_KEY if cls.BINANCE_TESTNET else cls.BINANCE_LIVE_API_KEY
        api_secret = cls.BINANCE_TESTNET_API_SECRET if cls.BINANCE_TESTNET else cls.BINANCE_LIVE_API_SECRET

        return {
            'api_key': api_key,
            'api_secret': api_secret,
            'testnet': cls.BINANCE_TESTNET,
            'base_url': 'https://testnet.binance.vision/api' if cls.BINANCE_TESTNET else 'https://api.binance.com/api'
        }

    @classmethod
    def get_redis_config(cls):
        """Get Redis connection configuration"""
        return {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'password': cls.REDIS_PASSWORD if cls.REDIS_PASSWORD else None,
            'decode_responses': True
        }

    @classmethod
    def get_postgres_config(cls):
        """Get PostgreSQL connection configuration"""
        return {
            'host': cls.POSTGRES_HOST,
            'port': cls.POSTGRES_PORT,
            'database': cls.POSTGRES_DB,
            'user': cls.POSTGRES_USER,
            'password': cls.POSTGRES_PASSWORD
        }


class DataConfig:
    """Data fetcher and storage configuration"""

    # Available trading pairs (shared across all pages)
    AVAILABLE_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

    # Timeframes to fetch
    TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

    # PostgreSQL retention (days back from today)
    POSTGRES_RETENTION = {
        '1m': 730,   # 2 years (~1M candles)
        '5m': 730,   # 2 years
        '15m': 730,  # 2 years
        '1h': 1095,  # 3 years
        '4h': 1095,  # 3 years
        '1d': 1825   # 5 years (from 2020)
    }

    # Rate limiting - SAFE configuration (33% margin below limits)
    BINANCE_REQUEST_DELAY = 0.15  # seconds between requests (was 0.1)
    MAX_RETRIES = 3

    # Binance API limits
    MAX_CANDLES_PER_REQUEST = 1000

    # Safety settings
    MAX_CONCURRENT_DOWNLOADS = 1  # Prevent parallel downloads that could exceed limits


class UIConfig:
    """UI and visualization configuration"""

    # Plotly chart theme for dark mode
    PLOTLY_THEME = {
        'template': 'plotly_dark',
        'layout': {
            'paper_bgcolor': '#0E1117',
            'plot_bgcolor': '#0E1117',
            'font': {'color': '#FAFAFA', 'size': 12},
            'xaxis': {
                'gridcolor': '#262730',
                'zerolinecolor': '#262730'
            },
            'yaxis': {
                'gridcolor': '#262730',
                'zerolinecolor': '#262730'
            },
            'colorway': ['#FF6B00', '#00D9FF', '#00FF88', '#FF0080', '#FFD700'],
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 60}
        }
    }

    # Color palette
    COLORS = {
        'primary': '#FF6B00',      # Bitcoin orange
        'secondary': '#00D9FF',    # Cyan
        'success': '#00FF88',      # Green
        'danger': '#FF0080',       # Pink/Red
        'warning': '#FFD700',      # Gold
        'info': '#00D9FF',         # Cyan
        'background': '#0E1117',   # Dark bg
        'card_bg': '#262730',      # Card background
        'text': '#FAFAFA'          # Off-white
    }


# Convenience instance
config = Config()

# Validate on import (optional - can be disabled if needed)
if __name__ != '__main__':
    try:
        config.validate()
    except ValueError as e:
        print(f"�  Config warning: {e}")