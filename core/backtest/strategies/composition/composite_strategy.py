"""
Composite Strategy - Combine multiple signals with custom logic

Allows building complex strategies by composing multiple indicator signals
with AND/OR logic for entry and exit conditions.

Supports regime filtering to only trade in specific market conditions.
"""
from typing import Dict, Any, Optional
import pandas as pd

from ..base import Strategy
from ...events import MarketEvent, SignalEvent
from .logic_tree import LogicTree
from .signal import IndicatorSignal

# Valid regime values for validation
VALID_SIMPLIFIED_REGIMES = ['TREND_UP', 'TREND_DOWN', 'RANGE', 'CHOPPY', 'NEUTRAL']
VALID_TREND_STATES = ['uptrend', 'downtrend', 'neutral']
VALID_VOLATILITY_STATES = ['low', 'high']
VALID_MOMENTUM_STATES = ['bullish', 'bearish', 'weak']


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
        description: str = "",
        regime_filter: Optional[list[str]] = None,
        sub_regime_filter: Optional[Dict[str, list[str]]] = None
    ):
        """
        Initialize composite strategy

        Args:
            name: Strategy name
            entry_logic: Logic tree for entry signals
            exit_logic: Logic tree for exit signals
            description: Strategy description
            regime_filter: List of allowed simplified regimes.
                          e.g., ["TREND_UP", "RANGE"] - only trade in these regimes
            sub_regime_filter: Filter by sub-regime components.
                              e.g., {"trend": ["uptrend"], "volatility": ["low"]}
        """
        # Set name BEFORE calling super().__init__() (it calls get_name())
        self.name = name
        self.entry_logic = entry_logic
        self.exit_logic = exit_logic
        self.description = description

        # Regime filtering
        self.regime_filter = regime_filter
        self.sub_regime_filter = sub_regime_filter

        # Validate regime filter values
        self._validate_regime_filters()

        # State - will be set by initialize()
        self._data_df = None
        self._entry_signals = None
        self._exit_signals = None
        self._in_position = False

        # Statistics for regime filtering
        self._regime_skipped_count = 0

        # Call parent __init__ after setting attributes
        super().__init__()

    def _validate_regime_filters(self):
        """Validate that regime filter values are valid"""
        if self.regime_filter:
            for regime in self.regime_filter:
                if regime not in VALID_SIMPLIFIED_REGIMES:
                    raise ValueError(
                        f"Invalid regime '{regime}'. "
                        f"Valid values: {VALID_SIMPLIFIED_REGIMES}"
                    )

        if self.sub_regime_filter:
            valid_components = {
                'trend': VALID_TREND_STATES,
                'volatility': VALID_VOLATILITY_STATES,
                'momentum': VALID_MOMENTUM_STATES
            }
            for component, values in self.sub_regime_filter.items():
                if component not in valid_components:
                    raise ValueError(
                        f"Invalid sub-regime component '{component}'. "
                        f"Valid components: {list(valid_components.keys())}"
                    )
                for value in values:
                    if value not in valid_components[component]:
                        raise ValueError(
                            f"Invalid value '{value}' for {component}. "
                            f"Valid values: {valid_components[component]}"
                        )

    def initialize(self, data: pd.DataFrame):
        """
        Initialize strategy with full dataset

        Pre-calculates all signals for entire period.
        This is called by BacktestEngine before running.

        Args:
            data: Full OHLCV DataFrame with datetime index
        """
        self._data_df = data
        self._regime_skipped_count = 0

        # Evaluate entry logic for entire series
        self._entry_signals = self.entry_logic.evaluate_series(data)

        # Evaluate exit logic for entire series
        self._exit_signals = self.exit_logic.evaluate_series(data)

    def _regime_allowed(self, market_event: MarketEvent) -> bool:
        """
        Check if current market regime is allowed for this strategy.

        Args:
            market_event: Current market data with regime metadata

        Returns:
            True if regime is allowed (or no filter set), False otherwise
        """
        # No filter = allow all
        if not self.regime_filter and not self.sub_regime_filter:
            return True

        # Get regime data from market event
        regime_data = market_event.metadata.get('regime', {})

        # If no regime data available, allow trading (conservative approach)
        if not regime_data:
            return True

        # Check simplified regime filter
        if self.regime_filter:
            simplified = regime_data.get('simplified')
            if simplified and simplified not in self.regime_filter:
                return False

        # Check sub-regime filter
        if self.sub_regime_filter:
            for component, allowed_values in self.sub_regime_filter.items():
                # Map component name to regime_data key
                state_key = f'{component}_state'
                current_value = regime_data.get(state_key)

                if current_value and current_value not in allowed_values:
                    return False

        return True

    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Generate trading signal from market event

        This is called by BacktestEngine for each new bar.
        Respects regime_filter - skips signals in disallowed regimes.

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

        # Check regime filter for ENTRY signals only
        # (we always allow exits to protect capital)
        if not self._in_position:
            # Check regime before considering entry
            if not self._regime_allowed(market_event):
                self._regime_skipped_count += 1
                return None

            if self._entry_signals.iloc[idx]:
                self._in_position = True
                # Include regime info in signal metadata
                regime_data = market_event.metadata.get('regime', {})
                return SignalEvent(
                    timestamp=timestamp,
                    symbol=market_event.symbol,
                    signal_type='BUY',
                    strength=1.0,
                    metadata={
                        'regime': regime_data.get('simplified'),
                        'regime_confidence': regime_data.get('confidence')
                    }
                )

        # Check exit signal (if in position) - always allow exits
        else:
            if self._exit_signals.iloc[idx]:
                self._in_position = False
                regime_data = market_event.metadata.get('regime', {})
                return SignalEvent(
                    timestamp=timestamp,
                    symbol=market_event.symbol,
                    signal_type='SELL',
                    strength=1.0,
                    metadata={
                        'regime': regime_data.get('simplified'),
                        'regime_confidence': regime_data.get('confidence')
                    }
                )

        return None

    def get_regime_stats(self) -> Dict[str, Any]:
        """Get statistics about regime filtering"""
        return {
            'regime_filter': self.regime_filter,
            'sub_regime_filter': self.sub_regime_filter,
            'signals_skipped_by_regime': self._regime_skipped_count
        }

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
        result = {
            'type': 'CompositeStrategy',
            'name': self.name,
            'description': self.description,
            'entry_logic': self.entry_logic.to_dict(),
            'exit_logic': self.exit_logic.to_dict()
        }

        # Include regime filters if set
        if self.regime_filter:
            result['regime_filter'] = self.regime_filter
        if self.sub_regime_filter:
            result['sub_regime_filter'] = self.sub_regime_filter

        return result

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
            description=data.get('description', ''),
            regime_filter=data.get('regime_filter'),
            sub_regime_filter=data.get('sub_regime_filter')
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
