"""Grid strategy based on absolute price levels for the WEGE3 backtest scenario."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .base import Strategy


@dataclass(slots=True)
class GridTradeRecord:
    """Strategy-level execution record used for audit and reporting."""

    timestamp: pd.Timestamp
    action: str
    price: float
    notional: float
    quantity: float
    cash_after: float
    position_after: float
    reference_after: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "price": self.price,
            "notional": self.notional,
            "quantity": self.quantity,
            "cash_after": self.cash_after,
            "position_after": self.position_after,
            "reference_after": self.reference_after,
        }


class LongOnlyPriceLadderStrategy(Strategy):
    """Long-only ladder strategy driven by absolute price thresholds."""

    def __init__(
        self,
        name: str = "Long Only Price Ladder",
        initial_investment: float = 10000.0,
        base_order_notional: float = 1000.0,
        buy_grid_step: float = 1.0,
        sell_grid_step: float | None = None,
        initial_execution_price: str = "open",
        buy_size_mode: str = "fixed",
        buy_multiplier: float = 1.0,
        max_buy_notional: float | None = None,
        sell_notional: float | None = None,
        cash_reserve: float = 0.0,
        reset_buy_scale_on_sell: bool = True,
    ) -> None:
        super().__init__(name)
        self.initial_investment = initial_investment
        self.base_order_notional = base_order_notional
        self.buy_grid_step = buy_grid_step
        self.sell_grid_step = sell_grid_step if sell_grid_step is not None else buy_grid_step
        self.initial_execution_price = initial_execution_price
        self.buy_size_mode = buy_size_mode
        self.buy_multiplier = buy_multiplier
        self.max_buy_notional = max_buy_notional
        self.sell_notional = sell_notional if sell_notional is not None else base_order_notional
        self.cash_reserve = cash_reserve
        self.reset_buy_scale_on_sell = reset_buy_scale_on_sell

        self.initialized = False
        self.last_trade_price: float | None = None
        self.position_shares: float = 0.0
        self.cost_basis_total: float = 0.0
        self.realized_pnl: float = 0.0
        self.trade_log: list[GridTradeRecord] = []
        self._next_layer_id = 1
        self._consecutive_buy_count = 0

    def on_bar(self, row: pd.Series, engine) -> None:
        timestamp = pd.Timestamp(row.name)
        open_price = float(row["Open"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        close_price = float(row["Close"])

        self._apply_split_adjustment(row)

        if not self.initialized:
            execution_price = open_price if self.initial_execution_price == "open" else close_price
            self._execute_buy(
                timestamp=timestamp,
                price=execution_price,
                notional=self.initial_investment,
                engine=engine,
                update_reference=True,
                count_for_progression=False,
            )
            self.initialized = True

        if self.last_trade_price is None:
            return

        # Gap handling: traverse the move from the last execution reference to the new open.
        self._process_segment(
            timestamp=timestamp,
            start_price=self.last_trade_price,
            end_price=open_price,
            engine=engine,
        )

        path = self._build_intrabar_path(open_price, high_price, low_price, close_price)
        current_price = open_price
        for next_price in path[1:]:
            self._process_segment(
                timestamp=timestamp,
                start_price=current_price,
                end_price=next_price,
                engine=engine,
            )
            current_price = next_price

    def _apply_split_adjustment(self, row: pd.Series) -> None:
        split_factor = float(row.get("Stock Splits", 0.0) or 0.0)
        if split_factor <= 0:
            return

        if self.last_trade_price is not None:
            self.last_trade_price /= split_factor
        self.position_shares *= split_factor
        # Total cost basis is unchanged; average cost per share drops with the split.

    def _build_intrabar_path(
        self,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
    ) -> list[float]:
        # Deterministic resolver without intraday data:
        # bullish candles are modeled as O-L-H-C, bearish candles as O-H-L-C.
        if close_price >= open_price:
            return [open_price, low_price, high_price, close_price]
        return [open_price, high_price, low_price, close_price]

    def _process_segment(
        self,
        *,
        timestamp: pd.Timestamp,
        start_price: float,
        end_price: float,
        engine,
    ) -> None:
        if self.last_trade_price is None or abs(end_price - start_price) < 1e-12:
            return

        if end_price > start_price:
            while self.last_trade_price is not None:
                next_level = self.last_trade_price + self.sell_grid_step
                if next_level > end_price + 1e-12:
                    break
                if not self._execute_sell(
                    timestamp=timestamp,
                    price=next_level,
                    requested_notional=self.sell_notional,
                    engine=engine,
                ):
                    break
            return

        while self.last_trade_price is not None:
            next_level = self.last_trade_price - self.buy_grid_step
            if next_level < end_price - 1e-12:
                break
            if not self._execute_buy(
                timestamp=timestamp,
                price=next_level,
                notional=self._resolve_buy_notional(),
                engine=engine,
                update_reference=True,
            ):
                break

    def _resolve_buy_notional(self) -> float:
        if self.buy_size_mode == "progressive":
            notional = self.base_order_notional * (self.buy_multiplier**self._consecutive_buy_count)
        else:
            notional = self.base_order_notional

        if self.max_buy_notional is not None:
            notional = min(notional, self.max_buy_notional)
        return notional

    def _execute_buy(
        self,
        *,
        timestamp: pd.Timestamp,
        price: float,
        notional: float,
        engine,
        update_reference: bool,
        count_for_progression: bool = True,
    ) -> bool:
        available_budget = max(engine.state.cash - self.cash_reserve, 0.0)
        if notional <= 0 or available_budget + 1e-9 < notional:
            return False
        spend_notional = notional

        quantity = spend_notional / price
        layer_id = self._next_layer_id
        if not engine.buy(timestamp, price, quantity, layer_id=layer_id):
            return False

        self._next_layer_id += 1
        self.position_shares += quantity
        self.cost_basis_total += spend_notional
        if update_reference:
            self.last_trade_price = price
        if count_for_progression:
            self._consecutive_buy_count += 1
        self.trade_log.append(
            GridTradeRecord(
                timestamp=timestamp,
                action="BUY",
                price=price,
                notional=spend_notional,
                quantity=quantity,
                cash_after=engine.state.cash,
                position_after=self.position_shares,
                reference_after=self.last_trade_price or price,
            )
        )
        return True

    def _execute_sell(
        self,
        *,
        timestamp: pd.Timestamp,
        price: float,
        requested_notional: float,
        engine,
    ) -> bool:
        if self.position_shares <= 1e-12:
            return False

        available_notional = self.position_shares * price
        sell_notional = min(requested_notional, available_notional)
        sell_quantity = sell_notional / price
        if sell_quantity <= 1e-12:
            return False

        remaining_quantity = sell_quantity
        for layer in list(reversed(engine.state.layers.copy())):
            if remaining_quantity <= 1e-12:
                break
            quantity_to_sell = min(layer.quantity, remaining_quantity)
            if quantity_to_sell <= 1e-12:
                continue
            if not engine.sell(timestamp, price, quantity_to_sell, layer.layer_id):
                return False
            remaining_quantity -= quantity_to_sell

        if remaining_quantity > 1e-9:
            return False

        average_cost = (
            self.cost_basis_total / self.position_shares if self.position_shares > 0 else 0.0
        )
        realized_cost = average_cost * sell_quantity
        self.cost_basis_total -= realized_cost
        self.position_shares -= sell_quantity
        self.realized_pnl += sell_notional - realized_cost
        self.last_trade_price = price
        if self.reset_buy_scale_on_sell:
            self._consecutive_buy_count = 0
        self.trade_log.append(
            GridTradeRecord(
                timestamp=timestamp,
                action="SELL",
                price=price,
                notional=sell_notional,
                quantity=sell_quantity,
                cash_after=engine.state.cash,
                position_after=self.position_shares,
                reference_after=price,
            )
        )
        return True

    def trade_log_frame(self) -> pd.DataFrame:
        if not self.trade_log:
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "action",
                    "price",
                    "notional",
                    "quantity",
                    "cash_after",
                    "position_after",
                    "reference_after",
                ]
            )
        return pd.DataFrame([record.to_dict() for record in self.trade_log])

    def final_average_price(self) -> float:
        if self.position_shares <= 1e-12:
            return 0.0
        return self.cost_basis_total / self.position_shares


class RegraAGridStrategy(LongOnlyPriceLadderStrategy):
    """Price-grid strategy that trades fixed notionals on R$1.00 moves."""

    def __init__(
        self,
        initial_investment: float = 10000.0,
        order_notional: float = 1000.0,
        grid_step: float = 1.0,
        initial_execution_price: str = "open",
    ) -> None:
        super().__init__(
            name="Regra A Grid",
            initial_investment=initial_investment,
            base_order_notional=order_notional,
            buy_grid_step=grid_step,
            sell_grid_step=grid_step,
            initial_execution_price=initial_execution_price,
            buy_size_mode="fixed",
            buy_multiplier=1.0,
            sell_notional=order_notional,
            cash_reserve=0.0,
            reset_buy_scale_on_sell=True,
        )
