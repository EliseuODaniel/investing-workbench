"""Dataset API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models import (
    DatasetDetailModel,
    DatasetImportRequest,
    DatasetRefreshDueRequest,
    DatasetRefreshPolicyRequest,
    DatasetRefreshRequest,
    DatasetSummaryModel,
)
from src.bitcoin_martingale.interfaces.api.deps import get_service
from src.bitcoin_martingale.interfaces.api.errors import to_http_exception

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetSummaryModel])
async def list_datasets(request: Request) -> list[DatasetSummaryModel]:
    """List discovered local datasets."""
    try:
        return get_service(request, "dataset_service").list_datasets()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/refresh-due", response_model=list[DatasetSummaryModel])
async def list_due_datasets(request: Request) -> list[DatasetSummaryModel]:
    """List datasets whose persisted refresh policy is currently due."""
    try:
        return get_service(request, "dataset_service").list_due_datasets()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/refresh-due", response_model=list[DatasetDetailModel])
async def refresh_due_datasets(
    payload: DatasetRefreshDueRequest, request: Request
) -> list[DatasetDetailModel]:
    """Refresh datasets that are currently due according to their policy."""
    try:
        return get_service(request, "dataset_service").refresh_due_datasets(limit=payload.limit)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/{dataset_id}", response_model=DatasetDetailModel)
async def get_dataset(dataset_id: str, request: Request) -> DatasetDetailModel:
    """Inspect a discovered local dataset."""
    try:
        return get_service(request, "dataset_service").get_dataset(dataset_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/import", response_model=DatasetDetailModel)
async def import_dataset(payload: DatasetImportRequest, request: Request) -> DatasetDetailModel:
    """Import a local CSV or Parquet file into the managed dataset catalog."""
    try:
        return get_service(request, "dataset_service").import_dataset(
            source_path=payload.source_path,
            dataset_name=payload.dataset_name,
            overwrite=payload.overwrite,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/{dataset_id}/refresh-policy", response_model=DatasetDetailModel)
async def set_dataset_refresh_policy(
    dataset_id: str, payload: DatasetRefreshPolicyRequest, request: Request
) -> DatasetDetailModel:
    """Persist a dataset refresh policy."""
    try:
        return get_service(request, "dataset_service").set_refresh_policy(
            dataset_id,
            enabled=payload.enabled,
            interval_days=payload.interval_days,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/{dataset_id}/refresh", response_model=DatasetDetailModel)
async def refresh_dataset(
    dataset_id: str, payload: DatasetRefreshRequest, request: Request
) -> DatasetDetailModel:
    """Refresh a supported cached dataset in place."""
    try:
        return get_service(request, "dataset_service").refresh_dataset(
            dataset_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc
