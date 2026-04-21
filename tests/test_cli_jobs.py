from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from src.bitcoin_martingale.interfaces.cli.main import main


def _services() -> SimpleNamespace:
    return SimpleNamespace(
        backtest_job_service=SimpleNamespace(
            list_jobs=lambda status=None, limit=None: [
                {
                    "job_id": "job_1",
                    "status": "queued",
                    "attempt_count": 1,
                }
            ],
            get_job=lambda job_id: {
                "job_id": job_id,
                "status": "completed",
                "run_id": "run_1",
            },
            run_worker_loop=lambda **kwargs: {
                "worker_id": kwargs.get("worker_id") or "worker_auto",
                "processed_jobs": 1,
                "execution_mode": "detached",
            },
        ),
    )


def test_backtest_jobs_list_cli_prints_json(capsys) -> None:
    with patch(
        "src.bitcoin_martingale.interfaces.cli.main.build_services",
        return_value=_services(),
    ):
        main(["backtest-jobs-list", "--limit", "5"])

    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["job_id"] == "job_1"


def test_backtest_jobs_worker_cli_runs_once(capsys) -> None:
    with patch(
        "src.bitcoin_martingale.interfaces.cli.main.build_services",
        return_value=_services(),
    ):
        main(["backtest-jobs-worker", "--once", "--worker-id", "worker_test"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["worker_id"] == "worker_test"
    assert payload["processed_jobs"] == 1
