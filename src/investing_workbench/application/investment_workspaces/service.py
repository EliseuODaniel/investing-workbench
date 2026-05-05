"""Save and retrieve reusable investment research artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from secrets import token_hex
from typing import Any

from src.investing_workbench.application.investment_workspaces.setup_scoring import (
    build_strategy_setup_scores,
)
from src.investing_workbench.infrastructure.persistence import (
    LocalInvestmentWorkspacesRepository,
)


class InvestmentWorkspaceService:
    """Persist saved custom portfolios and radar entries."""

    PORTFOLIO_TYPE = "portfolios"
    PAIRS_RADAR_TYPE = "pairs_radar"
    STRATEGY_RADAR_TYPE = "strategy_radar"
    STRATEGY_SETUP_RUN_TYPE = "strategy_setup_runs"

    def __init__(
        self,
        repository: LocalInvestmentWorkspacesRepository | None = None,
    ) -> None:
        self.repository = repository or LocalInvestmentWorkspacesRepository()

    def list_portfolios(self) -> list[dict[str, Any]]:
        """List saved investment portfolios."""
        return self.repository.list_items(self.PORTFOLIO_TYPE)

    def save_portfolio(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one reusable custom portfolio."""
        components = [
            {
                "component_id": str(component["component_id"]),
                "weight": float(component["weight"]),
            }
            for component in payload.get("components", [])
            if float(component.get("weight", 0.0) or 0.0) > 0
        ]
        if len(components) < 2:
            raise ValueError("A carteira salva precisa ter pelo menos dois ativos com peso.")

        now = datetime.now(UTC).isoformat()
        label = str(payload.get("label") or "Minha carteira").strip() or "Minha carteira"
        portfolio_id = str(payload.get("portfolio_id") or self._build_id("portfolio"))
        stored = {
            "portfolio_id": portfolio_id,
            "label": label,
            "description": self._optional_str(payload.get("description")),
            "rebalance_frequency": str(payload.get("rebalance_frequency") or "monthly"),
            "components": components,
            "created_at": str(payload.get("created_at") or now),
            "updated_at": now,
        }
        return self.repository.persist_item(self.PORTFOLIO_TYPE, portfolio_id, stored)

    def delete_portfolio(self, portfolio_id: str) -> None:
        """Delete one saved investment portfolio."""
        self.repository.delete_item(self.PORTFOLIO_TYPE, portfolio_id)

    def list_pairs_radar(self) -> list[dict[str, Any]]:
        """List saved pairs radar entries."""
        return self.repository.list_items(self.PAIRS_RADAR_TYPE)

    def save_pairs_radar_item(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one pairs radar favorite."""
        pairs_backtest_id = str(payload.get("pairs_backtest_id") or "").strip()
        if not pairs_backtest_id:
            raise ValueError("pairs_backtest_id e obrigatorio para salvar no radar.")
        now = datetime.now(UTC).isoformat()
        stored = {
            "pairs_backtest_id": pairs_backtest_id,
            "label": str(payload.get("label") or pairs_backtest_id),
            "preset_label": str(payload.get("preset_label") or "Pairs"),
            "created_at": str(payload.get("created_at") or now),
            "saved_at": now,
            "scenario_count": int(payload.get("scenario_count") or 0),
            "candidate_pair_count": int(payload.get("candidate_pair_count") or 0),
            "benchmark_ids": [str(item) for item in payload.get("benchmark_ids", [])],
        }
        return self.repository.persist_item(
            self.PAIRS_RADAR_TYPE,
            pairs_backtest_id,
            stored,
        )

    def delete_pairs_radar_item(self, pairs_backtest_id: str) -> None:
        """Delete one pairs radar favorite."""
        self.repository.delete_item(self.PAIRS_RADAR_TYPE, pairs_backtest_id)

    def list_strategy_radar(self) -> list[dict[str, Any]]:
        """List saved strategy radar favorites."""
        return self.repository.list_items(self.STRATEGY_RADAR_TYPE)

    def save_strategy_radar_item(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one strategy radar favorite."""
        strategy_id = str(payload.get("strategy_id") or "").strip()
        if not strategy_id:
            raise ValueError("strategy_id e obrigatorio para salvar no radar.")
        now = datetime.now(UTC).isoformat()
        stored = {
            "strategy_id": strategy_id,
            "label": str(payload.get("label") or strategy_id),
            "family": str(payload.get("family") or "strategy"),
            "direction": str(payload.get("direction") or "long"),
            "parameter_values": self._clean_mapping(payload.get("parameter_values")),
            "universe": [str(item) for item in payload.get("universe", []) if str(item)],
            "timeframe": self._optional_str(payload.get("timeframe")),
            "setup_notes": [
                str(item) for item in payload.get("setup_notes", []) if str(item).strip()
            ],
            "saved_at": now,
        }
        return self.repository.persist_item(
            self.STRATEGY_RADAR_TYPE,
            strategy_id,
            stored,
        )

    def delete_strategy_radar_item(self, strategy_id: str) -> None:
        """Delete one strategy radar favorite."""
        self.repository.delete_item(self.STRATEGY_RADAR_TYPE, strategy_id)

    def list_strategy_setup_runs(self) -> list[dict[str, Any]]:
        """List persisted strategy setup run summaries."""
        return self.repository.list_items(self.STRATEGY_SETUP_RUN_TYPE)

    def save_strategy_setup_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one strategy setup execution summary."""
        strategy_id = str(payload.get("strategy_id") or "").strip()
        if not strategy_id:
            raise ValueError("strategy_id e obrigatorio para salvar execucao do setup.")
        now = datetime.now(UTC).isoformat()
        ran_at = str(payload.get("ran_at") or now)
        run_id = self._optional_str(payload.get("run_id"))
        pairs_backtest_id = self._optional_str(payload.get("pairs_backtest_id"))
        item_id = self._build_setup_run_id(
            strategy_id,
            run_id or pairs_backtest_id,
            ran_at,
        )
        stored = {
            "strategy_id": strategy_id,
            "run_id": run_id,
            "pairs_backtest_id": pairs_backtest_id,
            "ran_at": ran_at,
            "strategy_count": int(payload.get("strategy_count") or 0),
            "best_strategy": self._optional_str(payload.get("best_strategy")),
            "total_return": self._optional_float(payload.get("total_return")),
            "max_drawdown": self._optional_float(payload.get("max_drawdown")),
            "trade_count": self._optional_int(payload.get("trade_count")),
            "route_hint": str(payload.get("route_hint") or "/backtest"),
            "saved_at": now,
        }
        return self.repository.persist_item(self.STRATEGY_SETUP_RUN_TYPE, item_id, stored)

    def list_strategy_setup_scores(self) -> list[dict[str, Any]]:
        """Rank setup executions with a first explainable score."""
        return build_strategy_setup_scores(
            setup_runs=self.list_strategy_setup_runs(),
            strategy_radar_items=self.list_strategy_radar(),
        )

    def _build_id(self, prefix: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"investment_{prefix}_{timestamp}_{token_hex(4)}"

    def _optional_str(self, value: object) -> str | None:
        if value in (None, ""):
            return None
        return str(value)

    def _clean_mapping(self, value: object) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        return {
            str(key): item
            for key, item in value.items()
            if isinstance(item, str | int | float | bool) or item is None
        }

    def _optional_float(self, value: object) -> float | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str | int | float):
            raise ValueError("Valor numerico invalido para resumo de execucao.")
        return float(value)

    def _optional_int(self, value: object) -> int | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str | int | float):
            raise ValueError("Valor inteiro invalido para resumo de execucao.")
        return int(value)

    def _build_setup_run_id(self, strategy_id: str, run_id: str | None, ran_at: str) -> str:
        safe_strategy = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in strategy_id)
        if run_id:
            safe_run = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
            return f"{safe_strategy}_{safe_run}"
        digest = token_hex(4)
        safe_time = "".join(ch if ch.isalnum() else "_" for ch in ran_at)[:32]
        return f"{safe_strategy}_{safe_time}_{digest}"
