"""Application service for local dataset discovery and inspection."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from src.benchmarks import BenchmarkData
from src.bitcoin_martingale.domain.datasets import (
    DatasetDetail,
    DatasetProvenance,
    DatasetProvenanceEntry,
    DatasetRefreshPolicy,
    DatasetSummary,
    DatasetValidationSummary,
)
from src.data import get_data


class DatasetCatalogService:
    """Discover local datasets and expose lightweight metadata for the product."""

    def __init__(self, data_dir: Path | str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.metadata_dir = self.data_dir / ".catalog"
        self.benchmark_data = BenchmarkData(cache_dir=str(self.data_dir))

    def list_datasets(self) -> list[dict[str, object]]:
        """List known local datasets ordered by name."""
        summaries = [self._build_summary(path) for path in self._iter_dataset_paths()]
        summaries.sort(key=lambda item: item.name.lower())
        return [summary.to_dict() for summary in summaries]

    def get_dataset(self, dataset_id: str) -> dict[str, object]:
        """Inspect one dataset in detail."""
        dataset_path = self._resolve_dataset_path(dataset_id)
        return self._build_detail(dataset_path).to_dict()

    def list_due_datasets(self) -> list[dict[str, object]]:
        """List datasets whose refresh policy says they are due now."""
        due_summaries: list[DatasetSummary] = []
        for path in self._iter_dataset_paths():
            summary = self._build_summary(path)
            if summary.refresh_due:
                due_summaries.append(summary)
        due_summaries.sort(key=lambda item: item.name.lower())
        return [summary.to_dict() for summary in due_summaries]

    def import_dataset(
        self,
        *,
        source_path: str,
        dataset_name: str | None = None,
        overwrite: bool = False,
    ) -> dict[str, object]:
        """Import a local CSV or Parquet file into the managed data directory."""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Dataset source not found: {source_path}")
        if source.suffix not in {".csv", ".parquet"}:
            raise ValueError("Only CSV and Parquet datasets are supported for import")

        self.data_dir.mkdir(parents=True, exist_ok=True)
        target_name = dataset_name or source.name
        if Path(target_name).suffix != source.suffix:
            target_name = f"{target_name}{source.suffix}"
        target = self.data_dir / Path(target_name).name

        if target.exists() and not overwrite:
            raise ValueError(f"Dataset already exists: {target}")

        shutil.copy2(source, target)
        self._write_metadata(
            target,
            {
                "managed": True,
                "source_kind": "imported",
                "source_path": str(source.resolve()),
                "refresh_strategy": None,
                "imported_at": self._now_iso(),
                "last_refreshed_at": None,
                "history": [
                    {
                        "event_type": "imported",
                        "occurred_at": self._now_iso(),
                        "details": {
                            "source_path": str(source.resolve()),
                            "overwrite": overwrite,
                        },
                    }
                ],
            },
        )
        return self._build_detail(target).to_dict()

    def register_pairs_borrow_snapshot(self, *, source_path: str) -> dict[str, object]:
        """Copy a local borrow snapshot into the managed catalog and persist provenance."""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Borrow snapshot source not found: {source_path}")
        if source.suffix != ".csv":
            raise ValueError("Pairs borrow snapshots must be provided as CSV files")

        self.data_dir.mkdir(parents=True, exist_ok=True)
        target = self.data_dir / f"pairs_borrow__{source.stem}.csv"
        target_existed = target.exists()
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)

        metadata = self._load_metadata(target) if target_existed else {}
        history = list(metadata.get("history", []))
        history.append(
            {
                "event_type": (
                    "pairs_borrow_snapshot_updated"
                    if target_existed
                    else "pairs_borrow_snapshot_registered"
                ),
                "occurred_at": self._now_iso(),
                "details": {
                    "source_path": str(source.resolve()),
                    "managed_path": str(target.resolve()),
                },
            }
        )
        metadata.update(
            {
                "managed": True,
                "source_kind": "pairs_borrow_snapshot",
                "source_path": str(source.resolve()),
                "refresh_strategy": None,
                "imported_at": metadata.get("imported_at") or self._now_iso(),
                "last_refreshed_at": self._now_iso(),
                "history": history,
            }
        )
        self._write_metadata(target, metadata)
        return self._build_detail(target).to_dict()

    def set_refresh_policy(
        self,
        dataset_id: str,
        *,
        enabled: bool,
        interval_days: int,
        start_date: str = "2020-01-01",
        end_date: str | None = None,
    ) -> dict[str, object]:
        """Persist a refresh policy for one dataset."""
        if interval_days < 1:
            raise ValueError("Refresh interval_days must be at least 1")

        dataset_path = self._resolve_dataset_path(dataset_id)
        if self._build_refresh_spec(dataset_path) is None:
            raise NotImplementedError("Refresh policy is not supported for this dataset")

        metadata = self._load_metadata(dataset_path)
        metadata["refresh_policy"] = {
            "enabled": enabled,
            "interval_days": interval_days,
            "start_date": start_date,
            "end_date": end_date,
        }
        history = list(metadata.get("history", []))
        history.append(
            {
                "event_type": "refresh_policy_updated",
                "occurred_at": self._now_iso(),
                "details": metadata["refresh_policy"],
            }
        )
        metadata["history"] = history
        self._write_metadata(dataset_path, metadata)
        return self._build_detail(dataset_path).to_dict()

    def refresh_dataset(
        self,
        dataset_id: str,
        *,
        start_date: str = "2020-01-01",
        end_date: str | None = None,
    ) -> dict[str, object]:
        """Refresh a supported dataset in place."""
        dataset_path = self._resolve_dataset_path(dataset_id)
        refresh_spec = self._build_refresh_spec(dataset_path)
        if refresh_spec is None:
            raise NotImplementedError("Dataset refresh is not supported for this dataset")

        if refresh_spec["kind"] == "market":
            get_data(
                start=start_date,
                end=end_date,
                cache_path=str(dataset_path),
                force_download=True,
            )
        elif refresh_spec["kind"] == "benchmark":
            self.benchmark_data.download_market_data(
                ticker=str(refresh_spec["ticker"]),
                start_date=start_date,
                end_date=end_date or pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
                force_download=True,
            )
        else:
            raise NotImplementedError("Dataset refresh is not supported for this dataset")

        metadata = self._load_metadata(dataset_path)
        history = list(metadata.get("history", []))
        history.append(
            {
                "event_type": "refreshed",
                "occurred_at": self._now_iso(),
                "details": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "refresh_strategy": refresh_spec["kind"],
                },
            }
        )
        metadata.update(
            {
                "managed": True,
                "source_kind": metadata.get("source_kind", "inferred"),
                "refresh_strategy": refresh_spec["kind"],
                "last_refreshed_at": self._now_iso(),
                "history": history,
            }
        )
        self._write_metadata(dataset_path, metadata)

        return self._build_detail(dataset_path).to_dict()

    def refresh_due_datasets(self, *, limit: int | None = None) -> list[dict[str, object]]:
        """Refresh all datasets that are due according to their persisted policy."""
        due_datasets = self.list_due_datasets()
        if limit is not None:
            due_datasets = due_datasets[:limit]

        refreshed: list[dict[str, object]] = []
        for dataset in due_datasets:
            detail = self.get_dataset(str(dataset["dataset_id"]))
            provenance = detail.get("provenance")
            if not isinstance(provenance, dict):
                continue
            refresh_policy = provenance.get("refresh_policy")
            if not isinstance(refresh_policy, dict):
                continue
            refreshed.append(
                self.refresh_dataset(
                    str(dataset["dataset_id"]),
                    start_date=str(refresh_policy.get("start_date", "2020-01-01")),
                    end_date=(
                        str(refresh_policy["end_date"])
                        if refresh_policy.get("end_date") is not None
                        else None
                    ),
                )
            )
        return refreshed

    def _iter_dataset_paths(self) -> list[Path]:
        if not self.data_dir.exists():
            return []

        dataset_paths: list[Path] = []
        for pattern in ("*.parquet", "*.csv"):
            dataset_paths.extend(sorted(self.data_dir.glob(pattern)))
        return dataset_paths

    def _resolve_dataset_path(self, dataset_id: str) -> Path:
        for path in self._iter_dataset_paths():
            if self._build_dataset_id(path) == dataset_id:
                return path
        raise FileNotFoundError(f"Dataset not found: {dataset_id}")

    def _build_summary(self, dataset_path: Path) -> DatasetSummary:
        dataframe = self._read_dataset(dataset_path)
        row_count = len(dataframe)
        start_timestamp, end_timestamp = self._resolve_time_bounds(dataframe)
        columns = [str(column) for column in dataframe.columns]
        stat = dataset_path.stat()
        metadata = self._load_metadata(dataset_path)
        refresh_policy = self._build_refresh_policy(dataset_path, metadata, stat.st_mtime)

        return DatasetSummary(
            dataset_id=self._build_dataset_id(dataset_path),
            name=dataset_path.stem,
            path=str(dataset_path),
            format=dataset_path.suffix.lstrip("."),
            category=self._categorize_dataset(dataset_path),
            row_count=row_count,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            columns=columns,
            file_size_bytes=stat.st_size,
            last_modified=self._to_iso_timestamp(stat.st_mtime),
            data_fingerprint=self._build_data_fingerprint(dataframe),
            refresh_due=refresh_policy.due_now if refresh_policy else False,
            next_refresh_due_at=refresh_policy.next_refresh_due_at if refresh_policy else None,
        )

    def _build_detail(self, dataset_path: Path) -> DatasetDetail:
        dataframe = self._read_dataset(dataset_path)
        summary = self._build_summary(dataset_path)
        preview_rows = self._build_preview_rows(dataframe)
        validation_warnings = self._build_validation_warnings(dataframe, dataset_path)

        return DatasetDetail(
            **summary.to_dict(),
            preview_rows=preview_rows,
            validation_warnings=validation_warnings,
            validation=self._build_validation_summary(dataframe, dataset_path),
            provenance=self._build_provenance(dataset_path),
        )

    def _read_dataset(self, dataset_path: Path) -> pd.DataFrame:
        if dataset_path.suffix == ".parquet":
            dataframe = pd.read_parquet(dataset_path)
        elif dataset_path.suffix == ".csv":
            dataframe = pd.read_csv(dataset_path)
        else:
            raise ValueError(f"Unsupported dataset format: {dataset_path.suffix}")

        if "Date" in dataframe.columns:
            dataframe["Date"] = pd.to_datetime(dataframe["Date"], errors="coerce")
            dataframe = dataframe.set_index("Date")

        if not isinstance(dataframe.index, pd.DatetimeIndex):
            try:
                dataframe.index = pd.to_datetime(dataframe.index)
            except (TypeError, ValueError):
                pass

        if isinstance(dataframe.index, pd.DatetimeIndex):
            dataframe = dataframe.sort_index()

        return dataframe

    def _build_dataset_id(self, dataset_path: Path) -> str:
        relative_path = dataset_path.relative_to(self.data_dir).as_posix()
        normalized = relative_path.replace("/", "__").replace(".", "_")
        return normalized

    def _categorize_dataset(self, dataset_path: Path) -> str:
        metadata = self._load_metadata(dataset_path)
        if metadata.get("source_kind") == "pairs_borrow_snapshot":
            return "borrow"
        stem = dataset_path.stem.lower()
        if stem.endswith("_benchmark"):
            return "benchmark"
        if "selic" in stem:
            return "rates"
        return "market"

    def _resolve_time_bounds(self, dataframe: pd.DataFrame) -> tuple[str | None, str | None]:
        if isinstance(dataframe.index, pd.DatetimeIndex) and len(dataframe.index) > 0:
            return dataframe.index[0].isoformat(), dataframe.index[-1].isoformat()
        return None, None

    def _build_data_fingerprint(self, dataframe: pd.DataFrame) -> str:
        hashed = pd.util.hash_pandas_object(dataframe, index=True)
        return hashlib.sha256(hashed.values.tobytes()).hexdigest()

    def _build_preview_rows(self, dataframe: pd.DataFrame) -> list[dict[str, object]]:
        preview_frame = dataframe.head(5).copy()
        preview_rows: list[dict[str, object]] = []
        for index, row in preview_frame.iterrows():
            payload = {
                key: self._normalize_preview_value(value) for key, value in row.to_dict().items()
            }
            payload["__index__"] = index.isoformat() if hasattr(index, "isoformat") else str(index)
            preview_rows.append(payload)
        return preview_rows

    def _build_validation_warnings(
        self,
        dataframe: pd.DataFrame,
        dataset_path: Path,
    ) -> list[str]:
        validation = self._build_validation_summary(dataframe, dataset_path)
        warnings: list[str] = []
        if dataframe.empty:
            warnings.append("Dataset is empty")
        if validation.missing_required_columns:
            warnings.append("OHLC dataset is missing one or more expected price columns")
        if validation.duplicate_index_count:
            warnings.append("Datetime index contains duplicate rows")
        if validation.date_gap_count:
            warnings.append("Datetime index has missing calendar gaps")
        if validation.price_anomaly_count:
            warnings.append("Dataset includes price anomalies outside expected OHLC bounds")
        if validation.missing_value_count:
            warnings.append("Dataset includes missing values")
        if validation.datetime_index_detected and not dataframe.index.is_monotonic_increasing:
            warnings.append("Datetime index is not sorted ascending")
        if not validation.supported_refresh:
            warnings.append("Refresh is not supported for this dataset type")
        return warnings

    def _build_validation_summary(
        self,
        dataframe: pd.DataFrame,
        dataset_path: Path,
    ) -> DatasetValidationSummary:
        datetime_index_detected = isinstance(dataframe.index, pd.DatetimeIndex)
        duplicate_index_count = (
            int(dataframe.index.duplicated().sum()) if datetime_index_detected else 0
        )
        missing_value_count = int(dataframe.isna().sum().sum())
        date_gap_count = self._count_date_gaps(dataframe.index) if datetime_index_detected else 0
        missing_required_columns = self._missing_required_columns(dataframe)
        price_anomaly_count = self._count_price_anomalies(dataframe)
        supported_refresh = self._build_refresh_spec(dataset_path) is not None

        return DatasetValidationSummary(
            datetime_index_detected=datetime_index_detected,
            duplicate_index_count=duplicate_index_count,
            missing_value_count=missing_value_count,
            date_gap_count=date_gap_count,
            missing_required_columns=missing_required_columns,
            price_anomaly_count=price_anomaly_count,
            supported_refresh=supported_refresh,
        )

    def _normalize_preview_value(self, value: object) -> object:
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except TypeError:
                return str(value)
        if pd.isna(value):
            return None
        if isinstance(value, (int, float, str, bool)) or value is None:
            return value
        return str(value)

    def _to_iso_timestamp(self, unix_seconds: float) -> str:
        return pd.Timestamp(unix_seconds, unit="s", tz="UTC").isoformat()

    def _now_iso(self) -> str:
        return datetime.now(UTC).isoformat()

    def _count_date_gaps(self, index: pd.DatetimeIndex) -> int:
        if len(index) < 2:
            return 0
        differences = index.to_series().diff().dropna()
        return int((differences > pd.Timedelta(days=1)).sum())

    def _missing_required_columns(self, dataframe: pd.DataFrame) -> list[str]:
        required_columns = {"Open", "High", "Low", "Close"}
        if not required_columns.intersection(dataframe.columns):
            return []
        return sorted(required_columns.difference(dataframe.columns))

    def _count_price_anomalies(self, dataframe: pd.DataFrame) -> int:
        required_columns = {"High", "Low", "Close"}
        if not required_columns.issubset(dataframe.columns):
            return 0

        high_low_invalid = (dataframe["High"] < dataframe["Low"]).sum()
        close_invalid = (
            (dataframe["Close"] > dataframe["High"]) | (dataframe["Close"] < dataframe["Low"])
        ).sum()
        return int(high_low_invalid + close_invalid)

    def _build_refresh_spec(self, dataset_path: Path) -> dict[str, Any] | None:
        stem = dataset_path.stem
        lower_stem = stem.lower()
        if dataset_path.suffix == ".parquet" and lower_stem == "btc_brl":
            return {"kind": "market", "ticker": "BTC-BRL"}
        if dataset_path.suffix == ".parquet" and lower_stem.endswith("_benchmark"):
            return {
                "kind": "benchmark",
                "ticker": stem.replace("_benchmark", "").replace("__", "^"),
            }
        return None

    def _metadata_path(self, dataset_path: Path) -> Path:
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        return self.metadata_dir / f"{self._build_dataset_id(dataset_path)}.json"

    def _load_metadata(self, dataset_path: Path) -> dict[str, Any]:
        metadata_path = self._metadata_path(dataset_path)
        if metadata_path.exists():
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        return self._build_inferred_metadata(dataset_path)

    def _write_metadata(self, dataset_path: Path, metadata: dict[str, Any]) -> None:
        metadata_path = self._metadata_path(dataset_path)
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _build_inferred_metadata(self, dataset_path: Path) -> dict[str, Any]:
        refresh_spec = self._build_refresh_spec(dataset_path)
        return {
            "managed": False,
            "source_kind": "inferred",
            "source_path": str(dataset_path),
            "refresh_strategy": refresh_spec["kind"] if refresh_spec else None,
            "refresh_policy": (
                {
                    "enabled": False,
                    "interval_days": 7,
                    "start_date": "2020-01-01",
                    "end_date": None,
                }
                if refresh_spec
                else None
            ),
            "imported_at": None,
            "last_refreshed_at": None,
            "history": [
                {
                    "event_type": "discovered",
                    "occurred_at": self._to_iso_timestamp(dataset_path.stat().st_mtime),
                    "details": {
                        "path": str(dataset_path),
                    },
                }
            ],
        }

    def _build_provenance(self, dataset_path: Path) -> DatasetProvenance:
        metadata = self._load_metadata(dataset_path)
        refresh_policy = self._build_refresh_policy(
            dataset_path,
            metadata,
            dataset_path.stat().st_mtime,
        )
        history = [
            DatasetProvenanceEntry(
                event_type=str(entry.get("event_type", "unknown")),
                occurred_at=str(entry.get("occurred_at", "")),
                details=dict(entry.get("details", {})),
            )
            for entry in metadata.get("history", [])
            if isinstance(entry, dict)
        ]
        return DatasetProvenance(
            managed=bool(metadata.get("managed", False)),
            source_kind=str(metadata.get("source_kind", "inferred")),
            source_path=str(metadata["source_path"]) if metadata.get("source_path") else None,
            refresh_strategy=(
                str(metadata["refresh_strategy"]) if metadata.get("refresh_strategy") else None
            ),
            imported_at=(str(metadata["imported_at"]) if metadata.get("imported_at") else None),
            last_refreshed_at=(
                str(metadata["last_refreshed_at"]) if metadata.get("last_refreshed_at") else None
            ),
            refresh_policy=refresh_policy,
            history=history,
        )

    def _build_refresh_policy(
        self,
        dataset_path: Path,
        metadata: dict[str, Any],
        modified_at_unix: float,
    ) -> DatasetRefreshPolicy | None:
        refresh_spec = self._build_refresh_spec(dataset_path)
        raw_policy = metadata.get("refresh_policy")
        if refresh_spec is None or not isinstance(raw_policy, dict):
            return None

        enabled = bool(raw_policy.get("enabled", False))
        interval_days = max(int(raw_policy.get("interval_days", 7)), 1)
        start_date = str(raw_policy.get("start_date", "2020-01-01"))
        end_date = str(raw_policy["end_date"]) if raw_policy.get("end_date") else None

        last_reference = (
            metadata.get("last_refreshed_at")
            or metadata.get("imported_at")
            or self._to_iso_timestamp(modified_at_unix)
        )
        last_reference_ts = pd.Timestamp(str(last_reference))
        if last_reference_ts.tzinfo is None:
            last_reference_ts = last_reference_ts.tz_localize("UTC")
        next_due_ts = last_reference_ts + timedelta(days=interval_days)
        now_ts = pd.Timestamp.now(tz="UTC")

        return DatasetRefreshPolicy(
            enabled=enabled,
            interval_days=interval_days,
            start_date=start_date,
            end_date=end_date,
            next_refresh_due_at=next_due_ts.isoformat(),
            due_now=enabled and now_ts >= next_due_ts,
        )
