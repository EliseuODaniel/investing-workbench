"""Focused tests for the lightweight system status route."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from src.investing_workbench.interfaces.api.routers.system import get_system_status
from tests.support import override_api_services


class _StubSystemStatusService:
    def get_status(self) -> dict[str, object]:
        return {
            "status": "ok",
            "api_version": "1.0.0",
            "checked_at": "2026-04-20T15:00:00+00:00",
            "config_count": 3,
            "dataset_count": 2,
            "due_dataset_count": 1,
            "artifact_counts": {
                "runs": 7,
                "optimizations": 2,
                "walkforward": 1,
                "montecarlo": 1,
                "pairs_backtests": 0,
                "research_workspaces": 4,
                "allocation_workspaces": 1,
            },
            "job_counts": {
                "queued": 1,
                "running": 0,
                "completed": 4,
                "failed": 0,
                "cancelled": 0,
            },
            "job_runtime": {
                "execution_mode": "inline",
                "max_workers": 2,
                "active_futures": 1,
            },
            "pairs_job_counts": {
                "queued": 0,
                "running": 0,
                "completed": 2,
                "failed": 0,
                "cancelled": 0,
            },
            "pairs_job_runtime": {
                "execution_mode": "inline",
                "max_workers": 2,
                "active_futures": 0,
            },
            "latest_run_id": "run_7",
            "latest_backtest_job_id": "job_4",
            "latest_pairs_backtest_job_id": "pairs_job_2",
            "latest_pairs_backtest_id": None,
            "latest_research_workspace_id": "research_ws_4",
            "warnings": [],
        }


def test_system_status_route_reads_current_service(monkeypatch) -> None:
    from src.api import main as api_main

    request = SimpleNamespace(app=api_main.app)

    with override_api_services(system_status_service=_StubSystemStatusService()):
        payload = asyncio.run(get_system_status(request))

    assert payload["status"] == "ok"
    assert payload["config_count"] == 3
    assert payload["due_dataset_count"] == 1
    assert payload["artifact_counts"]["runs"] == 7
    assert payload["job_counts"]["queued"] == 1
    assert payload["job_runtime"]["execution_mode"] == "inline"
    assert payload["job_runtime"]["max_workers"] == 2
    assert payload["pairs_job_counts"]["completed"] == 2
    assert payload["pairs_job_runtime"]["active_futures"] == 0
    assert payload["latest_run_id"] == "run_7"
    assert payload["latest_backtest_job_id"] == "job_4"
    assert payload["latest_pairs_backtest_job_id"] == "pairs_job_2"
