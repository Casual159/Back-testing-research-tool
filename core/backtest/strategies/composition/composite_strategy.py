"""
Composite Strategy - Combine multiple signals with custom logic

Allows building complex strategies by composing multiple indicator signals
with AND/OR logic for entry and exit conditions.
"""
from typing import Dict, Any, Optional
import pandas as pd

from ..base import Strategy
from ...events import MarketEvent, SignalEvent
from .logic_tree import LogicTree
from .signal import IndicatorSignal


class CompositeStrategy(Strategy):
    """
    Strategy composed of multiple indicator signals

    Uses event-driven architecture compatible with BacktestEngine.
    Pre-calculates all signals at initialization for efficiency.

    Example:
        # Create signals
        rsi_signal = IndicatorSignal(
            name="RSI_Oversold",
            indicator="RSI",
            parameters={'period': 14},
            condition=Condition("<", 30)
        )

        macd_signal = IndicatorSignal(
            name="MACD_BullishCross",
            indicator="MACD",
            parameters={'fast': 12, 'slow': 26, 'signal': 9},
            condition=Condition("cross_above", 0),
            indicator_component="macd"
        )

        # Combine with AND
        entry_logic = LogicTree.AND([rsi_signal, macd_signal])
        exit_logic = LogicTree(...)  # Define exit

        # Create strategy
        strategy = CompositeStrategy(
            name="RSI+MACD Combo",
            entry_logic=entry_logic,
            exit_logic=exit_logic
        )
    """

    def __init__(
        self,
        name: str,
        entry_logic: LogicTree,
        exit_logic: LogicTree,
        description: str = ""
    ):
        """
        Initialize composite strategy

        Args:
            name: Strategy name
            entry_logic: Logic tree for entry signals
            exit_logic: Logic tree for exit signals
            description: Strategy description
        """
        # Set name BEFORE calling super().__init__() (it calls get_name())
        self.name = name
        self.entry_logic = entry_logic
        self.exit_logic = exit_logic
        self.description = description

        # State - will be set by initialize()
        self._data_df = None
        self._entry_signals = None
        self._exit_signals = None
        self._in_position = False

        # Call parent __init__ after setting attributes
        super().__init__()

    def initialize(self, data: pd.DataFrame):
        """
        Initialize strategy with full dataset

        Pre-calculates all signals for entire period.
        This is called by BacktestEngine before running.

        Args:
            data: Full OHLCV DataFrame with datetime index
        """
        self._data_df = data

        # Evaluate entry logic for entire series
        self._entry_signals = self.entry_logic.evaluate_series(data)

        # Evaluate exit logic for entire series
        self._exit_signals = self.exit_logic.evaluate_series(data)

    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Generate trading signal from market event

        This is called by BacktestEngine for each new bar.

        Args:
            market_event: Current market data

        Returns:
            SignalEvent (BUY/SELL) or None
        """
        # Add market data to buffer (for compatibility)
        self.add_market_data(market_event)

        # Get current timestamp
        timestamp = market_event.timestamp

        # Check if we have pre-calculated signals
        if self._entry_signals is None or self._exit_signals is None:
            # Not initialized yet - shouldn't happen but handle gracefully
            return None

        # Find index for current timestamp in pre-calculated signals
        try:
            idx = self._data_df.index.get_loc(timestamp)
        except KeyError:
            # Timestamp not in index
            return None

        # Check entry signal (if not in position)
        if not self._in_position:
            if self._entry_signals.iloc[idx]:
                self._in_position = True
                return SignalEvent(
                    timestamp=timestamp,
                    symbol=market_event.symbol,
                    signal_type='BUY',
                    strength=1.0
                )

        # Check exit signal (if in position)
        else:
            if self._exit_signals.iloc[idx]:
                self._in_position = False
                return SignalEvent(
                    timestamp=timestamp,
                    symbol=market_event.symbol,
                    signal_type='SELL',
                    strength=1.0
                )

        return None

    def get_name(self) -> str:
        """Get strategy name"""
        return self.name

    def __str__(self) -> str:
        """String representation"""
        return f"CompositeStrategy({self.name})"

    def __repr__(self) -> str:
        entry_str = str(self.entry_logic)
        exit_str = str(self.exit_logic)
        return f"CompositeStrategy(\n  Entry: {entry_str}\n  Exit: {exit_str}\n)"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization

        Returns:
            Dictionary representation
        """
        return {
            'type': 'CompositeStrategy',
            'name': self.name,
            'description': self.description,
            'entry_logic': self.entry_logic.to_dict(),
            'exit_logic': self.exit_logic.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositeStrategy':
        """
        Create from dictionary

        Args:
            data: Dictionary representation

        Returns:
            CompositeStrategy instance
        """
        entry_logic = LogicTree.from_dict(data['entry_logic'])
        exit_logic = LogicTree.from_dict(data['exit_logic'])

        return cls(
            name=data['name'],
            entry_logic=entry_logic,
            exit_logic=exit_logic,
            description=data.get('description', '')
        )

    def get_entry_summary(self) -> str:
        """Get human-readable entry logic summary"""
        return f"Entry: {self.entry_logic}"

    def get_exit_summary(self) -> str:
        """Get human-readable exit logic summary"""
        return f"Exit: {self.exit_logic}"

    def get_all_signals(self) -> list:
        """Get all signals used in this strategy"""
        signals = []

        def collect_signals(node):
            if node.is_leaf:
                signals.append(node.signal)
            else:
                for child in node.children:
                    collect_signals(child)

        collect_signals(self.entry_logic.root)
        collect_signals(self.exit_logic.root)

        return signals
