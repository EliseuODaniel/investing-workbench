"""Run metadata domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RunManifest:
    """Metadata that makes a run reproducible and inspectable."""

    run_id: str
    created_at: datetime
    config_path: str
    artifact_dir: str
    strategy_names: list[str]
    benchmark_names: list[str]
    request_payload: dict[str, object]
    data_info: dict[str, object]
    config_snapshot_path: str
    data_profile_path: str
    data_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the manifest as a JSON-friendly dictionary."""
        return {
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "config_path": self.config_path,
            "artifact_dir": self.artifact_dir,
            "strategy_names": self.strategy_names,
            "benchmark_names": self.benchmark_names,
            "request_payload": self.request_payload,
            "data_info": self.data_info,
            "config_snapshot_path": self.config_snapshot_path,
            "data_profile_path": self.data_profile_path,
            "data_fingerprint": self.data_fingerprint,
        }
