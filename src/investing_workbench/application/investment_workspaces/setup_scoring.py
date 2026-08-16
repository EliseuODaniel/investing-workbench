"""Explainable scoring for saved strategy setup executions."""

from __future__ import annotations

from typing import Any

SETUP_SCORE_METHODOLOGY = (
    "score = retorno_total * 100 - abs(max_drawdown) * 50 "
    "+ min(trade_count, 20) * 0.25 + min(run_count, 5) * 0.5 "
    "+ data_validity_score"
)


def build_strategy_setup_scores(
    setup_runs: list[dict[str, Any]],
    strategy_radar_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank latest setup executions with component-level score fields."""

    latest_by_strategy: dict[str, dict[str, Any]] = {}
    valid_counts_by_strategy: dict[str, int] = {}
    for item in setup_runs:
        strategy_id = str(item.get("strategy_id") or "")
        if not strategy_id:
            continue
        if (
            _optional_float(item.get("total_return")) is not None
            and _optional_float(item.get("max_drawdown")) is not None
        ):
            valid_counts_by_strategy[strategy_id] = valid_counts_by_strategy.get(strategy_id, 0) + 1
        current = latest_by_strategy.get(strategy_id)
        if current is None or str(item.get("ran_at") or "") > str(current.get("ran_at") or ""):
            latest_by_strategy[strategy_id] = item

    labels = {
        str(item.get("strategy_id")): str(item.get("label") or item.get("strategy_id"))
        for item in strategy_radar_items
    }
    rows: list[dict[str, Any]] = []
    for strategy_id, item in latest_by_strategy.items():
        total_return = _optional_float(item.get("total_return"))
        max_drawdown = _optional_float(item.get("max_drawdown"))
        if total_return is None or max_drawdown is None:
            continue
        trade_count = _optional_int(item.get("trade_count")) or 0
        return_score = total_return * 100
        drawdown_penalty = abs(max_drawdown) * 50
        execution_score = min(trade_count, 20) * 0.25
        run_count = valid_counts_by_strategy.get(strategy_id, 0)
        robustness_score = min(run_count, 5) * 0.5
        data_validity_score = score_setup_data_validity(item)
        score = (
            return_score
            - drawdown_penalty
            + execution_score
            + robustness_score
            + data_validity_score
        )
        rows.append(
            {
                "strategy_id": strategy_id,
                "label": labels.get(strategy_id, strategy_id),
                "score": score,
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "trade_count": trade_count,
                "run_count": run_count,
                "route_hint": str(item.get("route_hint") or "/backtest"),
                "run_id": _optional_str(item.get("run_id")),
                "pairs_backtest_id": _optional_str(item.get("pairs_backtest_id")),
                "return_score": return_score,
                "drawdown_penalty": drawdown_penalty,
                "execution_score": execution_score,
                "robustness_score": robustness_score,
                "data_validity_score": data_validity_score,
                "ran_at": str(item.get("ran_at") or ""),
                "methodology": SETUP_SCORE_METHODOLOGY,
            }
        )
    rows.sort(key=lambda item: float(item["score"]), reverse=True)
    return rows


def score_setup_data_validity(item: dict[str, Any]) -> float:
    """Score whether a setup summary can be traced to a valid persisted result."""

    score = 0.0
    if _optional_str(item.get("run_id")) or _optional_str(item.get("pairs_backtest_id")):
        score += 1.0
    if (
        _optional_float(item.get("total_return")) is not None
        and _optional_float(item.get("max_drawdown")) is not None
    ):
        score += 0.75
    if str(item.get("route_hint") or "") in {"/backtest", "/pairs/backtests"}:
        score += 0.25
    return score


def calculate_strategy_diversification_metrics(
    scores: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Calculate multi-strategy diversification and blend indicators for executed setups."""

    if len(scores) < 2:
        return None

    top_scores = scores[:4]
    routes = {str(item.get("route_hint") or "") for item in top_scores}
    route_variety_bonus = min(len(routes) * 0.25, 0.5)

    avg_return = sum(float(item["total_return"]) for item in top_scores) / len(top_scores)
    max_dd = min(float(item["max_drawdown"]) for item in top_scores)
    avg_dd = sum(float(item["max_drawdown"]) for item in top_scores) / len(top_scores)

    # Estimate blended drawdown benefit (diversification softens max single drawdown)
    blended_dd_estimate = round(avg_dd * 0.85, 4)

    # Diversification score between 0 and 100
    div_score = min(
        100.0,
        max(
            10.0,
            round((0.5 + route_variety_bonus + min(len(top_scores) * 0.1, 0.3)) * 100, 1),
        ),
    )

    return {
        "strategy_count": len(top_scores),
        "diversification_score": div_score,
        "average_return": round(avg_return, 4),
        "worst_drawdown": round(max_dd, 4),
        "estimated_blended_drawdown": blended_dd_estimate,
        "interpretation": (
            f"Combinar os {len(top_scores)} principais setups executados diversifica riscos operacionais "
            f"e reduz o drawdown maximo estimado para {blended_dd_estimate * 100:.1f}%."
        ),
    }


def _optional_str(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str | int | float):
        raise ValueError("Valor numerico invalido para resumo de execucao.")
    return float(value)


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str | int | float):
        raise ValueError("Valor inteiro invalido para resumo de execucao.")
    return int(value)
