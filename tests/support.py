"""Shared helpers for API integration tests."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from typing import Iterator

from src.api.main import app
from src.bitcoin_martingale.interfaces.api import services as api_services


@contextmanager
def override_api_services(**overrides: object) -> Iterator[None]:
    """Temporarily replace selected services in the FastAPI service container."""
    created_container = False
    original_container = getattr(app.state, "service_container", None)
    if original_container is None:
        original_container = api_services.install_service_container(
            app,
            api_services.build_api_services(autostart_jobs=False),
        )
        created_container = True

    app.state.service_container = replace(original_container, **overrides)
    try:
        yield
    finally:
        app.state.service_container = original_container
        if created_container:
            api_services.shutdown_api_services(original_container, cancel_running=True)
            delattr(app.state, "service_container")
            if hasattr(app.state, "get_service"):
                delattr(app.state, "get_service")
