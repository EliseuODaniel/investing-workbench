"""System and configuration API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models import ConfigInfo, SystemStatusModel
from src.investing_workbench.interfaces.api.deps import get_service
from src.investing_workbench.interfaces.api.errors import to_http_exception

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Investing Workbench API", "version": "1.0.0"}


@router.get("/configs", response_model=list[ConfigInfo])
async def get_configs(request: Request) -> list[ConfigInfo]:
    """List available configuration files."""
    try:
        return get_service(request, "run_service").list_configs()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/system/status", response_model=SystemStatusModel)
async def get_system_status(request: Request) -> SystemStatusModel:
    """Return a lightweight operational snapshot of the local platform."""
    try:
        return get_service(request, "system_status_service").get_status()
    except Exception as exc:
        raise to_http_exception(exc) from exc
