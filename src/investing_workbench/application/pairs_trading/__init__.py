"""Application services for B3 pairs-trading workflows."""

from .benchmarks import PairsBenchmarkService
from .dto import (
    BorrowSnapshotRegistration,
    PairsBacktestManifest,
    PairsBacktestResults,
    PairsScreeningResult,
    PairsUniverseResolution,
)
from .execution import PairsScenarioExecutionService
from .ibov_history import B3IbovUniverseHistoryService
from .reporting import PairsReportingService
from .service import PairsExecutionCancelledError, PairsTradingService

__all__ = [
    "B3IbovUniverseHistoryService",
    "BorrowSnapshotRegistration",
    "PairsBacktestManifest",
    "PairsBenchmarkService",
    "PairsBacktestResults",
    "PairsExecutionCancelledError",
    "PairsReportingService",
    "PairsScenarioExecutionService",
    "PairsScreeningResult",
    "PairsTradingService",
    "PairsUniverseResolution",
]
