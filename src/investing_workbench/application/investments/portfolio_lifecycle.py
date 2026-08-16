"""Portfolio lifecycle scenario helpers for investment comparisons."""

from __future__ import annotations

import random
from typing import Any, TypedDict

from .smart_contributions import build_smart_contributions_plan


class _RetirementStressScenario(TypedDict):
    scenario_id: str
    label: str
    withdrawal_multiplier: float
    drawdown_buffer: float
    description: str


def build_portfolio_lifecycle_scenarios(
    *,
    results: list[dict[str, Any]],
    decision_profile: dict[str, Any],
) -> dict[str, Any]:
    """Build retirement, withdrawal, and diversification scenarios from result rows."""

    portfolio_rows = [
        row
        for row in results
        if row.get("component_breakdown") or row.get("source_kind") == "custom_portfolio"
    ]
    if not results:
        return {}

    candidate_rows = portfolio_rows or results
    best_income = max(candidate_rows, key=lambda row: _safe_float(row, "final_value_real_net"))
    best_preservation = max(candidate_rows, key=lambda row: _safe_float(row, "max_drawdown"))
    best_accumulation = max(candidate_rows, key=lambda row: _safe_float(row, "final_value"))
    best_real_return = max(candidate_rows, key=lambda row: _safe_float(row, "real_cagr"))

    monthly_income_target = _safe_float(decision_profile, "monthly_income_target")
    target_capital = monthly_income_target * 12 / 0.04 if monthly_income_target > 0 else None
    best_portfolio = max(
        portfolio_rows, key=lambda row: _safe_float(row, "final_value"), default=None
    )
    best_single = max(
        (row for row in results if row not in portfolio_rows),
        key=lambda row: _safe_float(row, "final_value"),
        default=None,
    )

    scenario_cards = [
        _scenario_card(
            scenario_id="real_monthly_withdrawal",
            label="Retirada mensal real estimada",
            description=(
                "Aproxima uma retirada mensal real usando 4% ao ano sobre o patrimonio real "
                "liquido final."
            ),
            row=best_income,
            metric_label="Renda mensal real estimada",
            metric_value=_safe_float(best_income, "final_value_real_net") * 0.04 / 12,
            metric_kind="currency",
            target_value=monthly_income_target or None,
        ),
        _scenario_card(
            scenario_id="retirement_target",
            label="Aposentadoria por alvo de renda",
            description=(
                "Compara o patrimonio real liquido final com o capital aproximado necessario "
                "para sustentar a renda mensal informada."
            ),
            row=best_real_return,
            metric_label="Patrimonio real liquido",
            metric_value=_safe_float(best_real_return, "final_value_real_net"),
            metric_kind="currency",
            target_value=target_capital,
        ),
        _scenario_card(
            scenario_id="pre_retirement_stability",
            label="Pre-aposentadoria e estabilidade",
            description=(
                "Prioriza a alternativa com menor queda historica entre as carteiras ou, se "
                "nao houver carteira, entre os comparativos selecionados."
            ),
            row=best_preservation,
            metric_label="Drawdown maximo",
            metric_value=_safe_float(best_preservation, "max_drawdown"),
            metric_kind="percent",
        ),
        _scenario_card(
            scenario_id="wealth_accumulation",
            label="Acumulacao de patrimonio",
            description=(
                "Mostra a linha que mais acumulou valor nominal com o mesmo fluxo de aportes."
            ),
            row=best_accumulation,
            metric_label="Valor final",
            metric_value=_safe_float(best_accumulation, "final_value"),
            metric_kind="currency",
        ),
    ]

    if best_portfolio is not None and best_single is not None:
        scenario_cards.append(
            {
                "scenario_id": "portfolio_vs_single_asset",
                "label": "Carteira versus ativo unico",
                "description": (
                    "Compara a melhor carteira selecionada contra o melhor ativo isolado no "
                    "mesmo periodo."
                ),
                "best_match_id": best_portfolio["instrument_id"],
                "best_match_label": best_portfolio["label"],
                "metric_label": "Diferença de valor final",
                "metric_value": _safe_float(best_portfolio, "final_value")
                - _safe_float(best_single, "final_value"),
                "metric_kind": "currency",
                "comparison_label": best_single["label"],
                "target_value": None,
                "target_met": None,
            }
        )

    return {
        "title": "Cenarios completos de carteira",
        "plain_language_summary": (
            "Traduz o comparativo em perguntas de vida financeira: retirada mensal, "
            "aposentadoria, pre-aposentadoria, acumulacao e diversificacao."
        ),
        "uses_portfolio_rows": bool(portfolio_rows),
        "portfolio_count": len(portfolio_rows),
        "scenario_cards": scenario_cards,
        "withdrawal_plan": _build_withdrawal_plan(
            candidate_rows=candidate_rows,
            monthly_income_target=monthly_income_target,
        ),
        "smart_contributions": build_smart_contributions_plan(
            results=results,
            contribution_amount=monthly_income_target if monthly_income_target > 0 else 1000.0,
        ),
        "assumptions": [
            "Retirada mensal usa uma regra didatica de 4% ao ano sobre patrimonio real liquido.",
            "O alvo de aposentadoria usa 25 vezes a renda anual desejada.",
            "Os cenarios reaproveitam o mesmo periodo historico e fluxo de aportes do estudo.",
            (
                "O plano de retirada ainda nao separa dividendos, JCP e renda de FIIs de "
                "valorizacao; ele usa patrimonio real liquido como base didatica."
            ),
            (
                "Stress tests usam multiplicadores didaticos e parte do drawdown historico "
                "como margem de seguranca; nao substituem Monte Carlo."
            ),
            (
                "A previa Monte Carlo usa uma aproximacao por percentis a partir de retorno "
                "real e volatilidade, simulando caminhos mensais deterministas por 30 anos."
            ),
        ],
        "next_steps": [
            (
                "Separar renda distribuida de ganho de capital quando dados de proventos "
                "estiverem normalizados."
            ),
            "Trocar a previa por Monte Carlo com reamostragem aleatoria de retornos mensais.",
            "Salvar carteiras como entidades compartilhadas entre retorno historico, beta e VaR.",
        ],
    }


