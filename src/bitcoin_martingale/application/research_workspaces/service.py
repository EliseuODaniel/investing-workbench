"""Save and retrieve research workspace selections."""

from __future__ import annotations

from datetime import UTC, datetime
from secrets import token_hex
from typing import Any

from src.bitcoin_martingale.application.experiments import ExperimentRegistryService
from src.bitcoin_martingale.application.research_workspaces.reporting import (
    build_workspace_report,
)
from src.bitcoin_martingale.infrastructure.persistence import LocalResearchWorkspacesRepository


class ResearchWorkspaceService:
    """Persist user-curated research comparison workspaces."""

    def __init__(
        self,
        repository: LocalResearchWorkspacesRepository | None = None,
        experiment_registry_service: ExperimentRegistryService | None = None,
    ) -> None:
        self.repository = repository or LocalResearchWorkspacesRepository()
        self.experiment_registry_service = (
            experiment_registry_service or ExperimentRegistryService()
        )

    def list_workspaces(self) -> list[dict[str, Any]]:
        """List saved research workspaces."""
        return self.repository.list_workspaces()

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        """Return one saved research workspace."""
        return self.repository.get_workspace(workspace_id)

    def build_report(self, workspace_id: str) -> dict[str, Any]:
        """Build a report payload for one saved research workspace."""
        workspace = self.get_workspace(workspace_id)
        return build_workspace_report(workspace)

    def update_workspace(
        self,
        workspace_id: str,
        *,
        name: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update editable metadata for one saved research workspace."""
        payload = self.repository.get_workspace(workspace_id)
        if name is not None:
            payload["name"] = name
        if notes is not None:
            payload["notes"] = notes
        return self.repository.persist_workspace(payload)

    def import_workspace(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Import a previously exported research workspace as a new saved workspace."""
        selected_experiment = payload.get("selected_experiment", {})
        selection = payload.get("selection", {})
        return self.save_workspace(
            name=self._optional_str(payload.get("name")),
            notes=self._optional_str(payload.get("notes")),
            selected_experiment_type=str(selected_experiment["experiment_type"]),
            selected_experiment_id=str(selected_experiment["experiment_id"]),
            optimization_id=self._optional_str(selection.get("optimization_id")),
            walkforward_id=self._optional_str(selection.get("walkforward_id")),
            montecarlo_id=self._optional_str(selection.get("montecarlo_id")),
            anchor_run_id=self._optional_str(selection.get("anchor_run_id")),
        )

    def save_workspace(
        self,
        *,
        selected_experiment_type: str,
        selected_experiment_id: str,
        name: str | None = None,
        notes: str | None = None,
        optimization_id: str | None = None,
        walkforward_id: str | None = None,
        montecarlo_id: str | None = None,
        anchor_run_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist a curated research workspace selection."""
        indexed_records = self._index_records()
        selected_record = self._require_record(
            indexed_records,
            selected_experiment_type,
            selected_experiment_id,
        )
        optimization_record = self._optional_record(
            indexed_records,
            "optimization",
            optimization_id,
        )
        walkforward_record = self._optional_record(indexed_records, "walkforward", walkforward_id)
        montecarlo_record = self._optional_record(indexed_records, "montecarlo", montecarlo_id)
        anchor_run_record = self._optional_record(indexed_records, "run", anchor_run_id)

        workspace_id = (
            f"research_ws_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{token_hex(4)}"
        )
        created_at = datetime.now(UTC).isoformat()
        workspace_name = name or f"{selected_experiment_type} · {selected_experiment_id}"

        payload = {
            "workspace_id": workspace_id,
            "created_at": created_at,
            "name": workspace_name,
            "notes": notes,
            "selected_experiment": {
                "experiment_type": selected_experiment_type,
                "experiment_id": selected_experiment_id,
            },
            "selection": {
                "optimization_id": optimization_id,
                "walkforward_id": walkforward_id,
                "montecarlo_id": montecarlo_id,
                "anchor_run_id": anchor_run_id,
            },
            "records": {
                "selected": selected_record,
                "optimization": optimization_record,
                "walkforward": walkforward_record,
                "montecarlo": montecarlo_record,
                "anchor_run": anchor_run_record,
            },
        }
        return self.repository.persist_workspace(payload)

    def _index_records(self) -> dict[tuple[str, str], dict[str, Any]]:
        records = self.experiment_registry_service.list_experiments()
        return {
            (str(record["experiment_type"]), str(record["experiment_id"])): record
            for record in records
        }

    def _require_record(
        self,
        indexed_records: dict[tuple[str, str], dict[str, Any]],
        experiment_type: str,
        experiment_id: str,
    ) -> dict[str, Any]:
        record = indexed_records.get((experiment_type, experiment_id))
        if record is None:
            raise FileNotFoundError(
                f"Experiment not found for workspace save: {experiment_type}/{experiment_id}"
            )
        return record

    def _optional_record(
        self,
        indexed_records: dict[tuple[str, str], dict[str, Any]],
        experiment_type: str,
        experiment_id: str | None,
    ) -> dict[str, Any] | None:
        if not experiment_id:
            return None
        return self._require_record(indexed_records, experiment_type, experiment_id)

    def _optional_str(self, value: object) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
