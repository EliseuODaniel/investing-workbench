"""Tests for the new domain models introduced during the refactor."""

from datetime import datetime

import pandas as pd

from src.investing_workbench.domain.execution import (
    OrderFill,
    OrderRequest,
    OrderSide,
    OrderType,
)
from src.investing_workbench.domain.market_data import MarketBar
from src.investing_workbench.domain.portfolio import PortfolioSnapshot, Position


def test_market_bar_from_series() -> None:
    row = pd.Series(
        {
            "Open": 10.0,
            "High": 11.0,
            "Low": 9.0,
            "Close": 10.5,
            "Volume": 1000.0,
        },
        name=pd.Timestamp("2024-01-01"),
    )

    bar = MarketBar.from_series(row, asset="BTC-BRL")

    assert bar.asset == "BTC-BRL"
    assert bar.close == 10.5
    assert bar.to_dict()["timestamp"] == "2024-01-01T00:00:00"


def test_order_fill_cash_flow_and_serialization() -> None:
    fill = OrderFill(
        order_id="order-1",
        asset="BTC-BRL",
        side=OrderSide.BUY,
        quantity=2.0,
        fill_price=100.0,
        filled_at=datetime(2024, 1, 1, 12, 0, 0),
        fees=1.5,
        requested_quantity=3.0,
    )

    assert fill.gross_value == 200.0
    assert fill.net_cash_flow == -201.5
    assert fill.to_dict()["side"] == "buy"
    assert fill.to_dict()["requested_quantity"] == 3.0


def test_portfolio_snapshot_invested_value() -> None:
    snapshot = PortfolioSnapshot(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        cash=500.0,
        total_equity=1100.0,
        positions=[
            Position(
                asset="BTC-BRL",
                quantity=2.0,
                average_entry_price=300.0,
                cost_basis=600.0,
            )
        ],
    )

    assert snapshot.invested_value == 600.0
    assert snapshot.to_dict()["positions"][0]["asset"] == "BTC-BRL"


def test_order_request_to_dict() -> None:
    request = OrderRequest(
        order_id="order-2",
        asset="BTC-BRL",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=1.0,
        requested_price=120.0,
        submitted_at=datetime(2024, 1, 2, 8, 30, 0),
    )

    payload = request.to_dict()
    assert payload["side"] == "sell"
    assert payload["order_type"] == "limit"
    assert payload["requested_price"] == 120.0


def test_domain_package_exports_resolve_without_circular_imports() -> None:
    from src.investing_workbench.domain.backtest import BacktestCoreEngine
    from src.investing_workbench.domain.portfolio import PortfolioLedger

    assert BacktestCoreEngine.__name__ == "BacktestCoreEngine"
    assert PortfolioLedger.__name__ == "PortfolioLedger"
