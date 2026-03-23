"""Tests for Monte Carlo robustness analysis."""

from __future__ import annotations

from pathlib import Path

from src.bitcoin_martingale.application.montecarlo import MonteCarloSimulationService
from src.bitcoin_martingale.application.runs import RunBacktestService
from src.bitcoin_martingale.domain.montecarlo import MonteCarloMethod, MonteCarloRequest
from src.bitcoin_martingale.infrastructure.persistence import (
    LocalMonteCarloRepository,
    LocalRunsRepository,
)


def test_montecarlo_execution_persists_results(tmp_path: Path) -> None:
    runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
    run_service = RunBacktestService(runs_repository=runs_repository)
    repository = LocalMonteCarloRepository(base_dir=tmp_path / "montecarlo")
    service = MonteCarloSimulationService(
        run_service=run_service,
        repository=repository,
        runs_repository=runs_repository,
    )

    result = service.execute(
        MonteCarloRequest(
            config_path="configs/test.yaml",
            strategy_names=["Simple Martingale"],
            simulation_count=25,
            random_seed=7,
        )
    )

    manifest = repository.get_manifest(result.montecarlo_id)
    persisted_results = repository.get_results(result.montecarlo_id)

    assert manifest["montecarlo_id"] == result.montecarlo_id
    assert manifest["simulation_count"] == 25
    assert manifest["source_run_id"].startswith("run_")
    assert persisted_results["results"][0]["strategy_name"] == "Simple Martingale"
    assert len(persisted_results["results"][0]["simulations"]) == 25


def test_montecarlo_can_reuse_existing_run(tmp_path: Path) -> None:
    runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
    run_service = RunBacktestService(runs_repository=runs_repository)
    initial_run = run_service.run_trial(
        config_path="configs/test.yaml",
        strategy_name="Simple Martingale",
        parameter_overrides={},
    )
    repository = LocalMonteCarloRepository(base_dir=tmp_path / "montecarlo")
    service = MonteCarloSimulationService(
        run_service=run_service,
        repository=repository,
        runs_repository=runs_repository,
    )

    result = service.execute(
        MonteCarloRequest(
            run_id=initial_run.run_info["run_id"],
            strategy_names=["Simple Martingale"],
            simulation_count=10,
            random_seed=13,
            method=MonteCarloMethod.SHUFFLE,
        )
    )

    assert result.source_run_id == initial_run.run_info["run_id"]
    assert result.results[0].simulation_count == 10
    assert result.results[0].method == MonteCarloMethod.SHUFFLE
