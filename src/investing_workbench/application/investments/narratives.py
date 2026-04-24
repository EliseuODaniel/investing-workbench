"""Didactic narrative builders for investment comparison payloads."""

from __future__ import annotations

import math
from typing import Any

from .decision_profile import build_decision_profile_notes

_SOURCE_KIND_EXPLANATIONS: dict[str, dict[str, str]] = {
    "listed_security": {
        "label": "Ativo negociado",
        "description": (
            "Acoes, ETFs, FIIs e BDRs usam uma serie historica ajustada para aproximar "
            "a experiencia de comprar e carregar o ativo."
        ),
        "limitations": (
            "Nao simula corretagem, spread, tributacao individual nem mudancas futuras "
            "de dividendos ou fundamentos."
        ),
    },
    "model_portfolio": {
        "label": "Carteira guiada",
        "description": (
            "Carteiras-modelo combinam varios ativos em uma alocacao fixa e rebalanceada "
            "periodicamente."
        ),
        "limitations": (
            "E uma aproximacao didatica: custos, impostos e friccoes de rebalanceamento "
            "podem mudar o resultado real."
        ),
    },
    "custom_portfolio": {
        "label": "Carteira personalizada",
        "description": (
            "A carteira criada pelo usuario normaliza os pesos informados e compara a alocacao "
            "contra os demais ativos no mesmo fluxo de aportes."
        ),
        "limitations": (
            "O resultado depende da selecao inicial e assume rebalanceamento periodico, "
            "sem otimizar pesos automaticamente."
        ),
    },
    "fixed_income_index": {
        "label": "Indice de renda fixa",
        "description": (
            "Indices como CDI e IDkA ajudam a comparar familias de renda fixa por duration "
            "e indexador com dados historicos consistentes."
        ),
        "limitations": (
            "Um indice nao e necessariamente um produto compravel; ele mede uma referencia "
            "metodologica, nao todas as friccoes de um investidor pessoa fisica."
        ),
    },
    "tesouro_direct_strategy": {
        "label": "Estrategia Tesouro Direto",
        "description": (
            "Simula compra e troca de titulos do Tesouro Direto usando historico oficial "
            "de precos e vencimentos disponiveis."
        ),
        "limitations": (
            "Ainda e uma regra mecanica: nao substitui escolha de vencimento, necessidade "
            "de liquidez, custodia, spread operacional ou impostos exatos do investidor."
        ),
    },
    "selic_proxy": {
        "label": "Proxy de caixa pos-fixado",
        "description": (
            "Representa uma alternativa defensiva que acompanha a SELIC/CDI para servir "
            "como base de comparacao."
        ),
        "limitations": (
            "Nao equivale automaticamente a um CDB, fundo DI ou Tesouro Selic especifico, "
            "porque cada produto tem taxas, liquidez e tributacao."
        ),
    },
    "rate_proxy": {
        "label": "Proxy de taxa fixa",
        "description": (
            "Usa uma taxa anual simplificada para representar um retorno prefixado ou "
            "IPCA+ didatico."
        ),
        "limitations": (
            "Nao sofre marcacao a mercado como um titulo real e deve ser lido como "
            "hipotese pedagogica, nao produto negociavel."
        ),
    },
    "inflation_proxy": {
        "label": "Proxy de inflacao",
        "description": (
            "Representa o poder de compra pelo IPCA para separar ganho nominal de ganho real."
        ),
        "limitations": "Nao e investimento; e uma referencia para medir preservacao de valor.",
    },
}


