"""Market ranking builders for investment comparison results."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from .result_payloads import time_weighted_returns
from .simulation_models import SimulationResult


def build_market_rankings(
    *,
    results: list[dict[str, Any]],
    benchmarks: list[dict[str, Any]],
    decision_profile: dict[str, Any] | None = None,
    simulation_results: list[SimulationResult] | None = None,
    benchmark_results: dict[str, SimulationResult] | None = None,
    beta_reference_id: str | None = None,
) -> dict[str, Any]:
    """Build QuantBrasil-inspired ranking tables from the current comparison universe."""

    normalized_profile = decision_profile or {}
    market_analytics = _build_market_analytics(
        simulation_results=simulation_results or [],
        benchmark_results=benchmark_results or {},
        beta_reference_id=beta_reference_id,
    )
    ranking_rows = [
        _ranking_base_row(item, analytics=market_analytics.get(str(item["instrument_id"]), {}))
        for item in results
    ]
    benchmark_rows = [_ranking_base_row(item, is_benchmark=True) for item in benchmarks]
    as_of_date = _latest_date(results + benchmarks, "availability_end")
    selected_count = len(results)

    rankings = [
        _ranking(
            ranking_id="period_return",
            label="Retorno no periodo",
            metric_label="Retorno sobre aportes",
            metric_kind="percent",
            rows=ranking_rows,
            value_key="total_return_on_invested",
            reverse=True,
            methodology=(
                "Ordena as alternativas pelo ganho total sobre o capital aportado no periodo "
                "selecionado."
            ),
        ),
        _ranking(
            ranking_id="real_return",
            label="Retorno real",
            metric_label="CAGR real",
            metric_kind="percent",
            rows=ranking_rows,
            value_key="real_cagr",
            reverse=True,
            methodology=(
                "Ordena pelo retorno anualizado depois de deflacionar a curva pelo IPCA "
                "mensal usado no estudo."
            ),
        ),
        _ranking(
            ranking_id="drawdown",
            label="Menor queda",
            metric_label="Drawdown maximo",
            metric_kind="percent",
            rows=ranking_rows,
            value_key="max_drawdown",
            reverse=True,
            methodology=(
                "Ordena da menor queda historica para a maior queda dentro do recorte " "comparado."
            ),
        ),
        _ranking(
            ranking_id="volatility",
            label="Baixa oscilacao",
            metric_label="Volatilidade anual",
            metric_kind="percent",
            rows=ranking_rows,
            value_key="annual_volatility",
            reverse=False,
            methodology=(
                "Ordena pela volatilidade anualizada estimada a partir da curva de retorno "
                "do estudo."
            ),
        ),
        _ranking(
            ranking_id="momentum_6m",
            label="Momentum recente",
            metric_label="Retorno TWR 6m",
            metric_kind="percent",
            rows=ranking_rows,
            value_key="momentum_6m",
            reverse=True,
            methodology=(
                "Ordena pelo retorno time-weighted aproximado dos ultimos 126 pregoes "
                "disponiveis na curva simulada."
            ),
        ),
        _ranking(
            ranking_id="ath_distance",
            label="Distancia do topo",
            metric_label="Queda desde o topo",
            metric_kind="percent",
            rows=ranking_rows,
            value_key="current_drawdown",
            reverse=True,
            methodology=(
                "Ordena ativos mais proximos do topo da propria curva no fim da janela; "
                "valores mais perto de zero indicam menor distancia do maximo historico."
            ),
        ),
        _ranking(
            ranking_id="beta_to_benchmark",
            label="Menor beta contra benchmark",
            metric_label="Beta",
            metric_kind="number",
            rows=ranking_rows,
            value_key="beta_to_reference",
            reverse=False,
            methodology=(
                "Calcula beta aproximado contra o benchmark de referencia usando retornos "
                "time-weighted alinhados; quando nao ha benchmark, a metrica fica neutra."
            ),
            sort_absolute=True,
        ),
        _guided_factor_ranking(
            rows=ranking_rows,
            objective=str(normalized_profile.get("objective", "balanced")),
        ),
    ]

    benchmark_context = []
    for benchmark in benchmark_rows:
        beat_count = sum(
            1
            for item in ranking_rows
            if float(item["final_value"]) > float(benchmark["final_value"])
        )
        benchmark_context.append(
            {
                "benchmark_id": benchmark["instrument_id"],
                "label": benchmark["label"],
                "metric_label": "Alternativas acima",
                "metric_kind": "count",
                "value": beat_count,
                "total": selected_count,
                "interpretation": (
                    f"{beat_count} de {selected_count} alternativas terminaram acima de "
                    f"{benchmark['label']} no mesmo fluxo de aportes."
                ),
            }
        )

    return {
        "title": "Rankings de mercado",
        "plain_language_summary": (
            "Listas inspiradas em exploradores quantitativos: retorno, retorno real, "
            "queda, oscilacao, momentum, distancia do topo, beta e um score fatorial "
            "simples para comparar as alternativas selecionadas sem transformar "
            "historico em recomendacao."
        ),
        "universe_label": f"{selected_count} alternativas selecionadas",
        "as_of_date": as_of_date,
        "source_label": "Dados locais/cacheados do Investing Workbench",
        "benchmark_context": benchmark_context,
        "rankings": rankings,
        "export_columns": [
            "ranking_id",
            "ranking_label",
            "rank",
            "instrument_id",
            "label",
            "category_label",
            "source_kind",
            "risk_label",
            "value",
            "secondary_value",
        ],
        "methodology_notes": [
            "Os rankings usam somente o universo selecionado no estudo atual.",
            "Retorno e risco usam o mesmo periodo, aportes e datas da comparacao.",
            (
                "O score fatorial e didatico: combina retorno real, retorno nominal, "
                "queda e volatilidade."
            ),
            (
                "Momentum, distancia do topo e beta usam as curvas simuladas do estudo; "
                "nao substituem indicadores de mercado calculados diretamente sobre preco."
            ),
            (
                "Listas WTD/MTD/YTD, VaR e fatores fundamentalistas dependem de um universo "
                "de mercado mais amplo e entram em ciclos posteriores."
            ),
        ],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _ranking_base_row(
    item: dict[str, Any],
    *,
    is_benchmark: bool = False,
    analytics: dict[str, float] | None = None,
) -> dict[str, Any]:
    market_analytics = analytics or {}
    return {
        "instrument_id": item.get("benchmark_id") or item["instrument_id"],
        "label": item["label"],
        "category_label": item.get("category_label", "Benchmark"),
        "source_kind": item.get("source_kind", "benchmark") if not is_benchmark else "benchmark",
        "risk_label": item.get("risk_label", "Referencia"),
        "total_return_on_invested": _safe_float(item, "total_return_on_invested"),
        "real_cagr": _safe_float(item, "real_cagr"),
        "max_drawdown": _safe_float(item, "max_drawdown"),
        "annual_volatility": _safe_float(item, "annual_volatility"),
        "final_value": _safe_float(item, "final_value"),
        "secondary_value": _safe_float(item, "final_value_real_net"),
        "momentum_6m": market_analytics.get("momentum_6m", 0.0),
        "current_drawdown": market_analytics.get("current_drawdown", 0.0),
        "beta_to_reference": market_analytics.get("beta_to_reference", 0.0),
    }


def _ranking(
    *,
    ranking_id: str,
    label: str,
    metric_label: str,
    metric_kind: str,
    rows: list[dict[str, Any]],
    value_key: str,
    reverse: bool,
    methodology: str,
    sort_absolute: bool = False,
) -> dict[str, Any]:
    ordered = sorted(
        rows,
        key=lambda item: abs(float(item[value_key])) if sort_absolute else float(item[value_key]),
        reverse=reverse,
    )
    return {
        "ranking_id": ranking_id,
        "label": label,
        "metric_label": metric_label,
        "metric_kind": metric_kind,
        "methodology": methodology,
        "rows": [
            {
                "rank": position,
                "instrument_id": item["instrument_id"],
                "label": item["label"],
                "category_label": item["category_label"],
                "source_kind": item["source_kind"],
                "risk_label": item["risk_label"],
                "value": float(item[value_key]),
                "secondary_value": float(item["secondary_value"]),
            }
            for position, item in enumerate(ordered[:8], start=1)
        ],
    }


def _guided_factor_ranking(
    *,
    rows: list[dict[str, Any]],
    objective: str,
) -> dict[str, Any]:
    real_scores = _normalize(rows, "real_cagr", higher_is_better=True)
    period_scores = _normalize(rows, "total_return_on_invested", higher_is_better=True)
    drawdown_scores = _normalize(rows, "max_drawdown", higher_is_better=True)
    volatility_scores = _normalize(rows, "annual_volatility", higher_is_better=False)

    weights = _factor_weights(objective)
    scored_rows = []
    for item in rows:
        instrument_id = str(item["instrument_id"])
        score = (
            weights["real_return"] * real_scores[instrument_id]
            + weights["period_return"] * period_scores[instrument_id]
            + weights["drawdown"] * drawdown_scores[instrument_id]
            + weights["volatility"] * volatility_scores[instrument_id]
        )
        scored_rows.append({**item, "guided_factor_score": score})

    return {
        "ranking_id": "guided_factor_score",
        "label": "Score fatorial guiado",
        "metric_label": "Score",
        "metric_kind": "percent",
        "methodology": (
            "Combina retorno real, retorno do periodo, drawdown e volatilidade com pesos "
            "ajustados ao objetivo informado no perfil."
        ),
        "weights": weights,
        "rows": [
            {
                "rank": position,
                "instrument_id": item["instrument_id"],
                "label": item["label"],
                "category_label": item["category_label"],
                "source_kind": item["source_kind"],
                "risk_label": item["risk_label"],
                "value": float(item["guided_factor_score"]),
                "secondary_value": float(item["real_cagr"]),
            }
            for position, item in enumerate(
                sorted(scored_rows, key=lambda row: row["guided_factor_score"], reverse=True)[:8],
                start=1,
            )
        ],
    }


def _factor_weights(objective: str) -> dict[str, float]:
    objective_key = objective.lower()
    if objective_key in {"reserve", "preservation"}:
        return {"real_return": 0.25, "period_return": 0.15, "drawdown": 0.35, "volatility": 0.25}
    if objective_key in {"growth", "accumulation"}:
        return {"real_return": 0.40, "period_return": 0.30, "drawdown": 0.15, "volatility": 0.15}
    if objective_key in {"income", "income_cashflow", "retirement"}:
        return {"real_return": 0.35, "period_return": 0.20, "drawdown": 0.25, "volatility": 0.20}
    return {"real_return": 0.35, "period_return": 0.25, "drawdown": 0.20, "volatility": 0.20}


def _build_market_analytics(
    *,
    simulation_results: list[SimulationResult],
    benchmark_results: dict[str, SimulationResult],
    beta_reference_id: str | None,
) -> dict[str, dict[str, float]]:
    reference_returns = _reference_returns(
        benchmark_results=benchmark_results,
        beta_reference_id=beta_reference_id,
    )
    analytics: dict[str, dict[str, float]] = {}
    for result in simulation_results:
        returns = time_weighted_returns(result.equity_curve, result.flow_curve)
        analytics[result.instrument.instrument_id] = {
            "momentum_6m": _trailing_return(returns, window=126),
            "current_drawdown": _current_drawdown(result.equity_curve),
            "beta_to_reference": _beta_to_reference(returns, reference_returns),
        }
    return analytics


def _reference_returns(
    *,
    benchmark_results: dict[str, SimulationResult],
    beta_reference_id: str | None,
) -> pd.Series | None:
    if not benchmark_results:
        return None
    reference = (
        benchmark_results.get(beta_reference_id or "")
        or benchmark_results.get("selic_cash")
        or next(iter(benchmark_results.values()))
    )
    return time_weighted_returns(reference.equity_curve, reference.flow_curve)


def _trailing_return(returns: pd.Series, *, window: int) -> float:
    if returns.empty:
        return 0.0
    trailing = returns.tail(window)
    value = float((1.0 + trailing).prod() - 1.0)
    return value if math.isfinite(value) else 0.0


def _current_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    peak = float(equity_curve.cummax().iloc[-1])
    current = float(equity_curve.iloc[-1])
    if peak <= 0:
        return 0.0
    value = current / peak - 1.0
    return value if math.isfinite(value) else 0.0


def _beta_to_reference(
    returns: pd.Series,
    reference_returns: pd.Series | None,
) -> float:
    if returns.empty or reference_returns is None or reference_returns.empty:
        return 0.0
    aligned = pd.concat(
        [returns.rename("asset"), reference_returns.rename("reference")],
        axis=1,
        sort=False,
    )
    aligned = aligned.dropna()
    if len(aligned) < 3:
        return 0.0
    reference_variance = float(aligned["reference"].var(ddof=0))
    if reference_variance <= 0:
        return 0.0
    beta = float(aligned["asset"].cov(aligned["reference"], ddof=0) / reference_variance)
    return beta if math.isfinite(beta) else 0.0


def _normalize(
    rows: list[dict[str, Any]],
    key: str,
    *,
    higher_is_better: bool,
) -> dict[str, float]:
    values = [float(item[key]) for item in rows]
    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        return {str(item["instrument_id"]): 1.0 for item in rows}
    scores: dict[str, float] = {}
    for item in rows:
        raw_score = (float(item[key]) - minimum) / (maximum - minimum)
        scores[str(item["instrument_id"])] = raw_score if higher_is_better else 1.0 - raw_score
    return scores


def _safe_float(item: dict[str, Any], key: str) -> float:
    try:
        return float(item.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _latest_date(items: list[dict[str, Any]], key: str) -> str | None:
    values = [str(item[key]) for item in items if item.get(key)]
    return max(values) if values else None
