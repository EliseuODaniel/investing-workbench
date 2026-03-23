"""FastAPI backend for Bitcoin Martingale backtesting UI."""

from typing import Any

__all__ = ["app"]


def __getattr__(name: str) -> Any:
    """Resolve the FastAPI app lazily to avoid import cycles."""
    if name == "app":
        from .main import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
