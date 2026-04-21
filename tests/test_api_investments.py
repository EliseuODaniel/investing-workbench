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
            "presets": [{"preset_id": "first_steps", "label": "Primeiros passos"}],
            "benchmark_options": [{"benchmark_id": "selic_cash", "label": "SELIC / caixa"}],
            "notes": ["Catalogo didatico para comparacoes B3."],
            "sources": [{"label": "B3", "url": "https://www.b3.com.br/"}],
        }

    def compare(
        self,
        *,
        asset_ids: list[str],
        start_date: str,
        end_date: str | None,
        initial_capital: float,
        monthly_contribution: float,
        benchmark_ids: list[str] | None,
        force_download: bool,
    ) -> dict[str, object]:
        return {
            "generated_at": datetime(2026, 4, 21, 12, 5, tzinfo=UTC),
            "request": {
                "asset_ids": asset_ids,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "monthly_contribution": monthly_contribution,
                "benchmark_ids": benchmark_ids or [],
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
                }
            ],
            "benchmarks": [
                {
                    "benchmark_id": "selic_cash",
                    "label": "SELIC / caixa",
                    "final_value": 12800.0,
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
            "class_summary": [
                {
                    "category_label": "Acoes brasileiras",
                    "asset_count": 1,
                    "average_final_value": 14500.0,
                    "average_cagr": 0.18,
                    "average_max_drawdown": -0.12,
                    "leader_label": "PETR4",
                }
            ],
            "highlights": {
                "best_final_value": {"instrument_id": "PETR4", "label": "PETR4"},
                "most_defensive": {"instrument_id": "PETR4", "label": "PETR4"},
                "beats_selic_count": 1,
                "beats_bova11_count": 1,
                "insights": ["PETR4 superou a SELIC no periodo."],
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
    assert payload["chart"]["reference_series_id"] == "selic_cash"
    assert payload["results"][0]["label"] == "PETR4"


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
