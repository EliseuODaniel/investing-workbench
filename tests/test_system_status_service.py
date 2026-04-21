"""Tests for platform status reporting."""

from __future__ import annotations

from typing import cast

from src.bitcoin_martingale.application.system import PlatformStatusService


class _StubRunService:
    def __init__(
        self, *, configs: list[object], runs: list[dict[str, object]] | None = None
    ) -> None:
        self._configs = configs
        self._runs = runs or []

    def list_configs(self) -> list[object]:
        return self._configs

    def list_runs(self) -> list[dict[str, object]]:
        return self._runs


class _StubDatasetService:
    def __init__(self, datasets: list[object], due_datasets: list[object] | None = None) -> None:
        self._datasets = datasets
        self._due_datasets = due_datasets or []

    def list_datasets(self) -> list[object]:
        return self._datasets

    def list_due_datasets(self) -> list[object]:
        return self._due_datasets


class _StubExperimentRegistryService:
    def __init__(self, experiments: list[dict[str, object]]) -> None:
        self._experiments = experiments

    def list_experiments(self) -> list[dict[str, object]]:
        return self._experiments


class _StubWorkspaceService:
    def __init__(self, workspaces: list[object]) -> None:
        self._workspaces = workspaces

    def list_workspaces(self) -> list[object]:
        return self._workspaces


class _StubBacktestJobService:
    def __init__(
        self,
        *,
        counts: dict[str, int],
        latest_job_id: str | None = None,
        runtime: dict[str, object] | None = None,
    ) -> None:
        self._counts = counts
        self._latest_job_id = latest_job_id
        self._runtime = runtime or {
            "execution_mode": "inline",
            "max_workers": 0,
            "active_futures": 0,
        }

    def get_job_counts(self) -> dict[str, int]:
        return self._counts

    def latest_job_id(self) -> str | None:
        return self._latest_job_id

    def get_runtime_summary(self) -> dict[str, object]:
        return self._runtime


def test_platform_status_reports_ok_when_core_assets_exist() -> None:
    service = PlatformStatusService(
        run_service=_StubRunService(configs=[{"name": "default"}]),
        dataset_service=_StubDatasetService([{"dataset_id": "btc"}]),
        experiment_registry_service=_StubExperimentRegistryService(
            [
                {"experiment_type": "run"},
                {"experiment_type": "run", "experiment_id": "run_latest"},
                {"experiment_type": "optimization"},
                {"experiment_type": "walkforward"},
                {"experiment_type": "montecarlo"},
            ]
        ),
        research_workspace_service=_StubWorkspaceService([{"workspace_id": "ws-1"}]),
        allocation_workspace_service=_StubWorkspaceService([{"workspace_id": "alloc-1"}]),
        backtest_job_service=_StubBacktestJobService(
            counts={
                "queued": 1,
                "running": 1,
                "completed": 2,
                "failed": 0,
                "cancelled": 0,
            },
            latest_job_id="job_latest",
            runtime={"execution_mode": "inline", "max_workers": 2, "active_futures": 1},
        ),
        pairs_backtest_job_service=_StubBacktestJobService(
            counts={
                "queued": 0,
                "running": 0,
                "completed": 3,
                "failed": 0,
                "cancelled": 0,
            },
            latest_job_id="pairs_job_latest",
            runtime={"execution_mode": "inline", "max_workers": 2, "active_futures": 0},
        ),
    )

    status = service.get_status()

    assert status["status"] == "ok"
    assert status["config_count"] == 1
    assert status["dataset_count"] == 1
    assert status["due_dataset_count"] == 0
    assert status["artifact_counts"] == {
        "runs": 2,
        "optimizations": 1,
        "walkforward": 1,
        "montecarlo": 1,
        "pairs_backtests": 0,
        "research_workspaces": 1,
        "allocation_workspaces": 1,
    }
    assert status["job_counts"] == {
        "queued": 1,
        "running": 1,
        "completed": 2,
        "failed": 0,
        "cancelled": 0,
    }
    assert status["job_runtime"] == {
        "execution_mode": "inline",
        "max_workers": 2,
        "active_futures": 1,
    }
    assert status["pairs_job_counts"] == {
        "queued": 0,
        "running": 0,
        "completed": 3,
        "failed": 0,
        "cancelled": 0,
    }
    assert status["pairs_job_runtime"] == {
        "execution_mode": "inline",
        "max_workers": 2,
        "active_futures": 0,
    }
    assert status["latest_run_id"] == "run_latest"
    assert status["latest_backtest_job_id"] == "job_latest"
    assert status["latest_pairs_backtest_job_id"] == "pairs_job_latest"
    assert status["latest_research_workspace_id"] == "ws-1"
    assert status["warnings"] == []


def test_platform_status_flags_missing_operational_basics() -> None:
    service = PlatformStatusService(
        run_service=_StubRunService(configs=[]),
        dataset_service=_StubDatasetService([], due_datasets=[{"dataset_id": "btc"}]),
        experiment_registry_service=_StubExperimentRegistryService([]),
        research_workspace_service=_StubWorkspaceService([]),
        allocation_workspace_service=_StubWorkspaceService([]),
        backtest_job_service=_StubBacktestJobService(
            counts={
                "queued": 0,
                "running": 0,
                "completed": 0,
                "failed": 1,
                "cancelled": 0,
            },
            runtime={"execution_mode": "inline", "max_workers": 2, "active_futures": 0},
        ),
        pairs_backtest_job_service=_StubBacktestJobService(
            counts={
                "queued": 0,
                "running": 0,
                "completed": 0,
                "failed": 1,
                "cancelled": 0,
            },
            runtime={"execution_mode": "inline", "max_workers": 2, "active_futures": 0},
        ),
    )

    status = service.get_status()
    artifact_counts = cast(dict[str, object], status["artifact_counts"])
    warnings = cast(list[str], status["warnings"])

    assert status["status"] == "degraded"
    assert artifact_counts["runs"] == 0
    assert status["due_dataset_count"] == 1
    assert "No configuration files were discovered." in warnings
    assert "No managed datasets were discovered." in warnings
    assert "No persisted backtest runs were discovered." in warnings
    assert "There are datasets whose refresh policy is currently due." in warnings
    assert "There are failed async backtest jobs that may need to be resumed." in warnings
    assert "There are failed async pairs jobs that may need to be resumed." in warnings


def test_platform_status_warns_when_detached_jobs_are_queued_without_worker_activity() -> None:
    service = PlatformStatusService(
        run_service=_StubRunService(configs=[{"name": "default"}]),
        dataset_service=_StubDatasetService([{"dataset_id": "btc"}]),
        experiment_registry_service=_StubExperimentRegistryService(
            [{"experiment_type": "run", "experiment_id": "run_latest"}]
        ),
        research_workspace_service=_StubWorkspaceService([]),
        allocation_workspace_service=_StubWorkspaceService([]),
        backtest_job_service=_StubBacktestJobService(
            counts={
                "queued": 2,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            },
            runtime={"execution_mode": "detached", "max_workers": 2, "active_futures": 0},
        ),
        pairs_backtest_job_service=_StubBacktestJobService(
            counts={
                "queued": 1,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            },
            runtime={"execution_mode": "detached", "max_workers": 2, "active_futures": 0},
        ),
    )

    status = service.get_status()
    warnings = cast(list[str], status["warnings"])

    assert (
        "Async backtest jobs are queued in detached mode. Run `python -m src backtest-jobs-worker` to process them."
        in warnings
    )
    assert (
        "Async pairs jobs are queued in detached mode. Run `python -m src pairs-backtest-jobs-worker` to process them."
        in warnings
    )
