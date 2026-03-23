"""Tests for optimization execution and persistence."""

from __future__ import annotations

from pathlib import Path

from src.bitcoin_martingale.application.optimizations import OptimizationExecutionService
from src.bitcoin_martingale.application.runs import RunBacktestService
from src.bitcoin_martingale.domain.optimizations import (
    OptimizationDirection,
    OptimizationMode,
    OptimizationRequest,
)
from src.bitcoin_martingale.infrastructure.persistence import (
    LocalOptimizationsRepository,
    LocalRunsRepository,
)


def test_optimization_execution_persists_manifest_and_ranked_results(tmp_path: Path) -> None:
    runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
    optimizations_repository = LocalOptimizationsRepository(base_dir=tmp_path / "optimizations")
    run_service = RunBacktestService(runs_repository=runs_repository)
    service = OptimizationExecutionService(
        run_service=run_service,
        repository=optimizations_repository,
    )

    request = OptimizationRequest(
        config_path="configs/test.yaml",
        strategy_names=["Simple Martingale"],
        parameter_space={"base_bet": {"values": [250.0, 500.0]}},
        objective="total_return",
    )

    result = service.execute(request)
    manifest = optimizations_repository.get_manifest(result.optimization_id)
    persisted_results = optimizations_repository.get_results(result.optimization_id)

    assert result.trial_count == 2
    assert result.completed_trial_count == 2
    assert manifest["optimization_id"] == result.optimization_id
    assert manifest["completed_trial_count"] == 2
    assert persisted_results["optimization_id"] == result.optimization_id
    assert len(persisted_results["ranked_results"]) == 2

    first_run_id = result.results[0].run_id
    assert first_run_id is not None
    assert runs_repository.get_manifest(first_run_id)["run_id"] == first_run_id


def test_optimization_execution_ranks_results_by_objective_direction(tmp_path: Path) -> None:
    runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
    optimizations_repository = LocalOptimizationsRepository(base_dir=tmp_path / "optimizations")
    run_service = RunBacktestService(runs_repository=runs_repository)
    service = OptimizationExecutionService(
        run_service=run_service,
        repository=optimizations_repository,
    )

    request = OptimizationRequest(
        config_path="configs/test.yaml",
        strategy_names=["Simple Martingale"],
        parameter_space={"base_bet": {"values": [250.0, 1000.0]}},
        objective="total_return",
        direction=OptimizationDirection.MAXIMIZE,
        mode=OptimizationMode.GRID,
    )

    result = service.execute(request)
    ranked_results = result.ranked_results()

    assert len(ranked_results) == 2
    assert ranked_results[0].objective_value is not None
    assert ranked_results[1].objective_value is not None
    assert ranked_results[0].objective_value >= ranked_results[1].objective_value


def test_optimization_execution_marks_trials_failed_for_unknown_objective(
    tmp_path: Path,
) -> None:
    runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
    optimizations_repository = LocalOptimizationsRepository(base_dir=tmp_path / "optimizations")
    run_service = RunBacktestService(runs_repository=runs_repository)
    service = OptimizationExecutionService(
        run_service=run_service,
        repository=optimizations_repository,
    )

    request = OptimizationRequest(
        config_path="configs/test.yaml",
        strategy_names=["Simple Martingale"],
        parameter_space={"base_bet": {"values": [250.0]}},
        objective="missing_metric",
    )

    result = service.execute(request)

    assert result.completed_trial_count == 0
    assert result.results[0].status == "failed"
    assert "missing_metric" in (result.results[0].error or "")
