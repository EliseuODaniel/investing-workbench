"""Dependency helpers for the FastAPI interface layer."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from src.investing_workbench.interfaces.api import services as api_services


def get_service(request: Request, service_name: str) -> Any:
    """Resolve one named service from the application state container."""
    resolver = getattr(request.app.state, "get_service", None)
    if callable(resolver):
        return resolver(service_name)

    container = api_services.ensure_service_container(request.app, autostart_jobs=True)
    return getattr(container, service_name)
