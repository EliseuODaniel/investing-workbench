"""Investment comparison API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models import (
    InvestmentCatalogResponseModel,
    InvestmentCompareRequestModel,
    InvestmentCompareResponseModel,
)
from src.bitcoin_martingale.interfaces.api.deps import get_service
from src.bitcoin_martingale.interfaces.api.errors import to_http_exception

router = APIRouter(tags=["investments"])


@router.get("/investments/catalog", response_model=InvestmentCatalogResponseModel)
async def get_investment_catalog(request: Request) -> InvestmentCatalogResponseModel:
    """Return the curated B3 investment catalog used by the didactic comparison flow."""
    try:
        return get_service(request, "investment_comparison_service").list_catalog()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/investments/compare", response_model=InvestmentCompareResponseModel)
async def compare_investments(
    payload: InvestmentCompareRequestModel,
    request: Request,
) -> InvestmentCompareResponseModel:
    """Compare the same cash-flow schedule across selected B3 investment alternatives."""
    try:
        return get_service(request, "investment_comparison_service").compare(
            asset_ids=payload.asset_ids,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_capital=payload.initial_capital,
            monthly_contribution=payload.monthly_contribution,
            benchmark_ids=payload.benchmark_ids,
            force_download=payload.force_download,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc
