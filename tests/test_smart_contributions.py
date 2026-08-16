"""Unit tests for smart contributions rebalancing optimizer."""

from __future__ import annotations

from src.investing_workbench.application.investments.smart_contributions import (
    build_smart_contributions_plan,
)


def test_smart_contributions_allocates_to_underweight_asset() -> None:
    results = [
        {
            "instrument_id": "asset_a",
            "label": "Ativo A (Overweight)",
            "final_value": 6000.0,
        },
        {
            "instrument_id": "asset_b",
            "label": "Ativo B (Underweight)",
            "final_value": 2000.0,
        },
    ]

    # Equal target weight 50% each, contribution 2000
    # Current total = 8000 (A=75%, B=25%). New total = 10000 (target A=5000, B=5000).
    # Since A is already 6000 > 5000, all 2000 should go to B.
    plan = build_smart_contributions_plan(results=results, contribution_amount=2000.0)

    assert plan is not None
    assert plan["title"] == "Aporte inteligente de rebalanceamento"
    assert plan["contribution_amount"] == 2000.0
    assert plan["current_total_balance"] == 8000.0
    assert plan["projected_total_balance"] == 10000.0
    assert len(plan["allocations"]) == 2

    alloc_a = next(a for a in plan["allocations"] if a["instrument_id"] == "asset_a")
    alloc_b = next(a for a in plan["allocations"] if a["instrument_id"] == "asset_b")

    assert alloc_a["suggested_contribution"] == 0.0
    assert alloc_a["rebalance_status"] == "overweight_hold"
    assert alloc_b["suggested_contribution"] == 2000.0
    assert alloc_b["rebalance_status"] == "underweight_receiving"
    assert alloc_b["projected_balance"] == 4000.0
    assert plan["efficiency_score_pct"] > 50.0


def test_smart_contributions_uses_portfolio_component_breakdown() -> None:
    results = [
        {
            "instrument_id": "portfolio_custom",
            "label": "Carteira Modelo",
            "source_kind": "custom_portfolio",
            "final_value": 10000.0,
            "component_breakdown": [
                {
                    "sleeve_id": "petr4",
                    "label": "PETR4",
                    "weight": 0.60,
                    "final_value": 5000.0,
                },
                {
                    "sleeve_id": "vale3",
                    "label": "VALE3",
                    "weight": 0.40,
                    "final_value": 5000.0,
                },
            ],
        }
    ]

    plan = build_smart_contributions_plan(results=results, contribution_amount=1000.0)

    assert plan is not None
    assert len(plan["allocations"]) == 2
    petr4 = next(a for a in plan["allocations"] if a["instrument_id"] == "petr4")
    vale3 = next(a for a in plan["allocations"] if a["instrument_id"] == "vale3")

    # Current: PETR4 50% (target 60%), VALE3 50% (target 40%)
    # Contribution should prioritize PETR4 to reach 60%
    assert petr4["suggested_contribution"] > vale3["suggested_contribution"]
    assert petr4["rebalance_status"] == "underweight_receiving"


def test_smart_contributions_handles_zero_balances() -> None:
    results = [
        {"instrument_id": "a", "label": "A", "final_value": 0.0},
        {"instrument_id": "b", "label": "B", "final_value": 0.0},
    ]
    plan = build_smart_contributions_plan(results=results, contribution_amount=1000.0)
    assert plan is not None
    assert plan["current_total_balance"] == 0.0
    assert plan["projected_total_balance"] == 1000.0
    for alloc in plan["allocations"]:
        assert alloc["suggested_contribution"] == 500.0
        assert alloc["rebalance_status"] == "balanced"


def test_smart_contributions_returns_none_for_insufficient_assets() -> None:
    assert build_smart_contributions_plan(results=[]) is None
    assert (
        build_smart_contributions_plan(results=[{"instrument_id": "solo", "final_value": 100.0}])
        is None
    )
