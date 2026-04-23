"""Focused tests for the didactic B3 investment comparison service."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.investing_workbench.application.investments.service import (
    InvestmentComparisonService,
)


def _fake_market_frame(start: str, end: str, base: float, step: float) -> pd.DataFrame:
    index = pd.date_range(start=start, end=end, freq="B")
    values = [base + step * offset for offset in range(len(index))]
    return pd.DataFrame({"Adj Close": values, "Close": values}, index=index)


def _stub_ipca() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2021, 2021, 2021, 2021, 2021, 2021],
            "month": [1, 2, 3, 4, 5, 6],
            "rate": [0.004, 0.005, 0.006, 0.005, 0.004, 0.005],
        }
    )


def _fixed_income_quotes(start: str, end: str, daily_return: float) -> pd.DataFrame:
    index = pd.date_range(start=start, end=end, freq="B")
    values = [1000.0 * ((1.0 + daily_return) ** offset) for offset in range(len(index))]
    return pd.DataFrame({"date": index, "close": values})


def _tesouro_history_fixture(start: str, end: str) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="MS")
    maturities = [
        pd.Timestamp("2020-01-01"),
        pd.Timestamp("2022-01-01"),
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2026-01-01"),
        pd.Timestamp("2028-01-01"),
    ]
    rows: list[dict[str, object]] = []
    for offset, date in enumerate(dates):
        for title_type in ("Tesouro Selic", "Tesouro Prefixado", "Tesouro IPCA+"):
            for maturity in maturities:
                if maturity <= date:
                    continue
                years_to_maturity = float((maturity - date).days / 365.25)
                if title_type == "Tesouro Selic":
                    base_price = 950.0 + offset * 6.0 + (1.0 / max(years_to_maturity, 0.5))
                    sell_rate = 0.12
                    buy_rate = 0.125
                elif title_type == "Tesouro Prefixado":
                    market_rate = max(0.05, 0.14 - offset * 0.0012)
                    base_price = 1000.0 / ((1.0 + market_rate) ** years_to_maturity)
                    sell_rate = market_rate
                    buy_rate = market_rate + 0.002
                else:
                    real_rate = max(0.03, 0.065 - offset * 0.0007)
                    inflation_factor = (1.0 + 0.004) ** offset
                    base_price = (
                        1000.0 * inflation_factor / ((1.0 + real_rate) ** years_to_maturity)
                    )
                    sell_rate = real_rate
                    buy_rate = real_rate + 0.002

                rows.append(
                    {
                        "title_type": title_type,
                        "maturity_date": maturity.normalize(),
                        "date": date.normalize(),
                        "investor_sell_rate": sell_rate,
                        "investor_buy_rate": buy_rate,
                        "investor_sell_price": base_price * 0.998,
                        "investor_buy_price": base_price * 1.002,
                        "base_price": base_price,
                        "years_to_maturity": years_to_maturity,
                        "title_key": f"{title_type}::{maturity.date()}",
                    }
                )
    return pd.DataFrame(rows)


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
        "src.investing_workbench.application.investments.service.get_data",
        fake_get_data,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame({"rate": [0.0001]}),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_ipca_data",
        lambda **_: _stub_ipca(),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_monthly_ipca_rate",
        lambda *_args, **_kwargs: 0.004,
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
    assert payload["results"][0]["final_value_real"] > 0
    assert payload["real_chart"]["points"]
    assert payload["inflation"]["accumulated_rate"] > 0
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
        "src.investing_workbench.application.investments.service.get_data",
        lambda **kwargs: _fake_market_frame(
            kwargs["start"],
            kwargs["end"],
            40.0,
            0.1,
        ),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame({"rate": [0.0001]}),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_ipca_data",
        lambda **_: _stub_ipca(),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_monthly_ipca_rate",
        lambda *_args, **_kwargs: 0.004,
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


def test_compare_supports_guided_model_portfolios(monkeypatch: Any, tmp_path: Any) -> None:
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
        base_map = {
            "IMAB11": 100.0,
            "IRFM11": 95.0,
            "ITUB4": 20.0,
            "BBSE3": 30.0,
            "TAEE11": 35.0,
            "SUZB3": 45.0,
            "FLRY3": 18.0,
            "SBSP3": 40.0,
            "VIVT3": 48.0,
            "QUAL": 120.0,
            "VEA": 50.0,
            "IAU": 35.0,
            "XLP": 55.0,
            "BQUA39": 18.0,
            "ACWI11": 12.0,
            "GOLD11": 10.0,
            "BKXI39": 14.0,
            "HGLG11": 165.0,
            "KNRI11": 145.0,
            "BOVA11": 100.0,
        }
        base = base_map[data_source]
        return _fake_market_frame(start, end, base, 0.1)

    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_data",
        fake_get_data,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame({"rate": [0.0001]}),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_ipca_data",
        lambda **_: _stub_ipca(),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_monthly_ipca_rate",
        lambda *_args, **_kwargs: 0.004,
    )

    service = InvestmentComparisonService(data_dir=tmp_path / "investments")
    payload = service.compare(
        asset_ids=["SARDINHA40_ORIGINAL", "SARDINHA40_B3"],
        start_date="2021-01-04",
        end_date="2021-06-30",
        initial_capital=10000.0,
        monthly_contribution=500.0,
        benchmark_ids=["selic_cash"],
    )

    result_ids = {row["instrument_id"] for row in payload["results"]}
    assert result_ids == {"SARDINHA40_ORIGINAL", "SARDINHA40_B3"}
    assert all(row["source_kind"] == "model_portfolio" for row in payload["results"])
    assert all(row["invested_total"] == 12500.0 for row in payload["results"])
    assert payload["class_summary"][0]["category_label"] == "Carteiras guiadas"
    assert payload["catalog_snapshot"]["selected_assets"][0]["components"]
    assert payload["results"][0]["component_breakdown"]
    assert payload["chart"]["reference_series_id"] == "selic_cash"


def test_compare_allows_guided_portfolio_components_with_late_history(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
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
        base_map = {
            "IMAB11": 100.0,
            "IRFM11": 95.0,
            "ITUB4": 20.0,
            "BBSE3": 30.0,
            "TAEE11": 35.0,
            "SUZB3": 45.0,
            "FLRY3": 18.0,
            "SBSP3": 40.0,
            "VIVT3": 48.0,
            "BQUA39": 18.0,
            "ACWI11": 12.0,
            "GOLD11": 10.0,
            "BKXI39": 14.0,
            "HGLG11": 165.0,
            "KNRI11": 145.0,
        }
        delayed_start = "2021-05-28" if data_source == "BQUA39" else start
        return _fake_market_frame(delayed_start, end, base_map[data_source], 0.1)

    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_data",
        fake_get_data,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame({"rate": [0.0001]}),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_ipca_data",
        lambda **_: _stub_ipca(),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_monthly_ipca_rate",
        lambda *_args, **_kwargs: 0.004,
    )

    service = InvestmentComparisonService(data_dir=tmp_path / "investments")
    payload = service.compare(
        asset_ids=["SARDINHA40_B3"],
        start_date="2021-01-04",
        end_date="2021-06-30",
        initial_capital=10000.0,
        monthly_contribution=500.0,
        benchmark_ids=["selic_cash"],
    )

    assert len(payload["results"]) == 1
    result = payload["results"][0]
    assert result["instrument_id"] == "SARDINHA40_B3"
    assert result["availability_start"] == "2021-05-28"


def test_compare_supports_custom_portfolios_and_rate_proxies(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
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
            "WEGE3": _fake_market_frame(start, end, 40.0, 0.15),
            "BOVA11": _fake_market_frame(start, end, 100.0, 0.08),
        }
        return mapping[data_source]

    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_data",
        fake_get_data,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame(
            {"date": pd.date_range("2021-01-04", "2021-03-31", freq="B"), "rate": 0.0001}
        ),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_ipca_data",
        lambda **_: _stub_ipca(),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_monthly_ipca_rate",
        lambda *_args, **_kwargs: 0.004,
    )

    service = InvestmentComparisonService(data_dir=tmp_path / "investments")
    payload = service.compare(
        asset_ids=["WEGE3", "CDI_PROXY", "IPCA_PLUS_6_PROXY"],
        custom_portfolios=[
            {
                "label": "Minha carteira",
                "components": [
                    {"component_id": "WEGE3", "weight": 70},
                    {"component_id": "CDI_PROXY", "weight": 30},
                ],
            }
        ],
        start_date="2021-01-04",
        end_date="2021-03-31",
        initial_capital=10000.0,
        monthly_contribution=500.0,
        benchmark_ids=["selic_cash"],
    )

    result_ids = {row["instrument_id"] for row in payload["results"]}
    assert "CDI_PROXY" in result_ids
    assert "IPCA_PLUS_6_PROXY" in result_ids
    assert "CUSTOM_PORTFOLIO_minha_carteira" in result_ids
    custom_result = next(
        row
        for row in payload["results"]
        if row["instrument_id"] == "CUSTOM_PORTFOLIO_minha_carteira"
    )
    assert custom_result["source_kind"] == "custom_portfolio"
    assert len(custom_result["component_breakdown"]) == 2
    assert payload["request"]["custom_portfolios"][0]["label"] == "Minha carteira"


def test_compare_builds_fixed_income_duration_backtest(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_fixed_income_quotes",
        lambda instrument_id, **_: {
            "CDI_INDEX": _fixed_income_quotes("2018-01-02", "2024-03-29", 0.00018),
            "IDKA_PRE_2A": _fixed_income_quotes("2018-01-02", "2024-03-29", 0.00022),
            "IDKA_IPCA_2A": _fixed_income_quotes("2018-01-02", "2024-03-29", 0.00026),
            "IDKA_IPCA_5A": _fixed_income_quotes("2018-01-02", "2024-03-29", 0.00024),
        }[instrument_id],
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_ipca_data",
        lambda **_: _stub_ipca(),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_monthly_ipca_rate",
        lambda *_args, **_kwargs: 0.004,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame(
            {"date": pd.date_range("2018-01-02", "2024-03-29", freq="B"), "rate": 0.0001}
        ),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )

    service = InvestmentComparisonService(
        data_dir=tmp_path / "investments",
        fixed_income_dir=tmp_path / "fixed_income_indexes",
    )
    payload = service.compare(
        asset_ids=["CDI_INDEX", "IDKA_PRE_2A", "IDKA_IPCA_2A", "IDKA_IPCA_5A"],
        start_date="2018-01-02",
        end_date="2024-03-29",
        initial_capital=1000.0,
        monthly_contribution=0.0,
        benchmark_ids=[],
    )

    fixed_income = payload["fixed_income_backtest"]
    assert fixed_income is not None
    assert fixed_income["selected_study_id"] == "index_duration"
    assert fixed_income["studies"][0]["study_id"] == "index_duration"
    assert fixed_income["full_period"]["leaders"]["overall"]["instrument_id"] == "IDKA_IPCA_2A"
    assert fixed_income["full_period"]["leaders"]["prefixado"]["instrument_id"] == "IDKA_PRE_2A"
    assert fixed_income["full_period"]["leaders"]["ipca_plus"]["instrument_id"] == "IDKA_IPCA_2A"
    assert fixed_income["methodology"]["benchmark_instrument_id"] == "CDI_INDEX"
    assert fixed_income["methodology"]["window_frequency_effective"] == "monthly"
    assert any(
        row["window_years"] == 5 and row["instrument_id"] == "IDKA_IPCA_2A"
        for row in fixed_income["rolling_windows"]
    )


def test_compare_builds_retail_treasury_fixed_income_study(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_fixed_income_quotes",
        lambda instrument_id, **_: {
            "CDI_INDEX": _fixed_income_quotes("2018-01-02", "2024-03-29", 0.00018),
        }[instrument_id],
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_tesouro_direto_history",
        lambda **_: _tesouro_history_fixture("2018-01-02", "2024-03-29"),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_ipca_data",
        lambda **_: _stub_ipca(),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_monthly_ipca_rate",
        lambda *_args, **_kwargs: 0.004,
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_or_create_daily_selic_data",
        lambda **_: pd.DataFrame(
            {"date": pd.date_range("2018-01-02", "2024-03-29", freq="B"), "rate": 0.0001}
        ),
    )
    monkeypatch.setattr(
        "src.investing_workbench.application.investments.service.get_daily_rate",
        lambda *_args, **_kwargs: 0.0001,
    )

    service = InvestmentComparisonService(
        data_dir=tmp_path / "investments",
        fixed_income_dir=tmp_path / "fixed_income_indexes",
        tesouro_direto_dir=tmp_path / "tesouro_direto",
    )
    payload = service.compare(
        asset_ids=["TD_SELIC", "TD_PREFIXADO_2A", "TD_IPCA_2A"],
        start_date="2018-01-02",
        end_date="2024-03-29",
        initial_capital=1000.0,
        monthly_contribution=0.0,
        benchmark_ids=[],
        fixed_income_study_mode="retail_treasury",
        fixed_income_tax_treatment="net",
        fixed_income_window_frequency="monthly",
    )

    fixed_income = payload["fixed_income_backtest"]
    assert fixed_income is not None
    assert fixed_income["selected_study_id"] == "retail_treasury"
    assert fixed_income["methodology"]["benchmark_instrument_id"] == "CDI_INDEX"
    assert fixed_income["methodology"]["window_frequency_effective"] == "monthly"
    assert fixed_income["study_count"] == 1
    treasury_rows = [
        row
        for row in fixed_income["full_period"]["results"]
        if row["source_kind"] == "tesouro_direct_strategy"
    ]
    assert treasury_rows
    assert all("display_value" in row for row in treasury_rows)
    assert any(row["taxes_paid_total"] > 0 for row in treasury_rows)
    assert all(row["final_value_net"] <= row["final_value"] for row in treasury_rows)
    assert fixed_income["rolling_windows"]
    assert any(item["study_id"] == "retail_treasury" for item in fixed_income["studies"])
