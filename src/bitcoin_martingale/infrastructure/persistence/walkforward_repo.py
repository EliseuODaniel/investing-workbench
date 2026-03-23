"""Persistence for walk-forward validation artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.bitcoin_martingale.domain.walkforward import WalkForwardExecutionResult


@dataclass(slots=True)
class PersistedWalkForwardArtifacts:
    """Paths generated for a persisted walk-forward execution."""

    artifact_dir: Path
    manifest_path: Path
    results_path: Path


class LocalWalkForwardRepository:
    """Store walk-forward manifests and results on local disk."""

    def __init__(self, base_dir: Path | str = "walkforward") -> None:
        self.base_dir = Path(base_dir)

    def persist_execution(
        self,
        execution_result: WalkForwardExecutionResult,
    ) -> PersistedWalkForwardArtifacts:
        """Persist walk-forward metadata and results."""
        artifact_dir = self.base_dir / execution_result.walkforward_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = artifact_dir / "manifest.json"
        results_path = artifact_dir / "results.json"

        manifest_path.write_text(
            json.dumps(execution_result.manifest_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        results_path.write_text(
            json.dumps(execution_result.results_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return PersistedWalkForwardArtifacts(
            artifact_dir=artifact_dir,
            manifest_path=manifest_path,
            results_path=results_path,
        )

    def list_executions(self) -> list[dict[str, Any]]:
        """List persisted walk-forward manifests ordered from newest to oldest."""
        if not self.base_dir.exists():
            return []

        manifests: list[dict[str, Any]] = []
        for manifest_path in sorted(self.base_dir.glob("*/manifest.json"), reverse=True):
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))

        manifests.sort(key=lambda manifest: str(manifest.get("created_at", "")), reverse=True)
        return manifests

    def get_manifest(self, walkforward_id: str) -> dict[str, Any]:
        """Load a persisted walk-forward manifest."""
        manifest_path = self.base_dir / walkforward_id / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Walk-forward manifest not found: {walkforward_id}")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def get_results(self, walkforward_id: str) -> dict[str, Any]:
        """Load a persisted walk-forward result set."""
        results_path = self.base_dir / walkforward_id / "results.json"
        if not results_path.exists():
            raise FileNotFoundError(f"Walk-forward results not found: {walkforward_id}")
        return json.loads(results_path.read_text(encoding="utf-8"))
