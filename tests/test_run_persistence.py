"""Tests for persisted run manifests and artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from src.api.models import BacktestRequest
from src.bitcoin_martingale.application.runs import RunBacktestService
from src.bitcoin_martingale.infrastructure.persistence import LocalRunsRepository


def test_run_service_persists_manifest_and_response(tmp_path: Path) -> None:
    repository = LocalRunsRepository(base_dir=tmp_path)
    service = RunBacktestService(runs_repository=repository)

    response = service.run(
        BacktestRequest(
            config_path="configs/test.yaml",
            start_date="2023-01-01",
            end_date="2023-01-10",
            initial_capital=10000.0,
        )
    )

    assert response.run_info is not None
    run_id = response.run_info["run_id"]
    artifact_dir = tmp_path / run_id
    manifest_path = artifact_dir / "manifest.json"
    response_path = artifact_dir / "response.json"

    assert artifact_dir.exists()
    assert manifest_path.exists()
    assert response_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    response_payload = json.loads(response_path.read_text(encoding="utf-8"))

    assert manifest["run_id"] == run_id
    assert manifest["config_path"] == "configs/test.yaml"
    assert "strategy_names" in manifest
    assert response_payload["run_info"]["run_id"] == run_id


def test_run_manifest_and_response_can_be_read_via_repository(tmp_path: Path) -> None:
    repository = LocalRunsRepository(base_dir=tmp_path)
    service = RunBacktestService(runs_repository=repository)

    response = service.run(BacktestRequest(config_path="configs/test.yaml"))
    run_id = response.run_info["run_id"]

    manifest = repository.get_manifest(run_id)
    response_payload = repository.get_response_payload(run_id)

    assert manifest["run_id"] == run_id
    assert response_payload["run_info"]["run_id"] == run_id


def test_run_repository_lists_runs_and_builds_csv(tmp_path: Path) -> None:
    repository = LocalRunsRepository(base_dir=tmp_path)
    service = RunBacktestService(runs_repository=repository)

    response = service.run(BacktestRequest(config_path="configs/test.yaml"))
    run_id = response.run_info["run_id"]
    listed_runs = repository.list_runs()
    csv_content = repository.build_trades_csv(run_id, next(iter(response.results.keys())))

    assert listed_runs[0]["run_id"] == run_id
    assert "timestamp,action,price,quantity,layer,pnl" in csv_content
