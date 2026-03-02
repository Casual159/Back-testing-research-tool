"""
Self-tests for synthetic data generators.

WHY: Generators are test infrastructure. If they produce invalid OHLCV data
(e.g., low > high, negative volume, non-monotonic timestamps), all downstream
tests would give false results. These tests validate the generators themselves.

RISK MITIGATED: Invalid synthetic data causing false positives/negatives in
bias detection, metric validation, and regression tests.
"""

import pandas as pd
import pytest

from .generators import (
    generate_flat,
    generate_ranging,
    generate_regime_sequence,
    generate_trending,
    generate_volatile_spikes,
)


class TestOHLCVValidity:
    """Validate structural invariants that every OHLCV DataFrame must satisfy.

    These invariants are assumed by BacktestEngine, TechnicalIndicators,
    and all strategy code. Breaking them would produce silent errors.
    """

    @pytest.mark.parametrize(
        "generator,kwargs",
        [
            (generate_trending, {"n_bars": 200, "seed": 42}),
            (generate_trending, {"n_bars": 200, "drift_per_bar": -0.0003, "seed": 99}),
            (generate_ranging, {"n_bars": 200, "seed": 42}),
            (generate_volatile_spikes, {"n_bars": 200, "seed": 42}),
            (generate_flat, {"n_bars": 200}),
        ],
    )
    def test_ohlcv_invariants(self, generator, kwargs):
        """high >= max(open, close) and low <= min(open, close) on every bar."""
        df = generator(**kwargs)

        bar_max = df[["open", "close"]].max(axis=1)
        bar_min = df[["open", "close"]].min(axis=1)

        assert (df["high"] >= bar_max - 1e-10).all(), "high must be >= max(open, close)"
        assert (df["low"] <= bar_min + 1e-10).all(), "low must be <= min(open, close)"

    @pytest.mark.parametrize(
        "generator,kwargs",
        [
            (generate_trending, {"n_bars": 200, "seed": 42}),
            (generate_ranging, {"n_bars": 200, "seed": 42}),
            (generate_volatile_spikes, {"n_bars": 200, "seed": 42}),
            (generate_flat, {"n_bars": 200}),
        ],
    )
    def test_positive_prices(self, generator, kwargs):
        """All prices must be strictly positive (crypto context)."""
        df = generator(**kwargs)
        for col in ["open", "high", "low", "close"]:
            assert (df[col] > 0).all(), f"{col} must be positive"

    @pytest.mark.parametrize(
        "generator,kwargs",
        [
            (generate_trending, {"n_bars": 200, "seed": 42}),
            (generate_ranging, {"n_bars": 200, "seed": 42}),
            (generate_volatile_spikes, {"n_bars": 200, "seed": 42}),
            (generate_flat, {"n_bars": 200}),
        ],
    )
    def test_positive_volume(self, generator, kwargs):
        """Volume must be strictly positive."""
        df = generator(**kwargs)
        assert (df["volume"] > 0).all(), "volume must be positive"

    @pytest.mark.parametrize(
        "generator,kwargs",
        [
            (generate_trending, {"n_bars": 200, "seed": 42}),
            (generate_ranging, {"n_bars": 200, "seed": 42}),
            (generate_volatile_spikes, {"n_bars": 200, "seed": 42}),
            (generate_flat, {"n_bars": 200}),
        ],
    )
    def test_monotonic_datetime_index(self, generator, kwargs):
        """DatetimeIndex must be strictly monotonic (no duplicates, no gaps)."""
        df = generator(**kwargs)
        assert isinstance(df.index, pd.DatetimeIndex), "Index must be DatetimeIndex"
        assert df.index.is_monotonic_increasing, "Index must be monotonic increasing"
        assert not df.index.has_duplicates, "Index must not have duplicate timestamps"

    @pytest.mark.parametrize(
        "generator,kwargs",
        [
            (generate_trending, {"n_bars": 200, "seed": 42}),
            (generate_ranging, {"n_bars": 200, "seed": 42}),
            (generate_volatile_spikes, {"n_bars": 200, "seed": 42}),
            (generate_flat, {"n_bars": 200}),
        ],
    )
    def test_required_columns(self, generator, kwargs):
        """DataFrame must have exactly the columns BacktestEngine expects."""
        df = generator(**kwargs)
        required = {"open", "high", "low", "close", "volume"}
        assert set(df.columns) == required, f"Expected columns {required}, got {set(df.columns)}"

    @pytest.mark.parametrize(
        "generator,kwargs",
        [
            (generate_trending, {"n_bars": 300, "seed": 42}),
            (generate_ranging, {"n_bars": 300, "seed": 42}),
            (generate_volatile_spikes, {"n_bars": 300, "seed": 42}),
            (generate_flat, {"n_bars": 300}),
        ],
    )
    def test_correct_length(self, generator, kwargs):
        """DataFrame has the requested number of bars."""
        df = generator(**kwargs)
        assert len(df) == kwargs["n_bars"]


