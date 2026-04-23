"""Persistence for curated pairs-trading backtest artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PersistedPairsArtifacts:
    """Paths generated for one persisted pairs-trading execution."""

    artifact_dir: Path
    manifest_path: Path
    results_path: Path


class LocalPairsBacktestsRepository:
    """Store pairs-trading manifests and detailed results on local disk."""

    def __init__(self, base_dir: Path | str = "pairs_backtests") -> None:
        self.base_dir = Path(base_dir)

    def persist_execution(
        self,
        *,
        backtest_id: str,
        manifest: dict[str, Any],
        results: dict[str, Any],
    ) -> PersistedPairsArtifacts:
        """Persist pairs backtest metadata and detailed results."""
        artifact_dir = self.base_dir / backtest_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = artifact_dir / "manifest.json"
        results_path = artifact_dir / "results.json"

        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        results_path.write_text(
            json.dumps(results, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return PersistedPairsArtifacts(
            artifact_dir=artifact_dir,
            manifest_path=manifest_path,
            results_path=results_path,
        )

    def list_backtests(self) -> list[dict[str, Any]]:
        """List persisted pairs-trading manifests from newest to oldest."""
        if not self.base_dir.exists():
            return []

        manifests: list[dict[str, Any]] = []
        for manifest_path in sorted(self.base_dir.glob("*/manifest.json"), reverse=True):
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))

        manifests.sort(key=lambda manifest: str(manifest.get("created_at", "")), reverse=True)
        return manifests

    def get_manifest(self, backtest_id: str) -> dict[str, Any]:
        """Load one persisted pairs-trading manifest."""
        manifest_path = self.base_dir / backtest_id / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Pairs backtest manifest not found: {backtest_id}")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def get_results(self, backtest_id: str) -> dict[str, Any]:
        """Load one persisted pairs-trading result set."""
        results_path = self.base_dir / backtest_id / "results.json"
        if not results_path.exists():
            raise FileNotFoundError(f"Pairs backtest results not found: {backtest_id}")
        return json.loads(results_path.read_text(encoding="utf-8"))