def _build_withdrawal_plan(
    *,
    candidate_rows: list[dict[str, Any]],
    monthly_income_target: float,
) -> dict[str, Any]:
    withdrawal_rate = 0.04
    ranked_rows = sorted(
        candidate_rows,
        key=lambda row: _safe_float(row, "final_value_real_net"),
        reverse=True,
    )[:5]
    candidates = [
        _build_withdrawal_candidate(
            row=row,
            monthly_income_target=monthly_income_target,
            withdrawal_rate=withdrawal_rate,
        )
        for row in ranked_rows
    ]
    best_candidate = candidates[0] if candidates else None
    target_met_count = sum(1 for candidate in candidates if candidate["target_met"] is True)
    stress_tests = _build_retirement_stress_tests(
        best_candidate=best_candidate,
        monthly_income_target=monthly_income_target,
    )
    monte_carlo_preview = _build_monte_carlo_preview(
        best_candidate=best_candidate,
        monthly_income_target=monthly_income_target,
    )

    if monthly_income_target <= 0:
        feasibility_label = "Defina uma meta de renda mensal para medir o gap."
    elif best_candidate and best_candidate["target_met"] is True:
        feasibility_label = "A melhor alternativa cobre a meta neste recorte historico."
    else:
        feasibility_label = "Nenhuma alternativa cobre a meta neste recorte historico."

    return {
        "title": "Plano didatico de retirada",
        "withdrawal_rate": withdrawal_rate,
        "monthly_income_target": monthly_income_target or None,
        "best_candidate_id": best_candidate["instrument_id"] if best_candidate else None,
        "best_candidate_label": best_candidate["label"] if best_candidate else None,
        "target_met_count": target_met_count,
        "candidate_count": len(candidates),
        "feasibility_label": feasibility_label,
        "candidates": candidates,
        "stress_tests": stress_tests,
        "stress_summary": _build_stress_summary(
            stress_tests=stress_tests,
            monthly_income_target=monthly_income_target,
        ),
        "monte_carlo_preview": monte_carlo_preview,
    }


