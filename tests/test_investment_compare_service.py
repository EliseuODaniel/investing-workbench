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
    assert payload["methodology_guide"]["title"] == "Como ler este estudo"
    assert any(
        item["kind"] == "listed_security" for item in payload["methodology_guide"]["evidence_types"]
    )
    assert payload["product_realism"]["title"] == "Realismo do produto investivel"
    assert any(
        item["dimension_id"] == "investable_product"
        for item in payload["product_realism"]["coverage"]
    )
    assert any(
        item["source_kind"] == "listed_security"
        for item in payload["product_realism"]["product_types"]
    )
    assert any(
        item["policy_id"] == "stocks_dividends_jcp"
        for item in payload["product_realism"]["income_policy_examples"]
    )
    assert any(
        item["policy_id"] == "fiis_monthly_income"
        for item in payload["product_realism"]["income_policy_examples"]
    )
    assert (
        payload["retail_fixed_income_equivalence"]["title"]
        == "Equivalencia liquida em renda fixa de varejo"
    )
    assert payload["retail_fixed_income_equivalence"]["rows"]
    assert any(
        row["tax_exempt_product"] == "Debenture incentivada"
        for row in payload["retail_fixed_income_equivalence"]["rows"]
    )
    assert any(
        row["equivalent_cdb_pct_cdi"] > row["tax_exempt_pct_cdi"]
        for row in payload["retail_fixed_income_equivalence"]["rows"]
        if row["holding_days"] >= 180
    )
    taxable_examples = payload["retail_fixed_income_equivalence"]["taxable_product_examples"]
    assert any(item["product_id"] == "tesouro_selic_proxy" for item in taxable_examples)
    assert any(item["product_id"] == "fundo_di_100_fee" for item in taxable_examples)
    assert all(item["net_pct_cdi"] < item["gross_pct_cdi"] for item in taxable_examples)
    assert payload["result_stories"]["title"] == "Leituras guiadas do resultado"
    assert any(
        item["story_id"] == "best_profile_match" for item in payload["result_stories"]["stories"]
    )
    assert any(item["story_id"] == "beat_selic" for item in payload["result_stories"]["stories"])
    assert any(item["ranking_id"] == "real_cagr" for item in payload["result_stories"]["rankings"])
    assert any(
        item["ranking_id"] == "income_generation" for item in payload["result_stories"]["rankings"]
    )
    assert any(
        item["ranking_id"] == "mark_to_market_stress"
        for item in payload["result_stories"]["rankings"]
    )
    assert payload["market_rankings"]["title"] == "Rankings de mercado"
    assert payload["market_rankings"]["benchmark_context"]
    assert any(
        item["ranking_id"] == "guided_factor_score"
        for item in payload["market_rankings"]["rankings"]
    )
    assert any(
        item["ranking_id"] == "momentum_6m" for item in payload["market_rankings"]["rankings"]
    )
    assert any(
        item["ranking_id"] == "ath_distance" for item in payload["market_rankings"]["rankings"]
    )
    assert any(
        item["ranking_id"] == "beta_to_benchmark" for item in payload["market_rankings"]["rankings"]
    )
    assert payload["market_screeners"]["title"] == "Screeners do universo comparado"
    assert any(
        item["preset_id"] == "positive_real_return"
        for item in payload["market_screeners"]["presets"]
    )
    assert all(
        "methodology" in item and item["rows"] for item in payload["market_rankings"]["rankings"]
    )
    assert "ranking_id" in payload["market_rankings"]["export_columns"]
    assert payload["cache_status"]["title"] == "Cache e preparacao dos dados"
    assert any(item["cache_id"] == "listed_assets" for item in payload["cache_status"]["caches"])
    assert all("freshness_status" in item for item in payload["cache_status"]["caches"])
    assert all("refresh_hint" in item for item in payload["cache_status"]["caches"])
    assert payload["study_quality"]["title"] == "Fechamento do estudo"
    assert payload["study_quality"]["readiness_score"] == 1.0
    assert all(item["status"] == "complete" for item in payload["study_quality"]["checks"])
    assert payload["portfolio_objective_summary"]["title"] == "Decisao por objetivo"
    assert payload["portfolio_lifecycle"]["title"] == "Cenarios completos de carteira"
    assert any(
        item["scenario_id"] == "real_monthly_withdrawal"
        for item in payload["portfolio_lifecycle"]["scenario_cards"]
    )
    assert (
        payload["portfolio_lifecycle"]["withdrawal_plan"]["title"]
        == "Plano didatico de retirada"
    )
    assert payload["portfolio_lifecycle"]["withdrawal_plan"]["candidates"]
    assert payload["portfolio_lifecycle"]["withdrawal_plan"]["stress_tests"]
    assert any(
        item["scenario_id"] == "sequence_stress"
        for item in payload["portfolio_lifecycle"]["withdrawal_plan"]["stress_tests"]
    )
    assert (
        payload["portfolio_lifecycle"]["withdrawal_plan"]["monte_carlo_preview"]["title"]
        == "Previa Monte Carlo"
    )
    assert any(
        item["scenario_id"] == "p10_adverse"
        for item in payload["portfolio_lifecycle"]["withdrawal_plan"]["monte_carlo_preview"][
            "scenarios"
        ]
    )
    monthly_sequence = payload["portfolio_lifecycle"]["withdrawal_plan"][
        "monte_carlo_preview"
    ]["monthly_sequence"]
    assert monthly_sequence["title"] == "Simulacao mensal de exaustao"
    assert monthly_sequence["horizon_years"] == 30
    assert any(item["path_id"] == "adverse_sequence" for item in monthly_sequence["paths"])
    stochastic = monthly_sequence["stochastic"]
    assert stochastic["title"] == "Monte Carlo estocastico mensal"
    assert stochastic["simulation_count"] == 250
    assert 0 <= stochastic["success_rate"] <= 1
    assert stochastic["percentiles"]["final_balance_p10"] <= stochastic["percentiles"][
        "final_balance_p90"
    ]
    assert payload["request"]["decision_profile"]["objective"] == "balanced"
    assert any(
        item["objective_id"] == "protect_purchasing_power"
        for item in payload["portfolio_objective_summary"]["objectives"]
    )
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


