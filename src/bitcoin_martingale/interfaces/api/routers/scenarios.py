"""Dedicated scenario API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models import Wege3RegraARunRequestModel, Wege3RegraAScenarioResponseModel
from src.bitcoin_martingale.interfaces.api.deps import get_service
from src.bitcoin_martingale.interfaces.api.errors import to_http_exception

router = APIRouter(tags=["scenarios"])


@router.post("/scenarios/wege3-regra-a", response_model=Wege3RegraAScenarioResponseModel)
async def run_wege3_regra_a(
    payload: Wege3RegraARunRequestModel,
    request: Request,
) -> Wege3RegraAScenarioResponseModel:
    """Run the dedicated WEGE3 Regra A scenario through the existing app engine."""
    try:
        return get_service(request, "wege3_regra_a_service").run(
            start_date=payload.start_date,
            end_date=payload.end_date,
            force_download=payload.force_download,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc
