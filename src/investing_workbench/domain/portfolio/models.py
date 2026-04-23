"""Portfolio-related domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Position:
    """Aggregated asset position."""

    asset: str
    quantity: float
    average_entry_price: float
    cost_basis: float

    @property
    def market_value(self) -> float:
        """Market value using the average entry price as a placeholder baseline."""
        return self.quantity * self.average_entry_price

    def to_dict(self) -> dict[str, object]:
        """Serialize position data."""
        return asdict(self)


@dataclass(slots=True)
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time."""

    timestamp: datetime
    cash: float
    total_equity: float
    positions: list[Position] = field(default_factory=list)

    @property
    def invested_value(self) -> float:
        """Total value represented by current positions."""
        return sum(position.market_value for position in self.positions)

    def to_dict(self) -> dict[str, object]:
        """Serialize the snapshot as a JSON-friendly dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cash": self.cash,
            "total_equity": self.total_equity,
            "invested_value": self.invested_value,
            "positions": [position.to_dict() for position in self.positions],
        }
