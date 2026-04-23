"""Domain models for Monte Carlo robustness analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MonteCarloMethod(str, Enum):
    """How trade outcomes should be re-sampled."""

    BOOTSTRAP = "bootstrap"
    SHUFFLE = "shuffle"


@dataclass(slots=True)
class MonteCarloRequest:
    """Request to execute Monte Carlo robustness analysis."""

    config_path: str | None = None
    run_id: str | None = None
    strategy_names: list[str] | None = None
    simulation_count: int = 500
    random_seed: int = 42
    method: MonteCarloMethod = MonteCarloMethod.BOOTSTRAP
    ruin_threshold_pct: float = 0.30

    def __post_init__(self) -> None:
        has_config = bool(self.config_path)
        has_run = bool(self.run_id)
        if has_config == has_run:
            raise ValueError("Provide exactly one of config_path or run_id")
        if self.simulation_count <= 0:
            raise ValueError("simulation_count must be greater than zero")
        if not 0 <= self.ruin_threshold_pct < 1:
            raise ValueError("ruin_threshold_pct must be between 0 and 1")


@dataclass(slots=True)
class MonteCarloSimulationSummary:
    """Outcome of one Monte Carlo simulation."""

    simulation_number: int
    final_equity: float
    total_return: float
    max_drawdown: float
    min_equity: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize one simulation summary."""
        return {
            "simulation_number": self.simulation_number,
            "final_equity": self.final_equity,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "min_equity": self.min_equity,
        }


@dataclass(slots=True)
class MonteCarloStrategyResult:
    """Aggregated Monte Carlo analysis for a single strategy."""

    strategy_name: str
    trade_count: int
    simulation_count: int
    method: MonteCarloMethod
    actual_final_equity: float
    actual_total_return: float
    actual_max_drawdown: float
    loss_probability: float
    ruin_probability: float
    percentile_05_final_equity: float
    median_final_equity: float
    percentile_95_final_equity: float
    percentile_05_total_return: float
    median_total_return: float
    percentile_95_total_return: float
    percentile_05_max_drawdown: float
    median_max_drawdown: float
    percentile_95_max_drawdown: float
    worst_final_equity: float
    best_final_equity: float
    warnings: list[str] = field(default_factory=list)
    simulations: list[MonteCarloSimulationSummary] = field(default_factory=list)

    def summary_dict(self) -> dict[str, Any]:
        """Serialize the high-level strategy summary."""
        return {
            "strategy_name": self.strategy_name,
            "trade_count": self.trade_count,
            "simulation_count": self.simulation_count,
            "method": self.method.value,
            "actual_final_equity": self.actual_final_equity,
            "actual_total_return": self.actual_total_return,
            "actual_max_drawdown": self.actual_max_drawdown,
            "loss_probability": self.loss_probability,
            "ruin_probability": self.ruin_probability,
            "percentile_05_final_equity": self.percentile_05_final_equity,
            "median_final_equity": self.median_final_equity,
            "percentile_95_final_equity": self.percentile_95_final_equity,
            "percentile_05_total_return": self.percentile_05_total_return,
            "median_total_return": self.median_total_return,
            "percentile_95_total_return": self.percentile_95_total_return,
            "percentile_05_max_drawdown": self.percentile_05_max_drawdown,
            "median_max_drawdown": self.median_max_drawdown,
            "percentile_95_max_drawdown": self.percentile_95_max_drawdown,
            "worst_final_equity": self.worst_final_equity,
            "best_final_equity": self.best_final_equity,
            "warnings": self.warnings,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full strategy result."""
        return {
            **self.summary_dict(),
            "simulations": [simulation.to_dict() for simulation in self.simulations],
        }


@dataclass(slots=True)
class MonteCarloExecutionResult:
    """Persistable execution result for Monte Carlo robustness analysis."""

    montecarlo_id: str
    created_at: datetime
    config_path: str | None
    source_run_id: str
    strategy_names: list[str]
    simulation_count: int
    random_seed: int
    method: MonteCarloMethod
    ruin_threshold_pct: float
    results: list[MonteCarloStrategyResult]
    warnings: list[str] = field(default_factory=list)

    def manifest_dict(self) -> dict[str, Any]:
        """Serialize high-level metadata for listing and inspection."""
        return {
            "montecarlo_id": self.montecarlo_id,
            "created_at": self.created_at.isoformat(),
            "config_path": self.config_path,
            "source_run_id": self.source_run_id,
            "strategy_names": self.strategy_names,
            "simulation_count": self.simulation_count,
            "random_seed": self.random_seed,
            "method": self.method.value,
            "ruin_threshold_pct": self.ruin_threshold_pct,
            "warnings": self.warnings,
            "strategy_summaries": self.strategy_summaries(),
        }

    def results_dict(self) -> dict[str, Any]:
        """Serialize the full Monte Carlo result set."""
        return {
            "montecarlo_id": self.montecarlo_id,
            "config_path": self.config_path,
            "source_run_id": self.source_run_id,
            "strategy_names": self.strategy_names,
            "simulation_count": self.simulation_count,
            "random_seed": self.random_seed,
            "method": self.method.value,
            "ruin_threshold_pct": self.ruin_threshold_pct,
            "warnings": self.warnings,
            "strategy_summaries": self.strategy_summaries(),
            "results": [result.to_dict() for result in self.results],
        }

    def strategy_summaries(self) -> list[dict[str, Any]]:
        """Return the summary payload for each strategy."""
        return [result.summary_dict() for result in self.results]
