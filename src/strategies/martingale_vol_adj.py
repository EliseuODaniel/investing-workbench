"""Volatility-adjusted Martingale strategy implementation."""

import pandas as pd
import numpy as np
from typing import Optional

from .base import MartingaleStrategy
from ..engine import State


class MartingaleVolatilityStrategy(MartingaleStrategy):
    """Martingale strategy with volatility-adjusted parameters.

    Adjusts drop step and position sizing based on recent volatility:
    - Higher volatility = wider drop steps
    - Volatility-based position sizing
    - Uses ATR or standard deviation for volatility measurement
    """

    def __init__(
        self,
        volatility_period: int = 20,
        vol_multiplier: float = 1.0,
        atr_period: int = 14,
        **kwargs
    ):
        """Initialize volatility-adjusted Martingale strategy.

        Args:
            volatility_period: Period for volatility calculation
            vol_multiplier: Multiplier for volatility-based adjustments
            atr_period: Period for ATR calculation
            **kwargs: Base Martingale parameters
        """
        super().__init__("Volatility-Adjusted Martingale", **kwargs)
        self.volatility_period = volatility_period
        self.vol_multiplier = vol_multiplier
        self.atr_period = atr_period
        self.last_buy_price: Optional[float] = None
        self.price_history: list = []
        self.current_volatility: float = 0.0
        self.current_atr: float = 0.0

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

        # Update price history and calculate volatility
        self._update_indicators(row)

        # Initial buy if no positions
        if not engine.state.layers:
            self._execute_initial_buy(timestamp, close_price, engine)
            return

        # Update reference to last layer
        last_layer = engine.state.layers[-1] if engine.state.layers else None
        if last_layer is None:
            return

        # Check for layer addition (buy signal) with volatility adjustment
        if self.can_add_layer(engine):
            adjusted_drop_step = self._get_adjusted_drop_step()
            target_buy_price = last_layer.entry_price * (1 - adjusted_drop_step)

            if low_price <= target_buy_price:
                adjusted_bet = self._get_adjusted_bet_size(len(engine.state.layers))
                self._execute_layer_buy(timestamp, close_price, adjusted_bet, engine)

        # Check for layer exit (sell signal) - can also adjust take profit based on volatility
        adjusted_tp = self._get_adjusted_take_profit()
        target_sell_price = last_layer.entry_price * (1 + adjusted_tp)

        if high_price >= target_sell_price:
            self._execute_layer_sell(timestamp, close_price, last_layer, engine)

    def _update_indicators(self, row: pd.Series) -> None:
        """Update volatility indicators.

        Args:
            row: Current OHLCV bar
        """
        self.price_history.append(float(row["Close"]))

        # Keep only recent history
        if len(self.price_history) > max(self.volatility_period, self.atr_period) * 2:
            self.price_history = self.price_history[-max(self.volatility_period, self.atr_period) * 2 :]

        # Calculate standard deviation volatility
        if len(self.price_history) >= self.volatility_period:
            recent_prices = self.price_history[-self.volatility_period:]
            returns = pd.Series(recent_prices).pct_change().dropna()
            if len(returns) > 1:
                self.current_volatility = returns.std() * np.sqrt(252)  # Annualized

        # Calculate ATR if we have enough OHLC data
        if len(self.price_history) >= self.atr_period:
            # For simplicity, using close prices - in production, use true ATR with high/low
            recent_prices = pd.Series(self.price_history[-self.atr_period:])
            if len(recent_prices) > 1:
                high_low_diff = recent_prices.diff().abs()
                self.current_atr = high_low_diff.mean()

    def _get_adjusted_drop_step(self) -> float:
        """Get volatility-adjusted drop step.

        Returns:
            Adjusted drop step percentage
        """
        # Higher volatility = wider drop steps
        if self.current_volatility > 0:
            vol_adjustment = 1 + (self.current_volatility * self.vol_multiplier)
            return min(self.drop_step * vol_adjustment, 0.5)  # Cap at 50%
        return self.drop_step

    def _get_adjusted_take_profit(self) -> float:
        """Get volatility-adjusted take profit.

        Returns:
            Adjusted take profit percentage
        """
        # Higher volatility = higher take profit targets
        if self.current_volatility > 0:
            vol_adjustment = 1 + (self.current_volatility * self.vol_multiplier * 0.5)
            return min(self.take_profit * vol_adjustment, 1.0)  # Cap at 100%
        return self.take_profit

    def _get_adjusted_bet_size(self, current_layers: int) -> float:
        """Get volatility-adjusted bet size.

        Args:
            current_layers: Current number of layers

        Returns:
            Adjusted bet amount
        """
        base_size = self.calculate_next_bet_size(current_layers)

        # Lower volatility = more aggressive sizing
        if self.current_volatility > 0:
            vol_adjustment = 1 / (1 + self.current_volatility * self.vol_multiplier)
            return base_size * vol_adjustment

        return base_size

    def _execute_initial_buy(self, timestamp, price: float, engine) -> None:
        """Execute initial position entry.

        Args:
            timestamp: Trade timestamp
            price: Execution price
            engine: Backtest engine instance
        """
        adjusted_bet = self._get_adjusted_bet_size(0)
        exec_price = price * (1 + self.slippage)
        if engine.state.cash >= adjusted_bet:
            quantity = self.calculate_position_size(adjusted_bet, exec_price)
            if engine.buy(timestamp, exec_price, quantity):
                self.last_buy_price = price

    def _execute_layer_buy(
        self, timestamp, price: float, bet_amount: float, engine
    ) -> None:
        """Execute additional layer buy with adjusted size.

        Args:
            timestamp: Trade timestamp
            price: Target buy price
            bet_amount: Adjusted bet amount
            engine: Backtest engine instance
        """
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
            # Update last buy price reference
            if len(engine.state.layers) > 0:
                self.last_buy_price = engine.state.layers[-1].entry_price
            else:
                self.last_buy_price = None
