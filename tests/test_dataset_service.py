"""Tests for local dataset cataloging."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.bitcoin_martingale.application.datasets import DatasetCatalogService


def test_dataset_catalog_lists_local_datasets() -> None:
    service = DatasetCatalogService()

    datasets = service.list_datasets()

    assert datasets
    assert any(dataset["path"] == "data/btc_brl.parquet" for dataset in datasets)


def test_dataset_catalog_returns_detail() -> None:
    service = DatasetCatalogService()
    datasets = service.list_datasets()

    detail = service.get_dataset(datasets[0]["dataset_id"])

    assert detail["dataset_id"] == datasets[0]["dataset_id"]
    assert "preview_rows" in detail
    assert "validation_warnings" in detail
    assert "validation" in detail
    assert "provenance" in detail


def test_dataset_imports_csv(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02"],
            "Open": [1.0, 2.0],
            "High": [2.0, 3.0],
            "Low": [0.5, 1.5],
            "Close": [1.5, 2.5],
        }
    ).to_csv(source_path, index=False)

    service = DatasetCatalogService(data_dir=tmp_path / "data")
    detail = service.import_dataset(source_path=str(source_path))

    assert detail["name"] == "sample"
    assert detail["path"].endswith("sample.csv")
    assert detail["provenance"]["source_kind"] == "imported"
    assert detail["provenance"]["history"][-1]["event_type"] == "imported"


def test_dataset_refresh_rejects_unsupported_dataset(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    dataset_path = data_dir / "custom.csv"
    pd.DataFrame({"value": [1, 2, 3]}).to_csv(dataset_path, index=False)

    service = DatasetCatalogService(data_dir=data_dir)
    dataset_id = service.list_datasets()[0]["dataset_id"]

    try:
        service.refresh_dataset(dataset_id)
    except NotImplementedError as exc:
        assert "not supported" in str(exc)
    else:
        raise AssertionError("Expected refresh to be unsupported for custom CSV datasets")


def test_imported_dataset_persists_metadata_between_reads(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.csv"
    pd.DataFrame({"Date": ["2024-01-01"], "Close": [1.0]}).to_csv(source_path, index=False)

    service = DatasetCatalogService(data_dir=tmp_path / "data")
    imported = service.import_dataset(source_path=str(source_path))
    fetched = service.get_dataset(imported["dataset_id"])

    assert fetched["provenance"]["source_kind"] == "imported"
    assert fetched["provenance"]["source_path"] == str(source_path.resolve())
