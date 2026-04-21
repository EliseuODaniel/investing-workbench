"""Tests for the price-grid strategy used in the WEGE3 scenario."""

from __future__ import annotations

import pandas as pd

from src.engine import BacktestEngine
from src.strategies.regra_a_grid import LongOnlyPriceLadderStrategy, RegraAGridStrategy


def test_regra_a_grid_executes_multiple_times_in_one_bar() -> None:
    data = pd.DataFrame(
        [
            {
                "Open": 10.0,
                "High": 12.0,
                "Low": 8.0,
                "Close": 11.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            }
        ],
        index=[pd.Timestamp("2023-01-02")],
    )

    engine = BacktestEngine(initial_cash=40000.0, close_positions_at_end=False)
    strategy = RegraAGridStrategy(initial_investment=10000.0, order_notional=1000.0, grid_step=1.0)
    engine.run(data, strategy)

    trade_prices = list(strategy.trade_log_frame()["price"])
    assert trade_prices == [10.0, 9.0, 8.0, 9.0, 10.0, 11.0, 12.0, 11.0]
    assert strategy.trade_log_frame()["action"].tolist() == [
        "BUY",
        "BUY",
        "BUY",
        "SELL",
        "SELL",
        "SELL",
        "SELL",
        "BUY",
    ]


def test_regra_a_grid_adjusts_reference_for_stock_split() -> None:
    data = pd.DataFrame(
        [
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 10.0,
                "Close": 10.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
            {
                "Open": 5.0,
                "High": 5.4,
                "Low": 4.6,
                "Close": 5.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 2.0,
            },
        ],
        index=[pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")],
    )

    engine = BacktestEngine(initial_cash=40000.0, close_positions_at_end=False)
    strategy = RegraAGridStrategy(initial_investment=10000.0, order_notional=1000.0, grid_step=1.0)
    engine.run(data, strategy)

    assert len(strategy.trade_log) == 1
    assert strategy.last_trade_price == 5.0
    assert strategy.position_shares == 2000.0


def test_long_only_price_ladder_supports_progressive_buys() -> None:
    data = pd.DataFrame(
        [
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 7.0,
                "Close": 7.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            }
        ],
        index=[pd.Timestamp("2023-01-02")],
    )

    engine = BacktestEngine(initial_cash=40000.0, close_positions_at_end=False)
    strategy = LongOnlyPriceLadderStrategy(
        initial_investment=10000.0,
        base_order_notional=1000.0,
        buy_grid_step=1.0,
        sell_grid_step=1.0,
        buy_size_mode="progressive",
        buy_multiplier=1.5,
        max_buy_notional=3000.0,
    )
    engine.run(data, strategy)

    trade_log = strategy.trade_log_frame()
    assert trade_log["action"].tolist() == ["BUY", "BUY", "BUY", "BUY"]
    assert trade_log["notional"].tolist() == [10000.0, 1000.0, 1500.0, 2250.0]


def test_long_only_price_ladder_respects_cash_reserve() -> None:
    data = pd.DataFrame(
        [
            {
                "Open": 10.0,
                "High": 10.0,
                "Low": 8.0,
                "Close": 8.0,
                "Volume": 1000.0,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            }
        ],
        index=[pd.Timestamp("2023-01-02")],
    )

    engine = BacktestEngine(initial_cash=12000.0, close_positions_at_end=False)
    strategy = LongOnlyPriceLadderStrategy(
        initial_investment=10000.0,
        base_order_notional=1000.0,
        buy_grid_step=1.0,
        sell_grid_step=1.0,
        cash_reserve=1500.0,
    )
    engine.run(data, strategy)

    trade_log = strategy.trade_log_frame()
    assert trade_log["action"].tolist() == ["BUY"]
    assert round(engine.state.cash, 2) == 2000.0
