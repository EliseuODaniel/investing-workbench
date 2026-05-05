"""Generic screener presets for the current investment comparison universe."""

from __future__ import annotations

from typing import Any, Callable


def build_market_screeners(
    *,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run reusable screener presets over comparison rows."""

    presets = [
        _preset(
            preset_id="positive_real_return",
            label="Retorno real positivo",
            rule_summary="CAGR real acima de zero.",
            rows=results,
            predicate=lambda row: _safe_float(row, "real_cagr") > 0,
            sort_key="real_cagr",
            reverse=True,
        ),
        _preset(
            preset_id="low_drawdown",
            label="Queda controlada",
            rule_summary="Drawdown maximo melhor que -10%.",
            rows=results,
            predicate=lambda row: _safe_float(row, "max_drawdown") >= -0.10,
            sort_key="max_drawdown",
            reverse=True,
        ),
        _preset(
            preset_id="low_volatility",
            label="Baixa oscilacao",
            rule_summary="Volatilidade anual abaixo de 12%.",
            rows=results,
            predicate=lambda row: _safe_float(row, "annual_volatility") <= 0.12,
            sort_key="annual_volatility",
            reverse=False,
        ),
        _preset(
            preset_id="income_candidates",
            label="Candidatos a renda",
            rule_summary="Lucro acumulado positivo e drawdown melhor que -20%.",
            rows=results,
            predicate=lambda row: _safe_float(row, "net_profit") > 0
            and _safe_float(row, "max_drawdown") >= -0.20,
            sort_key="net_profit",
            reverse=True,
        ),
    ]

    return {
        "title": "Screeners do universo comparado",
        "plain_language_summary": (
            "Um motor simples de filtros reaproveitaveis. Hoje ele roda sobre o universo "
            "selecionado; depois pode receber indicadores como IFR, Bollinger e momentum."
        ),
        "universe_count": len(results),
        "presets": presets,
        "methodology_notes": [
            "Cada screener declara a regra, o universo e a ordenacao usada.",
            "Os filtros nao recomendam compra; eles ajudam a separar candidatos para estudo.",
            "A mesma estrutura comporta presets tecnicos futuros sem criar telas hard-coded.",
        ],
    }


def _preset(
    *,
    preset_id: str,
    label: str,
    rule_summary: str,
    rows: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
    sort_key: str,
    reverse: bool,
) -> dict[str, Any]:
    matches = sorted(
        [row for row in rows if predicate(row)],
        key=lambda row: _safe_float(row, sort_key),
        reverse=reverse,
    )
    return {
        "preset_id": preset_id,
        "label": label,
        "rule_summary": rule_summary,
        "matched_count": len(matches),
        "universe_count": len(rows),
        "sort_key": sort_key,
        "rows": [
            {
                "rank": position,
                "instrument_id": row["instrument_id"],
                "label": row["label"],
                "category_label": row["category_label"],
                "real_cagr": _safe_float(row, "real_cagr"),
                "max_drawdown": _safe_float(row, "max_drawdown"),
                "annual_volatility": _safe_float(row, "annual_volatility"),
                "net_profit": _safe_float(row, "net_profit"),
            }
            for position, row in enumerate(matches[:8], start=1)
        ],
    }


def _safe_float(row: dict[str, Any], key: str) -> float:
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
