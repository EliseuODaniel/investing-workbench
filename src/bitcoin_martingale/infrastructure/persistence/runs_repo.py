"""Persistence for run artifacts and manifests."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

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

    def list_runs(self) -> list[dict[str, object]]:
        """List persisted runs ordered from newest to oldest."""
        if not self.base_dir.exists():
            return []

        manifests: list[dict[str, object]] = []
        for manifest_path in sorted(self.base_dir.glob("*/manifest.json"), reverse=True):
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))

        manifests.sort(key=lambda manifest: str(manifest.get("created_at", "")), reverse=True)
        return manifests

    def build_trades_csv(self, run_id: str, strategy_name: str) -> str:
        """Build a CSV export of trades for a strategy from a persisted response."""
        payload = self.get_response_payload(run_id)
        results = cast(dict[str, Any], payload.get("results", {}))
        if strategy_name not in results:
            raise FileNotFoundError(
                f"Strategy '{strategy_name}' not found in persisted run: {run_id}"
            )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "action", "price", "quantity", "layer", "pnl"])

        strategy_payload = cast(dict[str, Any], results[strategy_name])
        trades = cast(list[dict[str, Any]], strategy_payload.get("trades", []))

        for trade in trades:
            writer.writerow(
                [
                    trade.get("timestamp"),
                    trade.get("action"),
                    trade.get("price"),
                    trade.get("quantity"),
                    trade.get("layer"),
                    trade.get("pnl"),
                ]
            )

        return output.getvalue()
