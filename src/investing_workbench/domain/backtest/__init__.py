"""Backtest domain exports with lazy engine loading."""

from __future__ import annotations

from typing import Any

from .models import Layer, State, Trade

__all__ = ["BacktestCoreEngine", "Layer", "State", "Trade"]


def __getattr__(name: str) -> Any:
    """Resolve heavier exports lazily to avoid domain import cycles."""
    if name == "BacktestCoreEngine":
        from .engine import BacktestCoreEngine

        return BacktestCoreEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
