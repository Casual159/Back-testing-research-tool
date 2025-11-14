"""
Backtesting Engine for Trading Strategies

Event-driven backtesting framework with:
- BacktestEngine: Core event-driven simulation
- Portfolio: Position and trade tracking
- PerformanceMetrics: Comprehensive strategy evaluation
- Strategies: Base classes and implementations
"""

from .engine import BacktestEngine
from .portfolio import Portfolio, Trade, Position
from .metrics import PerformanceMetrics

__all__ = [
    'BacktestEngine',
    'Portfolio',
    'Trade',
    'Position',
    'PerformanceMetrics',
]
