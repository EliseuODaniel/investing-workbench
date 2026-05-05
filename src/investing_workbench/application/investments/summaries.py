"""Summary builders for investment comparison payloads."""

from __future__ import annotations

from typing import Any


def build_class_summary(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate comparison rows by asset class for the frontend overview."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(str(result["category_label"]), []).append(result)

    summary: list[dict[str, Any]] = []
    for category_label, items in grouped.items():
        summary.append(
            {
                "category_label": category_label,
                "asset_count": len(items),
                "average_final_value": _mean(items, "final_value"),
                "average_cagr": _mean(items, "cagr"),
                "average_real_cagr": _mean(items, "real_cagr"),
                "average_max_drawdown": _mean(items, "max_drawdown"),
                "leader_label": max(
                    items,
                    key=lambda item: float(item["final_value"]),
                )["label"],
            }
        )
    return sorted(summary, key=lambda item: item["average_final_value"], reverse=True)


def build_highlights(
    results: list[dict[str, Any]],
    benchmarks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build top-level result highlights and plain-language insight bullets."""

    ordered = sorted(results, key=lambda item: float(item["final_value"]), reverse=True)
    best = ordered[0]
    best_real = max(results, key=lambda item: float(item["real_cagr"]))
    defensive = max(results, key=lambda item: float(item["max_drawdown"]))
    selic = next((item for item in benchmarks if item["benchmark_id"] == "selic_cash"), None)
    bova11 = next((item for item in benchmarks if item["benchmark_id"] == "bova11"), None)

    beat_inflation_count = sum(
        1
        for item in results
        if float(item["final_value_real"]) > float(item["invested_total_real"])
    )
    insights = [
        f"{best['label']} foi o melhor comparativo em valor final nominal no periodo.",
        (
            f"{best_real['label']} entregou o melhor CAGR real, ou seja, "
            "o melhor ganho de poder de compra."
        ),
        (f"{defensive['label']} teve a queda maxima menos dolorosa " "entre os ativos escolhidos."),
        (
            f"{beat_inflation_count} de {len(results)} comparativos preservaram "
            "ou ampliaram poder de compra acima da inflacao."
        ),
    ]
    if selic is not None:
        beat_count = _count_beating(results, selic)
        insights.append(
            f"{beat_count} de {len(results)} investimentos terminaram acima da "
            "referencia de SELIC."
        )
    if bova11 is not None:
        beat_count = _count_beating(results, bova11)
        insights.append(
            f"{beat_count} de {len(results)} investimentos superaram o BOVA11 "
            "no mesmo fluxo de aportes."
        )

    return {
        "best_final_value": best,
        "best_real_cagr": best_real,
        "most_defensive": defensive,
        "beats_selic_count": _count_beating(results, selic),
        "beats_bova11_count": _count_beating(results, bova11),
        "beats_inflation_count": beat_inflation_count,
        "insights": insights,
    }


def build_result_stories(
    results: list[dict[str, Any]],
    benchmarks: list[dict[str, Any]],
    decision_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build didactic stories and rankings from comparison rows."""

    normalized_profile = decision_profile or {}
    objective = str(normalized_profile.get("objective", "balanced")).lower()
    profile_match = _best_match_for_profile(results, objective)
    profile_fit = _profile_fit_score(profile_match, objective)

    best_final = max(results, key=lambda item: float(item["final_value"]))
    best_real = max(results, key=lambda item: float(item["real_cagr"]))
    most_defensive = max(results, key=lambda item: float(item["max_drawdown"]))
    lowest_volatility = min(results, key=lambda item: float(item["annual_volatility"]))
    best_income = max(results, key=lambda item: float(item["net_profit"]))
    most_stressed = min(results, key=lambda item: float(item["max_drawdown"]))
    selic = next((item for item in benchmarks if item["benchmark_id"] == "selic_cash"), None)
    bova11 = next((item for item in benchmarks if item["benchmark_id"] == "bova11"), None)
    beat_selic_count = _count_beating(results, selic)
    beat_bova11_count = _count_beating(results, bova11)
    beat_inflation_count = sum(
        1
        for item in results
        if float(item["final_value_real"]) > float(item["invested_total_real"])
    )

    stories = [
        {
            "story_id": "highest_final_value",
            "label": "Quem terminou com mais dinheiro",
            "question": "Se eu olhasse so para o valor final, quem ganhou?",
            "winner_id": best_final["instrument_id"],
            "winner_label": best_final["label"],
            "metric_label": "Valor final",
            "metric_value": float(best_final["final_value"]),
            "metric_kind": "currency",
            "interpretation": (
                f"{best_final['label']} terminou com o maior patrimonio nominal no periodo."
            ),
            "caveat": (
                "Valor final nao mostra sozinho quanto risco, queda no caminho ou inflacao "
                "o investidor precisou aceitar."
            ),
        },
        {
            "story_id": "inflation_protection",
            "label": "Quem protegeu melhor contra inflacao",
            "question": "Quem mais aumentou poder de compra?",
            "winner_id": best_real["instrument_id"],
            "winner_label": best_real["label"],
            "metric_label": "CAGR real",
            "metric_value": float(best_real["real_cagr"]),
            "metric_kind": "percent",
            "interpretation": (
                f"{best_real['label']} teve o melhor retorno real anualizado. "
                f"{beat_inflation_count} de {len(results)} comparativos ficaram acima "
                "da inflacao acumulada."
            ),
            "caveat": (
                "Retorno real depende do IPCA usado e nao garante preservacao de poder "
                "de compra em janelas futuras."
            ),
        },
        {
            "story_id": "best_profile_match",
            "label": "Qual escolha fez mais sentido para seu perfil",
            "question": "Qual linha conversa melhor com a meta informada?",
            "winner_id": profile_match["instrument_id"],
            "winner_label": profile_match["label"],
            "metric_label": "Fit didatico",
            "metric_value": profile_fit,
            "metric_kind": "percent",
            "interpretation": (
                f"{profile_match['label']} foi a linha com melhor "
                f"compatibilidade com objetivo "
                f"'{normalized_profile.get('objective_label', objective)}'."
            ),
            "caveat": (
                "A compatibilidade é uma diretriz didatica baseada nos dados simulados; o "
                "melhor ajuste pode mudar com horizonte, liquidez e impostos reais."
            ),
        },
        {
            "story_id": "least_painful_drawdown",
            "label": "Quem caiu menos",
            "question": "Qual alternativa foi mais defensiva no caminho?",
            "winner_id": most_defensive["instrument_id"],
            "winner_label": most_defensive["label"],
            "metric_label": "Drawdown maximo",
            "metric_value": float(most_defensive["max_drawdown"]),
            "metric_kind": "percent",
            "interpretation": (
                f"{most_defensive['label']} teve a menor queda maxima entre os comparativos."
            ),
            "caveat": (
                "Menor drawdown pode vir junto de menor retorno esperado; use junto com "
                "retorno real e objetivo do investidor."
            ),
        },
        {
            "story_id": "lowest_volatility",
            "label": "Quem oscilou menos",
            "question": "Qual linha foi mais estável?",
            "winner_id": lowest_volatility["instrument_id"],
            "winner_label": lowest_volatility["label"],
            "metric_label": "Volatilidade anual",
            "metric_value": float(lowest_volatility["annual_volatility"]),
            "metric_kind": "percent",
            "interpretation": (
                f"{lowest_volatility['label']} teve a menor volatilidade anualizada."
            ),
            "caveat": (
                "Volatilidade historica nao captura todos os riscos, como credito, liquidez, "
                "impostos ou mudanca estrutural do produto."
            ),
        },
        {
            "story_id": "most_stressed_drawdown",
            "label": "Quem sofreu mais marcacao a mercado",
            "question": "Qual linha mostrou pior estresse de perda pelo caminho?",
            "winner_id": most_stressed["instrument_id"],
            "winner_label": most_stressed["label"],
            "metric_label": "Drawdown mais negativo",
            "metric_value": float(most_stressed["max_drawdown"]),
            "metric_kind": "percent",
            "interpretation": (
                f"{most_stressed['label']} acumulou a queda máxima mais pronunciada nesse "
                "recorte."
            ),
            "caveat": (
                "Esse comportamento pode ainda ser aceitavel para objetivos de longo prazo, "
                "dependendo da tolerancia a queda no extrato."
            ),
        },
        {
            "story_id": "income_generation",
            "label": "Quem gerou mais renda acumulada",
            "question": "Qual alternativa acumulou mais lucro no periodo?",
            "winner_id": best_income["instrument_id"],
            "winner_label": best_income["label"],
            "metric_label": "Lucro acumulado",
            "metric_value": float(best_income["net_profit"]),
            "metric_kind": "currency",
            "interpretation": (
                f"{best_income['label']} gerou o maior lucro acumulado, embora sem separar "
                "renda e ganho de preço."
            ),
            "caveat": (
                "Lucro acumulado mistura valorizacao e efeitos de aportes e nao equivale "
                "a renda mensal disponivel no curto prazo."
            ),
        },
    ]
    if selic is not None:
        stories.append(
            {
                "story_id": "beat_selic",
                "label": "Quem bateu a Selic",
                "question": "Quantas escolhas compensaram sair do caixa?",
                "winner_id": None,
                "winner_label": None,
                "metric_label": "Acima da Selic",
                "metric_value": float(beat_selic_count or 0),
                "metric_kind": "count",
                "interpretation": (
                    f"{beat_selic_count} de {len(results)} comparativos terminaram acima "
                    f"de {selic['label']}."
                ),
                "caveat": (
                    "Bater a Selic em valor final nao significa que o risco assumido fez "
                    "sentido para todo perfil."
                ),
            }
        )
    if bova11 is not None:
        stories.append(
            {
                "story_id": "beat_bova11",
                "label": "Quem bateu o BOVA11",
                "question": "Quantas alternativas superaram a bolsa ampla?",
                "winner_id": None,
                "winner_label": None,
                "metric_label": "Acima do BOVA11",
                "metric_value": float(beat_bova11_count or 0),
                "metric_kind": "count",
                "interpretation": (
                    f"{beat_bova11_count} de {len(results)} comparativos terminaram acima "
                    f"de {bova11['label']}."
                ),
                "caveat": (
                    "Comparar contra BOVA11 ajuda a medir custo de oportunidade, mas nao "
                    "substitui comparar risco, diversificacao e horizonte."
                ),
            }
        )

    return {
        "title": "Leituras guiadas do resultado",
        "plain_language_summary": (
            "Estas leituras transformam a tabela em perguntas praticas: quem ganhou, "
            "quem preservou poder de compra, quem caiu menos e quem superou benchmarks."
        ),
        "stories": stories,
        "rankings": [
            _ranking(
                ranking_id="final_value",
                label="Ranking por valor final",
                metric_label="Valor final",
                metric_kind="currency",
                rows=results,
                key="final_value",
                reverse=True,
            ),
            _ranking(
                ranking_id="real_cagr",
                label="Ranking por retorno real",
                metric_label="CAGR real",
                metric_kind="percent",
                rows=results,
                key="real_cagr",
                reverse=True,
            ),
            _ranking(
                ranking_id="drawdown",
                label="Ranking defensivo",
                metric_label="Drawdown maximo",
                metric_kind="percent",
                rows=results,
                key="max_drawdown",
                reverse=True,
            ),
            _ranking(
                ranking_id="volatility",
                label="Ranking por menor oscilacao",
                metric_label="Volatilidade anual",
                metric_kind="percent",
                rows=results,
                key="annual_volatility",
                reverse=False,
            ),
            _ranking(
                ranking_id="income_generation",
                label="Ranking por renda acumulada",
                metric_label="Lucro acumulado",
                metric_kind="currency",
                rows=results,
                key="net_profit",
                reverse=True,
            ),
            _ranking(
                ranking_id="mark_to_market_stress",
                label="Ranking por marcacao a mercado",
                metric_label="Drawdown mais negativo",
                metric_kind="percent",
                rows=results,
                key="max_drawdown",
                reverse=False,
            ),
        ],
        "next_questions": [
            "A melhor linha tambem combina com seu prazo e liquidez?",
            "O retorno real veio com quedas que voce toleraria?",
            "O produto usado e compravel ou e indice/proxy didatico?",
            "Sua meta de renda mensal foi respeitada com segurança em algum ativo?",
        ],
    }


def _mean(items: list[dict[str, Any]], key: str) -> float:
    return float(sum(float(item[key]) for item in items) / len(items))


def _ranking(
    *,
    ranking_id: str,
    label: str,
    metric_label: str,
    metric_kind: str,
    rows: list[dict[str, Any]],
    key: str,
    reverse: bool,
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: float(item[key]), reverse=reverse)
    return {
        "ranking_id": ranking_id,
        "label": label,
        "metric_label": metric_label,
        "metric_kind": metric_kind,
        "rows": [
            {
                "rank": position,
                "instrument_id": item["instrument_id"],
                "label": item["label"],
                "category_label": item["category_label"],
                "value": float(item[key]),
            }
            for position, item in enumerate(ordered[:8], start=1)
        ],
    }


def _safe_metric(row: dict[str, Any], key: str) -> float:
    try:
        return float(row[key])
    except (TypeError, ValueError, KeyError):
        return 0.0


def _best_match_for_profile(
    results: list[dict[str, Any]],
    objective: str,
) -> dict[str, Any]:
    objective_key = objective.lower()

    if objective_key in {"income", "income_cashflow", "renda"}:
        return max(results, key=lambda row: _safe_metric(row, "net_profit"))
    if objective_key in {"reserve", "real_return", "retirement"}:
        return max(results, key=lambda row: _safe_metric(row, "real_cagr"))
    if objective_key in {"growth", "balanced"}:
        return max(results, key=lambda row: _safe_metric(row, "final_value"))
    return max(results, key=lambda row: _safe_metric(row, "real_cagr"))


def _profile_fit_score(row: dict[str, Any], objective: str) -> float:
    objective_key = objective.lower()
    if objective_key in {"income", "income_cashflow", "renda"}:
        invested = abs(_safe_metric(row, "invested_total"))
        return min(1.0, max(0.0, _safe_metric(row, "net_profit") / max(1.0, invested)))
    if objective_key in {"reserve", "retirement"}:
        return min(1.0, max(0.0, 1.0 + _safe_metric(row, "max_drawdown")))
    if objective_key in {"growth", "balanced"}:
        return min(1.0, max(0.0, _safe_metric(row, "real_cagr")))
    return min(1.0, max(0.0, _safe_metric(row, "real_cagr")))


def _count_beating(
    results: list[dict[str, Any]],
    benchmark: dict[str, Any] | None,
) -> int | None:
    if benchmark is None:
        return None
    return sum(
        1 for item in results if float(item["final_value"]) > float(benchmark["final_value"])
    )
