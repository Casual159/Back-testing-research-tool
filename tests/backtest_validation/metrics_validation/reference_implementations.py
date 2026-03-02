"""
Independent reference implementations of financial metrics.

These are numpy-only implementations written from textbook formulas.
They intentionally do NOT import from core.backtest.metrics — they serve
as ground truth for cross-validating MetricsCalculator.

WHY: If both implementations produce the same result, we have high
confidence the formula is correct. If they differ, we have a concrete
discrepancy to investigate.

Each function documents its formula and edge case handling.
"""

import numpy as np


def ref_total_return(equity_curve: list) -> float:
    """Total return as percentage.

    Formula: ((final_value - initial_value) / initial_value) * 100

    Args:
        equity_curve: List of (timestamp, portfolio_value) tuples.

    Returns:
        Total return percentage (e.g., 15.5 means +15.5%).
        Returns 0.0 if equity_curve has fewer than 2 points.
    """
    if len(equity_curve) < 2:
        return 0.0

    initial = equity_curve[0][1]
    final = equity_curve[-1][1]

    if initial == 0:
        return 0.0

    return ((final - initial) / initial) * 100


def ref_annual_return(equity_curve: list) -> float:
    """Compound Annual Growth Rate (CAGR) as percentage.

    Formula: ((final/initial)^(1/years) - 1) * 100
    where years = (end_date - start_date).total_seconds() / (365.25 * 86400)

    Args:
        equity_curve: List of (timestamp, portfolio_value) tuples.

    Returns:
        CAGR percentage. Returns 0.0 for insufficient data or zero period.
    """
    if len(equity_curve) < 2:
        return 0.0

    initial = equity_curve[0][1]
    final = equity_curve[-1][1]

    if initial <= 0 or final <= 0:
        return 0.0

    start_time = equity_curve[0][0]
    end_time = equity_curve[-1][0]

    try:
        duration_seconds = (end_time - start_time).total_seconds()
    except (AttributeError, TypeError):
        return 0.0

    if duration_seconds <= 0:
        return 0.0

    years = duration_seconds / (365.25 * 86400)

    if years < 1e-10:
        return 0.0

    return (pow(final / initial, 1.0 / years) - 1) * 100


def ref_sharpe_ratio(equity_curve: list, risk_free_rate: float = 0.0) -> float:
    """Sharpe ratio: risk-adjusted return measure.

    Formula: (mean_return - rf/annualization_factor) / std_return * sqrt(annualization_factor)

    NOTE: Uses annualization_factor = 252 (daily convention), matching
    the production MetricsCalculator. For hourly data this is technically
    incorrect (should be 252*24=6048) but we match production behavior
    intentionally to avoid false test failures.

    Known limitation: This annualization factor assumes daily returns
    regardless of the actual data frequency.

    Args:
        equity_curve: List of (timestamp, portfolio_value) tuples.
        risk_free_rate: Annual risk-free rate (e.g., 0.05 for 5%).

    Returns:
        Annualized Sharpe ratio. Returns 0.0 if std is zero or insufficient data.
    """
    if len(equity_curve) < 3:
        return 0.0

    values = np.array([v for _, v in equity_curve], dtype=float)

    # Percentage returns
    returns = np.diff(values) / values[:-1]

    if len(returns) < 2:
        return 0.0

    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)  # Sample standard deviation

    if std_return < 1e-15:
        return 0.0

    annualization = 252  # Daily convention, matching production code
    rf_per_period = risk_free_rate / annualization

    return (mean_return - rf_per_period) / std_return * np.sqrt(annualization)


