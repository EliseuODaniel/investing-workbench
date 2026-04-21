"""Tests for local dataset cataloging."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

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


def test_pairs_borrow_snapshot_registration_is_cataloged(tmp_path: Path) -> None:
    source_path = tmp_path / "borrow_snapshot.csv"
    pd.DataFrame(
        {
            "ticker": ["PETR4", "VALE3"],
            "borrow_rate_annual": [0.07, 0.05],
            "short_eligible": [True, True],
            "margin_haircut": [0.45, 0.40],
        }
    ).to_csv(source_path, index=False)

    service = DatasetCatalogService(data_dir=tmp_path / "data")
    detail = service.register_pairs_borrow_snapshot(source_path=str(source_path))
    datasets = service.list_datasets()

    assert detail["category"] == "borrow"
    assert detail["provenance"]["source_kind"] == "pairs_borrow_snapshot"
    assert detail["provenance"]["source_path"] == str(source_path.resolve())
    assert any(item["dataset_id"] == detail["dataset_id"] for item in datasets)


def test_supported_dataset_can_store_refresh_policy(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02"],
            "Open": [1.0, 2.0],
            "High": [2.0, 3.0],
            "Low": [0.5, 1.5],
            "Close": [1.5, 2.5],
        }
    ).to_parquet(data_dir / "btc_brl.parquet", index=False)

    service = DatasetCatalogService(data_dir=data_dir)
    dataset_id = service.list_datasets()[0]["dataset_id"]

    detail = service.set_refresh_policy(
        dataset_id,
        enabled=True,
        interval_days=3,
        start_date="2023-01-01",
        end_date="2024-12-31",
    )

    refresh_policy = detail["provenance"]["refresh_policy"]
    assert refresh_policy["enabled"] is True
    assert refresh_policy["interval_days"] == 3
    assert refresh_policy["start_date"] == "2023-01-01"
    assert refresh_policy["end_date"] == "2024-12-31"
    assert detail["provenance"]["history"][-1]["event_type"] == "refresh_policy_updated"


def test_due_datasets_reflect_policy_state(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    dataset_path = data_dir / "btc_brl.parquet"
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02"],
            "Open": [1.0, 2.0],
            "High": [2.0, 3.0],
            "Low": [0.5, 1.5],
            "Close": [1.5, 2.5],
        }
    ).to_parquet(dataset_path, index=False)

    service = DatasetCatalogService(data_dir=data_dir)
    dataset_id = service.list_datasets()[0]["dataset_id"]
    detail = service.set_refresh_policy(dataset_id, enabled=True, interval_days=1)

    metadata_path = data_dir / ".catalog" / f"{dataset_id}.json"
    stale_timestamp = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["last_refreshed_at"] = stale_timestamp
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    due = service.list_due_datasets()

    assert len(due) == 1
    assert due[0]["dataset_id"] == dataset_id
    assert due[0]["refresh_due"] is True
    refreshed_detail = service.get_dataset(detail["dataset_id"])
    assert refreshed_detail["provenance"]["refresh_policy"]["due_now"] is True


def test_refresh_due_datasets_executes_due_entries(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02"],
            "Open": [1.0, 2.0],
            "High": [2.0, 3.0],
            "Low": [0.5, 1.5],
            "Close": [1.5, 2.5],
        }
    ).to_parquet(data_dir / "btc_brl.parquet", index=False)

    service = DatasetCatalogService(data_dir=data_dir)
    dataset_id = service.list_datasets()[0]["dataset_id"]
    service.set_refresh_policy(dataset_id, enabled=True, interval_days=1)

    metadata_path = data_dir / ".catalog" / f"{dataset_id}.json"
    stale_timestamp = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["last_refreshed_at"] = stale_timestamp
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with patch.object(service, "refresh_dataset", wraps=service.refresh_dataset) as refresh_mock:
        with patch(
            "src.bitcoin_martingale.application.datasets.service.get_data",
            return_value=pd.DataFrame({"Close": [1.0]}),
        ):
            refreshed = service.refresh_due_datasets()

    assert len(refreshed) == 1
    assert refresh_mock.call_count == 1
