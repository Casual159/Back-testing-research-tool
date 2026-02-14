"""
Trading strategies for backtesting.

Available strategies:
- MovingAverageCrossover: MA crossover trend-following
- RSIReversal: RSI overbought/oversold mean-reversion
- MACDCross: MACD signal line crossover
- BollingerBands: BB touch mean-reversion
"""

from .base import Strategy
from .bollinger_bands import BollingerBands
from .ma_crossover import MovingAverageCrossover
from .macd_cross import MACDCross
from .rsi_reversal import RSIReversal

__all__ = ["Strategy", "MovingAverageCrossover", "RSIReversal", "MACDCross", "BollingerBands"]
