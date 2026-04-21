"""Adaptive grid strategy with a permanent core position and ATR-based tactical bands."""

from __future__ import annotations

from collections import deque

import pandas as pd

from .base import Strategy


class AdaptiveCoreGridStrategy(Strategy):
    """Hold a core position and trade tactical inventory with ATR-sized steps."""

    def __init__(
        self,
        core_notional: float = 10000.0,
        order_notional: float = 1000.0,
        min_step: float = 1.0,
        atr_period: int = 14,
        atr_multiplier: float = 1.0,
        max_tactical_notional: float = 15000.0,
        initial_execution_price: str = "open",
    ) -> None:
        super().__init__("Adaptive Core Grid")
        self.core_notional = core_notional
        self.order_notional = order_notional
        self.min_step = min_step
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.max_tactical_notional = max_tactical_notional
        self.initial_execution_price = initial_execution_price

        self.initialized = False
        self.core_layer_id = 1
        self._next_layer_id = 2
        self.last_trade_price: float | None = None
        self.core_quantity = 0.0
        self.tactical_quantity = 0.0
        self._previous_close: float | None = None
        self._true_ranges: deque[float] = deque(maxlen=atr_period)

    def on_bar(self, row: pd.Series, engine) -> None:
        timestamp = pd.Timestamp(row.name)
        open_price = float(row["Open"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        close_price = float(row["Close"])

        self._apply_split_adjustment(row)
        step = self._current_step()

        if not self.initialized:
            execution_price = open_price if self.initial_execution_price == "open" else close_price
            buy_quantity = self.core_notional / execution_price
            if engine.buy(timestamp, execution_price, buy_quantity, layer_id=self.core_layer_id):
                self.core_quantity = buy_quantity
                self.last_trade_price = execution_price
                self.initialized = True

        if self.last_trade_price is not None:
            self._process_segment(
                timestamp=timestamp,
                start_price=self.last_trade_price,
                end_price=open_price,
                step=step,
                engine=engine,
            )

            current_price = open_price
            for next_price in self._intrabar_path(open_price, high_price, low_price, close_price)[1:]:
                self._process_segment(
                    timestamp=timestamp,
                    start_price=current_price,
                    end_price=next_price,
                    step=step,
                    engine=engine,
                )
                current_price = next_price

        self._update_atr(high_price, low_price, close_price)

    def _intrabar_path(
        self,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
    ) -> list[float]:
        if close_price >= open_price:
            return [open_price, low_price, high_price, close_price]
        return [open_price, high_price, low_price, close_price]

    def _update_atr(self, high_price: float, low_price: float, close_price: float) -> None:
        if self._previous_close is None:
            true_range = high_price - low_price
        else:
            true_range = max(
                high_price - low_price,
                abs(high_price - self._previous_close),
                abs(low_price - self._previous_close),
            )
        self._true_ranges.append(true_range)
        self._previous_close = close_price

    def _current_step(self) -> float:
        if not self._true_ranges:
            return self.min_step
        atr = sum(self._true_ranges) / len(self._true_ranges)
        return max(self.min_step, atr * self.atr_multiplier)

    def _apply_split_adjustment(self, row: pd.Series) -> None:
        split_factor = float(row.get("Stock Splits", 0.0) or 0.0)
        if split_factor <= 0:
            return

        if self.last_trade_price is not None:
            self.last_trade_price /= split_factor
        self.core_quantity *= split_factor
        self.tactical_quantity *= split_factor

    def _process_segment(
        self,
        *,
        timestamp: pd.Timestamp,
        start_price: float,
        end_price: float,
        step: float,
        engine,
    ) -> None:
        if self.last_trade_price is None or abs(end_price - start_price) < 1e-12:
            return

        if end_price > start_price:
            while self.last_trade_price is not None:
                next_level = self.last_trade_price + step
                if next_level > end_price + 1e-12:
                    break
                if not self._sell_tactical(timestamp=timestamp, price=next_level, engine=engine):
                    break
            return

        while self.last_trade_price is not None:
            next_level = self.last_trade_price - step
            if next_level < end_price - 1e-12:
                break
            if not self._buy_tactical(timestamp=timestamp, price=next_level, engine=engine):
                break

    def _buy_tactical(self, *, timestamp: pd.Timestamp, price: float, engine) -> bool:
        if engine.state.cash + 1e-9 < self.order_notional:
            return False
        if (self.tactical_quantity * price) + self.order_notional > self.max_tactical_notional + 1e-9:
            return False

        quantity = self.order_notional / price
        layer_id = self._next_layer_id
        if not engine.buy(timestamp, price, quantity, layer_id=layer_id):
            return False

        self._next_layer_id += 1
        self.tactical_quantity += quantity
        self.last_trade_price = price
        return True

    def _sell_tactical(self, *, timestamp: pd.Timestamp, price: float, engine) -> bool:
        if self.tactical_quantity <= 1e-12:
            return False

        available_notional = self.tactical_quantity * price
        sell_notional = min(self.order_notional, available_notional)
        sell_quantity = sell_notional / price
        if sell_quantity <= 1e-12:
            return False

        remaining_quantity = sell_quantity
        tactical_layers = [
            layer for layer in reversed(engine.state.layers.copy()) if layer.layer_id != self.core_layer_id
        ]
        for layer in tactical_layers:
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

        self.tactical_quantity -= sell_quantity
        if self.tactical_quantity < 1e-9:
            self.tactical_quantity = 0.0
        self.last_trade_price = price
        return True
