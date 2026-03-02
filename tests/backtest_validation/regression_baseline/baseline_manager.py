"""
Regression baseline management: load, save, and compare baseline JSON files.

Baselines are version-controlled JSON files that store expected metric values
for deterministic backtests. When code changes cause metrics to drift beyond
tolerance, the test fails — forcing the developer to either fix the
regression or intentionally regenerate the baseline.

WHY: Silent performance regressions are the most insidious bugs in a
backtesting platform. A "small fix" to an indicator formula could change
Sharpe ratios across every strategy without anyone noticing.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

BASELINES_DIR = Path(__file__).parent / "baselines"


@dataclass
class MetricComparison:
    """Result of comparing a single metric against its baseline value."""

    metric: str
    baseline_value: float
    current_value: float
    tolerance: float
    passed: bool
    absolute_diff: float


@dataclass
class BaselineResult:
    """Result of comparing all metrics against a baseline."""

    passed: bool
    comparisons: list = field(default_factory=list)
    baseline_name: str = ""

    @property
    def failed_metrics(self) -> list:
        return [c for c in self.comparisons if not c.passed]

    def summary(self) -> str:
        """Human-readable summary of comparison results."""
        lines = [f"Baseline: {self.baseline_name}"]
        lines.append(f"Overall: {'PASS' if self.passed else 'FAIL'}")
        lines.append("")

        for c in self.comparisons:
            status = "OK" if c.passed else "FAIL"
            lines.append(
                f"  [{status}] {c.metric}: "
                f"baseline={c.baseline_value:.6f}, "
                f"current={c.current_value:.6f}, "
                f"diff={c.absolute_diff:.6f}, "
                f"tolerance={c.tolerance:.6f}"
            )

        return "\n".join(lines)


def load_baseline(name: str) -> dict:
    """Load a baseline JSON file by name.

    Args:
        name: Baseline name without .json extension (e.g., "sma_crossover_trending").

    Returns:
        Parsed JSON as dict.

    Raises:
        FileNotFoundError: If baseline file doesn't exist.
    """
    path = BASELINES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Baseline '{name}' not found at {path}. " f"Run baseline generation first."
        )

    with open(path) as f:
        return json.load(f)


def save_baseline(name: str, data: dict) -> Path:
    """Save a baseline JSON file.

    Args:
        name: Baseline name without .json extension.
        data: Dict to serialize (must contain 'metrics' and 'tolerance' keys).

    Returns:
        Path to the saved file.
    """
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    path = BASELINES_DIR / f"{name}.json"

    data["generated_at"] = datetime.now().isoformat()

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return path


def compare_against_baseline(
    name: str,
    current_metrics: dict,
    tolerance_overrides: Optional[dict] = None,
) -> BaselineResult:
    """Compare current backtest metrics against a stored baseline.

    For each metric in the baseline:
        passed = abs(current - baseline) <= tolerance

    Args:
        name: Baseline name to load.
        current_metrics: Dict of current metric values (from MetricsCalculator).
        tolerance_overrides: Optional dict of {metric: tolerance} to override
                           per-metric tolerances from the baseline.

    Returns:
        BaselineResult with detailed per-metric comparison.
    """
    baseline = load_baseline(name)
    baseline_metrics = baseline["metrics"]
    baseline_tolerances = baseline.get("tolerance", {})

    if tolerance_overrides:
        baseline_tolerances = {**baseline_tolerances, **tolerance_overrides}

    comparisons = []
    all_passed = True

    for metric, baseline_value in baseline_metrics.items():
        current_value = current_metrics.get(metric)

        if current_value is None:
            comparisons.append(
                MetricComparison(
                    metric=metric,
                    baseline_value=baseline_value,
                    current_value=float("nan"),
                    tolerance=0,
                    passed=False,
                    absolute_diff=float("inf"),
                )
            )
            all_passed = False
            continue

        tolerance = baseline_tolerances.get(metric, 0.01)  # Default tolerance

        # Handle inf values
        if baseline_value == float("inf") and current_value == float("inf"):
            diff = 0.0
            passed = True
        elif baseline_value == float("inf") or current_value == float("inf"):
            diff = float("inf")
            passed = False
        else:
            diff = abs(current_value - baseline_value)
            passed = diff <= tolerance

        comparisons.append(
            MetricComparison(
                metric=metric,
                baseline_value=baseline_value,
                current_value=current_value,
                tolerance=tolerance,
                passed=passed,
                absolute_diff=diff,
            )
        )

        if not passed:
            all_passed = False

    return BaselineResult(
        passed=all_passed,
        comparisons=comparisons,
        baseline_name=name,
    )


def generate_baseline_data(
    strategy_name: str,
    data_generator_name: str,
    data_params: dict,
    metrics: dict,
    engine_params: dict,
    tolerance: Optional[dict] = None,
) -> dict:
    """Create a baseline data dict ready for save_baseline().

    Args:
        strategy_name: Human-readable strategy description.
        data_generator_name: Name of the generator function used.
        data_params: Parameters passed to the generator.
        metrics: Dict of metric values.
        engine_params: BacktestEngine parameters used.
        tolerance: Per-metric tolerance overrides.

    Returns:
        Dict ready for save_baseline().
    """
    default_tolerance = {
        "total_return": 0.1,
        "sharpe_ratio": 0.01,
        "max_drawdown": 0.1,
        "total_trades": 0,
        "win_rate": 0.1,
        "profit_factor": 0.01,
        "winning_trades": 0,
        "losing_trades": 0,
        "avg_win": 0.5,
        "avg_loss": 0.5,
        "avg_trade": 0.5,
        "max_win_streak": 0,
        "max_loss_streak": 0,
        "avg_trade_duration": 0.5,
        "annual_return": 0.5,
        "max_drawdown_duration": 1,
        "total_profit": 1.0,
        "total_loss": 1.0,
        "initial_capital": 0,
        "final_value": 1.0,
    }

    if tolerance:
        default_tolerance.update(tolerance)

    return {
        "strategy_name": strategy_name,
        "data_generator": data_generator_name,
        "data_params": data_params,
        "engine_params": engine_params,
        "metrics": metrics,
        "tolerance": default_tolerance,
    }
