from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from src.investing_workbench.interfaces.cli.main import main

STATUS_PAYLOAD = {
    "status": "degraded",
    "api_version": "1.0.0",
    "checked_at": "2026-04-20T15:00:00+00:00",
    "config_count": 2,
    "dataset_count": 3,
    "due_dataset_count": 1,
    "artifact_counts": {
        "runs": 4,
        "optimizations": 2,
        "walkforward": 1,
        "montecarlo": 1,
        "pairs_backtests": 0,
        "research_workspaces": 5,
        "allocation_workspaces": 2,
    },
    "job_counts": {
        "queued": 1,
        "running": 0,
        "completed": 4,
        "failed": 1,
        "cancelled": 0,
    },
    "job_runtime": {
        "execution_mode": "detached",
        "max_workers": 2,
        "active_futures": 0,
    },
    "latest_backtest_job_id": "job_9",
    "latest_run_id": "run_4",
    "latest_pairs_backtest_id": None,
    "latest_research_workspace_id": "research_ws_5",
    "warnings": ["There are datasets whose refresh policy is currently due."],
}


def _services() -> SimpleNamespace:
    return SimpleNamespace(
        system_status_service=SimpleNamespace(get_status=lambda: STATUS_PAYLOAD),
    )


def test_system_status_cli_prints_text_summary(capsys) -> None:
    with patch(
        "src.investing_workbench.interfaces.cli.main.build_services", return_value=_services()
    ):
        main(["system-status"])

    output = capsys.readouterr().out
    assert "status=degraded" in output
    assert "due_datasets=1" in output
    assert "latest_job=job_9" in output
    assert "latest_run=run_4" in output
    assert "latest_research_workspace=research_ws_5" in output


def test_system_status_cli_prints_json(capsys) -> None:
    with patch(
        "src.investing_workbench.interfaces.cli.main.build_services", return_value=_services()
    ):
        main(["system-status", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact_counts"]["runs"] == 4
    assert payload["due_dataset_count"] == 1
