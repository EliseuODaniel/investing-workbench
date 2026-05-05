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
            "market_explorer": {
                "title": "Explorador de mercado",
                "plain_language_summary": "Listas e facetas do catalogo.",
                "category_lists": [],
                "product_type_facets": [],
                "risk_facets": [],
                "region_facets": [],
                "ranking_backlog": [
                    {
                        "ranking_id": "guided_factor_score",
                        "label": "Score fatorial guiado",
                        "status": "available_in_market_rankings",
                    }
                ],
            },
            "product_data_plan": {
                "title": "Plano pos-roadmap de dados de produto",
                "plain_language_summary": "Fontes oficiais e cobertura por familia.",
                "status": "post_roadmap",
                "source_count": 1,
                "connected_source_count": 0,
                "partial_source_count": 1,
                "sources": [
                    {
                        "source_id": "b3_listed_products",
                        "label": "B3 - Produtos listados",
                        "url": "https://www.b3.com.br/",
                        "coverage": "Produtos listados e dados publicos.",
                        "freshness_policy": "refresh sob demanda",
                        "integration_status": "partial",
                        "families": ["stocks_brazil"],
                    }
                ],
                "family_coverage": [
                    {
                        "family_id": "stocks_brazil",
                        "label": "Acoes",
                        "instrument_count": 1,
                        "product_profile_count": 1,
                        "coverage_score": 1.0,
                        "external_data_status": "partial",
                    }
                ],
                "implementation_steps": ["Criar inventario de fontes oficiais."],
                "next_release_candidates": [
                    {
                        "release_id": "etf_fee_tracking",
                        "label": "ETFs/BDRs: taxa e tracking",
                        "source_ids": ["b3_listed_products"],
                        "user_value": "Mostrar diferenca entre indice e produto investivel.",
                    }
                ],
                "quality_gate": ["Fonte primaria ou secundaria marcada."],
            },
            "notes": ["Catalogo didatico para comparacoes B3."],
            "sources": [{"label": "B3", "url": "https://www.b3.com.br/"}],
        }


    def refresh_source(self, *, source_id: str, force: bool = False) -> dict[str, object]:
        return {
            "source_id": source_id,
            "status": "refreshed" if force else "cache_hit",
            "status_label": "cache atualizado" if force else "cache reaproveitado",
            "message": "Refresh controlado executado.",
            "manifest": {
                "source_id": source_id,
                "schema_version": "b3_fii_listed.v1",
                "row_count": 5,
                "checksum_sha256": "abc123",
            },
            "history": [
                {
                    "ran_at": "2026-05-04T12:00:00Z",
                    "source_id": source_id,
                    "status": "refreshed",
                    "status_label": "cache atualizado",
                    "message": "Refresh controlado executado.",
                    "row_count": 5,
                }
            ],
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
        decision_profile: dict[str, object],
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
                "decision_profile": decision_profile,
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
            "product_realism": {
                "title": "Realismo do produto investivel",
                "plain_language_summary": "Classifica indice, proxy e produto real.",
                "product_types": [{"source_kind": "listed_security", "label": "Ativo", "count": 1}],
                "coverage": [
                    {
                        "dimension_id": "investable_product",
                        "label": "Indice, proxy ou produto real",
                        "status": "partial",
                        "status_label": "parcial",
                        "summary": "Ha ativos compraveis e referencias.",
                        "current_scope": ["Ativo: 1"],
                        "limitations": "Ainda ha aproximacoes.",
                        "next_step": "Adicionar equivalentes investiveis.",
                    }
                ],
                "next_methodology_steps": ["Separar retorno bruto e liquido."],
            },
            "retail_fixed_income_equivalence": {
                "title": "Equivalencia liquida em renda fixa de varejo",
                "plain_language_summary": "Compara CDB tributado com LCI/LCA isenta.",
                "reference_cdi_annual_rate": 0.105,
                "profile_horizon_days": 3650,
                "profile_horizon_label": "10 ano(s)",
                "uses_fixed_income_backtest": True,
                "rows": [
                    {
                        "holding_days": 720,
                        "holding_years": 1.97,
                        "tax_exempt_product": "LCI/LCA",
                        "tax_exempt_pct_cdi": 0.9,
                        "tax_exempt_annual_rate": 0.0945,
                        "ir_rate": 0.175,
                        "iof_rate": 0.0,
                        "net_gain_retention": 0.825,
                        "equivalent_cdb_pct_cdi": 1.08,
                        "equivalent_cdb_annual_rate": 0.1134,
                        "interpretation": "Uma LCI/LCA a 90% do CDI equivale a CDB maior.",
                    }
                ],
                "assumptions": ["Sem ofertas reais."],
                "next_steps": ["Adicionar CDB e LCI/LCA editaveis."],
            },
            "result_stories": {
                "title": "Leituras guiadas do resultado",
                "plain_language_summary": "Perguntas praticas sobre o resultado.",
                "stories": [
                    {
                        "story_id": "beat_selic",
                        "label": "Quem bateu a Selic",
                        "question": "Quantas escolhas compensaram sair do caixa?",
                        "winner_id": None,
                        "winner_label": None,
                        "metric_label": "Acima da Selic",
                        "metric_value": 1,
                        "metric_kind": "count",
                        "interpretation": "1 de 1 comparativos terminou acima da Selic.",
                        "caveat": "Bater a Selic nao basta.",
                    }
                ],
                "rankings": [
                    {
                        "ranking_id": "final_value",
                        "label": "Ranking por valor final",
                        "metric_label": "Valor final",
                        "metric_kind": "currency",
                        "rows": [
                            {
                                "rank": 1,
                                "instrument_id": "PETR4",
                                "label": "PETR4",
                                "category_label": "Acoes brasileiras",
                                "value": 14500.0,
                            }
                        ],
                    }
                ],
                "next_questions": ["O risco fez sentido?"],
            },
            "market_rankings": {
                "title": "Rankings de mercado",
                "plain_language_summary": "Rankings exportaveis do universo selecionado.",
                "universe_label": "1 alternativa selecionada",
                "as_of_date": "2026-04-21",
                "source_label": "Dados locais/cacheados do Investing Workbench",
                "benchmark_context": [
                    {
                        "benchmark_id": "selic_cash",
                        "label": "SELIC / caixa",
                        "metric_label": "Alternativas acima",
                        "metric_kind": "count",
                        "value": 1,
                        "total": 1,
                        "interpretation": "1 de 1 alternativas terminaram acima da Selic.",
                    }
                ],
                "rankings": [
                    {
                        "ranking_id": "guided_factor_score",
                        "label": "Score fatorial guiado",
                        "metric_label": "Score",
                        "metric_kind": "percent",
                        "methodology": "Combina retorno real e risco.",
                        "rows": [
                            {
                                "rank": 1,
                                "instrument_id": "PETR4",
                                "label": "PETR4",
                                "category_label": "Acoes brasileiras",
                                "source_kind": "listed_security",
                                "risk_label": "Alta",
                                "value": 1.0,
                                "secondary_value": 0.11,
                            }
                        ],
                    }
                ],
                "export_columns": ["ranking_id", "rank", "instrument_id", "value"],
                "methodology_notes": ["Universo selecionado no estudo atual."],
                "generated_at": "2026-04-21T12:05:00+00:00",
            },
            "market_screeners": {
                "title": "Screeners do universo comparado",
                "plain_language_summary": "Filtros reutilizaveis do universo selecionado.",
                "universe_count": 1,
                "presets": [
                    {
                        "preset_id": "positive_real_return",
                        "label": "Retorno real positivo",
                        "rule_summary": "CAGR real acima de zero.",
                        "matched_count": 1,
                        "universe_count": 1,
                        "sort_key": "real_cagr",
                        "rows": [
                            {
                                "rank": 1,
                                "instrument_id": "PETR4",
                                "label": "PETR4",
                                "category_label": "Acoes brasileiras",
                                "real_cagr": 0.11,
                                "max_drawdown": -0.12,
                                "annual_volatility": 0.22,
                                "net_profit": 2500.0,
                            }
                        ],
                    }
                ],
                "methodology_notes": ["Cada screener declara a regra."],
            },
            "cache_status": {
                "title": "Cache e preparacao dos dados",
                "plain_language_summary": "Mostra preparo local.",
                "status": "warm",
                "status_label": "cache preparado",
                "checked_at": datetime(2026, 4, 21, 12, 5, tzinfo=UTC),
                "caches": [
                    {
                        "cache_id": "listed_assets",
                        "label": "Ativos listados",
                        "path": "data/investments",
                        "exists": True,
                        "file_count": 1,
                        "total_size_bytes": 1024,
                        "latest_file_at": "2026-04-21T12:00:00+00:00",
                        "status": "warm",
                        "status_label": "com arquivos locais",
                        "cold_start_note": "Pode baixar series historicas.",
                        "used_in_current_result": True,
                    }
                ],
                "takeaways": ["Cache local reduz cold start."],
            },
            "portfolio_lifecycle": {
                "title": "Cenarios completos de carteira",
                "plain_language_summary": "Cenarios de retirada e aposentadoria.",
                "uses_portfolio_rows": False,
                "portfolio_count": 0,
                "scenario_cards": [
                    {
                        "scenario_id": "real_monthly_withdrawal",
                        "label": "Retirada mensal real estimada",
                        "description": "Regra didatica de retirada.",
                        "best_match_id": "PETR4",
                        "best_match_label": "PETR4",
                        "metric_label": "Renda mensal real estimada",
                        "metric_value": 43.67,
                        "metric_kind": "currency",
                        "target_value": 3000.0,
                        "target_met": False,
                    }
                ],
                "assumptions": ["Retirada mensal usa regra didatica."],
                "next_steps": ["Adicionar risco de exaustao."],
            },
            "warnings": [],
        }

    def build_market_rankings_snapshot(self, **kwargs: object) -> dict[str, object]:
        return {
            "generated_at": datetime(2026, 4, 21, 12, 10, tzinfo=UTC),
            "request": kwargs,
            "market_rankings": {
                "title": "Rankings de mercado",
                "rankings": [{"ranking_id": "momentum_6m", "rows": []}],
            },
            "market_screeners": {"title": "Screeners do universo comparado", "presets": []},
            "cache_status": {"title": "Cache e preparacao dos dados", "caches": []},
            "warnings": [],
        }


