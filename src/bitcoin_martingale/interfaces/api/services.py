"""Shared API service factories and request translators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.api.models import MonteCarloRequestModel, OptimizationPlanRequest, WalkForwardRequestModel
from src.bitcoin_martingale.application.allocation_workspaces import AllocationWorkspaceService
from src.bitcoin_martingale.application.allocations import AllocationPlanningService
from src.bitcoin_martingale.application.backtest_jobs import (
    BacktestJobService,
    load_backtest_job_settings_from_env,
)
from src.bitcoin_martingale.application.datasets import DatasetCatalogService
from src.bitcoin_martingale.application.experiments import ExperimentRegistryService
from src.bitcoin_martingale.application.investments import InvestmentComparisonService
from src.bitcoin_martingale.application.montecarlo import MonteCarloSimulationService
from src.bitcoin_martingale.application.optimizations import (
    OptimizationExecutionService,
    OptimizationPlanningService,
)
from src.bitcoin_martingale.application.pairs_jobs import PairsBacktestJobService
from src.bitcoin_martingale.application.pairs_trading import PairsTradingService
from src.bitcoin_martingale.application.research_workspaces import ResearchWorkspaceService
from src.bitcoin_martingale.application.runs import RunBacktestService
from src.bitcoin_martingale.application.scenarios import Wege3RegraAScenarioService
from src.bitcoin_martingale.application.system import PlatformStatusService
from src.bitcoin_martingale.application.walkforward import WalkForwardValidationService
from src.bitcoin_martingale.domain.montecarlo import MonteCarloMethod, MonteCarloRequest
from src.bitcoin_martingale.domain.optimizations import (
    OptimizationDirection,
    OptimizationMode,
    OptimizationRequest,
)
from src.bitcoin_martingale.domain.walkforward import WalkForwardRequest


@dataclass(frozen=True)
class ApiServices:
    """Resolved service dependencies for the FastAPI interface layer."""

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
    wege3_regra_a_service: Wege3RegraAScenarioService
    investment_comparison_service: InvestmentComparisonService
    system_status_service: PlatformStatusService


def build_api_services(*, autostart_jobs: bool = True) -> ApiServices:
    """Build the API service graph in one explicit place."""
    job_settings = load_backtest_job_settings_from_env()
    run_service = RunBacktestService()
    dataset_service = DatasetCatalogService()
    pairs_trading_service = PairsTradingService(dataset_service=dataset_service)
    experiment_registry_service = ExperimentRegistryService(
        runs_repository=run_service.runs_repository,
        pairs_repository=pairs_trading_service.repository,
    )
    research_workspace_service = ResearchWorkspaceService(
        experiment_registry_service=experiment_registry_service,
    )
    optimization_planner = OptimizationPlanningService()
    optimization_service = OptimizationExecutionService(run_service=run_service)
    walkforward_service = WalkForwardValidationService()
    montecarlo_service = MonteCarloSimulationService(run_service=run_service)
    allocation_service = AllocationPlanningService()
    allocation_workspace_service = AllocationWorkspaceService(
        allocation_service=allocation_service,
    )
    wege3_regra_a_service = Wege3RegraAScenarioService()
    investment_comparison_service = InvestmentComparisonService()
    backtest_job_service = BacktestJobService(
        run_service=run_service,
        max_workers=job_settings.max_workers,
        resume_interrupted_jobs=job_settings.resume_interrupted_jobs,
        execution_mode=job_settings.execution_mode,
        autostart=autostart_jobs,
    )
    pairs_backtest_job_service = PairsBacktestJobService(
        pairs_service=pairs_trading_service,
        max_workers=job_settings.max_workers,
        resume_interrupted_jobs=job_settings.resume_interrupted_jobs,
        execution_mode=job_settings.execution_mode,
        autostart=autostart_jobs,
    )
    system_status_service = PlatformStatusService(
        run_service=run_service,
        dataset_service=dataset_service,
        experiment_registry_service=experiment_registry_service,
        research_workspace_service=research_workspace_service,
        allocation_workspace_service=allocation_workspace_service,
        pairs_trading_service=pairs_trading_service,
        backtest_job_service=backtest_job_service,
        pairs_backtest_job_service=pairs_backtest_job_service,
    )
    return ApiServices(
        run_service=run_service,
        dataset_service=dataset_service,
        experiment_registry_service=experiment_registry_service,
        research_workspace_service=research_workspace_service,
        optimization_planner=optimization_planner,
        optimization_service=optimization_service,
        walkforward_service=walkforward_service,
        montecarlo_service=montecarlo_service,
        pairs_trading_service=pairs_trading_service,
        pairs_backtest_job_service=pairs_backtest_job_service,
        allocation_service=allocation_service,
        allocation_workspace_service=allocation_workspace_service,
        backtest_job_service=backtest_job_service,
        wege3_regra_a_service=wege3_regra_a_service,
        investment_comparison_service=investment_comparison_service,
        system_status_service=system_status_service,
    )


def shutdown_api_services(services: ApiServices, *, cancel_running: bool = False) -> None:
    """Release in-memory worker resources owned by the API service graph."""
    services.backtest_job_service.shutdown(wait=True, cancel_running=cancel_running)
    services.pairs_backtest_job_service.shutdown(wait=True, cancel_running=cancel_running)


def install_service_container(app: Any, services: ApiServices) -> ApiServices:
    """Attach one API service container to the given FastAPI application state."""
    app.state.service_container = services
    app.state.get_service = lambda service_name: getattr(app.state.service_container, service_name)
    return services


def ensure_service_container(app: Any, *, autostart_jobs: bool = True) -> ApiServices:
    """Return the installed API service container, building it lazily when required."""
    container = getattr(app.state, "service_container", None)
    if container is not None:
        return container
    return install_service_container(
        app,
        build_api_services(autostart_jobs=autostart_jobs),
    )


def to_optimization_request(request: OptimizationPlanRequest) -> OptimizationRequest:
    """Convert API payloads into optimization domain requests."""
    return OptimizationRequest(
        config_path=request.config_path,
        strategy_names=request.strategies,
        parameter_space=request.parameter_space,
        strategy_parameter_spaces=request.strategy_parameter_spaces,
        mode=OptimizationMode(request.mode),
        max_trials=request.max_trials,
        random_seed=request.random_seed,
        objective=request.objective,
        direction=OptimizationDirection(request.direction),
    )


def to_walkforward_request(request: WalkForwardRequestModel) -> WalkForwardRequest:
    """Convert API payloads into walk-forward domain requests."""
    return WalkForwardRequest(
        config_path=request.config_path,
        strategy_names=request.strategies,
        train_window_days=request.train_window_days,
        test_window_days=request.test_window_days,
        step_days=request.step_days,
    )


def to_montecarlo_request(request: MonteCarloRequestModel) -> MonteCarloRequest:
    """Convert API payloads into Monte Carlo domain requests."""
    return MonteCarloRequest(
        config_path=request.config_path,
        run_id=request.run_id,
        strategy_names=request.strategies,
        simulation_count=request.simulation_count,
        random_seed=request.random_seed,
        method=MonteCarloMethod(request.method),
        ruin_threshold_pct=request.ruin_threshold_pct,
    )
