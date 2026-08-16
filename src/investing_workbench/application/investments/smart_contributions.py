"""Smart contribution and buy-only rebalancing optimizer for investment portfolios."""

from __future__ import annotations

from typing import Any, TypedDict


class AssetRebalanceItem(TypedDict):
    instrument_id: str
    label: str
    target_weight_pct: float
    current_balance: float
    current_weight_pct: float
    suggested_contribution: float
    suggested_contribution_pct: float
    projected_balance: float
    projected_weight_pct: float
    weight_gap_before_pct: float
    weight_gap_after_pct: float
    rebalance_status: str  # "underweight_receiving", "overweight_hold", "balanced"


class SmartContributionPlan(TypedDict):
    title: str
    description: str
    contribution_amount: float
    current_total_balance: float
    projected_total_balance: float
    allocations: list[AssetRebalanceItem]
    unallocated_amount: float
    efficiency_score_pct: float
    methodology: str


def build_smart_contributions_plan(
    *,
    results: list[dict[str, Any]],
    contribution_amount: float = 1000.0,
) -> dict[str, Any] | None:
    """Build a buy-only rebalancing contribution plan from portfolio or multi-asset comparison."""

    if not results:
        return None

    # Determine asset candidates: if there is a portfolio with component breakdown, use components;
    # otherwise, use individual assets with equal or specified weights.
    portfolio_rows = [
        row
        for row in results
        if row.get("component_breakdown") or row.get("source_kind") == "custom_portfolio"
    ]

    assets: list[dict[str, Any]] = []

    if portfolio_rows:
        best_portfolio = max(
            portfolio_rows,
            key=lambda r: float(r.get("final_value", 0.0) or 0.0),
        )
        components = best_portfolio.get("component_breakdown") or []
        if isinstance(components, list) and len(components) >= 2:
            for comp in components:
                sleeve_id = str(comp.get("sleeve_id") or comp.get("instrument_id") or "sleeve")
                assets.append(
                    {
                        "instrument_id": sleeve_id,
                        "label": str(comp.get("label") or "Ativo"),
                        "target_weight": float(comp.get("weight", 0.0) or 0.0),
                        "current_balance": float(comp.get("final_value", 0.0) or 0.0),
                    }
                )

    if not assets:
        # Fallback to multi-asset comparison with equal target weights
        equal_weight = 1.0 / len(results)
        for row in results:
            assets.append(
                {
                    "instrument_id": str(row.get("instrument_id") or "asset"),
                    "label": str(row.get("label") or "Ativo"),
                    "target_weight": equal_weight,
                    "current_balance": float(row.get("final_value", 0.0) or 0.0),
                }
            )

    if len(assets) < 2:
        return None

    # Normalize target weights to sum to 1.0
    total_target_weight = sum(a["target_weight"] for a in assets)
    if total_target_weight <= 0:
        equal_weight = 1.0 / len(assets)
        for a in assets:
            a["target_weight"] = equal_weight
    else:
        for a in assets:
            a["target_weight"] /= total_target_weight

    # Ensure contribution amount is positive
    contribution = max(0.0, float(contribution_amount or 1000.0))
    current_total = sum(a["current_balance"] for a in assets)

    if current_total <= 0:
        # If no current balance, allocate purely by target weight
        allocations: list[AssetRebalanceItem] = []
        for a in assets:
            contrib = round(contribution * a["target_weight"], 2)
            allocations.append(
                {
                    "instrument_id": a["instrument_id"],
                    "label": a["label"],
                    "target_weight_pct": round(a["target_weight"] * 100, 2),
                    "current_balance": 0.0,
                    "current_weight_pct": round(a["target_weight"] * 100, 2),
                    "suggested_contribution": contrib,
                    "suggested_contribution_pct": round(a["target_weight"] * 100, 2),
                    "projected_balance": contrib,
                    "projected_weight_pct": round(a["target_weight"] * 100, 2),
                    "weight_gap_before_pct": 0.0,
                    "weight_gap_after_pct": 0.0,
                    "rebalance_status": "balanced",
                }
            )
        return {
            "title": "Aporte inteligente de rebalanceamento",
            "description": (
                "Calcula a distribuicao otimizada do proximo aporte para aproximar a carteira "
                "dos pesos-alvo sem gerar vendas ou eventos tributaveis."
            ),
            "contribution_amount": round(contribution, 2),
            "current_total_balance": 0.0,
            "projected_total_balance": round(contribution, 2),
            "allocations": allocations,
            "unallocated_amount": 0.0,
            "efficiency_score_pct": 100.0,
            "methodology": (
                "Algoritmo de water-filling que direciona o fluxo de caixa exclusivamente "
                "para os ativos mais abaixo do peso-alvo, reduzindo desvios sem custos de venda."
            ),
        }

    # Water-filling algorithm for non-negative buy-only rebalancing:
    # We want a_i >= 0 such that sum(a_i) = contribution, minimizing
    # sum ( (V_i + a_i)/(V_total + C) - w_i )^2.
    # This brings (V_i + a_i)/w_i to a common water-level lambda for active assets.
    projected_total = current_total + contribution

    # Find lambda via bisection
    low = min(a["current_balance"] / max(a["target_weight"], 1e-6) for a in assets)
    high = (current_total + contribution) * 2.0

    for _ in range(50):
        mid = (low + high) / 2.0
        sum_contrib = sum(max(0.0, mid * a["target_weight"] - a["current_balance"]) for a in assets)
        if sum_contrib < contribution:
            low = mid
        else:
            high = mid

    optimal_lambda = (low + high) / 2.0

    raw_contributions = [
        max(0.0, optimal_lambda * a["target_weight"] - a["current_balance"]) for a in assets
    ]
    sum_raw = sum(raw_contributions)

    if sum_raw > 0:
        scaled_contributions = [round((c / sum_raw) * contribution, 2) for c in raw_contributions]
    else:
        scaled_contributions = [round(contribution * a["target_weight"], 2) for a in assets]

    # Fix rounding drift on the largest allocated component
    drift = contribution - sum(scaled_contributions)
    if abs(drift) > 0 and scaled_contributions:
        max_idx = max(range(len(scaled_contributions)), key=lambda i: scaled_contributions[i])
        scaled_contributions[max_idx] = round(scaled_contributions[max_idx] + drift, 2)

    allocations_list: list[AssetRebalanceItem] = []
    initial_sq_error = 0.0
    final_sq_error = 0.0

    for i, a in enumerate(assets):
        c_bal = a["current_balance"]
        t_wt = a["target_weight"]
        s_contrib = scaled_contributions[i]
        p_bal = c_bal + s_contrib

        c_wt = c_bal / current_total if current_total > 0 else t_wt
        p_wt = p_bal / projected_total if projected_total > 0 else t_wt

        gap_before = (c_wt - t_wt) * 100.0
        gap_after = (p_wt - t_wt) * 100.0

        initial_sq_error += (gap_before) ** 2
        final_sq_error += (gap_after) ** 2

        if gap_before < -0.5 and s_contrib > 0:
            status = "underweight_receiving"
        elif gap_before > 0.5:
            status = "overweight_hold"
        else:
            status = "balanced"

        allocations_list.append(
            {
                "instrument_id": a["instrument_id"],
                "label": a["label"],
                "target_weight_pct": round(t_wt * 100, 2),
                "current_balance": round(c_bal, 2),
                "current_weight_pct": round(c_wt * 100, 2),
                "suggested_contribution": round(s_contrib, 2),
                "suggested_contribution_pct": (
                    round((s_contrib / contribution) * 100, 2) if contribution > 0 else 0.0
                ),
                "projected_balance": round(p_bal, 2),
                "projected_weight_pct": round(p_wt * 100, 2),
                "weight_gap_before_pct": round(gap_before, 2),
                "weight_gap_after_pct": round(gap_after, 2),
                "rebalance_status": status,
            }
        )

    # Calculate rebalancing efficiency (% of squared weight error closed)
    if initial_sq_error > 0:
        efficiency = max(0.0, min(100.0, (1.0 - (final_sq_error / initial_sq_error)) * 100.0))
    else:
        efficiency = 100.0

    return {
        "title": "Aporte inteligente de rebalanceamento",
        "description": (
            "Calcula a distribuicao otimizada do proximo aporte para aproximar a carteira "
            "dos pesos-alvo sem gerar vendas ou eventos tributaveis."
        ),
        "contribution_amount": round(contribution, 2),
        "current_total_balance": round(current_total, 2),
        "projected_total_balance": round(projected_total, 2),
        "allocations": allocations_list,
        "unallocated_amount": 0.0,
        "efficiency_score_pct": round(efficiency, 1),
        "methodology": (
            "Algoritmo de water-filling que direciona o fluxo de caixa exclusivamente "
            "para os ativos mais abaixo do peso-alvo, reduzindo desvios sem custos de venda."
        ),
    }
