"""Persistence for saved allocation workspace manifests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class LocalAllocationWorkspacesRepository:
    """Store saved allocation workspaces on local disk."""

    def __init__(self, base_dir: Path | str = "allocation_workspaces") -> None:
        self.base_dir = Path(base_dir)

    def persist_workspace(self, workspace_payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one allocation workspace manifest."""
        workspace_id = str(workspace_payload["workspace_id"])
        artifact_dir = self.base_dir / workspace_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = artifact_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(workspace_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return workspace_payload

    def list_workspaces(self) -> list[dict[str, Any]]:
        """List saved allocation workspaces from newest to oldest."""
        if not self.base_dir.exists():
            return []

        manifests: list[dict[str, Any]] = []
        for manifest_path in sorted(self.base_dir.glob("*/manifest.json"), reverse=True):
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))

        manifests.sort(key=lambda manifest: str(manifest.get("created_at", "")), reverse=True)
        return manifests

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        """Load one saved allocation workspace manifest."""
        manifest_path = self.base_dir / workspace_id / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Allocation workspace not found: {workspace_id}")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def delete_workspace(self, workspace_id: str) -> None:
        """Delete a saved allocation workspace manifest."""
        workspace_dir = self.base_dir / workspace_id
        manifest_path = workspace_dir / "manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Allocation workspace not found: {workspace_id}")

        shutil.rmtree(workspace_dir, ignore_errors=True)
