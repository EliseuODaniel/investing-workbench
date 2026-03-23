"""Execution-related domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum


class OrderSide(StrEnum):
    """Order direction."""

    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    """Basic order type taxonomy for the new core."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


@dataclass(slots=True)
class OrderRequest:
    """Request emitted by a strategy or risk model before execution."""

    order_id: str
    asset: str
    side: OrderSide
    quantity: float
    submitted_at: datetime
    order_type: OrderType = OrderType.MARKET
    requested_price: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize the request as a JSON-friendly dictionary."""
        payload = asdict(self)
        payload["side"] = self.side.value
        payload["order_type"] = self.order_type.value
        payload["submitted_at"] = self.submitted_at.isoformat()
        return payload


@dataclass(slots=True)
class OrderFill:
    """Execution result of an order."""

    order_id: str
    asset: str
    side: OrderSide
    quantity: float
    fill_price: float
    filled_at: datetime
    fees: float = 0.0
    slippage: float = 0.0

    @property
    def gross_value(self) -> float:
        """Absolute notional value before fees."""
        return self.quantity * self.fill_price

    @property
    def net_cash_flow(self) -> float:
        """Cash impact including fees."""
        direction = -1.0 if self.side == OrderSide.BUY else 1.0
        return (self.gross_value * direction) - self.fees

    def to_dict(self) -> dict[str, object]:
        """Serialize the fill as a JSON-friendly dictionary."""
        payload = asdict(self)
        payload["side"] = self.side.value
        payload["filled_at"] = self.filled_at.isoformat()
        payload["gross_value"] = self.gross_value
        payload["net_cash_flow"] = self.net_cash_flow
        return payload
