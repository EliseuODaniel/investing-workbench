"""Fixed parameter Martingale strategy implementation."""

import pandas as pd
from typing import Optional

from .base import MartingaleStrategy
from ..engine import State


class MartingaleFixedStrategy(MartingaleStrategy):
    """Basic Martingale strategy with fixed parameters.

    Implements classic Martingale with LIFO exit:
    - Buy initial position
    - Add layers on fixed % drops
    - Exit layers on fixed % gains (LIFO order)
    """

    def __init__(self, **kwargs):
        """Initialize fixed Martingale strategy.

        Args:
            **kwargs: Strategy parameters (base_bet, multiplier, drop_step, take_profit, max_layers)
        """
        super().__init__("Fixed Martingale", **kwargs)
        self.last_buy_price: Optional[float] = None

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process current bar and generate trading signals.

        Args:
            row: Current OHLCV bar
            state: Current backtest state
        """
        close_price = float(row["Close"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        timestamp = row.name

        # Initial buy if no positions
        if not engine.state.layers:
            self._execute_initial_buy(timestamp, close_price, engine)
            return

        # Update reference to last layer
        last_layer = engine.state.layers[-1] if engine.state.layers else None
        if last_layer is None:
            return

        # Check for layer addition (buy signal)
        if self.can_add_layer(engine):
            target_buy_price = self.get_next_buy_price(last_layer.entry_price)
            if low_price <= target_buy_price:
                self._execute_layer_buy(timestamp, close_price, engine)

        # Check for layer exit (sell signal)
        target_sell_price = self.get_target_sell_price(last_layer.entry_price)
        if high_price >= target_sell_price:
            self._execute_layer_sell(timestamp, close_price, last_layer, engine)

    def _execute_initial_buy(self, timestamp, price: float, engine) -> None:
        """Execute initial position entry.

        Args:
            timestamp: Trade timestamp
            price: Execution price
            engine: Backtest engine instance
        """
        exec_price = price * (1 + self.slippage)
        if engine.state.cash >= self.base_bet:
            quantity = self.calculate_position_size(self.base_bet, exec_price)
            if engine.buy(timestamp, exec_price, quantity):
                self.last_buy_price = price

    def _execute_layer_buy(self, timestamp, price: float, engine) -> None:
        """Execute additional layer buy.

        Args:
            timestamp: Trade timestamp
            price: Target buy price
            engine: Backtest engine instance
        """
        current_layers = len(engine.state.layers)
        bet_amount = self.calculate_next_bet_size(current_layers)

        exec_price = price * (1 + self.slippage)
        if engine.state.cash >= bet_amount:
            quantity = self.calculate_position_size(bet_amount, exec_price)
            if engine.buy(timestamp, exec_price, quantity):
                self.last_buy_price = price

    def _execute_layer_sell(
        self, timestamp, price: float, layer, engine
    ) -> None:
        """Execute layer sell (LIFO).

        Args:
            timestamp: Trade timestamp
            price: Target sell price
            layer: Layer to sell
            engine: Backtest engine instance
        """
        # Sell entire layer position
        exec_price = price * (1 - self.slippage)
        if engine.sell(timestamp, exec_price, layer.quantity, layer.layer_id):
            # Last buy price becomes previous layer's entry price for reference
            if len(engine.state.layers) > 0:
                self.last_buy_price = engine.state.layers[-1].entry_price
            else:
                self.last_buy_price = None
