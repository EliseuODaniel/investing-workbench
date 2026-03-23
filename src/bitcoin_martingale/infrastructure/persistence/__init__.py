"""Persistence adapters for the platform."""

from .montecarlo_repo import LocalMonteCarloRepository
from .optimization_repo import LocalOptimizationsRepository
from .runs_repo import LocalRunsRepository
from .walkforward_repo import LocalWalkForwardRepository

__all__ = [
    "LocalMonteCarloRepository",
    "LocalOptimizationsRepository",
    "LocalRunsRepository",
    "LocalWalkForwardRepository",
]
