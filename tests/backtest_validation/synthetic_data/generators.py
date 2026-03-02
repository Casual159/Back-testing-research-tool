"""
Deterministic synthetic market data generators for backtesting validation.

Every generator accepts a `seed` parameter and uses np.random.default_rng(seed)
for full reproducibility. The generated data is structurally valid OHLCV
(high >= max(open, close), low <= min(open, close), volume > 0) with a
DatetimeIndex matching the format expected by BacktestEngine.

These generators serve as the foundation for all validation tests — they
eliminate dependency on real market data and enable testing with known
statistical properties.
"""

import numpy as np
import pandas as pd


def generate_ohlcv(
    close_prices: np.ndarray,
    start_date: str = "2024-01-01",
    freq: str = "1h",
    spread_pct: float = 0.002,
    volume_base: float = 1000.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Core builder: takes a close price array, generates realistic OHLCV.

    Produces open/high/low from close with controlled noise while
    maintaining OHLCV validity invariants:
        high >= max(open, close)
        low  <= min(open, close)
        volume > 0

    Args:
        close_prices: Array of close prices (the "truth" signal).
        start_date: Start of the DatetimeIndex.
        freq: Frequency for pd.date_range (e.g., "1h", "1d").
        spread_pct: Controls high/low spread around open/close.
        volume_base: Mean volume per bar.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns [open, high, low, close, volume]
        and DatetimeIndex named 'open_time'.
    """
    rng = np.random.default_rng(seed)
    n = len(close_prices)
    close = close_prices.astype(float)

    # Open = previous close + small gap noise
    open_prices = np.empty(n)
    open_prices[0] = close[0] * (1 + rng.normal(0, spread_pct * 0.1))
    open_prices[1:] = close[:-1] * (1 + rng.normal(0, spread_pct * 0.1, size=n - 1))

    # High >= max(open, close), Low <= min(open, close)
    bar_max = np.maximum(open_prices, close)
    bar_min = np.minimum(open_prices, close)
    high = bar_max + np.abs(rng.normal(0, spread_pct, size=n)) * close
    low = bar_min - np.abs(rng.normal(0, spread_pct, size=n)) * close

    # Ensure low > 0 (crypto prices are always positive)
    low = np.maximum(low, close * 0.001)

    # Volume with some noise
    volume = volume_base * (1 + np.abs(rng.normal(0, 0.5, size=n)))

    index = pd.date_range(start=start_date, periods=n, freq=freq, name="open_time")

    return pd.DataFrame(
        {
            "open": open_prices,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def generate_trending(
    n_bars: int = 500,
    start_price: float = 100.0,
    drift_per_bar: float = 0.0002,
    volatility: float = 0.005,
    seed: int = 42,
    **kwargs,
) -> pd.DataFrame:
    """Generate trending data using geometric Brownian motion.

    close[i] = close[i-1] * exp(drift + volatility * Z), Z ~ N(0,1)

    Use positive drift_per_bar for uptrend, negative for downtrend.

    Args:
        n_bars: Number of OHLCV bars.
        start_price: Initial close price.
        drift_per_bar: Mean return per bar (0.0002 = ~0.02% per bar).
        volatility: Standard deviation of returns per bar.
        seed: Random seed.

    Returns:
        Valid OHLCV DataFrame with DatetimeIndex.
    """
    rng = np.random.default_rng(seed)
    log_returns = rng.normal(drift_per_bar, volatility, size=n_bars)
    log_returns[0] = 0  # First bar starts at start_price
    close = start_price * np.exp(np.cumsum(log_returns))

    return generate_ohlcv(close, seed=seed + 1, **kwargs)


def generate_ranging(
    n_bars: int = 500,
    center_price: float = 100.0,
    amplitude: float = 5.0,
    mean_reversion_speed: float = 0.05,
    noise_std: float = 0.5,
    seed: int = 42,
    **kwargs,
) -> pd.DataFrame:
    """Generate mean-reverting ranging data via Ornstein-Uhlenbeck process.

    dp = theta * (mu - p) * dt + sigma * dW

    Produces oscillation around center_price with bounded range.

    Args:
        n_bars: Number of OHLCV bars.
        center_price: Mean-reversion target.
        amplitude: Controls the typical deviation from center.
        mean_reversion_speed: Theta parameter (higher = faster reversion).
        noise_std: Innovation noise standard deviation.
        seed: Random seed.

    Returns:
        Valid OHLCV DataFrame with DatetimeIndex.
    """
    rng = np.random.default_rng(seed)
    close = np.empty(n_bars)
    close[0] = center_price

    for i in range(1, n_bars):
        dp = mean_reversion_speed * (center_price - close[i - 1]) + noise_std * rng.normal()
        close[i] = close[i - 1] + dp

    # Ensure prices stay positive
    close = np.maximum(close, center_price * 0.5)

    return generate_ohlcv(close, seed=seed + 1, **kwargs)


def generate_volatile_spikes(
    n_bars: int = 500,
    base_price: float = 100.0,
    base_volatility: float = 0.003,
    spike_magnitude: float = 0.10,
    spike_frequency: float = 0.02,
    seed: int = 42,
    **kwargs,
) -> pd.DataFrame:
    """Generate data with occasional large price spikes.

    Normal bars: small random walk with base_volatility.
    Spike bars (occurring with spike_frequency probability):
    jump by spike_magnitude * current_price.

    Args:
        n_bars: Number of OHLCV bars.
        base_price: Starting price.
        base_volatility: Normal bar-to-bar volatility.
        spike_magnitude: Size of spike as fraction of price (0.10 = 10%).
        spike_frequency: Probability of spike on any given bar.
        seed: Random seed.

    Returns:
        Valid OHLCV DataFrame with DatetimeIndex.
    """
    rng = np.random.default_rng(seed)
    close = np.empty(n_bars)
    close[0] = base_price

    for i in range(1, n_bars):
        if rng.random() < spike_frequency:
            # Spike: random direction, large magnitude
            direction = rng.choice([-1, 1])
            close[i] = close[i - 1] * (1 + direction * spike_magnitude)
        else:
            # Normal: small random walk
            close[i] = close[i - 1] * (1 + rng.normal(0, base_volatility))

    close = np.maximum(close, 1.0)  # Floor at 1.0

    return generate_ohlcv(close, seed=seed + 1, **kwargs)


def generate_flat(
    n_bars: int = 200,
    price: float = 100.0,
    start_date: str = "2024-01-01",
    freq: str = "1h",
) -> pd.DataFrame:
    """Generate perfectly flat price data.

    All OHLCV values are constant (close=open=high=low=price).
    Useful for testing edge cases: zero volatility, zero drawdown, zero return.

    No randomness — fully deterministic without a seed.

    Args:
        n_bars: Number of bars.
        price: Constant price for all bars.
        start_date: Start of DatetimeIndex.
        freq: Frequency.

    Returns:
        Flat OHLCV DataFrame.
    """
    index = pd.date_range(start=start_date, periods=n_bars, freq=freq, name="open_time")
    return pd.DataFrame(
        {
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": 1000.0,
        },
        index=index,
    )


def generate_regime_sequence(
    regime_specs: list,
    seed: int = 42,
    start_date: str = "2024-01-01",
    freq: str = "1h",
) -> pd.DataFrame:
    """Generate concatenated regime data from specifications.

    Each spec is a dict: {"type": "trending"/"ranging"/"volatile"/"flat",
                          "n_bars": int, **kwargs}

    Segments are stitched together with smooth 5-bar linear transitions.
    DatetimeIndex is continuous across all segments.

    Args:
        regime_specs: List of regime specification dicts.
        seed: Base random seed (each segment uses seed+i).
        start_date: Start of DatetimeIndex.
        freq: Frequency.

    Returns:
        Combined OHLCV DataFrame with continuous DatetimeIndex.
    """
    generators = {
        "trending": _generate_trending_closes,
        "ranging": _generate_ranging_closes,
        "volatile": _generate_volatile_closes,
        "flat": _generate_flat_closes,
    }

    all_closes = []
    for i, spec in enumerate(regime_specs):
        regime_type = spec.pop("type")
        n_bars = spec.pop("n_bars")
        gen_fn = generators[regime_type]
        segment = gen_fn(n_bars=n_bars, seed=seed + i, **spec)

        if all_closes:
            # Smooth transition: blend last 5 bars of previous with first 5 of new
            blend_len = min(5, len(all_closes), len(segment))
            for j in range(blend_len):
                alpha = (j + 1) / (blend_len + 1)
                idx = len(all_closes) - blend_len + j
                all_closes[idx] = (1 - alpha) * all_closes[idx] + alpha * segment[j]

        all_closes.extend(segment.tolist())

    close_prices = np.array(all_closes)
    return generate_ohlcv(close_prices, start_date=start_date, freq=freq, seed=seed + 100)


def _generate_trending_closes(
    n_bars: int = 100,
    start_price: float = 100.0,
    drift_per_bar: float = 0.0002,
    volatility: float = 0.005,
    seed: int = 42,
) -> np.ndarray:
    """Generate close prices for a trending regime (GBM)."""
    rng = np.random.default_rng(seed)
    log_returns = rng.normal(drift_per_bar, volatility, size=n_bars)
    log_returns[0] = 0
    return start_price * np.exp(np.cumsum(log_returns))


def _generate_ranging_closes(
    n_bars: int = 100,
    center_price: float = 100.0,
    amplitude: float = 5.0,
    mean_reversion_speed: float = 0.05,
    noise_std: float = 0.5,
    seed: int = 42,
) -> np.ndarray:
    """Generate close prices for a ranging regime (OU process)."""
    rng = np.random.default_rng(seed)
    close = np.empty(n_bars)
    close[0] = center_price
    for i in range(1, n_bars):
        dp = mean_reversion_speed * (center_price - close[i - 1]) + noise_std * rng.normal()
        close[i] = close[i - 1] + dp
    return np.maximum(close, center_price * 0.5)


def _generate_volatile_closes(
    n_bars: int = 100,
    base_price: float = 100.0,
    base_volatility: float = 0.003,
    spike_magnitude: float = 0.10,
    spike_frequency: float = 0.02,
    seed: int = 42,
) -> np.ndarray:
    """Generate close prices with volatile spikes."""
    rng = np.random.default_rng(seed)
    close = np.empty(n_bars)
    close[0] = base_price
    for i in range(1, n_bars):
        if rng.random() < spike_frequency:
            direction = rng.choice([-1, 1])
            close[i] = close[i - 1] * (1 + direction * spike_magnitude)
        else:
            close[i] = close[i - 1] * (1 + rng.normal(0, base_volatility))
    return np.maximum(close, 1.0)


def _generate_flat_closes(
    n_bars: int = 100,
    price: float = 100.0,
    seed: int = 42,
) -> np.ndarray:
    """Generate constant close prices."""
    return np.full(n_bars, price)
