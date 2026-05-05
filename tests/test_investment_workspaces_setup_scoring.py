"""Tests for investment workspace setup scoring."""

from __future__ import annotations

from src.investing_workbench.application.investment_workspaces.setup_scoring import (
    SETUP_SCORE_METHODOLOGY,
    build_strategy_setup_scores,
    score_setup_data_validity,
)


def test_build_strategy_setup_scores_ranks_latest_runs_with_components() -> None:
    setup_runs = [
        {
            "strategy_id": "pairs_mean_reversion",
            "pairs_backtest_id": "pairs_old",
            "ran_at": "2026-04-26T12:00:00+00:00",
            "total_return": 0.05,
            "max_drawdown": -0.02,
            "trade_count": 1,
            "route_hint": "/pairs/backtests",
        },
        {
            "strategy_id": "buy_and_hold_value",
            "run_id": "run_123",
            "ran_at": "2026-04-27T12:00:00+00:00",
            "total_return": 0.10,
            "max_drawdown": -0.05,
            "trade_count": 0,
            "route_hint": "/backtest",
        },
        {
            "strategy_id": "pairs_mean_reversion",
            "pairs_backtest_id": "pairs_123",
            "ran_at": "2026-04-28T12:00:00+00:00",
            "total_return": 0.12,
            "max_drawdown": -0.04,
            "trade_count": 3,
            "route_hint": "/pairs/backtests",
        },
    ]
    radar_items = [
        {"strategy_id": "pairs_mean_reversion", "label": "Pairs mean reversion"},
        {"strategy_id": "buy_and_hold_value", "label": "Buy and hold valor"},
    ]

    scores = build_strategy_setup_scores(setup_runs, radar_items)

    assert [item["strategy_id"] for item in scores] == [
        "pairs_mean_reversion",
        "buy_and_hold_value",
    ]
    assert scores[0] == {
        "strategy_id": "pairs_mean_reversion",
        "label": "Pairs mean reversion",
        "score": 13.75,
        "total_return": 0.12,
        "max_drawdown": -0.04,
        "trade_count": 3,
        "run_count": 2,
        "route_hint": "/pairs/backtests",
        "run_id": None,
        "pairs_backtest_id": "pairs_123",
        "return_score": 12.0,
        "drawdown_penalty": 2.0,
        "execution_score": 0.75,
        "robustness_score": 1.0,
        "data_validity_score": 2.0,
        "ran_at": "2026-04-28T12:00:00+00:00",
        "methodology": SETUP_SCORE_METHODOLOGY,
    }
    assert scores[1]["score"] == 10.0


def test_build_strategy_setup_scores_skips_invalid_metric_runs() -> None:
    scores = build_strategy_setup_scores(
        setup_runs=[
            {
                "strategy_id": "draft_without_result",
                "run_id": "run_pending",
                "ran_at": "2026-04-28T12:00:00+00:00",
                "total_return": None,
                "max_drawdown": -0.03,
                "route_hint": "/backtest",
            }
        ],
        strategy_radar_items=[],
    )

    assert scores == []


def test_score_setup_data_validity_rewards_traceable_complete_results() -> None:
    assert (
        score_setup_data_validity(
            {
                "run_id": "run_123",
                "total_return": 0.10,
                "max_drawdown": -0.05,
                "route_hint": "/backtest",
            }
        )
        == 2.0
    )
    assert score_setup_data_validity({"total_return": 0.10}) == 0.0
