"""DTOs for application-layer run orchestration."""

from dataclasses import dataclass


@dataclass(slots=True)
class RunRequestSummary:
    """Minimal summary of a resolved run request."""

    config_path: str
    strategy_count: int
    benchmark_count: int
