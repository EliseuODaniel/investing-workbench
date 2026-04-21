"""Save and retrieve allocation planning workspaces."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from secrets import token_hex
from typing import Any

from src.bitcoin_martingale.application.allocations import AllocationPlanningService
from src.bitcoin_martingale.domain.allocations import RebalancePlanRequest
from src.bitcoin_martingale.infrastructure.persistence import LocalAllocationWorkspacesRepository


class AllocationWorkspaceService:
    """Persist portfolio allocation requests together with rebalance plans."""

    def __init__(
        self,
        repository: LocalAllocationWorkspacesRepository | None = None,
        allocation_service: AllocationPlanningService | None = None,
    ) -> None:
        self.repository = repository or LocalAllocationWorkspacesRepository()
        self.allocation_service = allocation_service or AllocationPlanningService()

    def list_workspaces(self) -> list[dict[str, Any]]:
        """List saved allocation workspaces."""
        return self.repository.list_workspaces()

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        """Return one saved allocation workspace."""
        return self.repository.get_workspace(workspace_id)

    def update_workspace(
        self,
        workspace_id: str,
        *,
        name: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update editable metadata for one saved allocation workspace."""
        payload = self.repository.get_workspace(workspace_id)
        if name is not None:
            payload["name"] = name
        if notes is not None:
            payload["notes"] = notes
        return self.repository.persist_workspace(payload)

    def delete_workspace(self, workspace_id: str) -> None:
        """Delete one saved allocation workspace."""
        self.repository.delete_workspace(workspace_id)

    def import_workspace(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Import a previously exported allocation workspace as a new saved workspace."""
        return self.save_workspace(
            request_payload=dict(payload.get("request", {})),
            name=self._optional_str(payload.get("name")),
            notes=self._optional_str(payload.get("notes")),
        )

    def save_workspace(
        self,
        *,
        request_payload: dict[str, Any],
        name: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Persist a rebalance planning request together with its computed plan."""
        request = RebalancePlanRequest.from_dict(request_payload)
        plan = self.allocation_service.build_plan(request)
        created_at = datetime.now(UTC).isoformat()
        workspace_id = (
            f"allocation_ws_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{token_hex(4)}"
        )
        normalized_request = request.to_dict()
        plan_payload = plan.to_dict()
        payload = {
            "workspace_id": workspace_id,
            "created_at": created_at,
            "name": name or f"Allocation plan · {workspace_id[-8:]}",
            "notes": notes,
            "request": normalized_request,
            "plan": plan_payload,
            "summary": self._build_summary(normalized_request, plan_payload),
        }
        return self.repository.persist_workspace(payload)

    def _build_summary(
        self,
        request_payload: dict[str, Any],
        plan_payload: dict[str, Any],
    ) -> dict[str, Any]:
        actions = list(plan_payload.get("actions", []))
        counts = Counter(str(action.get("action", "hold")) for action in actions)
        assets = sorted({str(action.get("asset", "")) for action in actions if action.get("asset")})
        return {
            "asset_count": len(assets),
            "assets": assets,
            "buy_count": counts.get("buy", 0),
            "sell_count": counts.get("sell", 0),
            "hold_count": counts.get("hold", 0),
            "needs_rebalance": bool(plan_payload.get("needs_rebalance", False)),
            "turnover_ratio": float(plan_payload.get("turnover_ratio", 0.0)),
            "turnover_notional": float(plan_payload.get("turnover_notional", 0.0)),
            "total_equity": float(plan_payload.get("total_equity", 0.0)),
            "current_cash_weight": float(plan_payload.get("current_cash_weight", 0.0)),
            "target_cash_weight": float(plan_payload.get("target_cash_weight", 0.0)),
            "projected_cash": float(plan_payload.get("projected_cash", 0.0)),
            "reserve_cash": float(request_payload.get("reserve_cash", 0.0)),
            "max_abs_drift_weight": float(plan_payload.get("max_abs_drift_weight", 0.0)),
        }

    def _optional_str(self, value: object) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
