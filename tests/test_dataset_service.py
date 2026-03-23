"""Tests for local dataset cataloging."""

from __future__ import annotations

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