def _build_withdrawal_candidate(
    *,
    row: dict[str, Any],
    monthly_income_target: float,
    withdrawal_rate: float,
) -> dict[str, Any]:
    final_value_real_net = _safe_float(row, "final_value_real_net")
    monthly_withdrawal = final_value_real_net * withdrawal_rate / 12
    income_gap = monthly_withdrawal - monthly_income_target if monthly_income_target > 0 else None
    return {
        "instrument_id": row["instrument_id"],
        "label": row["label"],
        "source_kind": row.get("source_kind"),
        "final_value_real_net": final_value_real_net,
        "monthly_withdrawal": monthly_withdrawal,
        "income_gap": income_gap,
        "target_met": income_gap >= 0 if income_gap is not None else None,
        "max_drawdown": _safe_float(row, "max_drawdown"),
        "real_cagr": _safe_float(row, "real_cagr"),
        "annual_volatility": _safe_float(row, "annual_volatility"),
    }


def _build_retirement_stress_tests(
    *,
    best_candidate: dict[str, Any] | None,
    monthly_income_target: float,
) -> list[dict[str, Any]]:
    if not best_candidate:
        return []

    historical_drawdown = abs(min(0.0, _safe_float(best_candidate, "max_drawdown")))
    scenarios: tuple[_RetirementStressScenario, ...] = (
        {
            "scenario_id": "base_rule",
            "label": "Base historica",
            "withdrawal_multiplier": 1.0,
            "drawdown_buffer": 0.0,
            "description": "Usa a retirada de 4% a.a. sobre o patrimonio real liquido final.",
        },
        {
            "scenario_id": "conservative_income",
            "label": "Renda conservadora",
            "withdrawal_multiplier": 0.85,
            "drawdown_buffer": historical_drawdown * 0.25,
            "description": (
                "Reduz a renda para criar margem contra anos ruins e custos nao modelados."
            ),
        },
        {
            "scenario_id": "sequence_stress",
            "label": "Estresse de sequencia",
            "withdrawal_multiplier": 0.70,
            "drawdown_buffer": historical_drawdown * 0.50,
            "description": (
                "Aplica uma margem mais dura para simular aposentadoria iniciando perto de "
                "um periodo ruim."
            ),
        },
    )

    stress_tests: list[dict[str, Any]] = []
    base_monthly_withdrawal = _safe_float(best_candidate, "monthly_withdrawal")
    for scenario in scenarios:
        stressed_monthly_withdrawal = (
            base_monthly_withdrawal
            * scenario["withdrawal_multiplier"]
            * (1.0 - min(scenario["drawdown_buffer"], 0.50))
        )
        income_gap = (
            stressed_monthly_withdrawal - monthly_income_target
            if monthly_income_target > 0
            else None
        )
        stress_tests.append(
            {
                "scenario_id": scenario["scenario_id"],
                "label": scenario["label"],
                "description": scenario["description"],
                "withdrawal_multiplier": scenario["withdrawal_multiplier"],
                "drawdown_buffer": scenario["drawdown_buffer"],
                "stressed_monthly_withdrawal": stressed_monthly_withdrawal,
                "income_gap": income_gap,
                "target_met": income_gap >= 0 if income_gap is not None else None,
                "interpretation": _build_stress_interpretation(
                    label=str(scenario["label"]),
                    stressed_monthly_withdrawal=stressed_monthly_withdrawal,
                    income_gap=income_gap,
                ),
            }
        )
    return stress_tests


def _build_stress_summary(
    *,
    stress_tests: list[dict[str, Any]],
    monthly_income_target: float,
) -> str:
    if monthly_income_target <= 0:
        return "Defina uma meta de renda para transformar o stress test em diagnostico."
    if not stress_tests:
        return "Sem candidato suficiente para montar o stress test."
    met_count = sum(1 for item in stress_tests if item["target_met"] is True)
    if met_count == len(stress_tests):
        return "A meta sobrevive aos tres cenarios didaticos de retirada."
    if met_count > 0:
        return "A meta passa no cenario base, mas precisa de margem nos cenarios adversos."
    return "A meta nao passa nem no cenario base deste recorte historico."


