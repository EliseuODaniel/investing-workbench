"""Persistence for versioned index-universe snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalIndexUniverseRepository:
    """Store cached index-universe snapshots on local disk."""

    def __init__(self, base_dir: Path | str = "data/index_universes") -> None:
        self.base_dir = Path(base_dir)

    def persist_snapshot(
        self,
        *,
        index_id: str,
        as_of_date: str,
        snapshot: dict[str, Any],
    ) -> Path:
        """Persist one resolved snapshot keyed by index and as-of date."""
        path = self._snapshot_path(index_id=index_id, as_of_date=as_of_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def get_snapshot(
        self,
        *,
        index_id: str,
        as_of_date: str,
    ) -> dict[str, Any]:
        """Load one cached snapshot or raise when it is unavailable."""
        path = self._snapshot_path(index_id=index_id, as_of_date=as_of_date)
        if not path.exists():
            raise FileNotFoundError(
                f"Index-universe snapshot not found for {index_id} at {as_of_date}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def find_snapshot(
        self,
        *,
        index_id: str,
        as_of_date: str,
    ) -> dict[str, Any] | None:
        """Load one cached snapshot when present."""
        path = self._snapshot_path(index_id=index_id, as_of_date=as_of_date)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_snapshots(self, *, index_id: str) -> list[dict[str, Any]]:
        """List cached snapshots from newest to oldest."""
        root = self.base_dir / index_id
        if not root.exists():
            return []

        snapshots: list[dict[str, Any]] = []
        for path in sorted(root.glob("*.json"), reverse=True):
            snapshots.append(json.loads(path.read_text(encoding="utf-8")))
        snapshots.sort(key=lambda item: str(item.get("as_of_date", "")), reverse=True)
        return snapshots

    def _snapshot_path(self, *, index_id: str, as_of_date: str) -> Path:
        return self.base_dir / index_id / f"{as_of_date}.json"