class _ErrorInvestmentComparisonService(_StubInvestmentComparisonService):
    def compare(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        raise ValueError("Comparativo indisponivel")


class _StubProductDataSourceService:
    def refresh_source(self, *, source_id: str, force: bool = False) -> dict[str, object]:
        return {
            "source_id": source_id,
            "status": "refreshed" if force else "cache_hit",
            "status_label": "cache atualizado" if force else "cache reaproveitado",
            "message": "Refresh controlado executado.",
            "manifest": {
                "source_id": source_id,
                "schema_version": "b3_fii_listed.v1",
                "row_count": 5,
                "checksum_sha256": "abc123",
            },
            "history": [
                {
                    "ran_at": "2026-05-04T12:00:00Z",
                    "source_id": source_id,
                    "status": "refreshed",
                    "status_label": "cache atualizado",
                    "message": "Refresh controlado executado.",
                    "row_count": 5,
                }
            ],
        }


class _StubInvestmentWorkspaceService:
    def __init__(self) -> None:
        self.portfolios: list[dict[str, object]] = []
        self.pairs_radar: list[dict[str, object]] = []
        self.strategy_radar: list[dict[str, object]] = []
        self.strategy_setup_runs: list[dict[str, object]] = []

    def list_portfolios(self) -> list[dict[str, object]]:
        return self.portfolios

    def save_portfolio(self, payload: dict[str, object]) -> dict[str, object]:
        saved = {
            **payload,
            "portfolio_id": payload.get("portfolio_id") or "portfolio_1",
            "created_at": "2026-04-27T12:00:00Z",
            "updated_at": "2026-04-27T12:00:00Z",
        }
        self.portfolios = [saved]
        return saved

    def delete_portfolio(self, portfolio_id: str) -> None:
        self.portfolios = [
            item for item in self.portfolios if item.get("portfolio_id") != portfolio_id
        ]

    def list_pairs_radar(self) -> list[dict[str, object]]:
        return self.pairs_radar

    def save_pairs_radar_item(self, payload: dict[str, object]) -> dict[str, object]:
        saved = {
            **payload,
            "saved_at": "2026-04-27T12:00:00Z",
        }
        self.pairs_radar = [saved]
        return saved

    def delete_pairs_radar_item(self, pairs_backtest_id: str) -> None:
        self.pairs_radar = [
            item for item in self.pairs_radar if item.get("pairs_backtest_id") != pairs_backtest_id
        ]

    def list_strategy_radar(self) -> list[dict[str, object]]:
        return self.strategy_radar

    def save_strategy_radar_item(self, payload: dict[str, object]) -> dict[str, object]:
        saved = {
            **payload,
            "saved_at": "2026-04-27T12:00:00Z",
        }
        self.strategy_radar = [saved]
        return saved

    def delete_strategy_radar_item(self, strategy_id: str) -> None:
        self.strategy_radar = [
            item for item in self.strategy_radar if item.get("strategy_id") != strategy_id
        ]

    def list_strategy_setup_runs(self) -> list[dict[str, object]]:
        return self.strategy_setup_runs

    def save_strategy_setup_run(self, payload: dict[str, object]) -> dict[str, object]:
        saved = {
            **payload,
            "saved_at": "2026-04-27T12:00:00Z",
        }
        self.strategy_setup_runs = [saved]
        return saved

    def list_strategy_setup_scores(self) -> list[dict[str, object]]:
        return [
            {
                "strategy_id": str(item["strategy_id"]),
                "label": str(item["strategy_id"]),
                "score": 13.25,
                "total_return": item["total_return"],
                "max_drawdown": item["max_drawdown"],
                "trade_count": item.get("trade_count", 0),
                "run_count": 1,
                "route_hint": str(item.get("route_hint", "/backtest")),
                "run_id": item.get("run_id"),
                "pairs_backtest_id": item.get("pairs_backtest_id"),
                "return_score": 10.0,
                "drawdown_penalty": 2.5,
                "execution_score": 3.25,
                "robustness_score": 0.5,
                "data_validity_score": 2.0,
                "ran_at": item["ran_at"],
                "methodology": (
                    "score = retorno_total * 100 - abs(max_drawdown) * 50 "
                    "+ min(trade_count, 20) * 0.25 + min(run_count, 5) * 0.5 "
                    "+ data_validity_score"
                ),
            }
            for item in self.strategy_setup_runs
        ]


def test_investments_catalog_route_uses_current_service_container() -> None:
    with override_api_services(
        investment_comparison_service=_StubInvestmentComparisonService(),
    ):
        response = client.get("/investments/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"][0]["category_id"] == "stocks_brazil"
    assert payload["presets"][0]["preset_id"] == "first_steps"
    assert payload["market_explorer"]["title"] == "Explorador de mercado"
    assert payload["market_explorer"]["ranking_backlog"][0]["ranking_id"] == "guided_factor_score"
    assert payload["product_data_plan"]["source_count"] == 1


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
                "decision_profile": {
                    "objective": "retirement",
                    "horizon_years": 15,
                    "liquidity_need": "long_term",
                    "mark_to_market_tolerance": "medium",
                    "tax_view": "net",
                    "monthly_income_target": 3000,
                },
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
    assert payload["request"]["decision_profile"]["objective"] == "retirement"
    assert payload["request"]["decision_profile"]["monthly_income_target"] == 3000
    assert payload["chart"]["reference_series_id"] == "selic_cash"
    assert payload["results"][0]["label"] == "PETR4"
    assert payload["fixed_income_backtest"]["methodology"]["benchmark_instrument_id"] == "CDI_INDEX"
    assert payload["product_realism"]["title"] == "Realismo do produto investivel"
    assert (
        payload["retail_fixed_income_equivalence"]["title"]
        == "Equivalencia liquida em renda fixa de varejo"
    )
    assert payload["result_stories"]["title"] == "Leituras guiadas do resultado"
    assert payload["market_rankings"]["title"] == "Rankings de mercado"
    assert payload["market_rankings"]["rankings"][0]["ranking_id"] == "guided_factor_score"
    assert payload["market_screeners"]["title"] == "Screeners do universo comparado"
    assert payload["cache_status"]["title"] == "Cache e preparacao dos dados"
    assert payload["portfolio_lifecycle"]["title"] == "Cenarios completos de carteira"


def test_investments_market_rankings_route_uses_current_service_container() -> None:
    with override_api_services(
        investment_comparison_service=_StubInvestmentComparisonService(),
    ):
        response = client.post(
            "/investments/market-rankings",
            json={
                "preset_id": "first_steps",
                "asset_ids": ["PETR4", "BOVA11"],
                "start_date": "2021-01-01",
                "benchmark_ids": ["selic_cash"],
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request"]["preset_id"] == "first_steps"
    assert payload["market_rankings"]["rankings"][0]["ranking_id"] == "momentum_6m"
    assert payload["market_screeners"]["title"] == "Screeners do universo comparado"


def test_investments_product_data_refresh_route_uses_current_service_container() -> None:
    with override_api_services(
        product_data_source_service=_StubProductDataSourceService(),
    ):
        response = client.post(
            "/investments/product-data/refresh",
            json={"source_id": "b3_fii_listed", "force": True},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "b3_fii_listed"
    assert payload["status"] == "refreshed"
    assert payload["manifest"]["row_count"] == 5
    assert payload["history"][0]["status"] == "refreshed"


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


def test_investment_workspace_portfolio_endpoints() -> None:
    workspace_service = _StubInvestmentWorkspaceService()

    with override_api_services(investment_workspace_service=workspace_service):
        save_response = client.post(
            "/investments/workspaces/portfolios",
            json={
                "label": "Minha carteira",
                "components": [
                    {"component_id": "PETR4", "weight": 0.6},
                    {"component_id": "BOVA11", "weight": 0.4},
                ],
            },
        )
        list_response = client.get("/investments/workspaces/portfolios")
        delete_response = client.delete("/investments/workspaces/portfolios/portfolio_1")

    assert save_response.status_code == 200
    assert save_response.json()["portfolio_id"] == "portfolio_1"
    assert list_response.status_code == 200
    assert list_response.json()[0]["label"] == "Minha carteira"
    assert delete_response.status_code == 204


def test_investment_workspace_pairs_radar_endpoints() -> None:
    workspace_service = _StubInvestmentWorkspaceService()

    with override_api_services(investment_workspace_service=workspace_service):
        save_response = client.post(
            "/investments/workspaces/pairs-radar",
            json={
                "pairs_backtest_id": "pairs_1",
                "label": "IBOV Proxy · 2021-01-01",
                "preset_label": "IBOV Proxy",
                "created_at": "2026-04-27T12:00:00Z",
                "scenario_count": 2,
                "candidate_pair_count": 5,
                "benchmark_ids": ["selic_cash"],
            },
        )
        list_response = client.get("/investments/workspaces/pairs-radar")
        delete_response = client.delete("/investments/workspaces/pairs-radar/pairs_1")

    assert save_response.status_code == 200
    assert save_response.json()["pairs_backtest_id"] == "pairs_1"
    assert list_response.status_code == 200
    assert list_response.json()[0]["preset_label"] == "IBOV Proxy"
    assert delete_response.status_code == 204


def test_investment_workspace_strategy_radar_endpoints() -> None:
    workspace_service = _StubInvestmentWorkspaceService()

    with override_api_services(investment_workspace_service=workspace_service):
        save_response = client.post(
            "/investments/workspaces/strategy-radar",
            json={
                "strategy_id": "pairs_cointegration",
                "label": "Pairs por cointegracao",
                "family": "market_neutral",
                "direction": "long_short",
                "parameter_values": {"formation_window": 252, "entry_zscore": 2.0},
                "universe": ["PETR4", "VALE3"],
                "timeframe": "daily",
            },
        )
        list_response = client.get("/investments/workspaces/strategy-radar")
        delete_response = client.delete(
            "/investments/workspaces/strategy-radar/pairs_cointegration"
        )

    assert save_response.status_code == 200
    assert save_response.json()["strategy_id"] == "pairs_cointegration"
    assert save_response.json()["parameter_values"]["formation_window"] == 252
    assert list_response.status_code == 200
    assert list_response.json()[0]["family"] == "market_neutral"
    assert delete_response.status_code == 204


def test_investment_workspace_strategy_setup_run_endpoints() -> None:
    workspace_service = _StubInvestmentWorkspaceService()

    with override_api_services(investment_workspace_service=workspace_service):
        save_response = client.post(
            "/investments/workspaces/strategy-setup-runs",
            json={
                "strategy_id": "pairs_cointegration",
                "pairs_backtest_id": "pairs_123",
                "ran_at": "2026-04-27T12:00:00Z",
                "strategy_count": 1,
                "best_strategy": "Realistic cointegration",
                "total_return": 0.1,
                "max_drawdown": -0.05,
                "trade_count": 13,
                "route_hint": "/pairs/backtests",
            },
        )
        list_response = client.get("/investments/workspaces/strategy-setup-runs")
        scores_response = client.get("/investments/workspaces/strategy-setup-scores")

    assert save_response.status_code == 200
    assert save_response.json()["pairs_backtest_id"] == "pairs_123"
    assert save_response.json()["trade_count"] == 13
    assert save_response.json()["total_return"] == 0.1
    assert list_response.status_code == 200
    assert list_response.json()[0]["best_strategy"] == "Realistic cointegration"
    assert scores_response.status_code == 200
    assert scores_response.json()[0]["score"] == 13.25
    assert scores_response.json()[0]["pairs_backtest_id"] == "pairs_123"
    assert scores_response.json()[0]["trade_count"] == 13
    assert scores_response.json()[0]["run_count"] == 1
    assert scores_response.json()[0]["robustness_score"] == 0.5
    assert scores_response.json()[0]["data_validity_score"] == 2.0
