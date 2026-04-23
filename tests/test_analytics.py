"""Tests for the refactored analytics layer."""

from __future__ import annotations

import pandas as pd

from src.investing_workbench.analytics import MetricsService


def test_metrics_service_composes_analyzers() -> None:
    service = MetricsService()
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    equity = pd.Series([10000.0, 10200.0, 10100.0, 10500.0], index=dates)
    trades = pd.DataFrame(
        [
            {
                "action": "BUY",
                "price": 100.0,
                "quantity": 1.0,
                "cost": 100.0,
                "timestamp": dates[0],
            },
            {
                "action": "SELL",
                "price": 110.0,
                "quantity": 1.0,
                "cost": 100.0,
                "pnl": 10.0,
                "layer": 1,
                "timestamp": dates[1],
            },
        ]
    )

    metrics = service.calculate(equity=equity, trades=trades, initial_capital=10000.0)

    assert metrics["total_return"] == 0.05
    assert metrics["total_trades"] == 2
    assert "mar_ratio" in metrics
    assert "layer_pnl" in metrics
