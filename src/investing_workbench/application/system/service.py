"""Application service for lightweight platform status reporting."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Protocol, Sequence


class _RunService(Protocol):
    def list_configs(self) -> Sequence[object]: ...


class _DatasetService(Protocol):
    def list_datasets(self) -> Sequence[dict[str, object]]: ...

    def list_due_datasets(self) -> Sequence[dict[str, object]]: ...


class _ExperimentRegistryService(Protocol):
    def list_experiments(self) -> Sequence[dict[str, object]]: ...


class _WorkspaceService(Protocol):
    def list_workspaces(self) -> Sequence[dict[str, object]]: ...


class _PairsTradingService(Protocol):
    def list_backtests(self) -> Sequence[dict[str, object]]: ...


class _AsyncJobService(Protocol):
    def get_job_counts(self) -> dict[str, int]: ...

    def get_runtime_summary(self) -> dict[str, object]: ...

    def latest_job_id(self) -> str | None: ...


class PlatformStatusService:
    """Summarize operational status across configs, datasets, and persisted artifacts."""

    def __init__(
        self,
        *,
        run_service: _RunService,
        dataset_service: _DatasetService,
        experiment_registry_service: _ExperimentRegistryService,
        research_workspace_service: _WorkspaceService,
        allocation_workspace_service: _WorkspaceService,
        pairs_trading_service: _PairsTradingService | None = None,
        backtest_job_service: _AsyncJobService | None = None,
        pairs_backtest_job_service: _AsyncJobService | None = None,
        api_version: str = "1.0.0",
    ) -> None:
        self.run_service = run_service
        self.dataset_service = dataset_service
        self.experiment_registry_service = experiment_registry_service
        self.research_workspace_service = research_workspace_service
        self.allocation_workspace_service = allocation_workspace_service
        self.pairs_trading_service = pairs_trading_service
        self.backtest_job_service = backtest_job_service
        self.pairs_backtest_job_service = pairs_backtest_job_service
        self.api_version = api_version

    def get_status(self) -> dict[str, object]:
        """Return a lightweight operational snapshot for the local platform."""
        configs = self.run_service.list_configs()
        datasets = self.dataset_service.list_datasets()
        due_datasets = self.dataset_service.list_due_datasets()
        experiments = self.experiment_registry_service.list_experiments()
        research_workspaces = self.research_workspace_service.list_workspaces()
        allocation_workspaces = self.allocation_workspace_service.list_workspaces()
        config_count = len(configs)
        dataset_count = len(datasets)
        experiment_counts = Counter(
            str(experiment.get("experiment_type", "unknown")) for experiment in experiments
        )
        research_workspace_count = len(research_workspaces)
        allocation_workspace_count = len(allocation_workspaces)
        persisted_pairs = (
            self.pairs_trading_service.list_backtests()
            if self.pairs_trading_service is not None
            else []
        )
        job_counts = (
            self.backtest_job_service.get_job_counts()
            if self.backtest_job_service is not None
            else {
                "queued": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            }
        )
        job_runtime = (
            self.backtest_job_service.get_runtime_summary()
            if self.backtest_job_service is not None
            else {
                "max_workers": 0,
                "active_futures": 0,
            }
        )
        pairs_job_counts = (
            self.pairs_backtest_job_service.get_job_counts()
            if self.pairs_backtest_job_service is not None
            else {
                "queued": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            }
        )
        pairs_job_runtime = (
            self.pairs_backtest_job_service.get_runtime_summary()
            if self.pairs_backtest_job_service is not None
            else {
                "max_workers": 0,
                "active_futures": 0,
            }
        )

        warnings: list[str] = []
        if config_count == 0:
            warnings.append("No configuration files were discovered.")
        if dataset_count == 0:
            warnings.append("No managed datasets were discovered.")
        if experiment_counts.get("run", 0) == 0:
            warnings.append("No persisted backtest runs were discovered.")
        if len(due_datasets) > 0:
            warnings.append("There are datasets whose refresh policy is currently due.")
        if job_counts.get("failed", 0) > 0:
            warnings.append("There are failed async backtest jobs that may need to be resumed.")
        if pairs_job_counts.get("failed", 0) > 0:
            warnings.append("There are failed async pairs jobs that may need to be resumed.")
        if (
            self.backtest_job_service is not None
            and str(job_runtime.get("execution_mode")) == "detached"
            and job_counts.get("queued", 0) > 0
            and job_counts.get("running", 0) == 0
        ):
            warnings.append(
                "Async backtest jobs are queued in detached mode. "
                "Run `python -m src backtest-jobs-worker` to process them."
            )
        if (
            self.pairs_backtest_job_service is not None
            and str(pairs_job_runtime.get("execution_mode")) == "detached"
            and pairs_job_counts.get("queued", 0) > 0
            and pairs_job_counts.get("running", 0) == 0
        ):
            warnings.append(
                "Async pairs jobs are queued in detached mode. "
                "Run `python -m src pairs-backtest-jobs-worker` to process them."
            )

        return {
            "status": "degraded" if warnings else "ok",
            "api_version": self.api_version,
            "checked_at": datetime.now(UTC).isoformat(),
            "config_count": config_count,
            "dataset_count": dataset_count,
            "due_dataset_count": len(due_datasets),
            "artifact_counts": {
                "runs": experiment_counts.get("run", 0),
                "optimizations": experiment_counts.get("optimization", 0),
                "walkforward": experiment_counts.get("walkforward", 0),
                "montecarlo": experiment_counts.get("montecarlo", 0),
                "pairs_backtests": len(persisted_pairs),
                "research_workspaces": research_workspace_count,
                "allocation_workspaces": allocation_workspace_count,
            },
            "job_counts": job_counts,
            "job_runtime": job_runtime,
            "pairs_job_counts": pairs_job_counts,
            "pairs_job_runtime": pairs_job_runtime,
            "latest_run_id": self._latest_experiment_id(experiments, "run"),
            "latest_backtest_job_id": (
                self.backtest_job_service.latest_job_id()
                if self.backtest_job_service is not None
                else None
            ),
            "latest_pairs_backtest_job_id": (
                self.pairs_backtest_job_service.latest_job_id()
                if self.pairs_backtest_job_service is not None
                else None
            ),
            "latest_research_workspace_id": (
                str(research_workspaces[0]["workspace_id"]) if research_workspaces else None
            ),
            "latest_pairs_backtest_id": (
                str(persisted_pairs[0]["pairs_backtest_id"]) if persisted_pairs else None
            ),
            "warnings": warnings,
        }

    def _latest_experiment_id(
        self, experiments: Sequence[dict[str, object]], experiment_type: str
    ) -> str | None:
        for experiment in experiments:
            if experiment.get("experiment_type") != experiment_type:
                continue
            experiment_id = experiment.get("experiment_id")
            if experiment_id:
                return str(experiment_id)
        return None
