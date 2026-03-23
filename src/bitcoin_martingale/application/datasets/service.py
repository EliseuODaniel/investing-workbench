"""Application service for local dataset discovery and inspection."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from src.benchmarks import BenchmarkData
from src.bitcoin_martingale.domain.datasets import (
    DatasetDetail,
    DatasetSummary,
    DatasetValidationSummary,
)
from src.data import get_data


class DatasetCatalogService:
    """Discover local datasets and expose lightweight metadata for the product."""

    def __init__(self, data_dir: Path | str = "data") -> None:
        self.data_dir = Path(data_dir)
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
        return self._build_detail(target).to_dict()

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

        return self._build_detail(dataset_path).to_dict()

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
                key: self._normalize_preview_value(value)
                for key, value in row.to_dict().items()
            }
            payload["__index__"] = (
                index.isoformat() if hasattr(index, "isoformat") else str(index)
            )
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
            warnings.append(
                "OHLC dataset is missing one or more expected price columns"
            )
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
            (dataframe["Close"] > dataframe["High"])
            | (dataframe["Close"] < dataframe["Low"])
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
