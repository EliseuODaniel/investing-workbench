"""Application service for local dataset discovery and inspection."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from src.bitcoin_martingale.domain.datasets import DatasetDetail, DatasetSummary


class DatasetCatalogService:
    """Discover local datasets and expose lightweight metadata for the product."""

    def __init__(self, data_dir: Path | str = "data") -> None:
        self.data_dir = Path(data_dir)

    def list_datasets(self) -> list[dict[str, object]]:
        """List known local datasets ordered by name."""
        summaries = [self._build_summary(path) for path in self._iter_dataset_paths()]
        summaries.sort(key=lambda item: item.name.lower())
        return [summary.to_dict() for summary in summaries]

    def get_dataset(self, dataset_id: str) -> dict[str, object]:
        """Inspect one dataset in detail."""
        dataset_path = self._resolve_dataset_path(dataset_id)
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
        warnings: list[str] = []
        if dataframe.empty:
            warnings.append("Dataset is empty")
        if dataset_path.suffix == ".parquet":
            required_columns = {"Open", "High", "Low", "Close"}
            if required_columns.intersection(dataframe.columns) and not required_columns.issubset(
                dataframe.columns
            ):
                warnings.append(
                    "OHLC dataset is missing one or more expected price columns"
                )
        if isinstance(dataframe.index, pd.DatetimeIndex):
            if dataframe.index.has_duplicates:
                warnings.append("Datetime index contains duplicate rows")
            if not dataframe.index.is_monotonic_increasing:
                warnings.append("Datetime index is not sorted ascending")
        return warnings

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
