"""
Performance metrics calculation for backtesting.

Calculates various metrics to evaluate strategy performance:
- Returns (total, annual)
- Risk metrics (Sharpe ratio, max drawdown)
- Trade statistics (win rate, profit factor)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from .portfolio import Portfolio


class MetricsCalculator:
    """
    Calculate backtest performance metrics.

    Metrics include:
    - Total return, annual return
    - Sharpe ratio, Sortino ratio
    - Maximum drawdown
    - Win rate, profit factor
    - Average win/loss
    - Trade statistics

    Attributes:
        portfolio: Portfolio instance with trade history
    """

    def __init__(self, portfolio: Portfolio):
        """
        Initialize metrics calculator.

        Args:
            portfolio: Portfolio with completed backtest
        """
        self.portfolio = portfolio

    def calculate_all(self) -> Dict[str, Any]:
        """
        Calculate all metrics.

        Returns:
            Dictionary with all performance metrics
        """
        metrics = {
            # Returns
            'initial_capital': self.portfolio.initial_capital,
            'final_value': self._final_value(),
            'total_return': self._total_return(),
            'annual_return': self._annual_return(),

            # Risk metrics
            'sharpe_ratio': self._sharpe_ratio(),
            'max_drawdown': self._max_drawdown(),
            'max_drawdown_duration': self._max_drawdown_duration(),

            # Trade statistics
            'total_trades': self.portfolio.total_trades(),
            'winning_trades': len(self.portfolio.winning_trades()),
            'losing_trades': len(self.portfolio.losing_trades()),
            'win_rate': self._win_rate(),

            # Profit metrics
            'total_profit': self._total_profit(),
            'total_loss': self._total_loss(),
            'profit_factor': self._profit_factor(),
            'avg_win': self._avg_win(),
            'avg_loss': self._avg_loss(),
            'avg_trade': self._avg_trade(),

            # Streaks
            'max_win_streak': self._max_win_streak(),
            'max_loss_streak': self._max_loss_streak(),

            # Duration
            'avg_trade_duration': self._avg_trade_duration(),
        }

        return metrics

    def _final_value(self) -> float:
        """Get final portfolio value."""
        if not self.portfolio.equity_curve:
            return self.portfolio.initial_capital
        return self.portfolio.equity_curve[-1][1]

    def _total_return(self) -> float:
        """Calculate total return percentage."""
        return self.portfolio.total_return()

    def _annual_return(self) -> float:
        """
        Calculate annualized return.

        Uses CAGR formula: ((final/initial)^(1/years) - 1) * 100
        """
        if not self.portfolio.equity_curve or len(self.portfolio.equity_curve) < 2:
            return 0.0

        # Calculate duration in years
        start_date = self.portfolio.equity_curve[0][0]
        end_date = self.portfolio.equity_curve[-1][0]

        # Handle case where dates might be integers (index positions)
        try:
            days = (end_date - start_date).days
        except AttributeError:
            # If not datetime objects, try to convert or use len as proxy
            from datetime import datetime
            if isinstance(start_date, (int, float)):
                # Assume it's index - use number of bars as proxy
                days = len(self.portfolio.equity_curve)
            else:
                days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days

        years = days / 365.25

        if years <= 0:
            return 0.0

        final_value = self._final_value()
        initial_capital = self.portfolio.initial_capital

        # CAGR formula
        cagr = (pow(final_value / initial_capital, 1 / years) - 1) * 100
        return cagr

    def _sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted return).

        Sharpe = (mean_return - risk_free_rate) / std_dev_return * sqrt(252)

        Args:
            risk_free_rate: Annual risk-free rate (default: 0%)

        Returns:
            Sharpe ratio (higher is better, >1 is good, >2 is excellent)
        """
        if len(self.portfolio.equity_curve) < 2:
            return 0.0

        # Calculate daily returns
        returns = []
        for i in range(1, len(self.portfolio.equity_curve)):
            prev_value = self.portfolio.equity_curve[i - 1][1]
            curr_value = self.portfolio.equity_curve[i][1]
            daily_return = (curr_value - prev_value) / prev_value
            returns.append(daily_return)

        if not returns:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualize (assuming 252 trading days)
        sharpe = (mean_return - risk_free_rate / 252) / std_return * np.sqrt(252)
        return float(sharpe)

    def _max_drawdown(self) -> float:
        """
        Calculate maximum drawdown percentage.

        Drawdown = (Trough - Peak) / Peak * 100

        Returns:
            Max drawdown as negative percentage (e.g., -25.5%)
        """
        if len(self.portfolio.equity_curve) < 2:
            return 0.0

        values = [val for _, val in self.portfolio.equity_curve]
        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value
            dd = (value - peak) / peak * 100
            if dd < max_dd:
                max_dd = dd

        return max_dd

    def _max_drawdown_duration(self) -> int:
        """
        Calculate longest drawdown period (in bars).

        Returns:
            Number of bars in longest drawdown
        """
        if len(self.portfolio.equity_curve) < 2:
            return 0

        values = [val for _, val in self.portfolio.equity_curve]
        peak = values[0]
        peak_idx = 0
        max_duration = 0
        current_duration = 0

        for i, value in enumerate(values):
            if value >= peak:
                peak = value
                peak_idx = i
                current_duration = 0
            else:
                current_duration = i - peak_idx
                if current_duration > max_duration:
                    max_duration = current_duration

        return max_duration

    def _win_rate(self) -> float:
        """Calculate win rate percentage."""
        return self.portfolio.win_rate()

    def _total_profit(self) -> float:
        """Calculate total profit from winning trades."""
        winning = self.portfolio.winning_trades()
        return sum(trade.pnl for trade in winning)

    def _total_loss(self) -> float:
        """Calculate total loss from losing trades."""
        losing = self.portfolio.losing_trades()
        return sum(abs(trade.pnl) for trade in losing)

    def _profit_factor(self) -> float:
        """
        Calculate profit factor.

        Profit Factor = Total Profit / Total Loss

        Returns:
            Profit factor (>1 is profitable, >2 is good)
        """
        total_loss = self._total_loss()
        if total_loss == 0:
            return float('inf') if self._total_profit() > 0 else 0.0

        return self._total_profit() / total_loss

    def _avg_win(self) -> float:
        """Calculate average winning trade."""
        winning = self.portfolio.winning_trades()
        if not winning:
            return 0.0
        return sum(trade.pnl for trade in winning) / len(winning)

    def _avg_loss(self) -> float:
        """Calculate average losing trade."""
        losing = self.portfolio.losing_trades()
        if not losing:
            return 0.0
        return sum(trade.pnl for trade in losing) / len(losing)

    def _avg_trade(self) -> float:
        """Calculate average trade P&L."""
        if not self.portfolio.trades:
            return 0.0
        return sum(trade.pnl for trade in self.portfolio.trades) / len(self.portfolio.trades)

    def _max_win_streak(self) -> int:
        """Calculate longest winning streak."""
        if not self.portfolio.trades:
            return 0

        max_streak = 0
        current_streak = 0

        for trade in self.portfolio.trades:
            if trade.is_winner():
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def _max_loss_streak(self) -> int:
        """Calculate longest losing streak."""
        if not self.portfolio.trades:
            return 0

        max_streak = 0
        current_streak = 0

        for trade in self.portfolio.trades:
            if not trade.is_winner():
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def _avg_trade_duration(self) -> float:
        """
        Calculate average trade duration.

        Returns:
            Average duration in hours
        """
        if not self.portfolio.trades:
            return 0.0

        total_duration = sum(trade.duration for trade in self.portfolio.trades)
        avg_seconds = total_duration / len(self.portfolio.trades)

        return avg_seconds / 3600  # Convert to hours

    def print_summary(self):
        """Print formatted metrics summary."""
        metrics = self.calculate_all()

        print("\n" + "=" * 70)
        print("BACKTEST PERFORMANCE METRICS")
        print("=" * 70)

        print("\nRETURNS")
        print(f"  Initial Capital:    ${metrics['initial_capital']:,.2f}")
        print(f"  Final Value:        ${metrics['final_value']:,.2f}")
        print(f"  Total Return:       {metrics['total_return']:>8.2f}%")
        print(f"  Annual Return:      {metrics['annual_return']:>8.2f}%")

        print("\nRISK METRICS")
        print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:>8.2f}")
        print(f"  Max Drawdown:       {metrics['max_drawdown']:>8.2f}%")
        print(f"  Max DD Duration:    {metrics['max_drawdown_duration']:>8} bars")

        print("\nTRADE STATISTICS")
        print(f"  Total Trades:       {metrics['total_trades']:>8}")
        print(f"  Winning Trades:     {metrics['winning_trades']:>8}")
        print(f"  Losing Trades:      {metrics['losing_trades']:>8}")
        print(f"  Win Rate:           {metrics['win_rate']:>8.2f}%")

        print("\nPROFIT METRICS")
        print(f"  Total Profit:       ${metrics['total_profit']:>8,.2f}")
        print(f"  Total Loss:         ${metrics['total_loss']:>8,.2f}")
        print(f"  Profit Factor:      {metrics['profit_factor']:>8.2f}")
        print(f"  Avg Win:            ${metrics['avg_win']:>8,.2f}")
        print(f"  Avg Loss:           ${metrics['avg_loss']:>8,.2f}")
        print(f"  Avg Trade:          ${metrics['avg_trade']:>8,.2f}")

        print("\nSTREAKS")
        print(f"  Max Win Streak:     {metrics['max_win_streak']:>8}")
        print(f"  Max Loss Streak:    {metrics['max_loss_streak']:>8}")

        print("\nDURATION")
        print(f"  Avg Trade Duration: {metrics['avg_trade_duration']:>8.1f} hours")

        print("\n" + "=" * 70)
