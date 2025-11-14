"""
Logic Tree for combining signals with AND/OR logic

Supports building complex logic trees like:
    (Signal1 AND Signal2) OR (Signal3 AND Signal4)
"""
from typing import List, Union, Dict, Any
from enum import Enum
import pandas as pd

from .signal import IndicatorSignal


class LogicOperator(Enum):
    """Logic operators"""
    AND = "AND"
    OR = "OR"


class LogicNode:
    """
    Node in logic tree

    Can be either:
    - Leaf node: Contains an IndicatorSignal
    - Branch node: Contains operator (AND/OR) and child nodes
    """

    def __init__(
        self,
        operator: Union[LogicOperator, str, None] = None,
        signal: IndicatorSignal = None,
        children: List['LogicNode'] = None
    ):
        """
        Initialize logic node

        Args:
            operator: Logic operator (AND/OR) for branch nodes
            signal: IndicatorSignal for leaf nodes
            children: Child nodes for branch nodes
        """
        if signal is not None and (operator is not None or children):
            raise ValueError("Node cannot be both leaf (signal) and branch (operator/children)")

        if signal is None and operator is None:
            raise ValueError("Node must be either leaf (signal) or branch (operator)")

        # Leaf node
        if signal is not None:
            self.is_leaf = True
            self.signal = signal
            self.operator = None
            self.children = []

        # Branch node
        else:
            self.is_leaf = False
            self.signal = None

            if isinstance(operator, str):
                operator = LogicOperator[operator.upper()]
            self.operator = operator

            self.children = children or []

    def add_child(self, child: 'LogicNode'):
        """Add child node (for branch nodes)"""
        if self.is_leaf:
            raise ValueError("Cannot add children to leaf node")
        self.children.append(child)

    def evaluate(self, data: pd.DataFrame, index: int = None) -> bool:
        """
        Evaluate node at specific point

        Args:
            data: OHLCV DataFrame
            index: Index to evaluate at

        Returns:
            True if condition is met, False otherwise
        """
        if self.is_leaf:
            # Evaluate signal
            return self.signal.evaluate(data, index)

        # Evaluate children
        if not self.children:
            return False

        results = [child.evaluate(data, index) for child in self.children]

        if self.operator == LogicOperator.AND:
            return all(results)
        elif self.operator == LogicOperator.OR:
            return any(results)

        return False

    def evaluate_series(self, data: pd.DataFrame) -> pd.Series:
        """
        Evaluate node for entire series

        Args:
            data: OHLCV DataFrame

        Returns:
            Boolean series
        """
        if self.is_leaf:
            # Evaluate signal series
            return self.signal.evaluate_series(data)

        # Evaluate children
        if not self.children:
            return pd.Series(False, index=data.index)

        results = [child.evaluate_series(data) for child in self.children]

        if self.operator == LogicOperator.AND:
            # Combine with AND
            combined = results[0]
            for result in results[1:]:
                combined = combined & result
            return combined

        elif self.operator == LogicOperator.OR:
            # Combine with OR
            combined = results[0]
            for result in results[1:]:
                combined = combined | result
            return combined

        return pd.Series(False, index=data.index)

    def __str__(self) -> str:
        """String representation"""
        if self.is_leaf:
            return f"[{self.signal.name}]"

        if not self.children:
            return "[]"

        if len(self.children) == 1:
            return str(self.children[0])

        children_str = f" {self.operator.value} ".join(str(child) for child in self.children)
        return f"({children_str})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        if self.is_leaf:
            return {
                'type': 'leaf',
                'signal': self.signal.to_dict()
            }
        return {
            'type': 'branch',
            'operator': self.operator.value,
            'children': [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogicNode':
        """Create from dictionary"""
        if data['type'] == 'leaf':
            signal = IndicatorSignal.from_dict(data['signal'])
            return cls(signal=signal)

        # Branch
        operator = LogicOperator[data['operator']]
        children = [cls.from_dict(child) for child in data['children']]
        return cls(operator=operator, children=children)


class LogicTree:
    """
    Logic tree for combining multiple signals

    Examples:
        # Simple AND
        tree = LogicTree.AND([signal1, signal2])

        # Simple OR
        tree = LogicTree.OR([signal1, signal2])

        # Complex: (S1 AND S2) OR S3
        tree = LogicTree(
            LogicNode(
                operator=LogicOperator.OR,
                children=[
                    LogicNode(
                        operator=LogicOperator.AND,
                        children=[
                            LogicNode(signal=signal1),
                            LogicNode(signal=signal2)
                        ]
                    ),
                    LogicNode(signal=signal3)
                ]
            )
        )
    """

    def __init__(self, root: LogicNode):
        """
        Initialize logic tree

        Args:
            root: Root node of the tree
        """
        self.root = root

    @classmethod
    def AND(cls, signals: List[IndicatorSignal]) -> 'LogicTree':
        """
        Create simple AND tree

        All signals must be true for the condition to trigger
        """
        if not signals:
            raise ValueError("Must provide at least one signal")

        if len(signals) == 1:
            return cls(LogicNode(signal=signals[0]))

        children = [LogicNode(signal=sig) for sig in signals]
        root = LogicNode(operator=LogicOperator.AND, children=children)
        return cls(root)

    @classmethod
    def OR(cls, signals: List[IndicatorSignal]) -> 'LogicTree':
        """
        Create simple OR tree

        Any signal being true will trigger the condition
        """
        if not signals:
            raise ValueError("Must provide at least one signal")

        if len(signals) == 1:
            return cls(LogicNode(signal=signals[0]))

        children = [LogicNode(signal=sig) for sig in signals]
        root = LogicNode(operator=LogicOperator.OR, children=children)
        return cls(root)

    def evaluate(self, data: pd.DataFrame, index: int = None) -> bool:
        """
        Evaluate tree at specific point

        Args:
            data: OHLCV DataFrame
            index: Index to evaluate at

        Returns:
            True if condition is met
        """
        return self.root.evaluate(data, index)

    def evaluate_series(self, data: pd.DataFrame) -> pd.Series:
        """
        Evaluate tree for entire series

        Args:
            data: OHLCV DataFrame

        Returns:
            Boolean series
        """
        return self.root.evaluate_series(data)

    def __str__(self) -> str:
        """String representation"""
        return str(self.root)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.root.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogicTree':
        """Create from dictionary"""
        root = LogicNode.from_dict(data)
        return cls(root)
