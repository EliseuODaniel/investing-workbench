"""Tests for asynchronous backtest job orchestration."""

from __future__ import annotations

import time
from pathlib import Path

from src.api.models import BacktestResponse
from src.investing_workbench.application.backtest_jobs import (
    BacktestJobCancelledError,
    BacktestJobService,
)
from src.investing_workbench.application.runs import RunBacktestService
from src.investing_workbench.infrastructure.persistence import (
    LocalBacktestJobsRepository,
    LocalRunsRepository,
)


def _wait_for_job_status(
    service: BacktestJobService,
    job_id: str,
    expected_status: str,
    *,
    timeout_seconds: float = 5.0,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        job = service.get_job(job_id)
        if str(job.get("status")) == expected_status:
            return job
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for job {job_id} to reach status {expected_status}")


class _StubRunService:
    def __init__(self) -> None:
        self._responses: dict[str, dict[str, object]] = {}
        self._counter = 0

    def run(
        self, request: object, *, progress_callback=None, should_cancel=None
    ) -> BacktestResponse:
        for step in range(1, 5):
            if should_cancel is not None and should_cancel():
                raise BacktestJobCancelledError("cancelled")
            if progress_callback is not None:
                progress_callback(
                    {
                        "phase": "strategy",
                        "message": f"Step {step}/4",
                        "percent": 20.0 + (step * 15.0),
                        "current_step": step,
                        "total_steps": 4,
                    }
                )
            time.sleep(0.03)

        self._counter += 1
        run_id = f"stub_run_{self._counter}"
        payload = {
            "results": {},
            "buy_hold_equity": [],
            "benchmarks": None,
            "run_info": {
                "run_id": run_id,
                "artifact_dir": f"runs/{run_id}",
            },
            "data_info": {
                "start_date": "2024-01-01T00:00:00+00:00",
                "end_date": "2024-01-02T00:00:00+00:00",
                "total_days": 2,
                "initial_price": 100.0,
                "final_price": 101.0,
            },
            "warnings": [],
        }
        self._responses[run_id] = payload
        return BacktestResponse(**payload)

    def get_run_response(self, run_id: str) -> dict[str, object]:
        return self._responses[run_id]


def test_backtest_job_service_completes_and_exposes_run_response(tmp_path: Path) -> None:
    run_service = RunBacktestService(
        runs_repository=LocalRunsRepository(base_dir=tmp_path / "runs")
    )
    job_service = BacktestJobService(
        run_service=run_service,
        jobs_repository=LocalBacktestJobsRepository(base_dir=tmp_path / "jobs"),
        max_workers=1,
    )

    job = job_service.create_job({"config_path": "configs/test.yaml"})
    completed_job = _wait_for_job_status(job_service, str(job["job_id"]), "completed")

    assert completed_job["result_available"] is True
    assert completed_job["run_id"]
    response = job_service.get_job_response(str(job["job_id"]))
    assert "results" in response
    assert "warnings" in response


def test_backtest_job_service_cancels_and_resumes_jobs(tmp_path: Path) -> None:
    job_service = BacktestJobService(
        run_service=_StubRunService(),
        jobs_repository=LocalBacktestJobsRepository(base_dir=tmp_path / "jobs"),
        max_workers=1,
    )

    job = job_service.create_job({"config_path": "configs/test.yaml"})
    running_job = _wait_for_job_status(job_service, str(job["job_id"]), "running")
    assert running_job["progress"]["phase"] in {"booting", "strategy"}

    job_service.cancel_job(str(job["job_id"]))
    cancelled_job = _wait_for_job_status(job_service, str(job["job_id"]), "cancelled")
    assert cancelled_job["cancel_requested"] is True

    resumed_job = job_service.resume_job(str(job["job_id"]))
    assert resumed_job["attempt_count"] == 2
    completed_job = _wait_for_job_status(job_service, str(job["job_id"]), "completed")
    assert completed_job["attempt_count"] == 2
    assert completed_job["run_id"] == "stub_run_1"


def test_backtest_job_service_recovers_interrupted_jobs_on_startup(tmp_path: Path) -> None:
    repository = LocalBacktestJobsRepository(base_dir=tmp_path / "jobs")
    repository.persist_job(
        {
            "job_id": "job_interrupted",
            "job_type": "backtest",
            "status": "running",
            "created_at": "2026-04-20T15:00:00+00:00",
            "updated_at": "2026-04-20T15:01:00+00:00",
            "started_at": "2026-04-20T15:00:10+00:00",
            "finished_at": None,
            "attempt_count": 1,
            "cancel_requested": False,
            "request_payload": {"config_path": "configs/test.yaml"},
            "config_path": "configs/test.yaml",
            "strategy_names": [],
            "progress": {
                "phase": "strategy",
                "message": "Running strategy",
                "percent": 55.0,
                "updated_at": "2026-04-20T15:01:00+00:00",
                "current_step": 1,
                "total_steps": 2,
            },
            "run_id": None,
            "result_available": False,
            "error": None,
            "events": [],
        }
    )

    job_service = BacktestJobService(
        run_service=_StubRunService(),
        jobs_repository=repository,
        max_workers=1,
        resume_interrupted_jobs=True,
    )

    completed_job = _wait_for_job_status(job_service, "job_interrupted", "completed")
    assert completed_job["attempt_count"] == 2
    assert completed_job["run_id"] == "stub_run_1"
    assert any(
        event["message"] == "Job recovered after process restart and queued again."
        for event in completed_job["events"]
    )


def test_detached_backtest_job_service_processes_queued_job_via_worker(tmp_path: Path) -> None:
    job_service = BacktestJobService(
        run_service=_StubRunService(),
        jobs_repository=LocalBacktestJobsRepository(base_dir=tmp_path / "jobs"),
        max_workers=1,
        execution_mode="detached",
    )

    job = job_service.create_job({"config_path": "configs/test.yaml"})
    assert job["status"] == "queued"

    completed_job = job_service.process_next_queued_job(worker_id="worker_cli")
    assert completed_job is not None
    assert completed_job["status"] == "completed"
    assert completed_job["worker_id"] == "worker_cli"
    assert completed_job["run_id"] == "stub_run_1"
