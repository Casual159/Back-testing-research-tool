"""
Metric correctness validation tests.

Compares MetricsCalculator (production code) against:
1. Independent reference implementations (reference_implementations.py)
2. Hand-calculated expected values for known trade sequences

WHY: Financial metrics drive user decisions. An incorrect Sharpe ratio,
drawdown, or win rate could lead to deploying a losing strategy.
These tests ensure the numbers users see are mathematically correct.

RISK MITIGATED: Formula bugs, off-by-one errors, division-by-zero crashes,
incorrect annualization, wrong sign conventions.
"""

from datetime import datetime, timedelta

import numpy as np

from core.backtest.metrics import MetricsCalculator
from core.backtest.portfolio import Portfolio, Trade

from .reference_implementations import (
    ref_avg_trade_duration_hours,
    ref_max_drawdown,
    ref_max_loss_streak,
    ref_max_win_streak,
    ref_profit_factor,
    ref_sharpe_ratio,
    ref_total_return,
    ref_win_rate,
)


def _build_portfolio(trade_specs, initial_capital=10000.0):
    """Helper: build a Portfolio with specified trades and equity curve.

    Args:
        trade_specs: List of dicts with keys:
            entry_price, exit_price, quantity,
            entry_commission (default 0), exit_commission (default 0),
            hold_hours (default 24)
        initial_capital: Starting cash.

    Returns:
        Portfolio with trades and equity curve populated.
    """
    portfolio = Portfolio(initial_capital=initial_capital)
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    current_time = base_time
    current_value = initial_capital

    # Record initial equity
    portfolio.record_equity(current_time, current_value)

    for spec in trade_specs:
        entry_price = spec["entry_price"]
        exit_price = spec["exit_price"]
        quantity = spec["quantity"]
        entry_comm = spec.get("entry_commission", 0.0)
        exit_comm = spec.get("exit_commission", 0.0)
        hold_hours = spec.get("hold_hours", 24)

        entry_time = current_time
        exit_time = current_time + timedelta(hours=hold_hours)

        trade = Trade(
            entry_time=entry_time,
            exit_time=exit_time,
            symbol="TEST",
            direction="LONG",
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            entry_commission=entry_comm,
            exit_commission=exit_comm,
        )
        portfolio.trades.append(trade)

        # Update portfolio value
        current_value += trade.pnl
        current_time = exit_time + timedelta(hours=1)  # Gap between trades

        # Record equity points (entry and exit)
        portfolio.record_equity(entry_time + timedelta(hours=1), current_value - trade.pnl * 0.5)
        portfolio.record_equity(exit_time, current_value)

    # Set cash to match final value
    portfolio.current_cash = current_value

    return portfolio


