import math

import pandas as pd

from src.engine import BacktestEngine


def test_buy_applies_slippage_and_fees():
    engine = BacktestEngine(
        initial_cash=10000.0,
        fee_rate=0.001,
        buy_slippage=0.002,
    )

    ok = engine.buy(pd.Timestamp("2023-01-01"), 100.0, 10.0)

    assert ok is True
    layer = engine.state.layers[0]
    trade = engine.state.trades[0]

    assert math.isclose(layer.entry_price, 100.2, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(trade.cost, 1003.002, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(engine.state.cash, 8996.998, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(engine.state.total_fees_paid, 1.002, rel_tol=0, abs_tol=1e-9)


def test_sell_applies_slippage_and_fees_to_pnl():
    engine = BacktestEngine(
        initial_cash=20000.0,
        fee_rate=0.001,
        buy_slippage=0.001,
        sell_slippage=0.002,
    )
    ts = pd.Timestamp("2023-01-01")

    assert engine.buy(ts, 100.0, 10.0, layer_id=1) is True
    assert engine.sell(ts, 110.0, 10.0, 1) is True

    sell_trade = engine.state.trades[-1]
    assert math.isclose(sell_trade.price, 109.78, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(sell_trade.pnl, 94.7012, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(engine.state.cash, 20094.7012, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(engine.state.total_fees_paid, 2.0988, rel_tol=0, abs_tol=1e-6)


def test_quantity_for_buy_budget_fits_available_cash():
    engine = BacktestEngine(
        initial_cash=40000.0,
        fee_rate=0.0003,
        buy_slippage=0.0005,
    )

    quantity = engine.quantity_for_buy_budget(100.0, 40000.0)
    total_cost = engine.estimate_buy_total_cost(100.0, quantity)

    assert quantity > 0
    assert total_cost <= 40000.0 + 1e-9


def test_quantity_for_buy_budget_executes_all_in_order():
    engine = BacktestEngine(
        initial_cash=40000.0,
        fee_rate=0.0003,
        buy_slippage=0.0005,
    )

    quantity = engine.quantity_for_buy_budget(100.0, engine.state.cash)

    assert quantity > 0
    assert engine.buy(pd.Timestamp("2023-01-01"), 100.0, quantity, layer_id=1) is True
    assert engine.state.trades[-1].action == "BUY"
    assert engine.state.cash >= 0
    assert engine.state.cash < 1e-6


def test_buy_partial_fill_respects_volume_participation_limit():
    engine = BacktestEngine(
        initial_cash=10000.0,
        max_volume_participation=0.1,
    )

    ok = engine.buy(
        pd.Timestamp("2023-01-01"),
        100.0,
        10.0,
        layer_id=1,
        market_volume=50.0,
    )

    assert ok is True
    trade = engine.state.trades[-1]
    assert math.isclose(trade.quantity, 5.0, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(trade.requested_quantity or 0.0, 10.0, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(trade.fill_ratio or 0.0, 0.5, rel_tol=0, abs_tol=1e-9)
    assert engine.state.execution_log[-1]["event_type"] == "partial_fill"


def test_buy_rejects_when_partial_fills_are_disabled_and_liquidity_is_insufficient():
    engine = BacktestEngine(
        initial_cash=10000.0,
        max_volume_participation=0.1,
        allow_partial_fills=False,
    )

    ok = engine.buy(
        pd.Timestamp("2023-01-01"),
        100.0,
        10.0,
        layer_id=1,
        market_volume=50.0,
    )

    assert ok is False
    assert engine.state.trades == []
    assert engine.state.execution_log[-1]["event_type"] == "buy_rejected"


def test_run_serializes_execution_log_for_partial_fill_behavior():
    engine = BacktestEngine(
        initial_cash=10000.0,
        max_volume_participation=0.1,
    )

    class BuyLargeOnceStrategy:
        def __init__(self) -> None:
            self.done = False

        def on_bar(self, row, eng) -> None:
            if not self.done:
                eng.buy(row.name, float(row["Close"]), 10.0, layer_id=1)
                self.done = True

    data = pd.DataFrame(
        [
            {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 50.0},
            {"Open": 102.0, "High": 103.0, "Low": 101.0, "Close": 102.0, "Volume": 60.0},
        ],
        index=[pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")],
    )

    result = engine.run(data, BuyLargeOnceStrategy())

    assert result["max_volume_participation"] == 0.1
    assert result["execution_log"][0]["event_type"] == "partial_fill"
    assert math.isclose(result["execution_log"][0]["filled_quantity"], 5.0, rel_tol=0, abs_tol=1e-9)
    assert result["execution_summary"]["partial_fill_count"] == 1
    assert result["execution_summary"]["liquidity_constrained"] is True
    assert result["warnings"] == [
        "One or more orders were partially filled due to configured liquidity limits."
    ]


def test_run_reports_execution_warning_for_rejected_buy():
    engine = BacktestEngine(
        initial_cash=500.0,
        allow_partial_fills=False,
        max_volume_participation=0.1,
    )

    class BuyTooLargeStrategy:
        def on_bar(self, row, eng) -> None:
            eng.buy(row.name, float(row["Close"]), 10.0, layer_id=1)

    data = pd.DataFrame(
        [
            {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 10.0},
        ],
        index=[pd.Timestamp("2023-01-01")],
    )

    result = engine.run(data, BuyTooLargeStrategy())

    assert result["execution_summary"]["rejected_buy_count"] == 1
    assert result["execution_summary"]["rejected_order_count"] == 1
    assert result["warnings"] == [
        "One or more buy orders were rejected because cash or liquidity was insufficient."
    ]