def _build_stress_interpretation(
    *,
    label: str,
    stressed_monthly_withdrawal: float,
    income_gap: float | None,
) -> str:
    if income_gap is None:
        return f"{label}: renda estimada sem meta mensal informada."
    if income_gap >= 0:
        return f"{label}: sobra estimada de {income_gap:.2f} por mes contra a meta."
    return f"{label}: faltam aproximadamente {abs(income_gap):.2f} por mes contra a meta."


def _build_monte_carlo_preview(
    *,
    best_candidate: dict[str, Any] | None,
    monthly_income_target: float,
) -> dict[str, Any]:
    if not best_candidate:
        return {}

    capital = _safe_float(best_candidate, "final_value_real_net")
    real_cagr = _safe_float(best_candidate, "real_cagr")
    annual_volatility = max(0.0, _safe_float(best_candidate, "annual_volatility"))
    base_monthly_withdrawal = _safe_float(best_candidate, "monthly_withdrawal")
    conservative_monthly_withdrawal = _preview_monthly_withdrawal(
        capital=capital,
        expected_real_return=real_cagr,
        annual_volatility=annual_volatility,
        z_score=-1.0,
    )
    adverse_monthly_withdrawal = _preview_monthly_withdrawal(
        capital=capital,
        expected_real_return=real_cagr,
        annual_volatility=annual_volatility,
        z_score=-2.0,
    )
    annual_income_target = monthly_income_target * 12 if monthly_income_target > 0 else 0.0
    years_of_income = capital / annual_income_target if annual_income_target > 0 else None
    monthly_sequence = _build_monthly_sequence_simulation(
        capital=capital,
        real_cagr=real_cagr,
        annual_volatility=annual_volatility,
        monthly_income_target=monthly_income_target,
        fallback_monthly_withdrawal=base_monthly_withdrawal,
        seed_label=str(best_candidate["instrument_id"]),
    )

    scenarios = [
        _monte_carlo_preview_scenario(
            scenario_id="p50_base",
            label="P50 aproximado",
            monthly_withdrawal=base_monthly_withdrawal,
            monthly_income_target=monthly_income_target,
            description="Usa a regra base de 4% como mediana didatica.",
        ),
        _monte_carlo_preview_scenario(
            scenario_id="p25_conservative",
            label="P25 conservador",
            monthly_withdrawal=conservative_monthly_withdrawal,
            monthly_income_target=monthly_income_target,
            description="Penaliza retorno real esperado por uma volatilidade anual.",
        ),
        _monte_carlo_preview_scenario(
            scenario_id="p10_adverse",
            label="P10 adverso",
            monthly_withdrawal=adverse_monthly_withdrawal,
            monthly_income_target=monthly_income_target,
            description="Penaliza retorno real esperado por duas volatilidades anuais.",
        ),
    ]
    target_met_count = sum(1 for item in scenarios if item["target_met"] is True)
    coverage_score = target_met_count / len(scenarios) if scenarios else 0.0

    return {
        "title": "Previa Monte Carlo",
        "methodology": (
            "Aproximacao deterministica por percentis usando retorno real historico, "
            "volatilidade anual e regra de retirada de 4%."
        ),
        "instrument_id": best_candidate["instrument_id"],
        "label": best_candidate["label"],
        "real_cagr": real_cagr,
        "annual_volatility": annual_volatility,
        "years_of_income_at_target": years_of_income,
        "coverage_score": coverage_score,
        "target_met_count": target_met_count,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "monthly_sequence": monthly_sequence,
        "caveat": (
            "Ainda nao reamostra retornos aleatorios; os caminhos mensais sao deterministas "
            "e servem como ponte didatica para o Monte Carlo completo."
        ),
    }


