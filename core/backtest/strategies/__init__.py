"""
Trading strategies for backtesting.

Available strategies:
- MovingAverageCrossover: MA crossover trend-following
- RSIReversal: RSI overbought/oversold mean-reversion
- MACDCross: MACD signal line crossover
- BollingerBands: BB touch mean-reversion
"""

from .base import Strategy
from .ma_crossover import MovingAverageCrossover
from .rsi_reversal import RSIReversal
from .macd_cross import MACDCross
from .bollinger_bands import BollingerBands

__all__ = [
    'Strategy',
    'MovingAverageCrossover',
    'RSIReversal',
    'MACDCross',
    'BollingerBands'
]
