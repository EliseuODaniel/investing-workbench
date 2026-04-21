"""Focused tests for the didactic B3 investment comparison service."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.bitcoin_martingale.application.investments.service import (
    InvestmentComparisonService,
)


def _fake_market_frame(start: str, end: str, base: float, step: float) -> pd.DataFrame:
    index = pd.date_range(start=start, end=end, freq="B")
    values = [base + step * offset for offset in range(len(index))]
    return pd.DataFrame({"Adj Close": values, "Close": values}, index=index)


def test_compare_builds_cross_asset_payload(monkeypatch: Any, tmp_path: Any) -> None:
    def fake_get_data(
        *,
        start: str,
        end: str,
        cache_path: str,
        force_download: bool,
        data_source: str,
        include_actions: bool,
    ) -> pd.DataFrame:
        del cache_path, force_download, include_actions
        mapping = {
            "PETR4": _fake_market_frame(start, end, 20.0, 0.2),
            "BOVA11": _fake_market_frame(start, end, 100.0, 0.1),
            "HGLG11": _fake_market_frame(start, end, 160.0, 0.05),
        }
        return mapping[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.investments.service.get_data",
        fake_get_data,
    )
    monkeypatch.setattr(
        "src.bitcoin_martingale.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame({"rate": [0.0001]}),
    )
    monkeypatch.setattr(
        "src.bitcoin_martingale.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )

    service = InvestmentComparisonService(data_dir=tmp_path / "investments")
    payload = service.compare(
        asset_ids=["PETR4", "SELIC_PROXY", "HGLG11"],
        start_date="2021-01-04",
        end_date="2021-03-31",
        initial_capital=10000.0,
        monthly_contribution=1000.0,
        benchmark_ids=["selic_cash", "bova11"],
    )

    assert payload["request"]["asset_ids"] == ["PETR4", "SELIC_PROXY", "HGLG11"]
    assert payload["chart"]["reference_series_id"] == "selic_cash"
    assert len(payload["results"]) == 3
    assert len(payload["benchmarks"]) == 2
    assert payload["results"][0]["final_value"] >= payload["results"][1]["final_value"]
    assert payload["results"][0]["invested_total"] == 12000.0
    assert payload["class_summary"]
    assert payload["highlights"]["best_final_value"]["instrument_id"] in {
        "PETR4",
        "SELIC_PROXY",
        "HGLG11",
    }
    assert any(
        point["selic_cash"] is not None and point["PETR4"] is not None
        for point in payload["chart"]["points"]
    )


def test_compare_warns_and_ignores_unknown_assets(monkeypatch: Any, tmp_path: Any) -> None:
    monkeypatch.setattr(
        "src.bitcoin_martingale.application.investments.service.get_data",
        lambda **kwargs: _fake_market_frame(
            kwargs["start"],
            kwargs["end"],
            40.0,
            0.1,
        ),
    )
    monkeypatch.setattr(
        "src.bitcoin_martingale.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame({"rate": [0.0001]}),
    )
    monkeypatch.setattr(
        "src.bitcoin_martingale.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )

    service = InvestmentComparisonService(data_dir=tmp_path / "investments")
    payload = service.compare(
        asset_ids=["UNKNOWN", "PETR4"],
        start_date="2021-01-04",
        end_date="2021-01-29",
        initial_capital=10000.0,
        benchmark_ids=[],
    )

    assert len(payload["results"]) == 1
    assert payload["results"][0]["instrument_id"] == "PETR4"
    assert "Ativo desconhecido ignorado: UNKNOWN" in payload["warnings"]
