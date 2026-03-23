"""Domain models for dataset cataloging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DatasetValidationSummary:
    """Structured validation details for a dataset."""

    datetime_index_detected: bool
    duplicate_index_count: int
    missing_value_count: int
    date_gap_count: int
    missing_required_columns: list[str] = field(default_factory=list)
    price_anomaly_count: int = 0
    supported_refresh: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize validation details."""
        return {
            "datetime_index_detected": self.datetime_index_detected,
            "duplicate_index_count": self.duplicate_index_count,
            "missing_value_count": self.missing_value_count,
            "date_gap_count": self.date_gap_count,
            "missing_required_columns": self.missing_required_columns,
            "price_anomaly_count": self.price_anomaly_count,
            "supported_refresh": self.supported_refresh,
        }


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
    validation: DatasetValidationSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the detail payload."""
        return {
            **DatasetSummary.to_dict(self),
            "preview_rows": self.preview_rows,
            "validation_warnings": self.validation_warnings,
            "validation": self.validation.to_dict() if self.validation else None,
        }
