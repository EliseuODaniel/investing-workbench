"""Feature-parity map inspired by the public Investidor Facil landing page."""

from __future__ import annotations

from typing import Any


def build_investor_easy_parity() -> dict[str, Any]:
    """Return local feature coverage for the Investidor Facil public offering."""

    calculators = _calculator_suite()
    available_count = sum(1 for item in calculators if item["status"] == "available")
    return {
        "title": "Paridade Investidor Facil",
        "source_url": "https://investidor-facil-gnje.vercel.app/",
        "plain_language_summary": (
            "O site observado oferece organizacao de carteira, metas, aportes, dashboard, "
            "relatorios, alertas e 15 calculadoras educativas. Este painel mostra o que ja "
            "existe no Investing Workbench e o que virou atalho/cobertura explicita."
        ),
        "observed_at": "2026-05-05",
        "calculator_count": len(calculators),
        "available_calculator_count": available_count,
        "feature_coverage": [
            {
                "feature_id": "organized_portfolio",
                "label": "Carteira organizada",
                "site_offer": "Painel simples para acompanhar patrimonio e distribuicao.",
                "local_status": "available",
                "local_surface": (
                    "Carteiras guiadas, carteiras personalizadas e painel de resultados."
                ),
            },
            {
                "feature_id": "financial_goals",
                "label": "Metas financeiras",
                "site_offer": "Metas e simuladores para objetivos financeiros.",
                "local_status": "available",
                "local_surface": (
                    "Perfil de decisao, meta de renda mensal e cenarios de aposentadoria."
                ),
            },
            {
                "feature_id": "contributions",
                "label": "Aportes",
                "site_offer": "Acompanhamento de aportes e evolucao.",
                "local_status": "available",
                "local_surface": "Comparacoes com capital inicial e aporte mensal padronizado.",
            },
            {
                "feature_id": "dashboard_visual",
                "label": "Dashboard visual",
                "site_offer": "Previa de patrimonio, evolucao e alocacao.",
                "local_status": "available",
                "local_surface": (
                    "Resultados, graficos, rankings, screeners e explorador de mercado."
                ),
            },
            {
                "feature_id": "monthly_reports",
                "label": "Relatorios mensais",
                "site_offer": "Relatorios avancados no plano Pro.",
                "local_status": "partial",
                "local_surface": (
                    "Relatorios HTML/CSV ja existem em backtests; PDF mensal fica "
                    "como proximo passo."
                ),
            },
            {
                "feature_id": "automatic_alerts",
                "label": "Alertas automaticos",
                "site_offer": "Alertas no plano Essencial.",
                "local_status": "partial",
                "local_surface": (
                    "Alertas de sinais existem no roadmap QuantBrasil; alertas pessoais ainda nao."
                ),
            },
            {
                "feature_id": "auth_and_plans",
                "label": "Login, cadastro e planos",
                "site_offer": "FREE, Essencial e Pro com limites comerciais.",
                "local_status": "not_applicable_local_first",
                "local_surface": (
                    "Projeto local-first sem cobranca; limites viram agrupamento de calculadoras."
                ),
            },
        ],
        "calculator_suite": calculators,
        "plan_equivalence": [
            {
                "plan_label": "Gratis",
                "site_limit": "5 calculadoras basicas, ate 5 ativos, 1 meta.",
                "local_equivalent": (
                    "Grupo Basico: 5 calculadoras essenciais, sem bloqueio comercial."
                ),
            },
            {
                "plan_label": "Essencial",
                "site_limit": "10 calculadoras, ativos/metas ilimitados e alertas.",
                "local_equivalent": (
                    "Grupo Essencial: 10 calculadoras e organizacao sem limite local."
                ),
            },
            {
                "plan_label": "Pro",
                "site_limit": (
                    "15 calculadoras, relatorios avancados, PDF e independencia financeira."
                ),
                "local_equivalent": (
                    "Grupo Pro: 15 calculadoras; PDF mensal segue como lacuna explicita."
                ),
            },
        ],
        "remaining_gaps": [
            "Exportacao PDF mensal pronta para usuario final.",
            "Alertas pessoais recorrentes por meta, aporte ou rebalanceamento.",
            "Autenticacao/cobranca nao se aplica ao modo local-first atual.",
        ],
    }


def _calculator_suite() -> list[dict[str, Any]]:
    definitions = (
        ("compound_interest", "Juros compostos", "basico", "future_value"),
        ("monthly_contribution_target", "Aporte necessario para meta", "basico", "goal_seek"),
        ("future_value_with_contributions", "Valor futuro com aportes", "basico", "future_value"),
        (
            "real_return_after_inflation",
            "Retorno real descontando inflacao",
            "basico",
            "real_return",
        ),
        ("emergency_reserve", "Reserva de emergencia", "basico", "cash_buffer"),
        ("passive_income_target", "Meta de renda passiva", "essencial", "income_target"),
        ("dividend_yield_income", "Dividendos e yield", "essencial", "income_yield"),
        ("retirement_number", "Numero da aposentadoria", "essencial", "retirement_target"),
        ("safe_withdrawal", "Retirada mensal sustentavel", "essencial", "withdrawal"),
        ("portfolio_rebalance", "Rebalanceamento de carteira", "essencial", "allocation"),
        ("asset_allocation", "Alocacao por classe", "pro", "allocation"),
        ("average_price", "Preco medio", "pro", "cost_basis"),
        ("accumulated_return", "Rentabilidade acumulada", "pro", "return"),
        ("net_fixed_income_equivalence", "Equivalencia CDB/LCI liquida", "pro", "tax_equivalence"),
        ("financial_independence", "Independencia financeira", "pro", "fire"),
    )
    return [
        {
            "calculator_id": calculator_id,
            "label": label,
            "tier": tier,
            "formula_family": formula_family,
            "status": "available",
            "local_surface": _local_surface_for_formula(formula_family),
        }
        for calculator_id, label, tier, formula_family in definitions
    ]


def _local_surface_for_formula(formula_family: str) -> str:
    surfaces = {
        "future_value": "Comparador com capital inicial, aporte mensal e curva historica.",
        "goal_seek": "Cenarios de meta e aporte mensal no fluxo de investimentos.",
        "real_return": "Historias de resultado, IPCA e rankings de retorno real.",
        "cash_buffer": "Perfis de preservacao, SELIC/CDI e reserva.",
        "income_target": "Meta de renda mensal no perfil de decisao.",
        "income_yield": "FIIs, renda passiva e politica de renda no realismo metodologico.",
        "retirement_target": "Portfolio lifecycle e cenarios de aposentadoria.",
        "withdrawal": "Plano de retirada mensal e stress tests.",
        "allocation": "Carteiras guiadas, personalizadas e rebalanceamento.",
        "cost_basis": "Organizador financeiro; calculadora declarada para uso didatico.",
        "return": "Resultados, rankings e curvas acumuladas.",
        "tax_equivalence": "Equivalencia liquida de renda fixa de varejo.",
        "fire": "Independencia financeira via meta de renda e patrimonio alvo.",
    }
    return surfaces.get(formula_family, "Calculadora educativa no catalogo local.")
