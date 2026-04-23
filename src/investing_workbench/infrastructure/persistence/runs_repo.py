"""Persistence for run artifacts and manifests."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from src.api.models import BacktestResponse
from src.investing_workbench.domain.runs import RunManifest


@dataclass(slots=True)
class PersistedRunArtifacts:
    """Paths generated for a persisted run."""

    artifact_dir: Path
    manifest_path: Path
    response_path: Path
    config_snapshot_path: Path
    data_profile_path: Path
    report_path: Path


class LocalRunsRepository:
    """Store run manifests and serialized responses on local disk."""

    def __init__(self, base_dir: Path | str = "runs") -> None:
        self.base_dir = Path(base_dir)

    def persist_run(
        self,
        *,
        manifest: RunManifest,
        response: BacktestResponse,
        config_snapshot: dict[str, Any],
        data_profile: dict[str, Any],
        report_html: str,
    ) -> PersistedRunArtifacts:
        """Persist manifest and response data for a run."""
        artifact_dir = self.base_dir / manifest.run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = artifact_dir / "manifest.json"
        response_path = artifact_dir / "response.json"
        config_snapshot_path = artifact_dir / "config_resolved.json"
        data_profile_path = artifact_dir / "data_profile.json"
        report_path = artifact_dir / "report.html"

        manifest_path.write_text(
            json.dumps(manifest.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        response_path.write_text(
            json.dumps(response.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        config_snapshot_path.write_text(
            json.dumps(config_snapshot, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        data_profile_path.write_text(
            json.dumps(data_profile, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        report_path.write_text(report_html, encoding="utf-8")

        return PersistedRunArtifacts(
            artifact_dir=artifact_dir,
            manifest_path=manifest_path,
            response_path=response_path,
            config_snapshot_path=config_snapshot_path,
            data_profile_path=data_profile_path,
            report_path=report_path,
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

    def get_config_snapshot(self, run_id: str) -> dict[str, object]:
        """Load the resolved config snapshot for a persisted run."""
        config_snapshot_path = self.base_dir / run_id / "config_resolved.json"
        if not config_snapshot_path.exists():
            raise FileNotFoundError(f"Run config snapshot not found: {run_id}")
        return json.loads(config_snapshot_path.read_text(encoding="utf-8"))

    def get_data_profile(self, run_id: str) -> dict[str, object]:
        """Load the dataset profile for a persisted run."""
        data_profile_path = self.base_dir / run_id / "data_profile.json"
        if not data_profile_path.exists():
            raise FileNotFoundError(f"Run data profile not found: {run_id}")
        return json.loads(data_profile_path.read_text(encoding="utf-8"))

    def list_runs(self) -> list[dict[str, object]]:
        """List persisted runs ordered from newest to oldest."""
        if not self.base_dir.exists():
            return []

        manifests: list[dict[str, object]] = []
        for manifest_path in sorted(self.base_dir.glob("*/manifest.json"), reverse=True):
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))

        manifests.sort(key=lambda manifest: str(manifest.get("created_at", "")), reverse=True)
        return manifests

    def get_html_report(self, run_id: str) -> str:
        """Load the persisted HTML report for a run."""
        report_path = self.base_dir / run_id / "report.html"
        if not report_path.exists():
            raise FileNotFoundError(f"Run HTML report not found: {run_id}")
        return report_path.read_text(encoding="utf-8")

    def find_latest_run_id_for_strategy(self, strategy_name: str) -> str:
        """Find the newest persisted run containing a given strategy."""
        for manifest in self.list_runs():
            strategy_names = cast(list[str], manifest.get("strategy_names", []))
            if strategy_name in strategy_names:
                run_id = cast(str | None, manifest.get("run_id"))
                if run_id:
                    return run_id
        raise FileNotFoundError(f"No persisted run found for strategy '{strategy_name}'")

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
