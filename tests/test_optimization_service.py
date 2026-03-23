"""Tests for optimization planning."""

from __future__ import annotations

import pytest

from src.bitcoin_martingale.application.optimizations import OptimizationPlanningService
from src.bitcoin_martingale.domain.optimizations import (
    OptimizationMode,
    OptimizationRequest,
    OptimizationSearchSpace,
)


def test_grid_plan_expands_discrete_space() -> None:
    service = OptimizationPlanningService()
    request = OptimizationRequest(
        config_path="configs/test.yaml",
        strategy_names=["Simple Martingale"],
        parameter_space={
            "base_bet": {"values": [250.0, 500.0]},
            "multiplier": {"values": [1.5, 2.0]},
        },
    )

    plan = service.build_plan(request)

    assert plan.trial_count == 4
    assert plan.trials[0].trial_id == "trial_0001"
    assert plan.trials[0].strategy_name == "Simple Martingale"
    assert plan.trials[0].parameters["drop_step"] == 0.10
    assert plan.trials[-1].parameters["base_bet"] == 500.0
    assert plan.trials[-1].parameters["multiplier"] == 2.0


def test_random_plan_is_reproducible_with_seed() -> None:
    service = OptimizationPlanningService()
    request = OptimizationRequest(
        config_path="configs/test.yaml",
        strategy_names=["Simple Martingale"],
        parameter_space={
            "base_bet": {"values": [250.0, 500.0, 750.0]},
            "multiplier": {"values": [1.5, 2.0]},
        },
        mode=OptimizationMode.RANDOM,
        max_trials=3,
        random_seed=7,
    )

    first_plan = service.build_plan(request)
    second_plan = service.build_plan(request)

    assert first_plan.trial_count == 3
    assert [trial.parameters for trial in first_plan.trials] == [
        trial.parameters for trial in second_plan.trials
    ]
    assert first_plan.truncated is False


def test_strategy_specific_space_and_unknown_parameters_add_warning() -> None:
    service = OptimizationPlanningService()
    request = OptimizationRequest(
        config_path="configs/test.yaml",
        strategy_names=["Simple Martingale"],
        parameter_space={"unknown": {"values": [1, 2]}},
        strategy_parameter_spaces={
            "Simple Martingale": {
                "max_layers": {"start": 3, "stop": 5, "step": 1},
            }
        },
    )

    plan = service.build_plan(request)

    assert plan.trial_count == 3
    assert plan.trials[0].parameters["max_layers"] == 3
    assert any("Skipping parameter 'unknown'" in warning for warning in plan.warnings)


def test_invalid_numeric_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="Range step must be greater than zero"):
        OptimizationSearchSpace.from_raw(
            "base_bet",
            {"start": 100, "stop": 300, "step": 0},
        )
