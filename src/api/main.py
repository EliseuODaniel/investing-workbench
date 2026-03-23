"""FastAPI main application."""

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from ..bitcoin_martingale.application.datasets import DatasetCatalogService
from ..bitcoin_martingale.application.montecarlo import MonteCarloSimulationService
from ..bitcoin_martingale.application.optimizations import (
    OptimizationExecutionService,
    OptimizationPlanningService,
)
from ..bitcoin_martingale.application.runs import RunBacktestService
from ..bitcoin_martingale.application.walkforward import WalkForwardValidationService
from ..bitcoin_martingale.domain.montecarlo import MonteCarloMethod, MonteCarloRequest
from ..bitcoin_martingale.domain.optimizations import (
    OptimizationDirection,
    OptimizationMode,
    OptimizationRequest,
)
from ..bitcoin_martingale.domain.walkforward import WalkForwardRequest
from ..bitcoin_martingale.infrastructure.logging import configure_logging
from ..bitcoin_martingale.interfaces.api.errors import to_http_exception
from .models import (
    BacktestRequest,
    BacktestResponse,
    ConfigInfo,
    DatasetDetailModel,
    DatasetSummaryModel,
    MonteCarloRequestModel,
    OptimizationPlanRequest,
    WalkForwardRequestModel,
)

configure_logging()
logger = logging.getLogger(__name__)
service = RunBacktestService()
dataset_service = DatasetCatalogService()
optimization_planner = OptimizationPlanningService()
optimization_service = OptimizationExecutionService(run_service=service)
walkforward_service = WalkForwardValidationService()
montecarlo_service = MonteCarloSimulationService(run_service=service)

app = FastAPI(
    title="Bitcoin Martingale Backtest API",
    description="Interactive backtesting API for Bitcoin Martingale strategies",
    version="1.0.0",
)


def _to_optimization_request(request: OptimizationPlanRequest) -> OptimizationRequest:
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


def _to_walkforward_request(request: WalkForwardRequestModel) -> WalkForwardRequest:
    """Convert API payloads into walk-forward domain requests."""
    return WalkForwardRequest(
        config_path=request.config_path,
        strategy_names=request.strategies,
        train_window_days=request.train_window_days,
        test_window_days=request.test_window_days,
        step_days=request.step_days,
    )


def _to_montecarlo_request(request: MonteCarloRequestModel) -> MonteCarloRequest:
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Bitcoin Martingale Backtest API", "version": "1.0.0"}


@app.get("/configs", response_model=list[ConfigInfo])
async def get_configs():
    """List available configuration files."""
    try:
        return service.list_configs()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/datasets", response_model=list[DatasetSummaryModel])
async def list_datasets():
    """List discovered local datasets."""
    try:
        return dataset_service.list_datasets()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/datasets/{dataset_id}", response_model=DatasetDetailModel)
async def get_dataset(dataset_id: str):
    """Inspect a discovered local dataset."""
    try:
        return dataset_service.get_dataset(dataset_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run backtest with specified parameters."""
    try:
        return service.run(request)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/reports/{strategy}/download")
async def download_csv(strategy: str):
    """Download CSV with trades and equity data for a strategy."""
    try:
        csv_content = service.download_csv(strategy)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{strategy}_latest_trades.csv"'},
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}")
async def get_run_manifest(run_id: str):
    """Return the persisted manifest for a run."""
    try:
        return service.get_run_manifest(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/response")
async def get_run_response(run_id: str):
    """Return the persisted response payload for a run."""
    try:
        return service.get_run_response(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/config")
async def get_run_config(run_id: str):
    """Return the resolved config snapshot for a run."""
    try:
        return service.get_run_config_snapshot(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/data-profile")
async def get_run_data_profile(run_id: str):
    """Return the dataset profile for a run."""
    try:
        return service.get_run_data_profile(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/report.html")
async def get_run_html_report(run_id: str):
    """Download the persisted HTML report for a run."""
    try:
        html_report = service.get_run_html_report(run_id)
        return Response(
            content=html_report,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{run_id}_report.html"'},
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs")
async def list_runs():
    """List persisted runs."""
    try:
        return service.list_runs()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/strategies/{strategy_name}/trades.csv")
async def download_run_strategy_csv(run_id: str, strategy_name: str):
    """Download a persisted strategy trades CSV."""
    try:
        csv_content = service.get_trades_csv(run_id, strategy_name)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{run_id}_{strategy_name}_trades.csv"'
                )
            },
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.post("/optimizations/plan")
async def plan_optimization(request: OptimizationPlanRequest) -> dict[str, Any]:
    """Preview a reproducible optimization trial plan."""
    try:
        optimization_request = _to_optimization_request(request)
        return optimization_planner.build_plan(optimization_request).to_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.post("/optimizations")
async def execute_optimization(request: OptimizationPlanRequest) -> dict[str, Any]:
    """Execute and persist an optimization job."""
    try:
        optimization_request = _to_optimization_request(request)
        return optimization_service.execute(optimization_request).results_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/optimizations")
async def list_optimizations() -> list[dict[str, Any]]:
    """List persisted optimization jobs."""
    try:
        return optimization_service.list_optimizations()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/optimizations/{optimization_id}")
async def get_optimization_manifest(optimization_id: str) -> dict[str, Any]:
    """Return the persisted manifest for an optimization job."""
    try:
        return optimization_service.get_manifest(optimization_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/optimizations/{optimization_id}/results")
async def get_optimization_results(optimization_id: str) -> dict[str, Any]:
    """Return the persisted ranked results for an optimization job."""
    try:
        return optimization_service.get_results(optimization_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.post("/walkforward")
async def execute_walkforward(request: WalkForwardRequestModel) -> dict[str, Any]:
    """Execute and persist walk-forward validation."""
    try:
        walkforward_request = _to_walkforward_request(request)
        return walkforward_service.execute(walkforward_request).results_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/walkforward")
async def list_walkforward_executions() -> list[dict[str, Any]]:
    """List persisted walk-forward validations."""
    try:
        return walkforward_service.list_executions()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/walkforward/{walkforward_id}")
async def get_walkforward_manifest(walkforward_id: str) -> dict[str, Any]:
    """Return the persisted manifest for a walk-forward validation."""
    try:
        return walkforward_service.get_manifest(walkforward_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/walkforward/{walkforward_id}/results")
async def get_walkforward_results(walkforward_id: str) -> dict[str, Any]:
    """Return the persisted results for a walk-forward validation."""
    try:
        return walkforward_service.get_results(walkforward_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.post("/montecarlo")
async def execute_montecarlo(request: MonteCarloRequestModel) -> dict[str, Any]:
    """Execute and persist Monte Carlo robustness analysis."""
    try:
        montecarlo_request = _to_montecarlo_request(request)
        return montecarlo_service.execute(montecarlo_request).results_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/montecarlo")
async def list_montecarlo_executions() -> list[dict[str, Any]]:
    """List persisted Monte Carlo analyses."""
    try:
        return montecarlo_service.list_executions()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/montecarlo/{montecarlo_id}")
async def get_montecarlo_manifest(montecarlo_id: str) -> dict[str, Any]:
    """Return the persisted manifest for a Monte Carlo analysis."""
    try:
        return montecarlo_service.get_manifest(montecarlo_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/montecarlo/{montecarlo_id}/results")
async def get_montecarlo_results(montecarlo_id: str) -> dict[str, Any]:
    """Return the persisted results for a Monte Carlo analysis."""
    try:
        return montecarlo_service.get_results(montecarlo_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc
