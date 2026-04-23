"""DTOs for normalized experiment registry records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ExperimentLineage:
    """Relationships connecting an experiment to upstream entities."""

    source_run_id: str | None = None
    best_run_id: str | None = None
    parent_optimization_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize lineage without empty values."""
        return {key: value for key, value in asdict(self).items() if value not in (None, "", [])}


@dataclass(slots=True)
class ExperimentRecord:
    """Normalized summary for any persisted research artifact."""

    experiment_id: str
    experiment_type: str
    created_at: str
    config_path: str | None
    strategy_names: list[str]
    artifact_dir: str
    status: str = "completed"
    lineage: ExperimentLineage = field(default_factory=ExperimentLineage)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize the registry record as a JSON-friendly dictionary."""
        payload = asdict(self)
        payload["lineage"] = self.lineage.to_dict()
        return payload


@dataclass(slots=True)
class ExperimentRelation:
    """A related experiment and the reason it is linked."""

    relationship: str
    record: ExperimentRecord

    def to_dict(self) -> dict[str, object]:
        """Serialize the relation payload as a JSON-friendly dictionary."""
        return {
            "relationship": self.relationship,
            "record": self.record.to_dict(),
        }


@dataclass(slots=True)
class ExperimentDetail:
    """Expanded detail payload for one persisted experiment."""

    record: ExperimentRecord
    manifest: dict[str, Any]
    related_experiments: list[ExperimentRelation] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize the detail payload as a JSON-friendly dictionary."""
        return {
            "record": self.record.to_dict(),
            "manifest": self.manifest,
            "related_experiments": [relation.to_dict() for relation in self.related_experiments],
        }