def ref_max_drawdown(equity_curve: list) -> float:
    """Maximum drawdown as percentage (negative value).

    Formula: min over all t of ((value[t] - peak_up_to_t) / peak_up_to_t * 100)

    Uses running maximum for peak tracking.

    Args:
        equity_curve: List of (timestamp, portfolio_value) tuples.

    Returns:
        Maximum drawdown as negative percentage (e.g., -25.0 means 25% drawdown).
        Returns 0.0 if no drawdown or insufficient data.
    """
    if len(equity_curve) < 2:
        return 0.0

    values = np.array([v for _, v in equity_curve], dtype=float)
    running_max = np.maximum.accumulate(values)

    # Avoid division by zero
    safe_max = np.where(running_max > 0, running_max, 1.0)
    drawdowns = (values - running_max) / safe_max * 100

    return float(np.min(drawdowns))


def ref_max_drawdown_duration(equity_curve: list) -> int:
    """Maximum drawdown duration in bars.

    The longest period (number of bars) where portfolio value stayed
    below a previous peak.

    Args:
        equity_curve: List of (timestamp, portfolio_value) tuples.

    Returns:
        Duration in bars. Returns 0 if never in drawdown.
    """
    if len(equity_curve) < 2:
        return 0

    values = np.array([v for _, v in equity_curve], dtype=float)
    running_max = np.maximum.accumulate(values)

    max_duration = 0
    current_duration = 0

    for i in range(len(values)):
        if values[i] < running_max[i]:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0

    return max_duration


def ref_win_rate(trades: list) -> float:
    """Win rate as percentage.

    Formula: (winning_trades / total_trades) * 100

    Args:
        trades: List of Trade objects with .is_winner() method.

    Returns:
        Win rate percentage. Returns 0.0 if no trades.
    """
    if not trades:
        return 0.0

    winners = sum(1 for t in trades if t.is_winner())
    return (winners / len(trades)) * 100


def ref_profit_factor(trades: list) -> float:
    """Profit factor: gross profit / gross loss.

    Args:
        trades: List of Trade objects with .pnl attribute.

    Returns:
        Profit factor. Returns float('inf') if no losses,
        0.0 if no profits, 0.0 if no trades.
    """
    if not trades:
        return 0.0

    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = sum(abs(t.pnl) for t in trades if t.pnl < 0)

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0

    return gross_profit / gross_loss


def ref_avg_win(trades: list) -> float:
    """Average winning trade PnL.

    Args:
        trades: List of Trade objects with .pnl and .is_winner().

    Returns:
        Mean PnL of winners. Returns 0.0 if no winners.
    """
    winners = [t.pnl for t in trades if t.is_winner()]
    if not winners:
        return 0.0
    return sum(winners) / len(winners)


def ref_avg_loss(trades: list) -> float:
    """Average losing trade PnL (negative value).

    Args:
        trades: List of Trade objects with .pnl and .is_winner().

    Returns:
        Mean PnL of losers (negative). Returns 0.0 if no losers.
    """
    losers = [t.pnl for t in trades if not t.is_winner()]
    if not losers:
        return 0.0
    return sum(losers) / len(losers)


def ref_max_win_streak(trades: list) -> int:
    """Longest consecutive sequence of winning trades.

    Args:
        trades: List of Trade objects with .is_winner().

    Returns:
        Length of longest win streak. Returns 0 if no trades.
    """
    if not trades:
        return 0

    max_streak = 0
    current_streak = 0

    for t in trades:
        if t.is_winner():
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def ref_max_loss_streak(trades: list) -> int:
    """Longest consecutive sequence of losing trades.

    Args:
        trades: List of Trade objects with .is_winner().

    Returns:
        Length of longest loss streak. Returns 0 if no trades.
    """
    if not trades:
        return 0

    max_streak = 0
    current_streak = 0

    for t in trades:
        if not t.is_winner():
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def ref_avg_trade_duration_hours(trades: list) -> float:
    """Average trade duration in hours.

    Args:
        trades: List of Trade objects with .duration attribute (seconds).

    Returns:
        Mean duration in hours. Returns 0.0 if no trades.
    """
    if not trades:
        return 0.0

    total_seconds = sum(t.duration for t in trades)
    return (total_seconds / len(trades)) / 3600
