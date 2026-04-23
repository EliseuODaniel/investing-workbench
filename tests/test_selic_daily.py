"""Tests for daily SELIC support."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.engine import BacktestEngine
from src.selic import (
    download_daily_selic_data,
    get_daily_rate,
    get_or_create_daily_selic_data,
    load_daily_selic_data,
    save_daily_selic_data,
)


def test_save_and_load_daily_selic_data(tmp_path: Path) -> None:
    data = pd.DataFrame(
        {
            "date": [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
            "rate": [0.001, 0.0011],
        }
    )
    path = tmp_path / "selic_daily.csv"

    save_daily_selic_data(data, str(path))
    loaded = load_daily_selic_data(str(path))

    assert loaded is not None
    assert len(loaded) == 2
    assert list(loaded.columns) == ["date", "rate"]
    assert loaded.iloc[0]["date"] == pd.Timestamp("2023-01-02")
    assert loaded.iloc[1]["rate"] == 0.0011


def test_get_daily_rate_uses_exact_or_previous_business_day() -> None:
    data = pd.DataFrame(
        {
            "date": [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
            "rate": [0.001, 0.0011],
        }
    )

    assert get_daily_rate(data, "2023-01-02") == 0.001
    assert get_daily_rate(data, "2023-01-04") == 0.0011


def test_engine_applies_real_daily_selic_from_file(tmp_path: Path) -> None:
    data = pd.DataFrame(
        {
            "date": [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
            "rate": [0.001, 0.002],
        }
    )
    path = tmp_path / "selic_daily.csv"
    save_daily_selic_data(data, str(path))

    engine = BacktestEngine(
        initial_cash=10000.0,
        apply_cash_yield=True,
        yield_frequency="daily",
        use_real_selic=True,
        selic_path=str(path),
    )

    engine._apply_cash_yield(pd.Timestamp("2023-01-02"))
    assert engine.state.cash == 10010.0

    engine._apply_cash_yield(pd.Timestamp("2023-01-03"))
    assert round(engine.state.cash, 2) == 10030.02


def test_engine_can_apply_daily_selic_after_strategy_actions(tmp_path: Path) -> None:
    selic = pd.DataFrame(
        {
            "date": [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
            "rate": [0.001, 0.002],
        }
    )
    selic_path = tmp_path / "selic_daily.csv"
    save_daily_selic_data(selic, str(selic_path))

    data = pd.DataFrame(
        [
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 10.0,
                "Close": 10.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 10.0,
                "Close": 10.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
        ],
        index=[pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
    )

    class OneShotBuyStrategy:
        def __init__(self) -> None:
            self.done = False

        def on_bar(self, row: pd.Series, engine: BacktestEngine) -> None:
            if self.done:
                return
            engine.buy(pd.Timestamp(row.name), float(row["Open"]), 1000.0, layer_id=1)
            self.done = True

    engine = BacktestEngine(
        initial_cash=40000.0,
        apply_cash_yield=True,
        yield_frequency="daily",
        cash_yield_timing="end_of_bar",
        use_real_selic=True,
        selic_path=str(selic_path),
        close_positions_at_end=False,
    )

    engine.run(data, OneShotBuyStrategy())

    assert round(engine.state.cash, 2) == 30090.06


def test_engine_refreshes_daily_selic_for_the_run_window(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str | None, str | None]] = []

    def fake_get_or_create_daily_selic_data(
        path: str = "data/selic_daily.csv",
        use_download: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        calls.append((start_date, end_date))
        return pd.DataFrame(
            {
                "date": [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
                "rate": [0.001, 0.001],
            }
        )

    monkeypatch.setattr(
        "src.investing_workbench.domain.backtest.engine.get_or_create_daily_selic_data",
        fake_get_or_create_daily_selic_data,
    )

    data = pd.DataFrame(
        [
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 10.0,
                "Close": 10.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 10.0,
                "Close": 10.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
        ],
        index=[pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
    )

    class CashOnlyStrategy:
        def on_bar(self, row: pd.Series, engine: BacktestEngine) -> None:
            return

    engine = BacktestEngine(
        initial_cash=40000.0,
        apply_cash_yield=True,
        yield_frequency="daily",
        use_real_selic=True,
        selic_path=str(tmp_path / "selic_daily.csv"),
        close_positions_at_end=False,
    )

    engine.run(data, CashOnlyStrategy())

    assert calls[0] == (None, None)
    assert ("2023-01-02", "2023-01-03") in calls


def test_download_daily_selic_data_chunks_long_ranges(monkeypatch) -> None:
    calls: list[tuple[str | None, str | None]] = []

    def fake_download_bcb_series(
        *,
        sgs_code: int,
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict[str, str]]:
        assert sgs_code == 11
        calls.append((start_date, end_date))
        assert start_date is not None
        assert end_date is not None
        return [{"data": pd.Timestamp(start_date).strftime("%d/%m/%Y"), "valor": "0.01"}]

    monkeypatch.setattr("src.selic._download_bcb_series", fake_download_bcb_series)

    downloaded = download_daily_selic_data("2005-12-30", "2026-03-31")

    assert downloaded is not None
    assert len(downloaded) == len(calls)
    assert len(calls) >= 3
    for start_date, end_date in calls:
        assert start_date is not None
        assert end_date is not None
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        assert end_ts >= start_ts
        assert end_ts <= start_ts + pd.DateOffset(years=10)


def test_get_or_create_daily_selic_data_merges_downloaded_range_into_cache(
    monkeypatch, tmp_path: Path
) -> None:
    path = tmp_path / "selic_daily.csv"
    save_daily_selic_data(
        pd.DataFrame(
            {
                "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")],
                "rate": [0.001, 0.0011],
            }
        ),
        str(path),
    )

    calls = {"count": 0}

    def fake_download_daily_selic_data(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        del start_date, end_date
        calls["count"] += 1
        return pd.DataFrame(
            {
                "date": [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
                "rate": [0.0009, 0.0010],
            }
        )

    monkeypatch.setattr("src.selic.download_daily_selic_data", fake_download_daily_selic_data)

    first = get_or_create_daily_selic_data(
        path=str(path),
        use_download=True,
        start_date="2023-01-02",
        end_date="2024-01-03",
    )
    second = get_or_create_daily_selic_data(
        path=str(path),
        use_download=True,
        start_date="2023-06-01",
        end_date="2024-01-03",
    )

    assert first is not None
    assert second is not None
    assert calls["count"] == 1
    assert first["date"].min() == pd.Timestamp("2023-01-02")
    assert first["date"].max() == pd.Timestamp("2024-01-03")
    reloaded = load_daily_selic_data(str(path))
    assert reloaded is not None
    assert reloaded["date"].min() == pd.Timestamp("2023-01-02")