def build_methodology_guide(
    *,
    results: list[dict[str, Any]],
    benchmarks: list[dict[str, Any]],
    fixed_income_backtest: dict[str, Any] | None,
    assumptions: list[str],
    decision_profile: dict[str, Any],
) -> dict[str, Any]:
    """Explain what kind of evidence is being mixed in the comparison."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(str(result.get("source_kind", "unknown")), []).append(result)

    evidence_types: list[dict[str, Any]] = []
    for source_kind, rows in sorted(grouped.items()):
        explanation = _SOURCE_KIND_EXPLANATIONS.get(
            source_kind,
            {
                "label": source_kind.replace("_", " ").title(),
                "description": "Serie historica usada como comparativo didatico.",
                "limitations": "Leia junto com as premissas e a cobertura de dados.",
            },
        )
        evidence_types.append(
            {
                "kind": source_kind,
                "label": explanation["label"],
                "description": explanation["description"],
                "limitations": explanation["limitations"],
                "included_count": len(rows),
                "included_labels": [str(row["label"]) for row in rows[:5]],
            }
        )

    if benchmarks:
        evidence_types.append(
            {
                "kind": "benchmark",
                "label": "Benchmark",
                "description": (
                    "Referencias usadas para responder se o risco assumido superou caixa, "
                    "bolsa ampla ou outro parametro escolhido."
                ),
                "limitations": (
                    "Benchmark nao e recomendacao; ele e uma regua para comparar o mesmo "
                    "fluxo de aportes."
                ),
                "included_count": len(benchmarks),
                "included_labels": [str(row["label"]) for row in benchmarks[:5]],
            }
        )

    caveats = [
        "O vencedor historico nao e recomendacao automatica para hoje.",
        (
            "Compare primeiro instrumentos do mesmo tipo; depois use benchmarks para entender "
            "o custo de oportunidade."
        ),
        (
            "Retorno real e drawdown importam tanto quanto valor final, especialmente para "
            "renda fixa e aposentadoria."
        ),
    ]
    if fixed_income_backtest is not None:
        caveats.append(
            "Em renda fixa, indice de duration, ETF de NTN-B e Tesouro Direto respondem "
            "perguntas parecidas, mas nao identicas."
        )
    if any(row.get("component_breakdown") for row in results):
        caveats.append(
            "Carteiras rebalanceadas mostram uma politica de alocacao; ativos avulsos "
            "mostram uma aposta isolada."
        )

    return {
        "title": "Como ler este estudo",
        "plain_language_summary": (
            "Este resultado compara evidencias diferentes no mesmo fluxo de dinheiro. "
            "A leitura mais segura e perguntar: o que cada linha mede, o que ela nao mede, "
            "e qual objetivo de investidor ela atende melhor."
        ),
        "evidence_types": evidence_types,
        "assumption_notes": assumptions,
        "caveats": caveats,
        "decision_profile_notes": build_decision_profile_notes(decision_profile),
        "realism_notes": _build_realism_notes(fixed_income_backtest),
    }


def build_fixed_income_decision_guide(
    *,
    fixed_income_backtest: dict[str, Any] | None,
    decision_profile: dict[str, Any],
) -> dict[str, Any] | None:
    """Turn fixed-income winners into investor-facing decision cards."""

    if fixed_income_backtest is None:
        return None

    full_period = fixed_income_backtest.get("full_period", {})
    leaders = full_period.get("leaders", {})
    methodology = fixed_income_backtest.get("methodology", {})
    benchmark = full_period.get("benchmark")
    cards: list[dict[str, Any]] = []

    post_fixed = leaders.get("post_fixed") or benchmark
    if isinstance(post_fixed, dict):
        cards.append(
            _with_fit(
                _decision_card(
                    decision_id="liquidity_and_reserve",
                    label="Reserva e liquidez",
                    when_it_fits=(
                        "Faz sentido quando a prioridade e estabilidade, liquidez e menor chance "
                        "de susto no extrato."
                    ),
                    watch_out=(
                        "Pode perder em retorno real para IPCA+ ou prefixado em ciclos longos de "
                        "juros reais elevados."
                    ),
                    row=post_fixed,
                    metric_label="Valor final",
                    metric_key="display_value",
                    metric_kind="currency",
                ),
                decision_profile,
                decision_id="liquidity_and_reserve",
            )
        )

    ipca_plus = leaders.get("ipca_plus") or leaders.get("best_real_cagr")
    if isinstance(ipca_plus, dict):
        cards.append(
            _with_fit(
                _decision_card(
                    decision_id="real_return",
                    label="Proteger poder de compra",
                    when_it_fits=(
                        "Combina melhor com horizontes de varios anos, quando o objetivo e ganhar "
                        "acima da inflacao."
                    ),
                    watch_out=(
                        "Sofre marcacao a mercado; vender antes do horizonte pode transformar "
                        "oscilacao temporaria em perda realizada."
                    ),
                    row=ipca_plus,
                    metric_label="CAGR real",
                    metric_key="display_real_cagr",
                    metric_kind="percent",
                ),
                decision_profile,
                decision_id="real_return",
            )
        )

    prefixado = leaders.get("prefixado")
    if isinstance(prefixado, dict):
        cards.append(
            _with_fit(
                _decision_card(
                    decision_id="nominal_rate_lock",
                    label="Travar taxa nominal",
                    when_it_fits=(
                        "Ajuda quando a taxa prefixada parece alta para o horizonte e voce aceita "
                        "abrir mao da protecao direta contra inflacao."
                    ),
                    watch_out=(
                        "Inflacao acima do esperado e alta adicional de juros podem machucar o "
                        "resultado real e o preco no meio do caminho."
                    ),
                    row=prefixado,
                    metric_label="CAGR",
                    metric_key="display_cagr",
                    metric_kind="percent",
                ),
                decision_profile,
                decision_id="nominal_rate_lock",
            )
        )

    consistent = leaders.get("most_consistent")
    if isinstance(consistent, dict):
        cards.append(
            _with_fit(
                {
                    "decision_id": "consistency",
                    "label": "Consistencia em janelas",
                    "when_it_fits": (
                        "E util quando voce quer saber se o resultado apareceu em varios pontos "
                        "de entrada, nao apenas no periodo completo."
                    ),
                    "watch_out": (
                        "Boa taxa de vitoria historica reduz a dependencia do ponto inicial, mas "
                        "nao elimina risco de ciclos futuros diferentes."
                    ),
                    "best_match_id": consistent.get("instrument_id"),
                    "best_match_label": consistent.get("label"),
                    "metric_label": f"Venceu em janelas de {consistent.get('window_years')} anos",
                    "metric_value": _safe_float(consistent.get("win_rate")),
                    "metric_kind": "percent",
                },
                decision_profile,
                decision_id="consistency",
            )
        )
    cards = sorted(cards, key=lambda item: float(item.get("fit_score", 0.0)), reverse=True)

    return {
        "title": "Como decidir em renda fixa",
        "plain_language_summary": (
            "A melhor renda fixa depende do prazo e da funcao do dinheiro. CDI/SELIC costuma "
            "ser conforto e liquidez; IPCA+ costuma ser poder de compra; prefixado e uma aposta "
            "mais direta na taxa contratada."
        ),
        "study_label": fixed_income_backtest.get("selected_study_label"),
        "tax_treatment": fixed_income_backtest.get("tax_treatment")
        or methodology.get("tax_treatment"),
        "window_frequency": methodology.get("window_frequency_effective")
        or fixed_income_backtest.get("window_frequency"),
        "decision_profile": decision_profile,
        "profile_summary": _fixed_income_profile_summary(decision_profile, cards),
        "decision_cards": cards,
        "next_questions": [
            "Quando eu preciso desse dinheiro de volta?",
            "Eu aguentaria ver queda temporaria por marcacao a mercado?",
            "Preciso de liquidez diaria ou posso carregar ate o vencimento?",
            "Estou olhando retorno bruto, liquido ou real?",
        ],
    }


def build_portfolio_objective_summary(
    *,
    results: list[dict[str, Any]],
    fixed_income_backtest: dict[str, Any] | None,
    decision_profile: dict[str, Any],
) -> dict[str, Any]:
    """Compare the same result set through common investor objectives."""

    if not results:
        return {
            "title": "Decisao por objetivo",
            "plain_language_summary": (
                "Rode uma comparacao para ver qual ativo combina com cada objetivo."
            ),
            "objectives": [],
            "portfolio_rows": [],
            "decision_profile": decision_profile,
            "scenario_cards": [],
            "next_steps": [],
        }

    best_final = max(results, key=lambda row: _safe_float(row.get("final_value")))
    best_real = max(results, key=lambda row: _safe_float(row.get("real_cagr")))
    defensive = max(results, key=lambda row: _safe_float(row.get("max_drawdown")))
    lowest_volatility = min(results, key=lambda row: _safe_float(row.get("annual_volatility")))
    portfolio_rows = [row for row in results if row.get("component_breakdown")]
    fixed_income_rows = [
        row
        for row in results
        if row.get("source_kind")
        in {"fixed_income_index", "tesouro_direct_strategy", "selic_proxy", "rate_proxy"}
    ]

    objectives = [
        _with_objective_fit(
            _objective(
                objective_id="grow_final_wealth",
                label="Maximizar patrimonio final",
                question="Quem teria transformado o mesmo fluxo no maior valor final?",
                row=best_final,
                reason="Bom para enxergar o vencedor bruto do periodo escolhido.",
                tradeoff=(
                    "Pode esconder volatilidade, drawdown e risco de depender de um unico ciclo."
                ),
                metric_label="Valor final",
                metric_key="final_value",
                metric_kind="currency",
            ),
            decision_profile,
            objective_id="grow_final_wealth",
        ),
        _with_objective_fit(
            _objective(
                objective_id="protect_purchasing_power",
                label="Ganhar poder de compra",
                question="Quem mais cresceu acima do IPCA?",
                row=best_real,
                reason=(
                    "Ajuda a separar ganho nominal de ganho que realmente aumentou poder "
                    "de compra."
                ),
                tradeoff="Pode favorecer ativos com oscilacoes que exigem horizonte e disciplina.",
                metric_label="CAGR real",
                metric_key="real_cagr",
                metric_kind="percent",
            ),
            decision_profile,
            objective_id="protect_purchasing_power",
        ),
        _with_objective_fit(
            _objective(
                objective_id="reduce_drawdown",
                label="Sofrer menos no caminho",
                question="Quem teve a menor queda maxima no periodo?",
                row=defensive,
                reason="Util para dinheiro com menor tolerancia a sustos.",
                tradeoff="Normalmente troca parte do potencial de retorno por estabilidade.",
                metric_label="Drawdown maximo",
                metric_key="max_drawdown",
                metric_kind="percent",
            ),
            decision_profile,
            objective_id="reduce_drawdown",
        ),
        _with_objective_fit(
            _objective(
                objective_id="smooth_ride",
                label="Buscar caminho mais calmo",
                question="Quem teve menor volatilidade anualizada?",
                row=lowest_volatility,
                reason="Ajuda a diferenciar conforto de extrato de retorno final.",
                tradeoff=(
                    "Volatilidade baixa nao garante liquidez, retorno real nem protecao "
                    "tributaria."
                ),
                metric_label="Volatilidade anual",
                metric_key="annual_volatility",
                metric_kind="percent",
            ),
            decision_profile,
            objective_id="smooth_ride",
        ),
    ]

    if portfolio_rows:
        best_portfolio = max(portfolio_rows, key=lambda row: _safe_float(row.get("final_value")))
        objectives.append(
            _with_objective_fit(
                _objective(
                    objective_id="compare_allocation",
                    label="Comparar carteira",
                    question="Minha combinacao ficou melhor que apostas isoladas?",
                    row=best_portfolio,
                    reason=(
                        "Carteiras mostram diversificacao, rebalanceamento e contribuicao por "
                        "sleeve."
                    ),
                    tradeoff=(
                        "O resultado depende dos pesos escolhidos e nao otimiza a carteira "
                        "automaticamente."
                    ),
                    metric_label="Valor final da carteira",
                    metric_key="final_value",
                    metric_kind="currency",
                ),
                decision_profile,
                objective_id="compare_allocation",
            )
        )

    if fixed_income_rows:
        best_fixed_income = max(
            fixed_income_rows,
            key=lambda row: _safe_float(row.get("real_cagr")),
        )
        objectives.append(
            _with_objective_fit(
                _objective(
                    objective_id="fixed_income_role",
                    label="Escolher renda fixa por funcao",
                    question="Qual linha de renda fixa melhor protegeu retorno real neste recorte?",
                    row=best_fixed_income,
                    reason=(
                        "Ajuda a comparar CDI, IPCA+, prefixado e estrategias de Tesouro sem "
                        "tratar tudo como a mesma coisa."
                    ),
                    tradeoff=(
                        "Indice, ETF e titulo real podem divergir por impostos, duration, "
                        "liquidez e marcacao a mercado."
                    ),
                    metric_label="CAGR real",
                    metric_key="real_cagr",
                    metric_kind="percent",
                ),
                decision_profile,
                objective_id="fixed_income_role",
            )
        )
    objectives = sorted(
        objectives, key=lambda item: float(item.get("fit_score", 0.0)), reverse=True
    )
    scenario_cards = _build_goal_scenarios(
        results=results,
        portfolio_rows=portfolio_rows,
        decision_profile=decision_profile,
    )

    return {
        "title": "Decisao por objetivo",
        "plain_language_summary": (
            "Nao existe uma melhor escolha universal. A mesma simulacao pode apontar respostas "
            "diferentes para crescer patrimonio, preservar poder de compra, sofrer menos ou "
            "avaliar uma carteira."
        ),
        "objectives": objectives,
        "portfolio_rows": [_portfolio_row(row) for row in portfolio_rows],
        "fixed_income_study_available": fixed_income_backtest is not None,
        "decision_profile": decision_profile,
        "scenario_cards": scenario_cards,
        "profile_summary": _portfolio_profile_summary(decision_profile, objectives),
        "next_steps": [
            "Use o vencedor historico como hipotese, nao como ordem de compra.",
            (
                "Troque o periodo visual no grafico para ver se a conclusao depende de "
                "uma janela especifica."
            ),
            (
                "Compare pelo menos uma carteira diversificada contra ativos isolados "
                "antes de decidir."
            ),
        ],
    }


def _decision_card(
    *,
    decision_id: str,
    label: str,
    when_it_fits: str,
    watch_out: str,
    row: dict[str, Any],
    metric_label: str,
    metric_key: str,
    metric_kind: str,
) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "label": label,
        "when_it_fits": when_it_fits,
        "watch_out": watch_out,
        "best_match_id": row.get("instrument_id"),
        "best_match_label": row.get("label"),
        "metric_label": metric_label,
        "metric_value": _safe_float(row.get(metric_key)),
        "metric_kind": metric_kind,
    }


def _objective(
    *,
    objective_id: str,
    label: str,
    question: str,
    row: dict[str, Any],
    reason: str,
    tradeoff: str,
    metric_label: str,
    metric_key: str,
    metric_kind: str,
) -> dict[str, Any]:
    return {
        "objective_id": objective_id,
        "label": label,
        "question": question,
        "best_match_id": row.get("instrument_id"),
        "best_match_label": row.get("label"),
        "reason": reason,
        "tradeoff": tradeoff,
        "metric_label": metric_label,
        "metric_value": _safe_float(row.get(metric_key)),
        "metric_kind": metric_kind,
    }


def _with_fit(
    card: dict[str, Any],
    profile: dict[str, Any],
    *,
    decision_id: str,
) -> dict[str, Any]:
    score = _fixed_income_fit_score(decision_id, profile)
    return {
        **card,
        "fit_score": score,
        "fit_label": _fit_label(score),
        "profile_reason": _fixed_income_fit_reason(decision_id, profile, score),
    }


def _with_objective_fit(
    objective: dict[str, Any],
    profile: dict[str, Any],
    *,
    objective_id: str,
) -> dict[str, Any]:
    score = _objective_fit_score(objective_id, profile)
    return {
        **objective,
        "fit_score": score,
        "fit_label": _fit_label(score),
        "profile_reason": _objective_fit_reason(objective_id, profile, score),
    }


def _fixed_income_fit_score(decision_id: str, profile: dict[str, Any]) -> float:
    score = 45.0
    objective = profile["objective"]
    horizon = int(profile["horizon_years"])
    liquidity = profile["liquidity_need"]
    tolerance = profile["mark_to_market_tolerance"]

    if decision_id == "liquidity_and_reserve":
        score += 25 if liquidity == "daily" else 10 if liquidity == "monthly" else -10
        score += 20 if tolerance == "low" else 5 if tolerance == "medium" else -5
        score += 20 if objective in {"reserve", "balanced"} else 0
        score += 5 if horizon <= 3 else -5
    elif decision_id == "real_return":
        score += 25 if objective in {"real_return", "retirement", "balanced"} else 5
        score += 20 if horizon >= 5 else -10
        score += 15 if liquidity == "long_term" else 0
        score += 10 if tolerance in {"medium", "high"} else -10
    elif decision_id == "nominal_rate_lock":
        score += 20 if objective in {"growth", "income"} else 0
        score += 15 if horizon >= 3 else -15
        score += 15 if tolerance == "high" else 0 if tolerance == "medium" else -15
        score += 10 if liquidity == "long_term" else -5
    elif decision_id == "consistency":
        score += 20 if objective in {"balanced", "retirement", "income"} else 5
        score += 15 if tolerance in {"low", "medium"} else 0
        score += 10 if horizon >= 5 else 0
    return _bounded_score(score)


def _objective_fit_score(objective_id: str, profile: dict[str, Any]) -> float:
    score = 45.0
    objective = profile["objective"]
    horizon = int(profile["horizon_years"])
    liquidity = profile["liquidity_need"]
    tolerance = profile["mark_to_market_tolerance"]

    if objective_id == "grow_final_wealth":
        score += 30 if objective == "growth" else 10 if objective == "balanced" else 0
        score += 15 if horizon >= 5 else -5
        score += 10 if tolerance == "high" else 0
    elif objective_id == "protect_purchasing_power":
        score += 30 if objective in {"real_return", "retirement"} else 10
        score += 15 if horizon >= 5 else -5
        score += 10 if liquidity == "long_term" else 0
    elif objective_id == "reduce_drawdown":
        score += 25 if objective in {"reserve", "retirement"} else 5
        score += 20 if tolerance == "low" else 5 if tolerance == "medium" else -10
        score += 15 if liquidity == "daily" else 0
    elif objective_id == "smooth_ride":
        score += 20 if objective in {"reserve", "balanced", "retirement"} else 0
        score += 15 if tolerance in {"low", "medium"} else 0
    elif objective_id == "compare_allocation":
        score += 25 if objective in {"balanced", "retirement", "income"} else 5
        score += 10 if horizon >= 3 else 0
    elif objective_id == "fixed_income_role":
        score += 25 if objective in {"reserve", "real_return", "income", "retirement"} else 5
        score += 10 if tolerance in {"low", "medium"} else 0
    return _bounded_score(score)


def _fit_label(score: float) -> str:
    if score >= 75:
        return "Alta aderencia ao perfil"
    if score >= 55:
        return "Aderencia media ao perfil"
    return "Baixa aderencia ao perfil"


def _fixed_income_fit_reason(
    decision_id: str,
    profile: dict[str, Any],
    score: float,
) -> str:
    prefix = _fit_label(score)
    if decision_id == "liquidity_and_reserve":
        return (
            f"{prefix}: combina melhor quando liquidez e baixo susto pesam mais que "
            "retorno maximo."
        )
    if decision_id == "real_return":
        return (
            f"{prefix}: fica mais forte quando o prazo e longo e o objetivo e preservar "
            "poder de compra."
        )
    if decision_id == "nominal_rate_lock":
        return f"{prefix}: exige aceitar risco de inflacao e marcacao a mercado no meio do caminho."
    return f"{prefix}: ajuda a reduzir dependencia de uma unica data inicial."


def _objective_fit_reason(
    objective_id: str,
    profile: dict[str, Any],
    score: float,
) -> str:
    prefix = _fit_label(score)
    if objective_id == "grow_final_wealth":
        return f"{prefix}: prioriza maior valor final e aceita mais variacao no caminho."
    if objective_id == "protect_purchasing_power":
        return f"{prefix}: prioriza ganho real acima do IPCA no horizonte informado."
    if objective_id == "reduce_drawdown":
        return f"{prefix}: prioriza reduzir sustos e quedas temporarias."
    if objective_id == "smooth_ride":
        return f"{prefix}: prioriza um trajeto mais estavel no extrato."
    if objective_id == "compare_allocation":
        return f"{prefix}: avalia se uma mistura de ativos funciona melhor que apostas isoladas."
    return f"{prefix}: conecta renda fixa a funcao do dinheiro no seu plano."


def _fixed_income_profile_summary(
    profile: dict[str, Any],
    cards: list[dict[str, Any]],
) -> str:
    if not cards:
        return "O perfil foi registrado, mas nao ha cartoes de renda fixa para ranquear."
    leader = cards[0]
    return (
        f"Para {profile['objective_label'].lower()}, prazo de {profile['horizon_years']} ano(s) "
        f"e liquidez '{profile['liquidity_need_label'].lower()}', a leitura mais aderente "
        f"comeca por {leader['label'].lower()}."
    )


def _portfolio_profile_summary(
    profile: dict[str, Any],
    objectives: list[dict[str, Any]],
) -> str:
    if not objectives:
        return "O perfil foi registrado, mas ainda nao ha objetivos ranqueados."
    leader = objectives[0]
    return (
        f"Com objetivo de {profile['objective_label'].lower()}, a primeira lente de leitura e "
        f"'{leader['label']}', mas a decisao final ainda deve considerar liquidez, impostos e "
        "tolerancia a quedas."
    )


def _build_goal_scenarios(
    *,
    results: list[dict[str, Any]],
    portfolio_rows: list[dict[str, Any]],
    decision_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    best_final = max(results, key=lambda row: _safe_float(row.get("final_value")))
    best_real = max(results, key=lambda row: _safe_float(row.get("real_cagr")))
    defensive = max(results, key=lambda row: _safe_float(row.get("max_drawdown")))
    preferred_allocation = (
        max(portfolio_rows, key=lambda row: _safe_float(row.get("final_value")))
        if portfolio_rows
        else best_final
    )
    target = _safe_float(decision_profile.get("monthly_income_target"))
    monthly_income_4pct = _safe_float(preferred_allocation.get("final_value")) * 0.04 / 12.0
    scenarios = [
        {
            "scenario_id": "income_capacity_4pct",
            "label": "Renda potencial com regra de 4%",
            "description": (
                "Estimativa simples de quanto o patrimonio final poderia sustentar por mes "
                "antes de impostos, inflacao futura e rebalanceamentos."
            ),
            "best_match_id": preferred_allocation.get("instrument_id"),
            "best_match_label": preferred_allocation.get("label"),
            "metric_label": "Renda mensal estimada",
            "metric_value": monthly_income_4pct,
            "metric_kind": "currency",
            "target_value": target,
            "target_met": monthly_income_4pct >= target if target > 0 else None,
        },
        {
            "scenario_id": "retirement_real_return",
            "label": "Aposentadoria e poder de compra",
            "description": (
                "Usa o melhor CAGR real como alerta de quem mais protegeu poder de compra "
                "no periodo."
            ),
            "best_match_id": best_real.get("instrument_id"),
            "best_match_label": best_real.get("label"),
            "metric_label": "CAGR real",
            "metric_value": _safe_float(best_real.get("real_cagr")),
            "metric_kind": "percent",
            "target_value": None,
            "target_met": None,
        },
        {
            "scenario_id": "capital_preservation",
            "label": "Preservacao de capital",
            "description": "Mostra a linha que sofreu a menor queda maxima no recorte.",
            "best_match_id": defensive.get("instrument_id"),
            "best_match_label": defensive.get("label"),
            "metric_label": "Drawdown maximo",
            "metric_value": _safe_float(defensive.get("max_drawdown")),
            "metric_kind": "percent",
            "target_value": None,
            "target_met": None,
        },
    ]
    if decision_profile["objective"] in {"growth", "balanced"}:
        scenarios.insert(
            1,
            {
                "scenario_id": "wealth_accumulation",
                "label": "Acumulacao de patrimonio",
                "description": "Mostra quem terminou com maior patrimonio no fluxo simulado.",
                "best_match_id": best_final.get("instrument_id"),
                "best_match_label": best_final.get("label"),
                "metric_label": "Valor final",
                "metric_value": _safe_float(best_final.get("final_value")),
                "metric_kind": "currency",
                "target_value": None,
                "target_met": None,
            },
        )
    return scenarios


def _build_realism_notes(fixed_income_backtest: dict[str, Any] | None) -> list[dict[str, Any]]:
    notes = [
        {
            "dimension": "Impostos",
            "status": "parcial",
            "note": (
                "Tesouro Direto pode usar visao liquida estimada; acoes, ETFs, FIIs e BDRs "
                "ainda nao simulam imposto individual."
            ),
        },
        {
            "dimension": "Taxas e custos",
            "status": "pendente",
            "note": (
                "Taxas de administracao de ETFs/fundos, corretagem e spreads ainda nao sao "
                "modelados por produto."
            ),
        },
        {
            "dimension": "Liquidez",
            "status": "didatico",
            "note": (
                "A liquidez entra como orientacao de decisao, mas o motor ainda nao limita "
                "execucao por volume ou prazo de resgate."
            ),
        },
        {
            "dimension": "Inflacao",
            "status": "implementado",
            "note": "O retorno real deflaciona as curvas pelo IPCA mensal disponivel.",
        },
    ]
    if fixed_income_backtest is not None:
        notes.append(
            {
                "dimension": "Marcacao a mercado",
                "status": "implementado para estudos de renda fixa",
                "note": (
                    "IDkA e Tesouro Direto capturam oscilacao de precos; proxies de taxa fixa "
                    "continuam sendo simplificacoes."
                ),
            }
        )
    return notes


def _bounded_score(score: float) -> float:
    return max(0.0, min(100.0, float(score)))


def _portfolio_row(row: dict[str, Any]) -> dict[str, Any]:
    components = row.get("component_breakdown") or []
    categories = row.get("category_breakdown") or []
    return {
        "instrument_id": row.get("instrument_id"),
        "label": row.get("label"),
        "source_kind": row.get("source_kind"),
        "final_value": _safe_float(row.get("final_value")),
        "real_cagr": _safe_float(row.get("real_cagr")),
        "max_drawdown": _safe_float(row.get("max_drawdown")),
        "component_count": len(components),
        "top_components": [
            {
                "label": item.get("label"),
                "target_weight": _safe_float(item.get("target_weight")),
                "ending_weight": _safe_float(item.get("ending_weight")),
                "final_value": _safe_float(item.get("final_value")),
            }
            for item in components[:5]
        ],
        "category_breakdown": [
            {
                "label": item.get("category_label"),
                "target_weight": _safe_float(item.get("target_weight")),
                "ending_weight": _safe_float(item.get("ending_weight")),
                "final_value": _safe_float(item.get("final_value")),
            }
            for item in categories[:5]
        ],
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default
