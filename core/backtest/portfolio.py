"""
Portfolio management for backtesting.

Tracks positions, cash, trades, and calculates portfolio value over time.
"""

from datetime import datetime
from typing import Dict, List, Tuple
from .events import FillEvent


class Trade:
    """
    Represents a completed trade (entry + exit).

    Attributes:
        entry_time: When position was opened
        exit_time: When position was closed
        symbol: Trading symbol
        direction: 'LONG' or 'SHORT'
        entry_price: Price at entry
        exit_price: Price at exit
        quantity: Amount traded
        pnl: Profit/Loss (after commissions)
        return_pct: Return as percentage
        duration: Time held (in seconds)
    """

    def __init__(
        self,
        entry_time: datetime,
        exit_time: datetime,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        entry_commission: float,
        exit_commission: float
    ):
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.symbol = symbol
        self.direction = direction
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.entry_commission = entry_commission
        self.exit_commission = exit_commission

        # Calculate P&L
        if direction == 'LONG':
            gross_pnl = (exit_price - entry_price) * quantity
        else:  # SHORT
            gross_pnl = (entry_price - exit_price) * quantity

        self.pnl = gross_pnl - entry_commission - exit_commission
        self.return_pct = (self.pnl / (entry_price * quantity)) * 100

        # Calculate duration
        try:
            self.duration = (exit_time - entry_time).total_seconds()
        except AttributeError:
            # Handle case where times might be integers or other types
            from datetime import datetime
            if isinstance(entry_time, (int, float)):
                entry_time = datetime.fromtimestamp(entry_time)
            if isinstance(exit_time, (int, float)):
                exit_time = datetime.fromtimestamp(exit_time)
            self.duration = (exit_time - entry_time).total_seconds()

    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl > 0

    def __repr__(self):
        return (f"Trade({self.direction} {self.symbol}, "
                f"PnL={self.pnl:.2f}, Return={self.return_pct:.2f}%)")


class Position:
    """
    Represents an open position.

    Attributes:
        symbol: Trading symbol
        quantity: Number of units held (positive for long, negative for short)
        entry_price: Average entry price
        entry_time: When position was opened
        entry_commission: Commission paid on entry
    """

    def __init__(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        entry_time: datetime,
        entry_commission: float
    ):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.entry_commission = entry_commission

    def current_value(self, current_price: float) -> float:
        """Calculate current position value."""
        return self.quantity * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized profit/loss."""
        return (current_price - self.entry_price) * self.quantity

    def __repr__(self):
        return f"Position({self.symbol}, qty={self.quantity:.4f}, entry={self.entry_price:.2f})"


class Portfolio:
    """
    Manages portfolio state during backtesting.

    Tracks:
    - Cash balance
    - Open positions
    - Completed trades
    - Equity curve (portfolio value over time)

    Attributes:
        initial_capital: Starting cash
        current_cash: Available cash
        positions: Dict mapping symbol to Position
        trades: List of completed trades
        equity_curve: List of (timestamp, portfolio_value) tuples
    """

    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize portfolio.

        Args:
            initial_capital: Starting cash amount
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []

        # Track fills for trade reconstruction
        self._fills: List[FillEvent] = []

    def update_from_fill(self, fill: FillEvent, current_price: float):
        """
        Update portfolio based on fill event.

        Args:
            fill: FillEvent from order execution
            current_price: Current market price (for position value calculation)
        """
        symbol = fill.symbol

        # Store fill for trade history
        self._fills.append(fill)

        if fill.direction == 'BUY':
            # Opening or adding to long position
            if symbol in self.positions:
                # Average up the position
                pos = self.positions[symbol]
                total_cost = (pos.quantity * pos.entry_price) + (fill.quantity * fill.fill_price)
                total_quantity = pos.quantity + fill.quantity
                pos.entry_price = total_cost / total_quantity
                pos.quantity = total_quantity
                pos.entry_commission += fill.commission
            else:
                # New position
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=fill.quantity,
                    entry_price=fill.fill_price,
                    entry_time=fill.timestamp,
                    entry_commission=fill.commission
                )

            # Deduct cost from cash
            self.current_cash -= fill.cost

        elif fill.direction == 'SELL':
            # Closing or reducing long position
            if symbol in self.positions:
                pos = self.positions[symbol]

                # Check if closing entire position
                if abs(fill.quantity - pos.quantity) < 1e-8:
                    # Full exit - create trade record
                    trade = Trade(
                        entry_time=pos.entry_time,
                        exit_time=fill.timestamp,
                        symbol=symbol,
                        direction='LONG',
                        entry_price=pos.entry_price,
                        exit_price=fill.fill_price,
                        quantity=pos.quantity,
                        entry_commission=pos.entry_commission,
                        exit_commission=fill.commission
                    )
                    self.trades.append(trade)

                    # Remove position
                    del self.positions[symbol]
                else:
                    # Partial exit
                    pos.quantity -= fill.quantity

                # Add proceeds to cash
                self.current_cash += abs(fill.cost)

    def current_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.

        Args:
            current_prices: Dict mapping symbol to current price

        Returns:
            Total portfolio value (cash + positions)
        """
        position_value = sum(
            pos.quantity * current_prices.get(pos.symbol, 0)
            for pos in self.positions.values()
        )
        return self.current_cash + position_value

    def record_equity(self, timestamp: datetime, portfolio_value: float):
        """
        Record portfolio value at a point in time.

        Args:
            timestamp: Current time
            portfolio_value: Total portfolio value
        """
        self.equity_curve.append((timestamp, portfolio_value))

    def get_position(self, symbol: str) -> Position:
        """Get current position for symbol (or None)."""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if holding position in symbol."""
        return symbol in self.positions

    def total_return(self) -> float:
        """Calculate total return percentage."""
        if not self.equity_curve:
            return 0.0
        final_value = self.equity_curve[-1][1]
        return ((final_value - self.initial_capital) / self.initial_capital) * 100

    def total_trades(self) -> int:
        """Get number of completed trades."""
        return len(self.trades)

    def winning_trades(self) -> List[Trade]:
        """Get list of profitable trades."""
        return [t for t in self.trades if t.is_winner()]

    def losing_trades(self) -> List[Trade]:
        """Get list of losing trades."""
        return [t for t in self.trades if not t.is_winner()]

    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if not self.trades:
            return 0.0
        return (len(self.winning_trades()) / len(self.trades)) * 100

    def __repr__(self):
        return (f"Portfolio(cash={self.current_cash:.2f}, "
                f"positions={len(self.positions)}, trades={len(self.trades)})")
