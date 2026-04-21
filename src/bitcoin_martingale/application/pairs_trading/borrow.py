"""Borrow snapshot ingestion helpers for B3 pairs workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.bitcoin_martingale.application.datasets import DatasetCatalogService
from src.bitcoin_martingale.domain.pairs_trading import BorrowOverride

from .dto import BorrowSnapshotRegistration


class PairsBorrowSnapshotService:
    """Load and govern optional borrow snapshot overrides for the requested universe."""

    def __init__(self, dataset_service: DatasetCatalogService) -> None:
        self.dataset_service = dataset_service

    def load_overrides(
        self,
        *,
        borrow_snapshot_path: str | None,
        requested_tickers: list[str],
    ) -> tuple[dict[str, BorrowOverride], list[str], BorrowSnapshotRegistration | None]:
        """Register one local borrow snapshot and return overrides for the requested tickers."""
        if borrow_snapshot_path is None or not borrow_snapshot_path.strip():
            return {}, [], None

        snapshot_path = Path(borrow_snapshot_path).expanduser()
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Borrow snapshot file not found: {snapshot_path}")

        registration_detail = self.dataset_service.register_pairs_borrow_snapshot(
            source_path=str(snapshot_path),
        )
        provenance = registration_detail.get("provenance", {})
        source_path = (
            str(provenance.get("source_path"))
            if isinstance(provenance, dict) and provenance.get("source_path")
            else str(snapshot_path.resolve())
        )
        registration = BorrowSnapshotRegistration(
            dataset_id=str(registration_detail["dataset_id"]),
            managed_path=str(registration_detail["path"]),
            source_path=source_path,
        )
        source_name = Path(registration.source_path).name
        managed_name = Path(registration.managed_path).name

        dataframe = pd.read_csv(Path(registration.managed_path))
        if "ticker" not in dataframe.columns:
            raise ValueError("Borrow snapshot CSV must include a 'ticker' column")

        overrides: dict[str, BorrowOverride] = {}
        requested_set = {ticker.upper().strip() for ticker in requested_tickers}
        for record in dataframe.to_dict(orient="records"):
            ticker = str(record.get("ticker", "")).upper().strip()
            if not ticker or ticker not in requested_set:
                continue
            borrow_rate_raw = record.get("borrow_rate_annual")
            short_eligible_raw = record.get("short_eligible")
            margin_haircut_raw = record.get("margin_haircut")
            overrides[ticker] = BorrowOverride(
                ticker=ticker,
                borrow_rate_annual=(float(borrow_rate_raw) if pd.notna(borrow_rate_raw) else None),
                short_eligible=self._parse_optional_bool(short_eligible_raw),
                margin_haircut=(
                    float(margin_haircut_raw) if pd.notna(margin_haircut_raw) else None
                ),
                source=source_name,
            )

        matched_count = len(overrides)
        warnings = [
            "Loaded borrow snapshot overrides for "
            f"{matched_count} of {len(requested_tickers)} requested tickers from "
            f"{source_name}."
        ]
        if source_name != managed_name:
            warnings.append(f"Managed borrow snapshot copy stored as {managed_name}.")
        return overrides, warnings, registration

    def _parse_optional_bool(self, value: Any) -> bool | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "y", "sim"}:
            return True
        if normalized in {"0", "false", "no", "n", "nao", "não"}:
            return False
        raise ValueError(f"Invalid boolean value in borrow snapshot: {value}")
