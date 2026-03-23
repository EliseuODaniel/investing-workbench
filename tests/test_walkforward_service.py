"""Tests for walk-forward validation."""

from __future__ import annotations

from pathlib import Path

from src.bitcoin_martingale.application.walkforward import WalkForwardValidationService
from src.bitcoin_martingale.domain.walkforward import WalkForwardRequest
from src.bitcoin_martingale.infrastructure.persistence import LocalWalkForwardRepository


def test_walkforward_execution_persists_results(tmp_path: Path) -> None:
    repository = LocalWalkForwardRepository(base_dir=tmp_path / "walkforward")
    service = WalkForwardValidationService(repository=repository)

    result = service.execute(
        WalkForwardRequest(
            config_path="configs/test.yaml",
            strategy_names=["Simple Martingale"],
            train_window_days=45,
            test_window_days=20,
            step_days=20,
        )
    )

    manifest = repository.get_manifest(result.walkforward_id)
    persisted_results = repository.get_results(result.walkforward_id)

    assert result.window_count > 0
    assert manifest["walkforward_id"] == result.walkforward_id
    assert manifest["window_count"] == result.window_count
    assert len(persisted_results["results"]) == result.window_count
    assert persisted_results["strategy_summaries"][0]["strategy_name"] == "Simple Martingale"


def test_walkforward_requires_enough_data(tmp_path: Path) -> None:
    repository = LocalWalkForwardRepository(base_dir=tmp_path / "walkforward")
    service = WalkForwardValidationService(repository=repository)

    try:
        service.execute(
            WalkForwardRequest(
                config_path="configs/test.yaml",
                strategy_names=["Simple Martingale"],
                train_window_days=500,
                test_window_days=50,
                step_days=25,
            )
        )
    except ValueError as exc:
        assert "Not enough data" in str(exc)
    else:
        raise AssertionError("Expected walk-forward execution to fail with oversized windows")
