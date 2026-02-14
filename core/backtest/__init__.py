"""
Backtesting Engine for Trading Strategies

Event-driven backtesting framework with:
- BacktestEngine: Core event-driven simulation
- Portfolio: Position and trade tracking
- PerformanceMetrics: Comprehensive strategy evaluation
- Strategies: Base classes and implementations
"""

from .engine import BacktestEngine
from .events import FillEvent, MarketEvent, OrderEvent, SignalEvent
from .metrics import MetricsCalculator
from .portfolio import Portfolio, Position, Trade

__all__ = [
    "BacktestEngine",
    "Portfolio",
    "Trade",
    "Position",
    "MetricsCalculator",
    "MarketEvent",
    "SignalEvent",
    "OrderEvent",
    "FillEvent",
]
