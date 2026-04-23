"""Persistence for asynchronous pairs backtest job manifests."""

from __future__ import annotations

from pathlib import Path

from .backtest_jobs_repo import LocalBacktestJobsRepository


class LocalPairsBacktestJobsRepository(LocalBacktestJobsRepository):
    """Store async pairs backtest job manifests on local disk."""

    def __init__(self, base_dir: Path | str = "pairs_backtests/jobs") -> None:
        super().__init__(base_dir=base_dir)
