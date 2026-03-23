"""Hybrid DCA + Martingale strategy implementation."""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from .base import MartingaleStrategy
from ..engine import State


class DCAHybridStrategy(MartingaleStrategy):
    """Hybrid strategy combining Dollar Cost Averaging with limited Martingale.

    Features:
    - Periodic DCA purchases (e.g., weekly/monthly)
    - Limited Martingale layers on significant dips
    - Risk management through position limits
    - Combines trend-following (DCA) with mean-reversion (Martingale)
    """

    def __init__(
        self,
        dca_amount: float = 500.0,
        dca_frequency: str = "weekly",  # daily, weekly, monthly
        max_martingale_layers: int = 3,
        dca_trigger_threshold: float = 0.05,  # 5% below moving average
        moving_average_period: int = 50,
        **kwargs
    ):
        """Initialize hybrid DCA-Martingale strategy.

        Args:
            dca_amount: Fixed amount for DCA purchases
            dca_frequency: Frequency of DCA purchases
            max_martingale_layers: Maximum Martingale layers (lower than pure Martingale)
            dca_trigger_threshold: Dip threshold for DCA activation
            moving_average_period: Period for moving average calculation
            **kwargs: Base Martingale parameters
        """
        super().__init__("DCA Hybrid Martingale", max_layers=max_martingale_layers, **kwargs)
        self.dca_amount = dca_amount
        self.dca_frequency = dca_frequency
        self.dca_trigger_threshold = dca_trigger_threshold
        self.moving_average_period = moving_average_period

        self.last_dca_date: Optional[datetime] = None
        self.price_history: list = []
        self.current_ma: float = 0.0

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

        # Update moving average
        self._update_moving_average(close_price)

        # Check for DCA opportunity
        self._check_dca_opportunity(timestamp, close_price, engine)

        # Check for Martingale layers (limited)
        if engine.state.layers:
            self._check_martingale_signals(timestamp, high_price, low_price, engine, close_price)

    def _update_moving_average(self, price: float) -> None:
        """Update moving average calculation.

        Args:
            price: Current price
        """
        self.price_history.append(price)

        # Keep only recent history
        if len(self.price_history) > self.moving_average_period * 2:
            self.price_history = self.price_history[-self.moving_average_period * 2 :]

        # Calculate moving average
        if len(self.price_history) >= self.moving_average_period:
            recent_prices = self.price_history[-self.moving_average_period:]
            self.current_ma = sum(recent_prices) / len(recent_prices)

    def _check_dca_opportunity(self, timestamp, price: float, engine) -> None:
        """Check if DCA purchase should be executed.

        Args:
            timestamp: Current timestamp
            price: Current price
            engine: Backtest engine instance
        """
        # Check if enough time has passed since last DCA
        if not self._should_dca(timestamp):
            return

        # Check if price is below threshold (dip buying)
        price_dip = (self.current_ma - price) / self.current_ma if self.current_ma > 0 else 0

        # DCA if:
        # 1. No positions (initial DCA)
        # 2. Price is significantly below moving average
        # 3. Have enough cash
        exec_price = price * (1 + self.slippage)
        if (not engine.state.layers or price_dip >= self.dca_trigger_threshold) and engine.state.cash >= self.dca_amount:
            if engine.buy(timestamp, exec_price, self.dca_amount / exec_price):
                self.last_dca_date = timestamp

    def _should_dca(self, timestamp) -> bool:
        """Check if DCA should be executed based on frequency.

        Args:
            timestamp: Current timestamp

        Returns:
            True if DCA should be executed
        """
        if self.last_dca_date is None:
            return True

        time_diff = timestamp - self.last_dca_date

        if self.dca_frequency == "daily":
            return time_diff >= timedelta(days=1)
        elif self.dca_frequency == "weekly":
            return time_diff >= timedelta(days=7)
        elif self.dca_frequency == "monthly":
            return time_diff >= timedelta(days=30)
        else:
            return False

    def _check_martingale_signals(
        self, timestamp, high_price: float, low_price: float, engine, close_price: float
    ) -> None:
        """Check for Martingale buy and sell signals.

        Args:
            timestamp: Current timestamp
            high_price: Current bar high
            low_price: Current bar low
            engine: Backtest engine instance
        """
        if not engine.state.layers:
            return

        # Get the most recent layer for LIFO logic
        last_layer = engine.state.layers[-1]

        # Check for Martingale layer addition (only if below max layers)
        if self.can_add_layer(engine):
            # Use more conservative drop step for hybrid
            conservative_drop_step = self.drop_step * 1.5  # Wider drops
            target_buy_price = last_layer.entry_price * (1 - conservative_drop_step)

            if low_price <= target_buy_price:
                self._execute_martingale_buy(timestamp, engine.state.layers[-1], engine, close_price)

        # Check for layer exit (take profit)
        target_sell_price = self.get_target_sell_price(last_layer.entry_price)
        if high_price >= target_sell_price:
            self._execute_martingale_sell(timestamp, close_price, last_layer, engine)

    def _execute_martingale_buy(self, timestamp, last_layer, engine, close_price: float) -> None:
        """Execute Martingale layer buy.

        Args:
            timestamp: Trade timestamp
            price: Target buy price
            engine: Backtest engine instance
        """
        current_layers = len(engine.state.layers)
        # More conservative sizing for hybrid
        conservative_multiplier = self.multiplier * 0.8
        bet_amount = self.base_bet * (conservative_multiplier ** current_layers)
        exec_price = close_price * (1 + self.slippage)

        if engine.state.cash >= bet_amount:
            quantity = self.calculate_position_size(bet_amount, exec_price)
            engine.buy(timestamp, exec_price, quantity)

    def _execute_martingale_sell(self, timestamp, price: float, layer, engine) -> None:
        """Execute Martingale layer sell.

        Args:
            timestamp: Trade timestamp
            price: Target sell price
            layer: Layer to sell
            engine: Backtest engine instance
        """
        exec_price = price * (1 - self.slippage)
        engine.sell(timestamp, exec_price, layer.quantity, layer.layer_id)

    def get_metrics(self) -> dict:
        """Get strategy-specific metrics.

        Returns:
            Dictionary with hybrid strategy metrics
        """
        base_metrics = super().get_metrics()
        hybrid_metrics = {
            "dca_amount": self.dca_amount,
            "dca_frequency": self.dca_frequency,
            "current_ma": self.current_ma,
            "last_dca_date": self.last_dca_date.isoformat() if self.last_dca_date else None,
        }
        base_metrics.update(hybrid_metrics)
        return base_metrics
