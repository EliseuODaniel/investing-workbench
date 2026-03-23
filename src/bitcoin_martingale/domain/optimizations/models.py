"""Optimization planning domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from itertools import product
from typing import Any


class OptimizationMode(str, Enum):
    """How a discrete search space should be explored."""

    GRID = "grid"
    RANDOM = "random"


class OptimizationDirection(str, Enum):
    """Desired optimization objective direction."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


@dataclass(slots=True)
class OptimizationSearchSpace:
    """Discrete values available for a single strategy parameter."""

    name: str
    values: list[Any]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError(f"Search space for '{self.name}' must include at least one value")

    @classmethod
    def from_raw(cls, name: str, raw: Any) -> "OptimizationSearchSpace":
        """Create a search space from a list or range-like mapping."""
        if isinstance(raw, list):
            return cls(name=name, values=raw)

        if not isinstance(raw, dict):
            raise TypeError(
                f"Search space for '{name}' must be a list or mapping, got {type(raw).__name__}"
            )

        if "values" in raw:
            values = raw["values"]
            if not isinstance(values, list):
                raise TypeError(f"'values' for '{name}' must be a list")
            return cls(name=name, values=values)

        required = {"start", "stop", "step"}
        if not required.issubset(raw):
            raise ValueError(
                f"Search space for '{name}' must define 'values' or the keys {sorted(required)}"
            )

        return cls(name=name, values=_expand_numeric_range(raw["start"], raw["stop"], raw["step"]))


@dataclass(slots=True)
class OptimizationRequest:
    """User request for planning an optimization workflow."""

    config_path: str
    strategy_names: list[str] | None = None
    parameter_space: dict[str, Any] = field(default_factory=dict)
    strategy_parameter_spaces: dict[str, dict[str, Any]] = field(default_factory=dict)
    mode: OptimizationMode = OptimizationMode.GRID
    max_trials: int | None = None
    random_seed: int = 42
    objective: str = "sharpe_ratio"
    direction: OptimizationDirection = OptimizationDirection.MAXIMIZE

    def __post_init__(self) -> None:
        if self.max_trials is not None and self.max_trials <= 0:
            raise ValueError("max_trials must be greater than zero when provided")


@dataclass(slots=True)
class OptimizationTrialCandidate:
    """A single candidate parameter set for future execution."""

    trial_id: str
    strategy_name: str
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the candidate for CLI or JSON responses."""
        return {
            "trial_id": self.trial_id,
            "strategy_name": self.strategy_name,
            "parameters": self.parameters,
        }


@dataclass(slots=True)
class OptimizationPlan:
    """Discrete plan of trials ready for execution in future iterations."""

    config_path: str
    objective: str
    direction: OptimizationDirection
    mode: OptimizationMode
    random_seed: int
    strategy_names: list[str]
    trials: list[OptimizationTrialCandidate]
    warnings: list[str] = field(default_factory=list)
    truncated: bool = False

    @property
    def trial_count(self) -> int:
        """Return the number of planned trials."""
        return len(self.trials)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the plan for CLI or future API usage."""
        return {
            "config_path": self.config_path,
            "objective": self.objective,
            "direction": self.direction.value,
            "mode": self.mode.value,
            "random_seed": self.random_seed,
            "strategy_names": self.strategy_names,
            "trial_count": self.trial_count,
            "truncated": self.truncated,
            "warnings": self.warnings,
            "trials": [trial.to_dict() for trial in self.trials],
        }


def build_parameter_combinations(
    spaces: list[OptimizationSearchSpace],
) -> list[dict[str, Any]]:
    """Expand discrete search spaces into all parameter combinations."""
    parameter_names = [space.name for space in spaces]
    value_groups = [space.values for space in spaces]
    combinations: list[dict[str, Any]] = []

    for values in product(*value_groups):
        combinations.append(dict(zip(parameter_names, values, strict=True)))

    return combinations


def _expand_numeric_range(start: Any, stop: Any, step: Any) -> list[int | float]:
    """Expand a numeric range inclusively using `Decimal` for stability."""
    start_decimal = Decimal(str(start))
    stop_decimal = Decimal(str(stop))
    step_decimal = Decimal(str(step))

    if step_decimal <= 0:
        raise ValueError("Range step must be greater than zero")
    if start_decimal > stop_decimal:
        raise ValueError("Range start must be less than or equal to stop")

    values: list[int | float] = []
    current = start_decimal
    integral_values = all(
        decimal == decimal.to_integral_value()
        for decimal in (start_decimal, stop_decimal, step_decimal)
    )

    while current <= stop_decimal:
        if integral_values:
            values.append(int(current))
        else:
            values.append(float(current))
        current += step_decimal

    return values
