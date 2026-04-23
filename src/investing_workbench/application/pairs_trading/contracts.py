"""Shared contracts for B3 pairs-trading application workflows."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.investing_workbench.domain.pairs_trading import (
    BorrowOverride,
    CointegrationPairsBacktester,
    PairsTradingConfig,
)

from .dto import BorrowSnapshotRegistration

DEFAULT_START_DATE = "2021-01-01"
ProgressCallback = Callable[[dict[str, Any]], None] | None


class PairsExecutionCancelledError(RuntimeError):
    """Raised when a pairs workflow is cancelled before completion."""


@dataclass(slots=True)
class PairsContext:
    """Resolved universe context shared across screener and backtest flows."""

    preset_metadata: dict[str, Any] | None
    requested_tickers: list[str]
    resolved_as_of_date: str | None
    sector_map: dict[str, str]
    unavailable_tickers: dict[str, str]
    warnings: list[str]
    data_by_ticker: dict[str, pd.DataFrame]
    borrow_overrides: dict[str, BorrowOverride]
    borrow_snapshot_registration: BorrowSnapshotRegistration | None
    config: PairsTradingConfig
    backtester: CointegrationPairsBacktester
    common_index: pd.DatetimeIndex
    universe_records: list[dict[str, Any]]
    eligible_records: list[dict[str, Any]]
    quality_report: dict[str, Any]


@dataclass(slots=True)
class ReconstitutionSegment:
    """One resolved IBOV universe slice used during reconstituted execution."""

    segment_id: str
    start_date: str
    end_date: str
    requested_as_of_date: str
    resolved_as_of_date: str
    context: PairsContext
