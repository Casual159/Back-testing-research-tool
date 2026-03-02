"""
Shared pytest fixtures for the backtest validation framework.

Provides:
- sys.path setup so all core imports resolve
- Seeded random generators for deterministic tests
- Pre-built OHLCV DataFrames for common scenarios
- Factory fixtures for creating strategies and running backtests
"""

import sys
from pathlib import Path

# Path setup: add project root and core/ so both import styles resolve:
#   - "from core.backtest.engine import ..." (project-root-relative)
#   - "from indicators.technical import ..." (core-relative, used by signal.py)
_project_root = str(Path(__file__).resolve().parents[2])
_core_root = str(Path(__file__).resolve().parents[2] / "core")
for p in (_project_root, _core_root):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from core.backtest.engine import BacktestEngine  # noqa: E402
from core.backtest.strategies.composition.composite_strategy import CompositeStrategy  # noqa: E402
from core.backtest.strategies.composition.condition import Condition  # noqa: E402
from core.backtest.strategies.composition.logic_tree import LogicTree  # noqa: E402
from core.backtest.strategies.composition.signal import IndicatorSignal  # noqa: E402

from .synthetic_data.generators import (  # noqa: E402
    generate_flat,
    generate_ranging,
    generate_trending,
    generate_volatile_spikes,
)

# ---------------------------------------------------------------------------
# Deterministic random seed fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seed() -> int:
    """Fixed random seed for all deterministic tests."""
    return 42


@pytest.fixture
def rng(seed) -> np.random.Generator:
    """Seeded numpy random generator."""
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# OHLCV DataFrame fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_ohlcv_trending_up() -> pd.DataFrame:
    """500-bar uptrending OHLCV data (positive drift GBM)."""
    return generate_trending(n_bars=500, drift_per_bar=0.0003, seed=42)


@pytest.fixture
def sample_ohlcv_trending_down() -> pd.DataFrame:
    """500-bar downtrending OHLCV data (negative drift GBM)."""
    return generate_trending(n_bars=500, drift_per_bar=-0.0003, seed=42)


@pytest.fixture
def sample_ohlcv_ranging() -> pd.DataFrame:
    """500-bar mean-reverting ranging OHLCV data (OU process)."""
    return generate_ranging(n_bars=500, center_price=100.0, amplitude=5.0, seed=42)


@pytest.fixture
def sample_ohlcv_volatile() -> pd.DataFrame:
    """500-bar data with occasional large price spikes."""
    return generate_volatile_spikes(n_bars=500, spike_magnitude=0.10, seed=42)


@pytest.fixture
def sample_ohlcv_flat() -> pd.DataFrame:
    """200-bar perfectly flat price data (close=100 every bar).
    For testing zero-volatility edge cases."""
    return generate_flat(n_bars=200, price=100.0)


# ---------------------------------------------------------------------------
# Strategy factory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_composite_strategy():
    """Factory fixture: create CompositeStrategy from IndicatorSignal lists.

    Usage:
        strategy = make_composite_strategy(
            entry_signals=[signal1, signal2],
            exit_signals=[signal3],
        )
    """

    def _make(
        entry_signals,
        exit_signals,
        name="test_strategy",
        regime_filter=None,
        logic="AND",
    ):
        if logic == "AND":
            entry_logic = LogicTree.AND(entry_signals)
            exit_logic = LogicTree.AND(exit_signals)
        else:
            entry_logic = LogicTree.OR(entry_signals)
            exit_logic = LogicTree.OR(exit_signals)

        return CompositeStrategy(
            name=name,
            entry_logic=entry_logic,
            exit_logic=exit_logic,
            regime_filter=regime_filter,
        )

    return _make


@pytest.fixture
def run_backtest():
    """Factory fixture: run BacktestEngine and return result dict.

    Disables regime detection by default for speed and isolation.
    Sets zero commission/slippage by default for predictable results.

    Usage:
        result = run_backtest(data, strategy)
        metrics = result["metrics"]
    """

    def _run(
        data,
        strategy,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        enable_regime_detection=False,
        position_size_pct=1.0,
    ):
        engine = BacktestEngine(
            data=data,
            strategy=strategy,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            enable_regime_detection=enable_regime_detection,
            position_size_pct=position_size_pct,
        )
        return engine.run()

    return _run


# ---------------------------------------------------------------------------
# Convenience signal fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sma_cross_above_signal():
    """SMA(5) cross_above SMA(20) — entry signal for trend-following."""
    return IndicatorSignal(
        name="sma5_cross_above_20",
        indicator="SMA",
        parameters={"period": 5},
        condition=Condition(operator="cross_above", threshold=0),
        # Note: cross_above with threshold=0 means "SMA crosses above 0"
        # For actual crossover we need two signals; this is a simplified version
    )


@pytest.fixture
def rsi_oversold_signal():
    """RSI(14) < 30 — buy signal for mean-reversion."""
    return IndicatorSignal(
        name="rsi_oversold",
        indicator="RSI",
        parameters={"period": 14},
        condition=Condition(operator="<", threshold=30.0),
    )


@pytest.fixture
def rsi_overbought_signal():
    """RSI(14) > 70 — sell signal for mean-reversion."""
    return IndicatorSignal(
        name="rsi_overbought",
        indicator="RSI",
        parameters={"period": 14},
        condition=Condition(operator=">", threshold=70.0),
    )
