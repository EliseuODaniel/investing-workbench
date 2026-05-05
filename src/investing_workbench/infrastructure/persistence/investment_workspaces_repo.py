"""Persistence for saved investment workspace artifacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class LocalInvestmentWorkspacesRepository:
    """Store saved investment portfolios and radar entries on local disk."""

    def __init__(self, base_dir: Path | str = "investment_workspaces") -> None:
        self.base_dir = Path(base_dir)

    def persist_item(self, item_type: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one investment workspace item."""
        item_dir = self.base_dir / item_type / item_id
        item_dir.mkdir(parents=True, exist_ok=True)
        (item_dir / "manifest.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return payload

    def list_items(self, item_type: str) -> list[dict[str, Any]]:
        """List saved items from newest to oldest."""
        item_root = self.base_dir / item_type
        if not item_root.exists():
            return []
        manifests = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(item_root.glob("*/manifest.json"), reverse=True)
        ]
        manifests.sort(
            key=lambda item: str(item.get("updated_at") or item.get("saved_at") or ""),
            reverse=True,
        )
        return manifests

    def delete_item(self, item_type: str, item_id: str) -> None:
        """Delete one saved item."""
        item_dir = self.base_dir / item_type / item_id
        manifest_path = item_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Investment workspace item not found: {item_id}")
        shutil.rmtree(item_dir, ignore_errors=True)