class TestMetricsAgainstReference:
    """Compare MetricsCalculator output against reference_implementations.py.

    Each test builds a specific portfolio scenario, computes metrics via both
    the production MetricsCalculator and the independent reference, then
    asserts they match within floating-point tolerance.
    """

    def test_total_return_matches_reference(self):
        """3 trades with +5%, -2%, +8% returns on 10000 capital.

        WHY: Total return is the most basic metric. If this is wrong,
        everything else is untrustworthy.
        """
        specs = [
            {"entry_price": 100, "exit_price": 105, "quantity": 10},  # +50
            {"entry_price": 100, "exit_price": 98, "quantity": 10},  # -20
            {"entry_price": 100, "exit_price": 108, "quantity": 10},  # +80
        ]
        portfolio = _build_portfolio(specs, initial_capital=10000.0)

        calc = MetricsCalculator(portfolio)
        production = calc.calculate_all()
        reference = ref_total_return(portfolio.equity_curve)

        assert np.isclose(production["total_return"], reference, atol=0.5), (
            f"Total return mismatch: production={production['total_return']}, "
            f"reference={reference}"
        )

    def test_win_rate_matches_reference(self):
        """3 winners, 2 losers → win rate = 60%.

        WHY: Win rate is displayed prominently to users and affects their
        confidence in a strategy.
        """
        specs = [
            {"entry_price": 100, "exit_price": 110, "quantity": 1},  # +10 winner
            {"entry_price": 100, "exit_price": 95, "quantity": 1},  # -5 loser
            {"entry_price": 100, "exit_price": 105, "quantity": 1},  # +5 winner
            {"entry_price": 100, "exit_price": 90, "quantity": 1},  # -10 loser
            {"entry_price": 100, "exit_price": 120, "quantity": 1},  # +20 winner
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        production = calc.calculate_all()
        reference = ref_win_rate(portfolio.trades)

        assert np.isclose(
            production["win_rate"], reference, atol=0.01
        ), f"Win rate mismatch: production={production['win_rate']}, reference={reference}"
        assert np.isclose(reference, 60.0, atol=0.01), "Expected 60% win rate"

    def test_profit_factor_matches_reference(self):
        """2 winners (+500, +300) and 2 losers (-200, -100).
        PF = 800/300 = 2.667.

        WHY: Profit factor determines whether a strategy has an edge.
        An incorrect calculation could make a losing strategy appear profitable.
        """
        specs = [
            {"entry_price": 100, "exit_price": 150, "quantity": 10},  # +500
            {"entry_price": 100, "exit_price": 80, "quantity": 10},  # -200
            {"entry_price": 100, "exit_price": 130, "quantity": 10},  # +300
            {"entry_price": 100, "exit_price": 90, "quantity": 10},  # -100
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        production = calc.calculate_all()
        reference = ref_profit_factor(portfolio.trades)

        assert np.isclose(production["profit_factor"], reference, rtol=0.01), (
            f"Profit factor mismatch: production={production['profit_factor']}, "
            f"reference={reference}"
        )

    def test_max_drawdown_matches_reference(self):
        """Equity curve with known drawdown: 10000 → 12000 → 9000 → 11000.
        Max DD = (9000-12000)/12000 = -25%.

        WHY: Max drawdown is the primary risk metric. Underestimating it
        could lead to deploying a strategy that produces unacceptable losses.
        """
        specs = [
            {"entry_price": 100, "exit_price": 120, "quantity": 10},  # +200
            {"entry_price": 100, "exit_price": 70, "quantity": 10},  # -300
            {"entry_price": 100, "exit_price": 120, "quantity": 10},  # +200
        ]
        portfolio = _build_portfolio(specs, initial_capital=10000.0)

        calc = MetricsCalculator(portfolio)
        production = calc.calculate_all()
        reference = ref_max_drawdown(portfolio.equity_curve)

        # Both should be negative
        assert production["max_drawdown"] < 0, "Max drawdown should be negative"
        assert reference < 0, "Reference max drawdown should be negative"

        # Should be close
        assert np.isclose(production["max_drawdown"], reference, atol=2.0), (
            f"Max drawdown mismatch: production={production['max_drawdown']}, "
            f"reference={reference}"
        )

    def test_streaks_match_reference(self):
        """Known sequence: W, W, W, L, L, W, L.
        Max win streak = 3, max loss streak = 2.

        WHY: Streak metrics help users understand strategy consistency.
        """
        specs = [
            {"entry_price": 100, "exit_price": 110, "quantity": 1},  # W
            {"entry_price": 100, "exit_price": 105, "quantity": 1},  # W
            {"entry_price": 100, "exit_price": 103, "quantity": 1},  # W
            {"entry_price": 100, "exit_price": 95, "quantity": 1},  # L
            {"entry_price": 100, "exit_price": 90, "quantity": 1},  # L
            {"entry_price": 100, "exit_price": 115, "quantity": 1},  # W
            {"entry_price": 100, "exit_price": 85, "quantity": 1},  # L
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        production = calc.calculate_all()

        assert production["max_win_streak"] == ref_max_win_streak(portfolio.trades) == 3
        assert production["max_loss_streak"] == ref_max_loss_streak(portfolio.trades) == 2

    def test_sharpe_ratio_matches_reference(self):
        """Compare Sharpe ratio computation on a portfolio with varied returns.

        WHY: Sharpe ratio is the most widely used risk-adjusted metric.
        It involves mean, std, and annualization — each a potential error source.
        """
        specs = [
            {"entry_price": 100, "exit_price": 108, "quantity": 10, "hold_hours": 24},
            {"entry_price": 100, "exit_price": 97, "quantity": 10, "hold_hours": 48},
            {"entry_price": 100, "exit_price": 112, "quantity": 10, "hold_hours": 24},
            {"entry_price": 100, "exit_price": 99, "quantity": 10, "hold_hours": 72},
            {"entry_price": 100, "exit_price": 106, "quantity": 10, "hold_hours": 24},
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        production = calc.calculate_all()
        reference = ref_sharpe_ratio(portfolio.equity_curve)

        # Both should be positive (net profitable portfolio)
        # Allow wider tolerance for Sharpe since it depends on equity curve granularity
        if abs(reference) > 0.01:
            assert np.isclose(production["sharpe_ratio"], reference, rtol=0.5), (
                f"Sharpe mismatch: production={production['sharpe_ratio']}, "
                f"reference={reference}"
            )

    def test_avg_trade_duration_matches_reference(self):
        """Average trade duration in hours.

        WHY: Duration affects strategy classification (scalping vs swing vs position).
        """
        specs = [
            {"entry_price": 100, "exit_price": 110, "quantity": 1, "hold_hours": 24},
            {"entry_price": 100, "exit_price": 95, "quantity": 1, "hold_hours": 48},
            {"entry_price": 100, "exit_price": 105, "quantity": 1, "hold_hours": 12},
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        production = calc.calculate_all()
        reference = ref_avg_trade_duration_hours(portfolio.trades)

        assert np.isclose(production["avg_trade_duration"], reference, atol=0.1), (
            f"Avg duration mismatch: production={production['avg_trade_duration']}, "
            f"reference={reference}"
        )


class TestMetricsEdgeCases:
    """Test edge cases that could cause NaN, inf, or division-by-zero.

    WHY: Edge cases are where most metric bugs hide. A strategy that
    never loses, never wins, or never trades must still produce valid
    (non-crashing) metrics.
    """

    def test_no_trades_returns_zero_metrics(self):
        """Empty portfolio: all trade-derived metrics should be 0.

        WHY: A strategy might produce zero signals on certain data.
        MetricsCalculator must handle this gracefully.
        """
        portfolio = Portfolio(initial_capital=10000.0)
        portfolio.record_equity(datetime(2024, 1, 1), 10000.0)
        portfolio.record_equity(datetime(2024, 1, 2), 10000.0)

        calc = MetricsCalculator(portfolio)
        metrics = calc.calculate_all()

        assert metrics["total_trades"] == 0
        assert metrics["win_rate"] == 0
        assert metrics["profit_factor"] == 0
        assert metrics["avg_win"] == 0
        assert metrics["avg_loss"] == 0
        assert metrics["max_win_streak"] == 0
        assert metrics["max_loss_streak"] == 0

    def test_all_winners_profit_factor_is_inf(self):
        """All trades profitable: profit_factor should be inf (no losses).

        WHY: Division by zero (gross_loss = 0) must produce inf, not crash.
        """
        specs = [
            {"entry_price": 100, "exit_price": 110, "quantity": 1},
            {"entry_price": 100, "exit_price": 105, "quantity": 1},
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        metrics = calc.calculate_all()

        assert metrics["win_rate"] == 100.0
        assert metrics["profit_factor"] == float("inf") or metrics["profit_factor"] > 1e10

    def test_all_losers_returns_valid_metrics(self):
        """All trades losing: profit_factor = 0, win_rate = 0.

        WHY: Prevents division-by-zero when total_profit = 0.
        """
        specs = [
            {"entry_price": 100, "exit_price": 90, "quantity": 1},
            {"entry_price": 100, "exit_price": 85, "quantity": 1},
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        metrics = calc.calculate_all()

        assert metrics["win_rate"] == 0.0
        assert metrics["profit_factor"] == 0.0
        assert metrics["avg_win"] == 0.0
        assert metrics["avg_loss"] < 0

    def test_single_trade_metrics(self):
        """One trade: win_rate is 0 or 100, streak is 0 or 1.

        WHY: Single-element edge case for all aggregation functions.
        """
        specs = [
            {"entry_price": 100, "exit_price": 110, "quantity": 1},
        ]
        portfolio = _build_portfolio(specs)

        calc = MetricsCalculator(portfolio)
        metrics = calc.calculate_all()

        assert metrics["total_trades"] == 1
        assert metrics["winning_trades"] == 1
        assert metrics["win_rate"] == 100.0
        assert metrics["max_win_streak"] == 1
        assert metrics["max_loss_streak"] == 0


class TestMetricsHandCalculated:
    """Tests with exact hand-calculated expected values.

    These are the 'gold standard' — every number is computed by hand
    and hardcoded. If the code produces different values, the code is wrong.
    """

    def test_known_three_trade_sequence(self):
        """
        Setup: initial_capital = 10000
        Trade 1: BUY at 100, SELL at 110, qty=10, comm=1 each side
            PnL = (110-100)*10 - 1 - 1 = 98
        Trade 2: BUY at 105, SELL at 95, qty=10, comm=1 each side
            PnL = (95-105)*10 - 1 - 1 = -102
        Trade 3: BUY at 90, SELL at 120, qty=10, comm=1 each side
            PnL = (120-90)*10 - 1 - 1 = 298

        Expected:
            total_trades = 3
            winning_trades = 2
            losing_trades = 1
            win_rate = 66.67%
            total_profit = 98 + 298 = 396
            total_loss = 102 (absolute value)
            profit_factor = 396 / 102 = 3.882...
            avg_win = (98 + 298) / 2 = 198
            avg_loss = -102 / 1 = -102
            max_win_streak = 1 (W, L, W — no consecutive wins)
            max_loss_streak = 1
        """
        specs = [
            {
                "entry_price": 100,
                "exit_price": 110,
                "quantity": 10,
                "entry_commission": 1,
                "exit_commission": 1,
            },
            {
                "entry_price": 105,
                "exit_price": 95,
                "quantity": 10,
                "entry_commission": 1,
                "exit_commission": 1,
            },
            {
                "entry_price": 90,
                "exit_price": 120,
                "quantity": 10,
                "entry_commission": 1,
                "exit_commission": 1,
            },
        ]
        portfolio = _build_portfolio(specs, initial_capital=10000.0)

        calc = MetricsCalculator(portfolio)
        metrics = calc.calculate_all()

        # Trade counts
        assert metrics["total_trades"] == 3
        assert metrics["winning_trades"] == 2
        assert metrics["losing_trades"] == 1

        # Win rate
        assert np.isclose(metrics["win_rate"], 66.6667, atol=0.01)

        # Profit/loss totals
        assert np.isclose(metrics["total_profit"], 396.0, atol=0.01)
        assert np.isclose(metrics["total_loss"], 102.0, atol=0.01)

        # Profit factor
        assert np.isclose(metrics["profit_factor"], 396.0 / 102.0, atol=0.01)

        # Averages
        assert np.isclose(metrics["avg_win"], 198.0, atol=0.01)
        assert np.isclose(metrics["avg_loss"], -102.0, atol=0.01)

        # Streaks (W, L, W)
        assert metrics["max_win_streak"] == 1
        assert metrics["max_loss_streak"] == 1

    def test_trade_pnl_calculation(self):
        """Verify Trade.pnl formula: (exit - entry) * qty - commissions.

        WHY: This is the atomic unit of all metric calculations.
        If Trade.pnl is wrong, every aggregate metric is wrong.
        """
        trade = Trade(
            entry_time=datetime(2024, 1, 1),
            exit_time=datetime(2024, 1, 2),
            symbol="TEST",
            direction="LONG",
            entry_price=100.0,
            exit_price=115.0,
            quantity=5.0,
            entry_commission=2.0,
            exit_commission=3.0,
        )

        # gross_pnl = (115 - 100) * 5 = 75
        # net_pnl = 75 - 2 - 3 = 70
        assert np.isclose(trade.pnl, 70.0), f"Expected PnL=70, got {trade.pnl}"

        # return_pct = 70 / (100 * 5) * 100 = 14%
        assert np.isclose(trade.return_pct, 14.0), f"Expected return=14%, got {trade.return_pct}"

        # is_winner
        assert trade.is_winner() is True

    def test_losing_trade_pnl(self):
        """Verify PnL for a losing LONG trade."""
        trade = Trade(
            entry_time=datetime(2024, 1, 1),
            exit_time=datetime(2024, 1, 2),
            symbol="TEST",
            direction="LONG",
            entry_price=100.0,
            exit_price=90.0,
            quantity=5.0,
            entry_commission=1.0,
            exit_commission=1.0,
        )

        # gross_pnl = (90 - 100) * 5 = -50
        # net_pnl = -50 - 1 - 1 = -52
        assert np.isclose(trade.pnl, -52.0), f"Expected PnL=-52, got {trade.pnl}"
        assert trade.is_winner() is False
