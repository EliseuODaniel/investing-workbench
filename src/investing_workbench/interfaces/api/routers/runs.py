"""Backtest and persisted run API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from src.api.models import (
    BacktestJobModel,
    BacktestRequest,
    BacktestResponse,
    SavedStrategyRadarItemModel,
    StrategySetupPlanModel,
)
from src.investing_workbench.application.backtests.strategy_catalog import (
    build_strategy_catalog_payload,
    build_strategy_setup_plan,
)
from src.investing_workbench.interfaces.api.deps import get_service
from src.investing_workbench.interfaces.api.errors import to_http_exception

router = APIRouter(tags=["runs"])


@router.get("/backtests/strategy-catalog")
async def get_strategy_catalog() -> dict[str, object]:
    """Return strategy catalog and score metadata for the backtest workspace."""
    return build_strategy_catalog_payload()


@router.post("/backtests/strategy-setup-plan", response_model=StrategySetupPlanModel)
async def create_strategy_setup_plan(
    payload: SavedStrategyRadarItemModel,
) -> StrategySetupPlanModel:
    """Prepare an explainable execution plan from a saved strategy setup."""
    return StrategySetupPlanModel.model_validate(build_strategy_setup_plan(payload.model_dump()))


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(payload: BacktestRequest, request: Request) -> BacktestResponse:
    """Run backtest with specified parameters."""
    try:
        return get_service(request, "run_service").run(payload)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/backtest/jobs", response_model=BacktestJobModel)
async def create_backtest_job(payload: BacktestRequest, request: Request) -> BacktestJobModel:
    """Queue a backtest job for asynchronous execution."""
    try:
        return get_service(request, "backtest_job_service").create_job(payload)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/backtest/jobs", response_model=list[BacktestJobModel])
async def list_backtest_jobs(
    request: Request,
    status: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=100),
) -> list[BacktestJobModel]:
    """List persisted async backtest jobs."""
    try:
        return get_service(request, "backtest_job_service").list_jobs(status=status, limit=limit)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/backtest/jobs/{job_id}", response_model=BacktestJobModel)
async def get_backtest_job(job_id: str, request: Request) -> BacktestJobModel:
    """Return one async backtest job manifest."""
    try:
        return get_service(request, "backtest_job_service").get_job(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/backtest/jobs/{job_id}/cancel", response_model=BacktestJobModel)
async def cancel_backtest_job(job_id: str, request: Request) -> BacktestJobModel:
    """Request cancellation for an async backtest job."""
    try:
        return get_service(request, "backtest_job_service").cancel_job(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/backtest/jobs/{job_id}/resume", response_model=BacktestJobModel)
async def resume_backtest_job(job_id: str, request: Request) -> BacktestJobModel:
    """Resume a failed or cancelled async backtest job."""
    try:
        return get_service(request, "backtest_job_service").resume_job(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/backtest/jobs/{job_id}/response")
async def get_backtest_job_response(job_id: str, request: Request) -> dict[str, object]:
    """Return the completed run response linked to one async backtest job."""
    try:
        return get_service(request, "backtest_job_service").get_job_response(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/reports/{strategy}/download")
async def download_csv(strategy: str, request: Request) -> Response:
    """Download CSV with trades and equity data for a strategy."""
    try:
        csv_content = get_service(request, "run_service").download_csv(strategy)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{strategy}_latest_trades.csv"'},
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/runs")
async def list_runs(request: Request) -> list[dict[str, object]]:
    """List persisted runs."""
    try:
        return get_service(request, "run_service").list_runs()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/runs/{run_id}")
async def get_run_manifest(run_id: str, request: Request) -> dict[str, object]:
    """Return the persisted manifest for a run."""
    try:
        return get_service(request, "run_service").get_run_manifest(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/runs/{run_id}/response")
async def get_run_response(run_id: str, request: Request) -> dict[str, object]:
    """Return the persisted response payload for a run."""
    try:
        return get_service(request, "run_service").get_run_response(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/runs/{run_id}/config")
async def get_run_config(run_id: str, request: Request) -> dict[str, object]:
    """Return the resolved config snapshot for a run."""
    try:
        return get_service(request, "run_service").get_run_config_snapshot(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/runs/{run_id}/data-profile")
async def get_run_data_profile(run_id: str, request: Request) -> dict[str, object]:
    """Return the dataset profile for a run."""
    try:
        return get_service(request, "run_service").get_run_data_profile(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/runs/{run_id}/report.html")
async def get_run_html_report(run_id: str, request: Request) -> Response:
    """Download the persisted HTML report for a run."""
    try:
        html_report = get_service(request, "run_service").get_run_html_report(run_id)
        return Response(
            content=html_report,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{run_id}_report.html"'},
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/runs/{run_id}/strategies/{strategy_name}/trades.csv")
async def download_run_strategy_csv(run_id: str, strategy_name: str, request: Request) -> Response:
    """Download a persisted strategy trades CSV."""
    try:
        csv_content = get_service(request, "run_service").get_trades_csv(run_id, strategy_name)
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
