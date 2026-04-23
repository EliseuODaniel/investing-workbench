"""Persistence adapters for the platform."""

from .allocation_workspaces_repo import LocalAllocationWorkspacesRepository
from .backtest_jobs_repo import LocalBacktestJobsRepository
from .index_universe_repo import LocalIndexUniverseRepository
from .montecarlo_repo import LocalMonteCarloRepository
from .optimization_repo import LocalOptimizationsRepository
from .pairs_jobs_repo import LocalPairsBacktestJobsRepository
from .pairs_repo import LocalPairsBacktestsRepository
from .research_workspaces_repo import LocalResearchWorkspacesRepository
from .runs_repo import LocalRunsRepository
from .walkforward_repo import LocalWalkForwardRepository

__all__ = [
    "LocalAllocationWorkspacesRepository",
    "LocalBacktestJobsRepository",
    "LocalIndexUniverseRepository",
    "LocalMonteCarloRepository",
    "LocalOptimizationsRepository",
    "LocalPairsBacktestsRepository",
    "LocalPairsBacktestJobsRepository",
    "LocalResearchWorkspacesRepository",
    "LocalRunsRepository",
    "LocalWalkForwardRepository",
]
