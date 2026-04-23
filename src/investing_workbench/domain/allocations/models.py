"""Allocation and rebalance domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class RebalanceActionType(StrEnum):
    """Suggested rebalance trade directions."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(slots=True)
class AllocationHolding:
    """Current position used for allocation planning."""

    asset: str
    quantity: float

    def to_dict(self) -> dict[str, object]:
        """Serialize the holding as a JSON-friendly dictionary."""
        return asdict(self)


@dataclass(slots=True)
class AllocationTarget:
    """Target portfolio weight for one asset."""

    asset: str
    target_weight: float

    def to_dict(self) -> dict[str, object]:
        """Serialize the target as a JSON-friendly dictionary."""
        return asdict(self)


@dataclass(slots=True)
class RebalancePlanRequest:
    """Normalized request used by the allocation planning service."""

    cash: float
    holdings: list[AllocationHolding]
    prices: dict[str, float]
    targets: list[AllocationTarget]
    weight_tolerance: float = 0.0
    min_trade_notional: float = 0.0
    reserve_cash: float = 0.0

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RebalancePlanRequest":
        """Build a typed request from a JSON-like payload."""
        holdings = [
            AllocationHolding(
                asset=str(item["asset"]),
                quantity=float(item["quantity"]),
            )
            for item in payload.get("holdings", [])
        ]
        targets = [
            AllocationTarget(
                asset=str(item["asset"]),
                target_weight=float(item["target_weight"]),
            )
            for item in payload.get("targets", [])
        ]
        prices = {str(asset): float(price) for asset, price in payload.get("prices", {}).items()}
        return cls(
            cash=float(payload.get("cash", 0.0)),
            holdings=holdings,
            prices=prices,
            targets=targets,
            weight_tolerance=float(payload.get("weight_tolerance", 0.0)),
            min_trade_notional=float(payload.get("min_trade_notional", 0.0)),
            reserve_cash=float(payload.get("reserve_cash", 0.0)),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the request as a JSON-friendly dictionary."""
        return {
            "cash": self.cash,
            "holdings": [holding.to_dict() for holding in self.holdings],
            "prices": self.prices.copy(),
            "targets": [target.to_dict() for target in self.targets],
            "weight_tolerance": self.weight_tolerance,
            "min_trade_notional": self.min_trade_notional,
            "reserve_cash": self.reserve_cash,
        }


@dataclass(slots=True)
class RebalanceAction:
    """One asset-level rebalance recommendation."""

    asset: str
    action: RebalanceActionType
    price: float
    current_quantity: float
    current_value: float
    current_weight: float
    target_quantity: float
    target_value: float
    target_weight: float
    quantity_delta: float
    notional_delta: float
    drift_weight: float
    projected_quantity: float
    reason: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the action as a JSON-friendly dictionary."""
        payload = asdict(self)
        payload["action"] = self.action.value
        return payload


@dataclass(slots=True)
class RebalancePlan:
    """Portfolio-level rebalance recommendation."""

    total_equity: float
    current_cash: float
    target_cash: float
    projected_cash: float
    current_cash_weight: float
    target_cash_weight: float
    turnover_notional: float
    turnover_ratio: float
    cash_gap_to_target: float
    max_abs_drift_weight: float
    needs_rebalance: bool
    actions: list[RebalanceAction] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize the plan as a JSON-friendly dictionary."""
        return {
            "total_equity": self.total_equity,
            "current_cash": self.current_cash,
            "target_cash": self.target_cash,
            "projected_cash": self.projected_cash,
            "current_cash_weight": self.current_cash_weight,
            "target_cash_weight": self.target_cash_weight,
            "turnover_notional": self.turnover_notional,
            "turnover_ratio": self.turnover_ratio,
            "cash_gap_to_target": self.cash_gap_to_target,
            "max_abs_drift_weight": self.max_abs_drift_weight,
            "needs_rebalance": self.needs_rebalance,
            "actions": [action.to_dict() for action in self.actions],
            "warnings": list(self.warnings),
        }
