"""Unit tests for portfolio factsheet HTML generation."""

from __future__ import annotations

from src.investing_workbench.infrastructure.reporting.portfolio_factsheet import (
    build_portfolio_factsheet_html,
)


def test_build_portfolio_factsheet_html() -> None:
    html_output = build_portfolio_factsheet_html(
        study_title="Carteira Aposentadoria 2040",
        profile={"objective": "balanced", "horizon": "long_term", "liquidity": "medium"},
        results=[
            {
                "label": "PETR4",
                "category_id": "Ações B3",
                "final_value": 50000.0,
                "cagr": 0.12,
                "max_drawdown": -0.25,
            },
            {
                "label": "Tesouro IPCA+",
                "category_id": "Renda Fixa",
                "final_value": 70000.0,
                "cagr": 0.09,
                "max_drawdown": -0.05,
            },
        ],
        metrics_summary={
            "final_value": 120000.0,
            "real_cagr": 0.065,
            "max_drawdown": -0.12,
            "annual_volatility": 0.14,
            "sharpe_ratio": 0.85,
        },
        smart_contributions={
            "allocations": [
                {
                    "label": "PETR4",
                    "target_weight_pct": 50.0,
                    "current_weight_pct": 41.7,
                    "suggested_contribution": 1000.0,
                    "rebalance_status": "underweight_receiving",
                }
            ]
        },
    )

    assert "<!DOCTYPE html>" in html_output
    assert "Carteira Aposentadoria 2040" in html_output
    assert "PETR4" in html_output
    assert "Tesouro IPCA+" in html_output
    assert "Plano de Aporte Inteligente" in html_output
    assert "R$ 120,000.00" in html_output
