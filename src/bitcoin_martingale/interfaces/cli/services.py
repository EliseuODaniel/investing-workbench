"""Service assembly for the CLI interface layer."""

from __future__ import annotations

from dataclasses import dataclass

from src.bitcoin_martingale.application.allocation_workspaces import AllocationWorkspaceService
from src.bitcoin_martingale.application.allocations import AllocationPlanningService
from src.bitcoin_martingale.application.backtest_jobs import (
    BacktestJobService,
    load_backtest_job_settings_from_env,
)
from src.bitcoin_martingale.application.datasets import DatasetCatalogService
from src.bitcoin_martingale.application.experiments import ExperimentRegistryService
from src.bitcoin_martingale.application.montecarlo import MonteCarloSimulationService
from src.bitcoin_martingale.application.optimizations import (
    OptimizationExecutionService,
    OptimizationPlanningService,
)
from src.bitcoin_martingale.application.pairs_jobs import PairsBacktestJobService
from src.bitcoin_martingale.application.pairs_trading import PairsTradingService
from src.bitcoin_martingale.application.research_workspaces import ResearchWorkspaceService
from src.bitcoin_martingale.application.runs import RunBacktestService
from src.bitcoin_martingale.application.system import PlatformStatusService
from src.bitcoin_martingale.application.walkforward import WalkForwardValidationService


@dataclass(frozen=True)
class CliServices:
    """Runtime services used by CLI command handlers."""

    run_service: RunBacktestService
    dataset_service: DatasetCatalogService
    experiment_registry_service: ExperimentRegistryService
    research_workspace_service: ResearchWorkspaceService
    optimization_planner: OptimizationPlanningService
    optimization_service: OptimizationExecutionService
    walkforward_service: WalkForwardValidationService
    montecarlo_service: MonteCarloSimulationService
    pairs_trading_service: PairsTradingService
    pairs_backtest_job_service: PairsBacktestJobService
    allocation_service: AllocationPlanningService
    allocation_workspace_service: AllocationWorkspaceService
    backtest_job_service: BacktestJobService
    system_status_service: PlatformStatusService


def build_services() -> CliServices:
    """Instantiate the service graph used by the CLI."""
    job_settings = load_backtest_job_settings_from_env()
    run_service = RunBacktestService()
    dataset_service = DatasetCatalogService()
    pairs_trading_service = PairsTradingService(dataset_service=dataset_service)
    experiment_registry_service = ExperimentRegistryService(
        runs_repository=run_service.runs_repository,
        pairs_repository=pairs_trading_service.repository,
    )
    research_workspace_service = ResearchWorkspaceService(
        experiment_registry_service=experiment_registry_service
    )
    allocation_service = AllocationPlanningService()
    allocation_workspace_service = AllocationWorkspaceService(
        allocation_service=allocation_service,
    )
    backtest_job_service = BacktestJobService(
        run_service=run_service,
        max_workers=job_settings.max_workers,
        resume_interrupted_jobs=job_settings.resume_interrupted_jobs,
        execution_mode=job_settings.execution_mode,
        autostart=False,
    )
    pairs_backtest_job_service = PairsBacktestJobService(
        pairs_service=pairs_trading_service,
        max_workers=job_settings.max_workers,
        resume_interrupted_jobs=job_settings.resume_interrupted_jobs,
        execution_mode=job_settings.execution_mode,
        autostart=False,
    )
    return CliServices(
        run_service=run_service,
        dataset_service=dataset_service,
        experiment_registry_service=experiment_registry_service,
        research_workspace_service=research_workspace_service,
        optimization_planner=OptimizationPlanningService(),
        optimization_service=OptimizationExecutionService(),
        walkforward_service=WalkForwardValidationService(),
        montecarlo_service=MonteCarloSimulationService(run_service=run_service),
        pairs_trading_service=pairs_trading_service,
        pairs_backtest_job_service=pairs_backtest_job_service,
        allocation_service=allocation_service,
        allocation_workspace_service=allocation_workspace_service,
        backtest_job_service=backtest_job_service,
        system_status_service=PlatformStatusService(
            run_service=run_service,
            dataset_service=dataset_service,
            experiment_registry_service=experiment_registry_service,
            research_workspace_service=research_workspace_service,
            allocation_workspace_service=allocation_workspace_service,
            pairs_trading_service=pairs_trading_service,
            backtest_job_service=backtest_job_service,
            pairs_backtest_job_service=pairs_backtest_job_service,
        ),
    )
