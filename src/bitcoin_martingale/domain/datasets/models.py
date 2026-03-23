"""Domain models for dataset cataloging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DatasetSummary:
    """Lightweight dataset catalog entry."""

    dataset_id: str
    name: str
    path: str
    format: str
    category: str
    row_count: int
    start_timestamp: str | None
    end_timestamp: str | None
    columns: list[str]
    file_size_bytes: int
    last_modified: str
    data_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the summary."""
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "path": self.path,
            "format": self.format,
            "category": self.category,
            "row_count": self.row_count,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "columns": self.columns,
            "file_size_bytes": self.file_size_bytes,
            "last_modified": self.last_modified,
            "data_fingerprint": self.data_fingerprint,
        }


@dataclass(slots=True)
class DatasetDetail(DatasetSummary):
    """Detailed dataset inspection payload."""

    preview_rows: list[dict[str, Any]] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the detail payload."""
        return {
            **DatasetSummary.to_dict(self),
            "preview_rows": self.preview_rows,
            "validation_warnings": self.validation_warnings,
        }
