"""Regression tests for the overlay grid strategy."""

from __future__ import annotations

import pandas as pd

from src.engine import BacktestEngine
from src.strategies.adaptive_core_grid import AdaptiveCoreGridStrategy


def test_adaptive_core_grid_preserves_core_when_selling() -> None:
    data = pd.DataFrame(
        [
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 10.0,
                "Close": 10.0,
                "Volume": 100.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 8.0,
                "Close": 8.5,
                "Volume": 100.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
            {
                "Open": 8.5,
                "High": 12.0,
                "Low": 8.5,
                "Close": 11.0,
                "Volume": 100.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
        ],
        index=pd.to_datetime(["2023-01-02", "2023-01-03", "2023-01-04"]),
    )

    engine = BacktestEngine(initial_cash=40000.0, close_positions_at_end=False)
    strategy = AdaptiveCoreGridStrategy(core_notional=10000.0, order_notional=1000.0, min_step=1.0)
    engine.run(data, strategy)

    assert strategy.core_quantity == 1000.0
    assert engine.ledger.total_quantity() >= strategy.core_quantity
    assert any(layer.layer_id == 1 for layer in engine.state.layers)
