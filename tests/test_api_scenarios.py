"""Focused API tests for dedicated scenario routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from tests.support import override_api_services

client = TestClient(app)


class _StubWege3ScenarioService:
    def run(
        self,
        *,
        start_date: str = "2021-01-01",
        end_date: str | None = None,
        force_download: bool = False,
    ) -> dict[str, object]:
        return {
            "scenario_id": "wege3_regra_a",
            "scenario_label": "WEGE3 Regra A",
            "generated_at": "2026-04-21T03:30:00Z",
            "request": {
                "start_date": start_date,
                "end_date": end_date,
                "force_download": force_download,
            },
            "assumptions": {"cash_yield_timing": "end_of_bar"},
            "dataset": {"start_session": "2021-01-04", "end_session": "2026-04-20"},
            "result": {"saldo_final_total": 84951.82},
            "statistics": {"numero_total_compras": 225},
            "benchmarks": {
                "benchmark_a_10000_wege3_30000_caixa": {"final_total": 81033.49},
            },
            "audit": {"trade_csv_path": "reports/wege3.csv"},
            "comparison_variants": [],
            "best_strategy": {},
            "parameter_search": {},
            "strategy_context": {},
            "comparison_chart": {"series": [], "points": [], "reference_series_id": "selic_cash"},
            "trades": [
                {
                    "timestamp": "2021-01-04",
                    "action": "BUY",
                    "price": 37.92,
                    "notional": 10000.0,
                    "quantity": 263.67,
                    "cash_after": 30000.0,
                    "position_after": 263.67,
                    "reference_after": 37.92,
                }
            ],
            "artifacts": {
                "summary_output_path": "reports/wege3_summary.json",
                "trades_output_path": "reports/wege3.csv",
                "comparison_output_path": "reports/wege3_comparison.csv",
                "comparison_trades_output_path": "reports/wege3_comparison_trades.csv",
                "search_output_path": "reports/wege3_search.csv",
            },
            "reproduction_command": "./.venv/bin/python -m src.bitcoin_martingale.application.scenarios.wege3_regra_a",
        }


class _ErrorWege3ScenarioService(_StubWege3ScenarioService):
    def run(
        self,
        *,
        start_date: str = "2021-01-01",
        end_date: str | None = None,
        force_download: bool = False,
    ) -> dict[str, object]:
        raise ValueError("Scenario dataset unavailable")


def test_wege3_regra_a_route_uses_current_service_container() -> None:
    with override_api_services(wege3_regra_a_service=_StubWege3ScenarioService()):
        response = client.post(
            "/scenarios/wege3-regra-a",
            json={"start_date": "2021-01-01", "force_download": True},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] == "wege3_regra_a"
    assert payload["request"]["force_download"] is True
    assert payload["result"]["saldo_final_total"] == 84951.82
    assert payload["trades"][0]["action"] == "BUY"


def test_wege3_regra_a_route_translates_value_errors() -> None:
    with override_api_services(wege3_regra_a_service=_ErrorWege3ScenarioService()):
        response = client.post("/scenarios/wege3-regra-a", json={})

    assert response.status_code == 400
    assert "Scenario dataset unavailable" in response.json()["detail"]
