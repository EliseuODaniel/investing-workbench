"""Tests for the refactored core engine and ledger."""

from __future__ import annotations

import pandas as pd
import pytest

from src.investing_workbench.domain.backtest import BacktestCoreEngine
from src.investing_workbench.domain.execution import OrderFill, OrderSide
from src.investing_workbench.domain.portfolio import PortfolioLedger


def test_portfolio_ledger_builds_aggregated_position() -> None:
    ledger = PortfolioLedger(asset="BTC-BRL", initial_cash=10000.0)

    ledger.apply_buy(
        fill=OrderFill(
            order_id="buy-1",
            asset="BTC-BRL",
            side=OrderSide.BUY,
            quantity=0.1,
            fill_price=50000.0,
            filled_at=pd.Timestamp("2024-01-01").to_pydatetime(),
        ),
        layer_id=1,
    )
    ledger.apply_buy(
        fill=OrderFill(
            order_id="buy-2",
            asset="BTC-BRL",
            side=OrderSide.BUY,
            quantity=0.05,
            fill_price=40000.0,
            filled_at=pd.Timestamp("2024-01-02").to_pydatetime(),
        ),
        layer_id=2,
    )

    position = ledger.build_position()

    assert position.quantity == pytest.approx(0.15)
    assert round(position.cost_basis, 2) == 7000.0
    assert round(position.average_entry_price, 2) == round(7000.0 / 0.15, 2)


def test_core_engine_preserves_legacy_run_contract() -> None:
    engine = BacktestCoreEngine(initial_cash=10000.0)

    class BuyOnceStrategy:
        def __init__(self) -> None:
            self.done = False

        def on_bar(self, row, eng) -> None:
            if not self.done:
                eng.buy(row.name, float(row["Close"]), 0.1, layer_id=1)
                self.done = True

    data = pd.DataFrame(
        [
            {"Open": 50000.0, "High": 50500.0, "Low": 49500.0, "Close": 50000.0, "Volume": 1000.0},
            {"Open": 51000.0, "High": 51500.0, "Low": 50500.0, "Close": 51000.0, "Volume": 1000.0},
        ],
        index=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
    )

    result = engine.run(data, BuyOnceStrategy())

    assert list(result["equity"].columns) == ["equity", "cash"]
    assert result["total_trades"] == 2
    assert result["open_layers"] == 0
    assert result["final_cash"] > engine.initial_cash
    assert engine.state.trades[-1].action == "SELL"
