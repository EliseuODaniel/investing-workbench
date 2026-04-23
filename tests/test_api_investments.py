"""API tests for the B3 investment comparison routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from src.api.main import app
from tests.support import override_api_services

client = TestClient(app)


class _StubInvestmentComparisonService:
    def list_catalog(self) -> dict[str, object]:
        return {
            "generated_at": datetime(2026, 4, 21, 12, 0, tzinfo=UTC),
            "categories": [{"category_id": "stocks_brazil", "label": "Acoes", "count": 1}],
            "instruments": [{"instrument_id": "PETR4", "label": "PETR4"}],
            "presets": [
                {
                    "preset_id": "first_steps",
                    "label": "Primeiros passos",
                    "default_benchmark_ids": [],
                }
            ],
            "benchmark_options": [{"benchmark_id": "selic_cash", "label": "SELIC / caixa"}],
            "notes": ["Catalogo didatico para comparacoes B3."],
            "sources": [{"label": "B3", "url": "https://www.b3.com.br/"}],
        }

    def compare(
        self,
        *,
        asset_ids: list[str],
        custom_portfolios: list[dict[str, object]],
        start_date: str,
        end_date: str | None,
        initial_capital: float,
        monthly_contribution: float,
        benchmark_ids: list[str] | None,
        fixed_income_study_mode: str,
        fixed_income_tax_treatment: str,
        fixed_income_window_frequency: str,
        force_download: bool,
    ) -> dict[str, object]:
        return {
            "generated_at": datetime(2026, 4, 21, 12, 5, tzinfo=UTC),
            "request": {
                "asset_ids": asset_ids,
                "custom_portfolios": custom_portfolios,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "monthly_contribution": monthly_contribution,
                "benchmark_ids": benchmark_ids or [],
                "fixed_income_study_mode": fixed_income_study_mode,
                "fixed_income_tax_treatment": fixed_income_tax_treatment,
                "fixed_income_window_frequency": fixed_income_window_frequency,
                "force_download": force_download,
            },
            "catalog_snapshot": {"categories": [], "selected_assets": [], "presets": []},
            "assumptions": ["Mesma agenda de aportes para todos os ativos."],
            "results": [
                {
                    "instrument_id": "PETR4",
                    "label": "PETR4",
                    "final_value": 14500.0,
                    "invested_total": 12000.0,
                    "final_value_real": 13100.0,
                    "invested_total_real": 11500.0,
                    "net_profit": 2500.0,
                    "net_profit_real": 1600.0,
                    "cagr": 0.18,
                    "real_cagr": 0.11,
                    "annual_volatility": 0.22,
                    "max_drawdown": -0.12,
                    "availability_start": "2021-01-04",
                    "availability_end": "2026-04-21",
                    "final_value_net": 14500.0,
                    "net_profit_net": 2500.0,
                    "cagr_net": 0.18,
                    "final_value_real_net": 13100.0,
                    "net_profit_real_net": 1600.0,
                    "real_cagr_net": 0.11,
                    "total_return_on_invested": 0.2083,
                    "real_total_return_on_invested": 0.1391,
                    "time_weighted_return": 0.81,
                    "real_time_weighted_return": 0.54,
                    "description": "desc",
                    "rationale": "why",
                    "risk_label": "Alta",
                    "region_label": "Brasil",
                    "category_id": "stocks_brazil",
                    "category_label": "Acoes brasileiras",
                    "source_kind": "listed_security",
                    "component_breakdown": [],
                    "category_breakdown": [],
                }
            ],
            "benchmarks": [
                {
                    "benchmark_id": "selic_cash",
                    "label": "SELIC / caixa",
                    "final_value": 12800.0,
                    "final_value_real": 11900.0,
                    "invested_total": 12000.0,
                    "invested_total_real": 11500.0,
                    "net_profit": 800.0,
                    "net_profit_real": 400.0,
                    "cagr": 0.09,
                    "real_cagr": 0.03,
                    "annual_volatility": 0.01,
                    "max_drawdown": 0.0,
                    "availability_start": "2021-01-04",
                    "availability_end": "2026-04-21",
                    "final_value_net": 12800.0,
                    "net_profit_net": 800.0,
                    "cagr_net": 0.09,
                    "final_value_real_net": 11900.0,
                    "net_profit_real_net": 400.0,
                    "real_cagr_net": 0.03,
                    "total_return_on_invested": 0.066,
                    "real_total_return_on_invested": 0.034,
                    "time_weighted_return": 0.25,
                    "real_time_weighted_return": 0.11,
                    "description": "desc",
                    "rationale": "why",
                    "risk_label": "Baixa",
                    "region_label": "Brasil",
                    "category_id": "fixed_income_b3",
                    "category_label": "Renda fixa / juros na B3",
                    "source_kind": "selic_proxy",
                    "component_breakdown": [],
                    "category_breakdown": [],
                    "equity_curve": [{"date": "2021-01-04", "equity": 10000.0}],
                }
            ],
            "chart": {
                "reference_series_id": "selic_cash",
                "series": [
                    {"id": "PETR4", "label": "PETR4", "color": "#f97316"},
                    {"id": "selic_cash", "label": "SELIC / caixa", "color": "#10b981"},
                ],
                "points": [{"date": "2021-01-04", "PETR4": 10000.0, "selic_cash": 10000.0}],
            },
            "real_chart": {
                "reference_series_id": "selic_cash",
                "series": [
                    {"id": "PETR4", "label": "PETR4", "color": "#f97316"},
                    {"id": "selic_cash", "label": "SELIC / caixa", "color": "#10b981"},
                ],
                "points": [{"date": "2021-01-04", "PETR4": 10000.0, "selic_cash": 10000.0}],
            },
            "inflation": {
                "label": "IPCA acumulado",
                "accumulated_rate": 0.12,
                "purchasing_power_loss": 0.1,
                "availability_start": "2021-01-01",
                "availability_end": "2026-04-21",
                "source_label": "Banco Central do Brasil / SGS 433",
            },
            "class_summary": [
                {
                    "category_label": "Acoes brasileiras",
                    "asset_count": 1,
                    "average_final_value": 14500.0,
                    "average_cagr": 0.18,
                    "average_real_cagr": 0.11,
                    "average_max_drawdown": -0.12,
                    "leader_label": "PETR4",
                }
            ],
            "highlights": {
                "best_final_value": {"instrument_id": "PETR4", "label": "PETR4"},
                "most_defensive": {"instrument_id": "PETR4", "label": "PETR4"},
                "beats_selic_count": 1,
                "beats_bova11_count": 1,
                "beats_inflation_count": 1,
                "insights": ["PETR4 superou a SELIC no periodo."],
            },
            "fixed_income_backtest": {
                "requested_study_mode": fixed_income_study_mode,
                "tax_treatment": fixed_income_tax_treatment,
                "window_frequency": fixed_income_window_frequency,
                "methodology": {
                    "benchmark_instrument_id": "CDI_INDEX",
                    "benchmark_label": "CDI",
                    "series_source_label": "Mais Retorno API publica / indices de renda fixa",
                    "index_methodology_label": "ANBIMA IDkA para durations constantes",
                    "rolling_window_note": "Janelas moveis por indices",
                    "full_period_note": "Acumulado com mesmo fluxo",
                    "selected_fixed_income_ids": ["CDI_INDEX"],
                    "video_reference_match": False,
                },
                "full_period": {"results": []},
                "rolling_windows": [],
                "takeaways": [],
            },
            "warnings": [],
        }


class _ErrorInvestmentComparisonService(_StubInvestmentComparisonService):
    def compare(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        raise ValueError("Comparativo indisponivel")


def test_investments_catalog_route_uses_current_service_container() -> None:
    with override_api_services(
        investment_comparison_service=_StubInvestmentComparisonService(),
    ):
        response = client.get("/investments/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"][0]["category_id"] == "stocks_brazil"
    assert payload["presets"][0]["preset_id"] == "first_steps"


def test_investments_compare_route_uses_current_service_container() -> None:
    with override_api_services(
        investment_comparison_service=_StubInvestmentComparisonService(),
    ):
        response = client.post(
            "/investments/compare",
            json={
                "asset_ids": ["PETR4"],
                "custom_portfolios": [
                    {
                        "label": "Minha carteira",
                        "components": [
                            {"component_id": "PETR4", "weight": 60},
                            {"component_id": "BOVA11", "weight": 40},
                        ],
                    }
                ],
                "start_date": "2021-01-01",
                "initial_capital": 10000,
                "monthly_contribution": 500,
                "benchmark_ids": ["selic_cash"],
                "force_download": True,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request"]["asset_ids"] == ["PETR4"]
    assert payload["request"]["custom_portfolios"][0]["label"] == "Minha carteira"
    assert payload["request"]["fixed_income_study_mode"] == "auto"
    assert payload["request"]["fixed_income_tax_treatment"] == "gross"
    assert payload["request"]["fixed_income_window_frequency"] == "monthly"
    assert payload["chart"]["reference_series_id"] == "selic_cash"
    assert payload["results"][0]["label"] == "PETR4"
    assert payload["fixed_income_backtest"]["methodology"]["benchmark_instrument_id"] == "CDI_INDEX"


def test_investments_compare_route_translates_value_errors() -> None:
    with override_api_services(
        investment_comparison_service=_ErrorInvestmentComparisonService(),
    ):
        response = client.post(
            "/investments/compare",
            json={"asset_ids": ["PETR4"]},
        )

    assert response.status_code == 400
    assert "Comparativo indisponivel" in response.json()["detail"]
