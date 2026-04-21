"""Tests for portfolio allocation planning."""

from __future__ import annotations

import pytest

from src.bitcoin_martingale.application.allocations import AllocationPlanningService
from src.bitcoin_martingale.domain.allocations import RebalancePlanRequest


def test_allocation_planner_builds_rebalance_plan() -> None:
    service = AllocationPlanningService()

    plan = service.build_plan(
        RebalancePlanRequest.from_dict(
            {
                "cash": 2000.0,
                "holdings": [
                    {"asset": "BTC-BRL", "quantity": 0.05},
                    {"asset": "ETH-USD", "quantity": 2.0},
                ],
                "prices": {
                    "BTC-BRL": 60000.0,
                    "ETH-USD": 2000.0,
                    "SPY": 900.0,
                },
                "targets": [
                    {"asset": "BTC-BRL", "target_weight": 0.5},
                    {"asset": "ETH-USD", "target_weight": 0.2},
                    {"asset": "SPY", "target_weight": 0.1},
                ],
                "reserve_cash": 1000.0,
            }
        )
    )

    assert plan.needs_rebalance is True
    assert plan.total_equity == pytest.approx(9000.0)
    assert plan.target_cash == pytest.approx(1800.0)
    assert plan.projected_cash == pytest.approx(1800.0)

    actions = {action.asset: action for action in plan.actions}
    assert actions["ETH-USD"].action.value == "sell"
    assert actions["BTC-BRL"].action.value == "buy"
    assert actions["SPY"].action.value == "buy"
    assert actions["ETH-USD"].notional_delta == pytest.approx(-2200.0)
    assert actions["BTC-BRL"].notional_delta == pytest.approx(1500.0)
    assert actions["SPY"].notional_delta == pytest.approx(900.0)


def test_allocation_planner_rejects_target_weights_above_one() -> None:
    service = AllocationPlanningService()

    with pytest.raises(ValueError, match="sum to at most 1.0"):
        service.build_plan(
            RebalancePlanRequest.from_dict(
                {
                    "cash": 1000.0,
                    "holdings": [],
                    "prices": {"BTC-BRL": 60000.0, "SPY": 900.0},
                    "targets": [
                        {"asset": "BTC-BRL", "target_weight": 0.7},
                        {"asset": "SPY", "target_weight": 0.5},
                    ],
                }
            )
        )


def test_allocation_planner_holds_small_drifts_below_trade_threshold() -> None:
    service = AllocationPlanningService()

    plan = service.build_plan(
        RebalancePlanRequest.from_dict(
            {
                "cash": 1000.0,
                "holdings": [{"asset": "SPY", "quantity": 10.0}],
                "prices": {"SPY": 100.0},
                "targets": [{"asset": "SPY", "target_weight": 0.49}],
                "weight_tolerance": 0.02,
            }
        )
    )

    assert plan.needs_rebalance is False
    assert plan.actions[0].action.value == "hold"
    assert plan.actions[0].reason == "Within weight_tolerance"


def test_allocation_planner_rejects_targets_that_breach_cash_reserve() -> None:
    service = AllocationPlanningService()

    with pytest.raises(ValueError, match="reserve_cash"):
        service.build_plan(
            RebalancePlanRequest.from_dict(
                {
                    "cash": 1000.0,
                    "holdings": [],
                    "prices": {"BTC-BRL": 60000.0},
                    "targets": [{"asset": "BTC-BRL", "target_weight": 0.95}],
                    "reserve_cash": 600.0,
                }
            )
        )
