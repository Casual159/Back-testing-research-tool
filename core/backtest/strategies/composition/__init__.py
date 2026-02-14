"""
Strategy Composition Framework

Allows composing complex strategies by combining multiple indicators
with AND/OR logic across single or multiple timeframes.
"""

from .composite_strategy import CompositeStrategy
from .condition import Condition, ConditionOperator
from .logic_tree import LogicNode, LogicTree
from .multi_timeframe import MultiTimeframeData
from .signal import IndicatorSignal

__all__ = [
    "Condition",
    "ConditionOperator",
    "IndicatorSignal",
    "LogicTree",
    "LogicNode",
    "CompositeStrategy",
    "MultiTimeframeData",
]
