"""Domain models for walk-forward validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class WalkForwardRequest:
    """Request to execute walk-forward validation."""

    config_path: str
    strategy_names: list[str] | None = None
    train_window_days: int = 90
    test_window_days: int = 30
    step_days: int = 30

    def __post_init__(self) -> None:
        if self.train_window_days <= 0:
            raise ValueError("train_window_days must be greater than zero")
        if self.test_window_days <= 0:
            raise ValueError("test_window_days must be greater than zero")
        if self.step_days <= 0:
            raise ValueError("step_days must be greater than zero")


@dataclass(slots=True)
class WalkForwardWindowResult:
    """Train/test outcome for a single strategy window."""

    window_id: str
    strategy_name: str
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_metrics: dict[str, Any]
    test_metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the window result."""
        return {
            "window_id": self.window_id,
            "strategy_name": self.strategy_name,
            "train_start": self.train_start,
            "train_end": self.train_end,
            "test_start": self.test_start,
            "test_end": self.test_end,
            "train_metrics": self.train_metrics,
            "test_metrics": self.test_metrics,
        }


@dataclass(slots=True)
class WalkForwardExecutionResult:
    """Persistable execution result for walk-forward validation."""

    walkforward_id: str
    created_at: datetime
    config_path: str
    strategy_names: list[str]
    train_window_days: int
    test_window_days: int
    step_days: int
    window_count: int
    results: list[WalkForwardWindowResult]

    def manifest_dict(self) -> dict[str, Any]:
        """Serialize high-level metadata for listing and inspection."""
        return {
            "walkforward_id": self.walkforward_id,
            "created_at": self.created_at.isoformat(),
            "config_path": self.config_path,
            "strategy_names": self.strategy_names,
            "train_window_days": self.train_window_days,
            "test_window_days": self.test_window_days,
            "step_days": self.step_days,
            "window_count": self.window_count,
            "strategy_summaries": self.strategy_summaries(),
        }

    def results_dict(self) -> dict[str, Any]:
        """Serialize full walk-forward results."""
        return {
            "walkforward_id": self.walkforward_id,
            "config_path": self.config_path,
            "strategy_names": self.strategy_names,
            "train_window_days": self.train_window_days,
            "test_window_days": self.test_window_days,
            "step_days": self.step_days,
            "window_count": self.window_count,
            "strategy_summaries": self.strategy_summaries(),
            "results": [result.to_dict() for result in self.results],
        }

    def strategy_summaries(self) -> list[dict[str, Any]]:
        """Aggregate train/test metrics by strategy."""
        summaries: list[dict[str, Any]] = []
        for strategy_name in self.strategy_names:
            strategy_results = [
                result for result in self.results if result.strategy_name == strategy_name
            ]
            if not strategy_results:
                continue

            summaries.append(
                {
                    "strategy_name": strategy_name,
                    "window_count": len(strategy_results),
                    "avg_train_total_return": _average_metric(
                        strategy_results, "train_metrics", "total_return"
                    ),
                    "avg_test_total_return": _average_metric(
                        strategy_results, "test_metrics", "total_return"
                    ),
                    "avg_test_sharpe_ratio": _average_metric(
                        strategy_results, "test_metrics", "sharpe_ratio"
                    ),
                    "worst_test_drawdown": min(
                        float(result.test_metrics.get("max_drawdown", 0.0))
                        for result in strategy_results
                    ),
                }
            )

        return summaries


def _average_metric(
    strategy_results: list[WalkForwardWindowResult],
    metrics_key: str,
    metric_name: str,
) -> float:
    values = [
        float(getattr(result, metrics_key).get(metric_name, 0.0))
        for result in strategy_results
    ]
    return sum(values) / len(values)
