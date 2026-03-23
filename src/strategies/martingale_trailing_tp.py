"""Martingale strategy with trailing take-profit implementation."""

import pandas as pd
from typing import Optional, Dict

from .base import MartingaleStrategy
from ..engine import State, Layer


class MartingaleTrailingTPStrategy(MartingaleStrategy):
    """Martingale strategy with trailing take-profit.

    Features:
    - Fixed Martingale entry logic
    - Trailing take-profit for each layer
    - Individual trailing stops per layer
    - LIFO exit with trailing protection
    """

    def __init__(self, trailing_percent: float = 0.05, **kwargs):
        """Initialize trailing take-profit Martingale strategy.

        Args:
            trailing_percent: Trailing stop percentage (e.g., 0.05 = 5%)
            **kwargs: Base Martingale parameters
        """
        super().__init__("Trailing TP Martingale", **kwargs)
        self.trailing_percent = trailing_percent
        self.last_buy_price: Optional[float] = None
        self.layer_trailing_stops: Dict[int, float] = {}  # layer_id -> trailing_stop_price

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

        # Update trailing stops for all layers
        self._update_trailing_stops(high_price, engine)

        # Check for layer addition (buy signal)
        if self.can_add_layer(engine):
            last_layer = engine.state.layers[-1]
            target_buy_price = self.get_next_buy_price(last_layer.entry_price)
            if low_price <= target_buy_price:
                self._execute_layer_buy(timestamp, close_price, engine)

        # Check for trailing stop exits (sell signals)
        self._check_trailing_stops(low_price, close_price, timestamp, engine)

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
                # Initialize trailing stop for new layer
                if engine.state.layers:
                    layer = engine.state.layers[-1]
                    self.layer_trailing_stops[layer.layer_id] = layer.entry_price

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
                # Initialize trailing stop for new layer
                if engine.state.layers:
                    layer = engine.state.layers[-1]
                    initial_tp = self.get_target_sell_price(layer.entry_price)
                    self.layer_trailing_stops[layer.layer_id] = initial_tp

    def _update_trailing_stops(self, high_price: float, engine) -> None:
        """Update trailing stops for all open layers.

        Args:
            high_price: Current bar high price
            engine: Backtest engine instance
        """
        for layer in engine.state.layers:
            if layer.layer_id not in self.layer_trailing_stops:
                # Initialize trailing stop if not exists
                self.layer_trailing_stops[layer.layer_id] = layer.entry_price

            current_stop = self.layer_trailing_stops[layer.layer_id]

            # Calculate new potential trailing stop
            new_stop = layer.entry_price * (1 + self.take_profit)
            if high_price > layer.entry_price * (1 + self.take_profit):
                # Price is above initial take profit, start trailing
                trail_price = high_price * (1 - self.trailing_percent)
                new_stop = max(current_stop, trail_price)

            self.layer_trailing_stops[layer.layer_id] = new_stop

    def _check_trailing_stops(self, low_price: float, close_price: float, timestamp, engine) -> None:
        """Check if any trailing stops have been triggered.

        Args:
            low_price: Current bar low price
            timestamp: Trade timestamp
            engine: Backtest engine instance
        """
        # Check layers in reverse order for LIFO
        layers_to_check = list(reversed(engine.state.layers))

        for layer in layers_to_check:
            if layer.layer_id in self.layer_trailing_stops:
                trailing_stop = self.layer_trailing_stops[layer.layer_id]

                # Check if trailing stop was hit
                if low_price <= trailing_stop:
                    exec_price = close_price * (1 - self.slippage)
                    self._execute_trailing_sell(timestamp, exec_price, layer, engine)

                    # Remove trailing stop for this layer
                    del self.layer_trailing_stops[layer.layer_id]
                    break  # Only sell one layer per bar (LIFO)

    def _execute_trailing_sell(
        self, timestamp, price: float, layer: Layer, engine
    ) -> None:
        """Execute trailing stop sell.

        Args:
            timestamp: Trade timestamp
            price: Trailing stop execution price
            layer: Layer to sell
            engine: Backtest engine instance
        """
        if engine.sell(timestamp, price, layer.quantity, layer.layer_id):
            # Update last buy price reference
            if len(engine.state.layers) > 0:
                self.last_buy_price = engine.state.layers[-1].entry_price
            else:
                self.last_buy_price = None

    def get_metrics(self) -> dict:
        """Get strategy-specific metrics.

        Returns:
            Dictionary with trailing TP metrics
        """
        base_metrics = super().get_metrics()
        trailing_metrics = {
            "trailing_percent": self.trailing_percent,
            "active_trailing_stops": len(self.layer_trailing_stops),
        }
        base_metrics.update(trailing_metrics)
        return base_metrics
