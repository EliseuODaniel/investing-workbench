"""Persistence for run artifacts and manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.api.models import BacktestResponse
from src.bitcoin_martingale.domain.runs import RunManifest


@dataclass(slots=True)
class PersistedRunArtifacts:
    """Paths generated for a persisted run."""

    artifact_dir: Path
    manifest_path: Path
    response_path: Path


class LocalRunsRepository:
    """Store run manifests and serialized responses on local disk."""

    def __init__(self, base_dir: Path | str = "runs") -> None:
        self.base_dir = Path(base_dir)

    def persist_run(
        self,
        *,
        manifest: RunManifest,
        response: BacktestResponse,
    ) -> PersistedRunArtifacts:
        """Persist manifest and response data for a run."""
        artifact_dir = self.base_dir / manifest.run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = artifact_dir / "manifest.json"
        response_path = artifact_dir / "response.json"

        manifest_path.write_text(
            json.dumps(manifest.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        response_path.write_text(
            json.dumps(response.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return PersistedRunArtifacts(
            artifact_dir=artifact_dir,
            manifest_path=manifest_path,
            response_path=response_path,
        )

    def get_manifest(self, run_id: str) -> dict[str, object]:
        """Load a persisted manifest by run id."""
        manifest_path = self.base_dir / run_id / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Run manifest not found: {run_id}")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def get_response_payload(self, run_id: str) -> dict[str, object]:
        """Load a persisted response payload by run id."""
        response_path = self.base_dir / run_id / "response.json"
        if not response_path.exists():
            raise FileNotFoundError(f"Run response not found: {run_id}")
        return json.loads(response_path.read_text(encoding="utf-8"))
