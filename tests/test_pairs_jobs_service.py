"""Tests for asynchronous pairs backtest job orchestration."""

from __future__ import annotations

import time
from pathlib import Path

from src.investing_workbench.application.pairs_jobs import (
    PairsBacktestJobCancelledError,
    PairsBacktestJobService,
)
from src.investing_workbench.infrastructure.persistence import LocalPairsBacktestJobsRepository


def _wait_for_job_status(
    service: PairsBacktestJobService,
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


class _StubPairsService:
    def __init__(self) -> None:
        self._responses: dict[str, dict[str, object]] = {}
        self._counter = 0

    def run_backtest(self, **kwargs: object) -> dict[str, object]:
        progress_callback = kwargs.get("progress_callback")
        should_cancel = kwargs.get("should_cancel")
        for step in range(1, 5):
            if callable(should_cancel) and should_cancel():
                raise PairsBacktestJobCancelledError("cancelled")
            if callable(progress_callback):
                progress_callback(
                    {
                        "phase": "pairs_backtest",
                        "message": f"Scenario step {step}/4",
                        "percent": 20.0 + (step * 15.0),
                        "current_step": step,
                        "total_steps": 4,
                    }
                )
            time.sleep(0.03)

        self._counter += 1
        backtest_id = f"pairs_stub_{self._counter}"
        payload = {
            "pairs_backtest_id": backtest_id,
            "created_at": "2026-04-20T15:00:00+00:00",
            "manifest": {"pairs_backtest_id": backtest_id},
            "preset": {"preset_id": "ibov_proxy"},
            "universe": {},
            "candidate_pairs": [],
            "benchmarks": [],
            "scenarios": [{"scenario_id": "realistic_cointegration"}],
            "robustness_report": {"rankings": []},
            "warnings": [],
        }
        self._responses[backtest_id] = payload
        return payload

    def run_batch(self, **kwargs: object) -> dict[str, object]:
        payload = self.run_backtest(**kwargs)
        payload["scenarios"] = [
            {"scenario_id": "realistic_cointegration"},
            {"scenario_id": "low_friction_cointegration"},
        ]
        return payload

    def get_results(self, backtest_id: str) -> dict[str, object]:
        return self._responses[backtest_id]


def test_pairs_backtest_job_service_completes_and_exposes_results(tmp_path: Path) -> None:
    job_service = PairsBacktestJobService(
        pairs_service=_StubPairsService(),
        jobs_repository=LocalPairsBacktestJobsRepository(base_dir=tmp_path / "pairs_jobs"),
        max_workers=1,
    )

    job = job_service.create_job({"preset_id": "ibov_proxy", "tickers": ["PETR4", "VALE3"]})
    completed_job = _wait_for_job_status(job_service, str(job["job_id"]), "completed")

    assert completed_job["result_available"] is True
    assert completed_job["pairs_backtest_id"]
    response = job_service.get_job_response(str(job["job_id"]))
    assert response["pairs_backtest_id"] == completed_job["pairs_backtest_id"]
    assert "scenarios" in response


def test_pairs_backtest_job_service_cancels_and_resumes_jobs(tmp_path: Path) -> None:
    job_service = PairsBacktestJobService(
        pairs_service=_StubPairsService(),
        jobs_repository=LocalPairsBacktestJobsRepository(base_dir=tmp_path / "pairs_jobs"),
        max_workers=1,
    )

    job = job_service.create_job({"preset_id": "ibov_proxy", "tickers": ["PETR4", "VALE3"]})
    running_job = _wait_for_job_status(job_service, str(job["job_id"]), "running")
    assert running_job["progress"]["phase"] in {"booting", "pairs_backtest"}

    job_service.cancel_job(str(job["job_id"]))
    cancelled_job = _wait_for_job_status(job_service, str(job["job_id"]), "cancelled")
    assert cancelled_job["cancel_requested"] is True

    resumed_job = job_service.resume_job(str(job["job_id"]))
    assert resumed_job["attempt_count"] == 2
    completed_job = _wait_for_job_status(job_service, str(job["job_id"]), "completed")
    assert completed_job["attempt_count"] == 2
    assert completed_job["pairs_backtest_id"] == "pairs_stub_1"
