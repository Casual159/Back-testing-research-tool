"""
Condition evaluation for indicator signals

Supports various comparison operators:
- Numeric: >, <, >=, <=, ==, !=
- Crossovers: cross_above, cross_below
- Range: between, outside
"""
from enum import Enum
from typing import Union, Optional
import pandas as pd
import numpy as np


class ConditionOperator(Enum):
    """Supported comparison operators"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    CROSS_ABOVE = "cross_above"
    CROSS_BELOW = "cross_below"
    BETWEEN = "between"
    OUTSIDE = "outside"


class Condition:
    """
    Evaluation condition for indicator signals

    Examples:
        # Simple comparison
        Condition(">", 70)  # value > 70

        # Crossover
        Condition("cross_above", 0)  # MACD crosses above zero

        # Range
        Condition("between", 30, 70)  # RSI between 30 and 70
    """

    def __init__(
        self,
        operator: Union[str, ConditionOperator],
        threshold: float,
        threshold2: Optional[float] = None
    ):
        """
        Initialize condition

        Args:
            operator: Comparison operator
            threshold: Primary threshold value
            threshold2: Secondary threshold (for between/outside)
        """
        if isinstance(operator, str):
            # Convert string to enum
            operator_map = {
                ">": ConditionOperator.GREATER_THAN,
                "<": ConditionOperator.LESS_THAN,
                ">=": ConditionOperator.GREATER_EQUAL,
                "<=": ConditionOperator.LESS_EQUAL,
                "==": ConditionOperator.EQUAL,
                "!=": ConditionOperator.NOT_EQUAL,
                "cross_above": ConditionOperator.CROSS_ABOVE,
                "cross_below": ConditionOperator.CROSS_BELOW,
                "between": ConditionOperator.BETWEEN,
                "outside": ConditionOperator.OUTSIDE
            }
            if operator not in operator_map:
                raise ValueError(f"Unknown operator: {operator}")
            operator = operator_map[operator]

        self.operator = operator
        self.threshold = threshold
        self.threshold2 = threshold2

        # Validate
        if self.operator in (ConditionOperator.BETWEEN, ConditionOperator.OUTSIDE):
            if threshold2 is None:
                raise ValueError(f"{self.operator.value} requires threshold2")

    def evaluate(
        self,
        current_value: float,
        previous_value: Optional[float] = None
    ) -> bool:
        """
        Evaluate condition for current value

        Args:
            current_value: Current indicator value
            previous_value: Previous indicator value (for crossovers)

        Returns:
            True if condition is met, False otherwise
        """
        if pd.isna(current_value):
            return False

        if self.operator == ConditionOperator.GREATER_THAN:
            return current_value > self.threshold

        elif self.operator == ConditionOperator.LESS_THAN:
            return current_value < self.threshold

        elif self.operator == ConditionOperator.GREATER_EQUAL:
            return current_value >= self.threshold

        elif self.operator == ConditionOperator.LESS_EQUAL:
            return current_value <= self.threshold

        elif self.operator == ConditionOperator.EQUAL:
            return abs(current_value - self.threshold) < 1e-6

        elif self.operator == ConditionOperator.NOT_EQUAL:
            return abs(current_value - self.threshold) >= 1e-6

        elif self.operator == ConditionOperator.BETWEEN:
            return self.threshold <= current_value <= self.threshold2

        elif self.operator == ConditionOperator.OUTSIDE:
            return current_value < self.threshold or current_value > self.threshold2

        elif self.operator == ConditionOperator.CROSS_ABOVE:
            if previous_value is None or pd.isna(previous_value):
                return False
            return previous_value <= self.threshold < current_value

        elif self.operator == ConditionOperator.CROSS_BELOW:
            if previous_value is None or pd.isna(previous_value):
                return False
            return previous_value >= self.threshold > current_value

        return False

    def evaluate_series(
        self,
        series: pd.Series
    ) -> pd.Series:
        """
        Evaluate condition for entire series

        Args:
            series: Pandas series of indicator values

        Returns:
            Boolean series indicating where condition is met
        """
        if self.operator == ConditionOperator.GREATER_THAN:
            return series > self.threshold

        elif self.operator == ConditionOperator.LESS_THAN:
            return series < self.threshold

        elif self.operator == ConditionOperator.GREATER_EQUAL:
            return series >= self.threshold

        elif self.operator == ConditionOperator.LESS_EQUAL:
            return series <= self.threshold

        elif self.operator == ConditionOperator.EQUAL:
            return (series - self.threshold).abs() < 1e-6

        elif self.operator == ConditionOperator.NOT_EQUAL:
            return (series - self.threshold).abs() >= 1e-6

        elif self.operator == ConditionOperator.BETWEEN:
            return (series >= self.threshold) & (series <= self.threshold2)

        elif self.operator == ConditionOperator.OUTSIDE:
            return (series < self.threshold) | (series > self.threshold2)

        elif self.operator == ConditionOperator.CROSS_ABOVE:
            prev_series = series.shift(1)
            return (prev_series <= self.threshold) & (series > self.threshold)

        elif self.operator == ConditionOperator.CROSS_BELOW:
            prev_series = series.shift(1)
            return (prev_series >= self.threshold) & (series < self.threshold)

        return pd.Series(False, index=series.index)

    def __str__(self) -> str:
        """String representation"""
        if self.operator in (ConditionOperator.BETWEEN, ConditionOperator.OUTSIDE):
            return f"{self.operator.value} {self.threshold} and {self.threshold2}"
        return f"{self.operator.value} {self.threshold}"

    def __repr__(self) -> str:
        return f"Condition({self.operator.value}, {self.threshold}, {self.threshold2})"