def _preview_monthly_withdrawal(
    *,
    capital: float,
    expected_real_return: float,
    annual_volatility: float,
    z_score: float,
) -> float:
    stressed_return = expected_real_return + z_score * annual_volatility
    real_return_buffer = max(-0.50, min(stressed_return, 0.50))
    withdrawal_rate = max(0.01, min(0.04 + real_return_buffer * 0.25, 0.06))
    return capital * withdrawal_rate / 12


def _monte_carlo_preview_scenario(
    *,
    scenario_id: str,
    label: str,
    monthly_withdrawal: float,
    monthly_income_target: float,
    description: str,
) -> dict[str, Any]:
    income_gap = monthly_withdrawal - monthly_income_target if monthly_income_target > 0 else None
    return {
        "scenario_id": scenario_id,
        "label": label,
        "description": description,
        "monthly_withdrawal": monthly_withdrawal,
        "income_gap": income_gap,
        "target_met": income_gap >= 0 if income_gap is not None else None,
    }


def _build_monthly_sequence_simulation(
    *,
    capital: float,
    real_cagr: float,
    annual_volatility: float,
    monthly_income_target: float,
    fallback_monthly_withdrawal: float,
    seed_label: str,
) -> dict[str, Any]:
    horizon_years = 30
    horizon_months = horizon_years * 12
    monthly_withdrawal = (
        monthly_income_target if monthly_income_target > 0 else fallback_monthly_withdrawal
    )
    monthly_base_return = (1.0 + max(real_cagr, -0.95)) ** (1.0 / 12.0) - 1.0
    monthly_volatility = max(0.0, annual_volatility) / (12.0**0.5)
    path_definitions = (
        {
            "path_id": "favorable_sequence",
            "label": "Sequencia favoravel",
            "monthly_return": monthly_base_return + monthly_volatility * 0.35,
            "early_shock": 0.0,
        },
        {
            "path_id": "base_sequence",
            "label": "Sequencia base",
            "monthly_return": monthly_base_return,
            "early_shock": 0.0,
        },
        {
            "path_id": "adverse_sequence",
            "label": "Sequencia adversa",
            "monthly_return": monthly_base_return - monthly_volatility * 0.75,
            "early_shock": monthly_volatility * 0.50,
        },
    )
    paths = [
        _simulate_monthly_withdrawal_path(
            capital=capital,
            monthly_withdrawal=monthly_withdrawal,
            horizon_months=horizon_months,
            path_id=str(path["path_id"]),
            label=str(path["label"]),
            monthly_return=float(path["monthly_return"]),
            early_shock=float(path["early_shock"]),
        )
        for path in path_definitions
    ]
    success_count = sum(1 for path in paths if path["exhaustion_month"] is None)
    stochastic = _build_stochastic_monthly_monte_carlo(
        capital=capital,
        monthly_withdrawal=monthly_withdrawal,
        horizon_months=horizon_months,
        monthly_base_return=monthly_base_return,
        monthly_volatility=monthly_volatility,
        seed_label=seed_label,
    )
    return {
        "title": "Simulacao mensal de exaustao",
        "horizon_years": horizon_years,
        "monthly_withdrawal": monthly_withdrawal,
        "monthly_base_return": monthly_base_return,
        "monthly_volatility": monthly_volatility,
        "success_count": success_count,
        "path_count": len(paths),
        "success_rate": success_count / len(paths) if paths else 0.0,
        "paths": paths,
        "stochastic": stochastic,
        "methodology": (
            "Projeta 30 anos em caminhos mensais usando retorno real historico, "
            "volatilidade anual convertida para mes e retirada constante em termos reais."
        ),
    }