class TestDeterminism:
    """Verify that generators produce identical output for the same seed.

    WHY: Non-deterministic generators would make all downstream tests flaky.
    This is the foundational guarantee of the entire validation framework.
    """

    def test_trending_deterministic(self):
        """Same seed produces bit-identical DataFrames."""
        df1 = generate_trending(n_bars=100, seed=42)
        df2 = generate_trending(n_bars=100, seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_ranging_deterministic(self):
        df1 = generate_ranging(n_bars=100, seed=42)
        df2 = generate_ranging(n_bars=100, seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_volatile_deterministic(self):
        df1 = generate_volatile_spikes(n_bars=100, seed=42)
        df2 = generate_volatile_spikes(n_bars=100, seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_differ(self):
        """Different seeds produce different data."""
        df1 = generate_trending(n_bars=100, seed=42)
        df2 = generate_trending(n_bars=100, seed=99)
        assert not df1["close"].equals(df2["close"])


class TestTrendingBehavior:
    """Verify that trending generators produce expected statistical properties."""

    def test_uptrend_positive_return(self):
        """Positive drift produces net positive price change over 500 bars."""
        df = generate_trending(n_bars=500, drift_per_bar=0.0003, seed=42)
        assert df["close"].iloc[-1] > df["close"].iloc[0], "Uptrend should end higher"

    def test_downtrend_negative_return(self):
        """Negative drift produces net negative price change."""
        df = generate_trending(n_bars=500, drift_per_bar=-0.0003, seed=42)
        assert df["close"].iloc[-1] < df["close"].iloc[0], "Downtrend should end lower"

    def test_zero_drift_roughly_flat(self):
        """Zero drift should produce roughly flat prices (within noise)."""
        df = generate_trending(n_bars=500, drift_per_bar=0.0, volatility=0.001, seed=42)
        total_return = (df["close"].iloc[-1] / df["close"].iloc[0]) - 1
        assert abs(total_return) < 0.20, "Zero drift should be roughly flat"


class TestRangingBehavior:
    """Verify that ranging data stays bounded around center price."""

    def test_ranging_stays_bounded(self):
        """Close prices stay within reasonable bounds of center_price."""
        center = 100.0
        df = generate_ranging(n_bars=500, center_price=center, amplitude=5.0, seed=42)

        # With OU process and these parameters, 99.7% should be within 3*amplitude
        max_deviation = (df["close"] - center).abs().max()
        assert max_deviation < 30, f"Max deviation {max_deviation} too large for ranging data"

    def test_ranging_mean_near_center(self):
        """Mean close price is near the center price."""
        center = 100.0
        df = generate_ranging(n_bars=1000, center_price=center, seed=42)
        assert abs(df["close"].mean() - center) < 5.0, "Mean should be near center"


class TestVolatileSpikes:
    """Verify that volatile spike data has expected spike characteristics."""

    def test_has_large_moves(self):
        """At least one bar-to-bar return exceeds half the spike magnitude."""
        df = generate_volatile_spikes(
            n_bars=500, spike_magnitude=0.10, spike_frequency=0.02, seed=42
        )
        returns = df["close"].pct_change().abs()
        assert returns.max() > 0.05, "Should have at least one large move"


class TestFlatData:
    """Verify that flat data is truly constant."""

    def test_flat_prices_constant(self):
        """All close prices are exactly equal."""
        df = generate_flat(n_bars=100, price=100.0)
        assert (df["close"] == 100.0).all(), "Flat data close must be constant"
        assert (df["open"] == 100.0).all(), "Flat data open must be constant"
        assert (df["high"] == 100.0).all(), "Flat data high must be constant"
        assert (df["low"] == 100.0).all(), "Flat data low must be constant"


class TestRegimeSequence:
    """Verify that concatenated regime sequences are structurally valid."""

    def test_continuous_index(self):
        """DatetimeIndex is monotonic across stitched segments."""
        specs = [
            {"type": "trending", "n_bars": 100, "drift_per_bar": 0.0003},
            {"type": "ranging", "n_bars": 100},
            {"type": "volatile", "n_bars": 100},
        ]
        # Need to copy specs since generate_regime_sequence pops keys
        import copy

        df = generate_regime_sequence(copy.deepcopy(specs), seed=42)
        assert df.index.is_monotonic_increasing
        assert not df.index.has_duplicates

    def test_correct_total_length(self):
        """Total bars equals sum of segment bars."""
        import copy

        specs = [
            {"type": "trending", "n_bars": 100},
            {"type": "flat", "n_bars": 50},
            {"type": "ranging", "n_bars": 100},
        ]
        df = generate_regime_sequence(copy.deepcopy(specs), seed=42)
        assert len(df) == 250

    def test_ohlcv_validity_across_regimes(self):
        """OHLCV invariants hold across stitched regime transitions."""
        import copy

        specs = [
            {"type": "trending", "n_bars": 100, "drift_per_bar": 0.001},
            {"type": "ranging", "n_bars": 100},
        ]
        df = generate_regime_sequence(copy.deepcopy(specs), seed=42)

        bar_max = df[["open", "close"]].max(axis=1)
        bar_min = df[["open", "close"]].min(axis=1)
        assert (df["high"] >= bar_max - 1e-10).all()
        assert (df["low"] <= bar_min + 1e-10).all()
