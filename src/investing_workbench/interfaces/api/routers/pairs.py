"""Pairs-trading API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models import (
    PairsBacktestJobModel,
    PairsBacktestManifestModel,
    PairsBacktestRequestModel,
    PairsBacktestResultsModel,
    PairsBatchRequestModel,
    PairsIbovBackfillRequestModel,
    PairsIbovBackfillResponseModel,
    PairsIbovSnapshotModel,
    PairsScreenPayloadModel,
    PairsScreenRequestModel,
    PairsUniversePayloadModel,
    PairsUniverseResolveRequestModel,
)
from src.investing_workbench.interfaces.api.deps import get_service
from src.investing_workbench.interfaces.api.errors import to_http_exception

router = APIRouter(tags=["pairs"])


@router.get("/pairs/universes")
async def list_pairs_universes(request: Request) -> list[dict[str, object]]:
    """List curated B3 universe presets for pairs trading."""
    try:
        return get_service(request, "pairs_trading_service").list_universe_presets()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/ibov-snapshots", response_model=list[PairsIbovSnapshotModel])
async def list_ibov_snapshots(request: Request) -> list[PairsIbovSnapshotModel]:
    """List cached official IBOV snapshots."""
    try:
        return get_service(request, "pairs_trading_service").list_ibov_snapshots()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/ibov-snapshots/{as_of_date}", response_model=PairsIbovSnapshotModel)
async def get_ibov_snapshot(as_of_date: str, request: Request) -> PairsIbovSnapshotModel:
    """Return one cached official IBOV snapshot by resolved as-of date."""
    try:
        return get_service(request, "pairs_trading_service").get_ibov_snapshot(
            as_of_date=as_of_date
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post(
    "/pairs/ibov-snapshots/backfill",
    response_model=PairsIbovBackfillResponseModel,
)
async def backfill_ibov_snapshots(
    payload: PairsIbovBackfillRequestModel,
    request: Request,
) -> PairsIbovBackfillResponseModel:
    """Backfill official IBOV snapshots around the rebalance cadence."""
    try:
        return get_service(request, "pairs_trading_service").backfill_ibov_snapshots(
            **payload.model_dump()
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/universe/resolve", response_model=PairsUniversePayloadModel)
async def resolve_pairs_universe(
    payload: PairsUniverseResolveRequestModel,
    request: Request,
) -> PairsUniversePayloadModel:
    """Resolve one B3 pairs universe and return quality diagnostics."""
    try:
        return get_service(request, "pairs_trading_service").resolve_universe(
            **payload.model_dump()
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/screener", response_model=PairsScreenPayloadModel)
async def screen_pairs(
    payload: PairsScreenRequestModel,
    request: Request,
) -> PairsScreenPayloadModel:
    """Run the B3 cointegration screener over one resolved universe."""
    try:
        return get_service(request, "pairs_trading_service").screen_pairs(**payload.model_dump())
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/backtests", response_model=PairsBacktestResultsModel)
async def run_pairs_backtest(
    payload: PairsBacktestRequestModel,
    request: Request,
) -> PairsBacktestResultsModel:
    """Execute and persist one B3 pairs-trading backtest."""
    try:
        return get_service(request, "pairs_trading_service").run_backtest(**payload.model_dump())
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/backtests/jobs", response_model=PairsBacktestJobModel)
async def create_pairs_backtest_job(
    payload: PairsBacktestRequestModel,
    request: Request,
) -> PairsBacktestJobModel:
    """Queue one pairs backtest job for asynchronous execution."""
    try:
        return get_service(request, "pairs_backtest_job_service").create_job(payload)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/backtests/jobs/batch", response_model=PairsBacktestJobModel)
async def create_pairs_batch_backtest_job(
    payload: PairsBatchRequestModel,
    request: Request,
) -> PairsBacktestJobModel:
    """Queue one multi-scenario pairs backtest batch for asynchronous execution."""
    try:
        return get_service(request, "pairs_backtest_job_service").create_job(
            payload,
            batch_mode=True,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/backtests/jobs", response_model=list[PairsBacktestJobModel])
async def list_pairs_backtest_jobs(
    request: Request,
    status: str | None = None,
    limit: int | None = None,
) -> list[PairsBacktestJobModel]:
    """List persisted async pairs backtest jobs."""
    try:
        return get_service(request, "pairs_backtest_job_service").list_jobs(
            status=status,
            limit=limit,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/backtests/jobs/{job_id}", response_model=PairsBacktestJobModel)
async def get_pairs_backtest_job(job_id: str, request: Request) -> PairsBacktestJobModel:
    """Return one async pairs backtest job manifest."""
    try:
        return get_service(request, "pairs_backtest_job_service").get_job(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/backtests/jobs/{job_id}/cancel", response_model=PairsBacktestJobModel)
async def cancel_pairs_backtest_job(job_id: str, request: Request) -> PairsBacktestJobModel:
    """Request cancellation for an async pairs backtest job."""
    try:
        return get_service(request, "pairs_backtest_job_service").cancel_job(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/backtests/jobs/{job_id}/resume", response_model=PairsBacktestJobModel)
async def resume_pairs_backtest_job(job_id: str, request: Request) -> PairsBacktestJobModel:
    """Resume a failed or cancelled async pairs backtest job."""
    try:
        return get_service(request, "pairs_backtest_job_service").resume_job(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/backtests/jobs/{job_id}/response", response_model=PairsBacktestResultsModel)
async def get_pairs_backtest_job_response(
    job_id: str,
    request: Request,
) -> PairsBacktestResultsModel:
    """Return the completed pairs result linked to one async job."""
    try:
        return get_service(request, "pairs_backtest_job_service").get_job_response(job_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/pairs/backtests/batch", response_model=PairsBacktestResultsModel)
async def run_pairs_backtest_batch(
    payload: PairsBatchRequestModel,
    request: Request,
) -> PairsBacktestResultsModel:
    """Execute and persist a multi-scenario B3 pairs-trading batch."""
    try:
        return get_service(request, "pairs_trading_service").run_batch(**payload.model_dump())
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/backtests", response_model=list[PairsBacktestManifestModel])
async def list_pairs_backtests(request: Request) -> list[PairsBacktestManifestModel]:
    """List persisted B3 pairs-trading backtests."""
    try:
        return get_service(request, "pairs_trading_service").list_backtests()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/backtests/{backtest_id}", response_model=PairsBacktestManifestModel)
async def get_pairs_backtest_manifest(
    backtest_id: str,
    request: Request,
) -> PairsBacktestManifestModel:
    """Return one persisted pairs-trading manifest."""
    try:
        return get_service(request, "pairs_trading_service").get_manifest(backtest_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/pairs/backtests/{backtest_id}/results", response_model=PairsBacktestResultsModel)
async def get_pairs_backtest_results(
    backtest_id: str,
    request: Request,
) -> PairsBacktestResultsModel:
    """Return one persisted pairs-trading result set."""
    try:
        return get_service(request, "pairs_trading_service").get_results(backtest_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc
