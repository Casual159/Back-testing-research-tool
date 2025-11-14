"""
Strategy Composition Framework

Allows composing complex strategies by combining multiple indicators
with AND/OR logic across single or multiple timeframes.
"""

from .condition import Condition, ConditionOperator
from .signal import IndicatorSignal
from .logic_tree import LogicTree, LogicNode
from .composite_strategy import CompositeStrategy
from .multi_timeframe import MultiTimeframeData

__all__ = [
    'Condition',
    'ConditionOperator',
    'IndicatorSignal',
    'LogicTree',
    'LogicNode',
    'CompositeStrategy',
    'MultiTimeframeData'
]
