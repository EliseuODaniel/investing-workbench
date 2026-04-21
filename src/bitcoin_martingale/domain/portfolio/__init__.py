"""Portfolio domain exports with lazy ledger loading."""

from __future__ import annotations

from typing import Any

from .models import PortfolioSnapshot, Position

__all__ = ["PortfolioLedger", "PortfolioSnapshot", "Position"]


def __getattr__(name: str) -> Any:
    """Resolve ledger exports lazily to avoid domain import cycles."""
    if name == "PortfolioLedger":
        from .ledger import PortfolioLedger

        return PortfolioLedger
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