def test_catalog_exposes_ntnb_etfs_preset(tmp_path: Any) -> None:
    service = InvestmentComparisonService(data_dir=tmp_path / "investments")

    payload = service.list_catalog()
    visible_ids = {item["instrument_id"] for item in payload["instruments"]}
    preset = next(
        item for item in payload["presets"] if item["preset_id"] == "fixed_income_ntnb_etfs"
    )

    assert {"IMAB11", "IMBB11", "B5P211", "B5MB11"} <= visible_ids
    assert {"HASH11", "VISC11", "KNCR11", "AMZO34", "TSLA34"} <= visible_ids
    profiles = {item["instrument_id"]: item["product_profile"] for item in payload["instruments"]}
    assert profiles["HGLG11"]["investment_type_label"] == "FII listado"
    assert "isentos" in profiles["HGLG11"]["tax_treatment_label"]
    assert profiles["TD_SELIC"]["investment_type_label"] == "Tesouro Direto"
    assert (
        profiles["CDI_INDEX"]["investability_label"]
        == "Referencia teorica, nao produto de prateleira."
    )
    assert profiles["PETR4"]["investment_type_label"] == "Acao listada"
    assert preset["asset_ids"] == ["IMAB11", "IMBB11", "B5P211", "B5MB11"]
    assert preset["default_benchmark_ids"] == ["selic_cash"]
    assert preset["default_start_date"] == "2020-11-16"
    assert any(item["preset_id"] == "fii_income_ladder" for item in payload["presets"])
    assert any(item["preset_id"] == "global_bdr_growth" for item in payload["presets"])
    assert payload["market_explorer"]["title"] == "Explorador de mercado"
    assert payload["market_explorer"]["category_lists"]
    assert any(
        item["list_id"] == "monthly_income_candidates"
        for item in payload["market_explorer"]["curated_lists"]
    )
    assert any(
        item["list_id"] == "risk_ladder" for item in payload["market_explorer"]["curated_lists"]
    )
    assert any(
        item["ranking_id"] == "drawdown" for item in payload["market_explorer"]["ranking_backlog"]
    )
    assert any(
        item["ranking_id"] == "final_value"
        for item in payload["market_explorer"]["ranking_backlog"]
    )
    assert any(
        item["ranking_id"] == "real_cagr" for item in payload["market_explorer"]["ranking_backlog"]
    )
    assert any(
        item["ranking_id"] == "income_generation"
        for item in payload["market_explorer"]["ranking_backlog"]
    )
    assert payload["product_data_plan"]["title"] == "Plano pos-roadmap de dados de produto"
    assert any(
        source["source_id"] == "tesouro_transparente"
        and source["integration_status"] == "connected"
        for source in payload["product_data_plan"]["sources"]
    )
    assert any(
        row["family_id"] == "fiis" and row["external_data_status"] == "connected_seeded"
        for row in payload["product_data_plan"]["family_coverage"]
    )
    assert payload["product_data_plan"]["roadmap_completion_pct"] == 1.0
    assert payload["product_data_plan"]["next_release_candidates"][0]["release_id"] == (
        "fii_income_data"
    )
    assert payload["product_data_plan"]["source_manifest"]["title"] == (
        "Manifesto local de dados externos"
    )
    assert payload["product_data_plan"]["source_manifest"]["source_count"] == 4
    assert any(
        item["step_id"] == "dataset_versioning"
        and item["status"] == "manifest_available"
        for item in payload["product_data_plan"]["roadmap_steps"]
    )
    assert any(
        item["release_id"] == "etf_bdr_fee_tracking"
        for item in payload["product_data_plan"]["next_release_candidates"]
    )
    assert any(
        item["filter_id"] == "liquidity"
        for item in payload["product_data_plan"]["market_filter_backlog"]
    )
    assert any(
        item["gate_id"] == "cache_manifest"
        for item in payload["product_data_plan"]["validation_plan"]
    )
    assert payload["investor_easy_parity"]["calculator_count"] == 15
    assert payload["investor_easy_parity"]["available_calculator_count"] == 15
    assert any(
        item["feature_id"] == "automatic_alerts" and item["local_status"] == "partial"
        for item in payload["investor_easy_parity"]["feature_coverage"]
    )
    assert any(
        item["calculator_id"] == "financial_independence"
        for item in payload["investor_easy_parity"]["calculator_suite"]
    )


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
        decision_profile={
            "objective": "income",
            "horizon_years": 12,
            "liquidity_need": "long_term",
            "mark_to_market_tolerance": "medium",
            "tax_view": "net",
            "monthly_income_target": 25.0,
        },
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
    assert payload["portfolio_objective_summary"]["portfolio_rows"]
    assert payload["portfolio_objective_summary"]["decision_profile"]["objective"] == "income"
    assert payload["portfolio_objective_summary"]["scenario_cards"][0]["target_value"] == 25.0
    assert any(
        item["objective_id"] == "compare_allocation"
        for item in payload["portfolio_objective_summary"]["objectives"]
    )


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
    assert payload["fixed_income_decision_guide"]["title"] == "Como decidir em renda fixa"
    assert any(
        item["decision_id"] == "real_return"
        for item in payload["fixed_income_decision_guide"]["decision_cards"]
    )
    assert payload["fixed_income_decision_guide"]["decision_cards"][0]["fit_label"]
    assert payload["portfolio_objective_summary"]["fixed_income_study_available"] is True


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
    tax_realism = next(
        item for item in payload["product_realism"]["coverage"] if item["dimension_id"] == "taxes"
    )
    assert tax_realism["status"] == "partial"
    assert any("IR regressivo" in item for item in tax_realism["current_scope"])
    assert any(
        item["policy_id"] == "treasury_cashflows"
        for item in payload["product_realism"]["income_policy_examples"]
    )
    assert fixed_income["rolling_windows"]
    assert any(item["study_id"] == "retail_treasury" for item in fixed_income["studies"])
    assert payload["fixed_income_decision_guide"]["decision_cards"]
