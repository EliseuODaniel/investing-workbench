"""DTOs for pairs-trading application workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class BorrowSnapshotRegistration:
    """Managed catalog entry created for a local borrow snapshot."""

    dataset_id: str
    managed_path: str
    source_path: str

    def to_dict(self) -> dict[str, str]:
        """Serialize a lightweight borrow snapshot registration."""
        return asdict(self)


@dataclass(slots=True)
class PairsUniverseResolution:
    """API-facing payload for a resolved pairs universe."""

    preset: dict[str, Any] | None
    requested_tickers: list[str]
    as_of_date: str | None
    resolved_as_of_date: str | None
    start_date: str
    end_date: str | None
    common_index_start: str | None
    common_index_end: str | None
    common_index_days: int
    quality_report: dict[str, Any]
    assets: list[dict[str, Any]]
    eligible_assets: list[dict[str, Any]]
    unavailable_tickers: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the universe resolution payload."""
        return asdict(self)


@dataclass(slots=True)
class PairsScreeningResult:
    """API-facing payload for the pairs screener."""

    preset: dict[str, Any] | None
    requested_tickers: list[str]
    resolved_as_of_date: str | None
    screening_window: dict[str, Any]
    criteria: dict[str, Any]
    summary: dict[str, Any]
    quality_report: dict[str, Any]
    selected_pairs: list[dict[str, Any]]
    candidate_pairs: list[dict[str, Any]]
    rejected_pairs: list[dict[str, Any]] = field(default_factory=list)
    rejection_summary: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the screening payload."""
        return asdict(self)


@dataclass(slots=True)
class PairsBacktestManifest:
    """Normalized summary for one persisted pairs execution."""

    pairs_backtest_id: str
    created_at: str
    preset_id: str
    preset_label: str
    universe_as_of_date: str | None
    start_date: str
    end_date: str | None
    requested_tickers: list[str]
    available_tickers: list[str]
    eligible_tickers: list[str]
    scenario_count: int
    batch_mode: bool
    benchmark_ids: list[str]
    candidate_pair_count: int
    reconstitution_segment_count: int
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PairsBacktestManifest":
        """Build the manifest DTO from a persisted JSON payload."""
        return cls(
            pairs_backtest_id=str(payload["pairs_backtest_id"]),
            created_at=str(payload.get("created_at", "")),
            preset_id=str(payload.get("preset_id", "custom")),
            preset_label=str(payload.get("preset_label", "Custom")),
            universe_as_of_date=(
                str(payload["universe_as_of_date"])
                if payload.get("universe_as_of_date") is not None
                else None
            ),
            start_date=str(payload.get("start_date", "")),
            end_date=str(payload["end_date"]) if payload.get("end_date") is not None else None,
            requested_tickers=[str(item) for item in payload.get("requested_tickers", [])],
            available_tickers=[str(item) for item in payload.get("available_tickers", [])],
            eligible_tickers=[str(item) for item in payload.get("eligible_tickers", [])],
            scenario_count=int(payload.get("scenario_count", 0)),
            batch_mode=bool(payload.get("batch_mode", False)),
            benchmark_ids=[str(item) for item in payload.get("benchmark_ids", [])],
            candidate_pair_count=int(payload.get("candidate_pair_count", 0)),
            reconstitution_segment_count=int(payload.get("reconstitution_segment_count", 0)),
            warnings=[str(item) for item in payload.get("warnings", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the manifest payload."""
        return asdict(self)


@dataclass(slots=True)
class PairsBacktestResults:
    """Normalized detail payload for one persisted pairs execution."""

    pairs_backtest_id: str
    created_at: str
    manifest: dict[str, Any]
    preset: dict[str, Any] | None
    universe: dict[str, Any]
    candidate_pairs: list[dict[str, Any]]
    benchmarks: list[dict[str, Any]]
    scenarios: list[dict[str, Any]]
    robustness_report: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PairsBacktestResults":
        """Build the results DTO from a persisted JSON payload."""
        manifest_payload = payload.get("manifest")
        manifest = dict(manifest_payload) if isinstance(manifest_payload, Mapping) else {}
        return cls(
            pairs_backtest_id=str(payload["pairs_backtest_id"]),
            created_at=str(payload.get("created_at", "")),
            manifest=manifest,
            preset=dict(payload["preset"]) if isinstance(payload.get("preset"), Mapping) else None,
            universe=dict(payload.get("universe", {})),
            candidate_pairs=[
                dict(item)
                for item in payload.get("candidate_pairs", [])
                if isinstance(item, Mapping)
            ],
            benchmarks=[
                dict(item) for item in payload.get("benchmarks", []) if isinstance(item, Mapping)
            ],
            scenarios=[
                dict(item) for item in payload.get("scenarios", []) if isinstance(item, Mapping)
            ],
            robustness_report=dict(payload.get("robustness_report", {})),
            warnings=[str(item) for item in payload.get("warnings", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the detailed results payload."""
        return asdict(self)