def _simulate_monthly_withdrawal_path(
    *,
    capital: float,
    monthly_withdrawal: float,
    horizon_months: int,
    path_id: str,
    label: str,
    monthly_return: float,
    early_shock: float,
) -> dict[str, Any]:
    balance = max(0.0, capital)
    lowest_balance = balance
    exhaustion_month: int | None = None
    checkpoints: list[dict[str, Any]] = []
    for month in range(1, horizon_months + 1):
        effective_return = monthly_return
        if early_shock > 0 and month <= 24:
            effective_return -= early_shock
        balance = max(0.0, balance * (1.0 + effective_return) - monthly_withdrawal)
        lowest_balance = min(lowest_balance, balance)
        if month in {60, 120, 180, 240, 300, 360}:
            checkpoints.append(
                {
                    "month": month,
                    "year": month // 12,
                    "balance": balance,
                }
            )
        if balance <= 0 and exhaustion_month is None:
            exhaustion_month = month
            break

    return {
        "path_id": path_id,
        "label": label,
        "monthly_return": monthly_return,
        "early_shock": early_shock,
        "final_balance": balance,
        "lowest_balance": lowest_balance,
        "exhaustion_month": exhaustion_month,
        "exhaustion_year": (
            round(exhaustion_month / 12.0, 1) if exhaustion_month is not None else None
        ),
        "survived_horizon": exhaustion_month is None,
        "checkpoints": checkpoints,
    }


def _build_stochastic_monthly_monte_carlo(
    *,
    capital: float,
    monthly_withdrawal: float,
    horizon_months: int,
    monthly_base_return: float,
    monthly_volatility: float,
    seed_label: str,
) -> dict[str, Any]:
    simulation_count = 250
    seed = _stable_seed(seed_label)
    rng = random.Random(seed)
    paths: list[dict[str, Any]] = []
    for index in range(simulation_count):
        balance = max(0.0, capital)
        exhaustion_month: int | None = None
        worst_balance = balance
        for month in range(1, horizon_months + 1):
            shock = rng.gauss(0.0, monthly_volatility)
            monthly_return = max(-0.80, min(monthly_base_return + shock, 0.80))
            balance = max(0.0, balance * (1.0 + monthly_return) - monthly_withdrawal)
            worst_balance = min(worst_balance, balance)
            if balance <= 0:
                exhaustion_month = month
                break
        paths.append(
            {
                "path_index": index + 1,
                "final_balance": balance,
                "lowest_balance": worst_balance,
                "exhaustion_month": exhaustion_month,
                "survived_horizon": exhaustion_month is None,
            }
        )

    success_count = sum(1 for path in paths if path["survived_horizon"] is True)
    final_balances = sorted(float(path["final_balance"]) for path in paths)
    exhaustion_months = sorted(
        int(path["exhaustion_month"]) for path in paths if path["exhaustion_month"] is not None
    )
    return {
        "title": "Monte Carlo estocastico mensal",
        "simulation_count": simulation_count,
        "seed": seed,
        "success_count": success_count,
        "success_rate": success_count / simulation_count,
        "percentiles": {
            "final_balance_p10": _percentile(final_balances, 0.10),
            "final_balance_p50": _percentile(final_balances, 0.50),
            "final_balance_p90": _percentile(final_balances, 0.90),
        },
        "median_exhaustion_month": (
            _percentile(exhaustion_months, 0.50) if exhaustion_months else None
        ),
        "median_exhaustion_year": (
            round(float(_percentile(exhaustion_months, 0.50)) / 12.0, 1)
            if exhaustion_months
            else None
        ),
        "sample_paths": paths[:5],
        "methodology": (
            "Reamostra choques mensais gaussianos em torno do retorno real historico. "
            "E deterministico pela seed para manter o estudo reproduzivel."
        ),
    }


def _stable_seed(label: str) -> int:
    seed = 17
    for char in label:
        seed = (seed * 31 + ord(char)) % 2_147_483_647
    return seed


def _percentile(values: list[float] | list[int], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    position = pct * (len(values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return float(values[lower]) * (1.0 - weight) + float(values[upper]) * weight


def _scenario_card(
    *,
    scenario_id: str,
    label: str,
    description: str,
    row: dict[str, Any],
    metric_label: str,
    metric_value: float,
    metric_kind: str,
    target_value: float | None = None,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "label": label,
        "description": description,
        "best_match_id": row["instrument_id"],
        "best_match_label": row["label"],
        "metric_label": metric_label,
        "metric_value": metric_value,
        "metric_kind": metric_kind,
        "target_value": target_value,
        "target_met": metric_value >= target_value if target_value is not None else None,
    }


def _safe_float(row: dict[str, Any], key: str) -> float:
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
