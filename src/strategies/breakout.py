"""Breakout Strategy - Trade based on price breakouts from n-day highs."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base import BaseStrategy


class BreakoutStrategy(BaseStrategy):
    """Breakout strategy implementation.

    Buys when price breaks above n-day high.
    Uses trailing stop loss for exits.
    Includes position sizing based on breakout strength.
    """

    def __init__(
        self,
        initial_capital: float = 30000.0,
        lookback_period: int = 20,  # Number of days for high/low calculation
        breakout_threshold: float = 0.001,  # Minimum breakout % (0.1% default)
        trailing_stop_pct: float = 0.05,  # 5% trailing stop
        position_size_pct: float = 0.5,  # Use 50% of available cash per position
        min_cash_reserve: float = 1000.0,
        max_positions: int = 1,  # Max concurrent positions
        slippage: float = 0.0005
    ):
        """Initialize Breakout strategy.

        Args:
            initial_capital: Starting capital amount
            lookback_period: Period for calculating high/low levels
            breakout_threshold: Minimum percentage above high to consider breakout
            trailing_stop_pct: Trailing stop loss percentage
            position_size_pct: Percentage of cash to use per position
            min_cash_reserve: Minimum cash to keep in reserve
            max_positions: Maximum number of concurrent positions
        """
        super().__init__(f"Breakout ({lookback_period}d)", initial_capital)
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.trailing_stop_pct = trailing_stop_pct
        self.position_size_pct = position_size_pct
        self.min_cash_reserve = min_cash_reserve
        self.max_positions = max_positions
        self.slippage = slippage

        # Track state
        self.price_history = []
        self.highs = []
        self.lows = []
        self.positions = []  # Track multiple positions
        self.trade_count = 0

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process each bar for breakout logic.

        Args:
            row: Current OHLCV data row
            engine: Backtest engine instance
        """
        current_date = row.name
        current_price = float(row["Close"])
        current_high = float(row["High"])
        current_low = float(row["Low"])

        # Store price data
        self.price_history.append(current_price)

        # Need enough data for lookback
        if len(self.price_history) < self.lookback_period:
            self.highs.append(current_high)
            self.lows.append(current_low)
            return

        # Calculate rolling high and low
        recent_prices = pd.Series(self.price_history[-self.lookback_period:])
        recent_highs = pd.Series(self.highs[-self.lookback_period:])
        recent_lows = pd.Series(self.lows[-self.lookback_period:])

        rolling_high = max(recent_highs.max(), recent_prices.max())
        rolling_low = min(recent_lows.min(), recent_prices.min())

        # Update rolling highs/lows
        self.highs.append(current_high)
        self.lows.append(current_low)
        if len(self.highs) > self.lookback_period * 2:  # Keep history manageable
            self.highs = self.highs[-self.lookback_period:]
        if len(self.lows) > self.lookback_period * 2:
            self.lows = self.lows[-self.lookback_period:]

        # Check for new breakouts
        self._check_breakouts(current_date, current_price, rolling_high, engine)
        self._update_stops(current_date, current_price, engine)

    def _check_breakouts(self, timestamp, price, resistance_level, engine):
        """Check for new breakout opportunities."""
        if len(self.positions) >= self.max_positions:
            return

        # Check if we have enough cash
        available_cash = max(engine.state.cash - self.min_cash_reserve, 0)
        if available_cash <= 0:
            return

        # Calculate breakout strength
        breakout_pct = (price - resistance_level) / resistance_level

        # Only trade if breakout is significant enough
        if breakout_pct < self.breakout_threshold:
            return

        # Position sizing based on breakout strength
        cash_to_use = available_cash * self.position_size_pct
        exec_price = price * (1 + self.slippage)
        quantity = cash_to_use / exec_price

        if quantity > 0:
            # Execute buy
            engine.buy(timestamp=timestamp, price=exec_price, quantity=quantity, layer_id=len(self.positions) + 1)

            # Calculate stop loss
            stop_loss = exec_price * (1 - self.trailing_stop_pct)

            # Track position
            position = {
                "entry_price": exec_price,
                "quantity": quantity,
                "entry_date": timestamp,
                "stop_loss": stop_loss,
                "highest_price": exec_price,  # For trailing stop
                "layer": len(self.positions) + 1
            }
            self.positions.append(position)
            self.trade_count += 1

            self.trades.append({
                "timestamp": timestamp,
                "action": "BUY",
                "price": exec_price,
                "quantity": quantity,
                "layer": position["layer"],
                "signal": "BREAKOUT_BUY",
                "reason": f"Breakout: {price:.2f} (+{breakout_pct:.2%}) above {resistance_level:.2f}, Stop: {stop_loss:.2f}"
            })

    def _update_stops(self, timestamp, price, engine):
        """Update trailing stops and check for exits."""
        positions_to_remove = []

        for i, position in enumerate(self.positions):
            # Update trailing stop if price moved up
            if price > position["highest_price"]:
                new_stop = price * (1 - self.trailing_stop_pct)
                if new_stop > position["stop_loss"]:
                    position["stop_loss"] = new_stop
                    position["highest_price"] = price

            # Check if stop loss triggered
            if price <= position["stop_loss"]:
                # Execute sell
                exec_price = price * (1 - self.slippage)
                engine.sell(
                    timestamp=timestamp,
                    price=exec_price,
                    quantity=position["quantity"],
                    layer_id=position["layer"]
                )

                # Calculate P&L
                pnl = (exec_price - position["entry_price"]) * position["quantity"]
                holding_days = (timestamp - position["entry_date"]).days

                self.trades.append({
                    "timestamp": timestamp,
                    "action": "SELL",
                    "price": price,
                    "quantity": position["quantity"],
                    "layer": position["layer"],
                    "pnl": pnl,
                    "signal": "BREAKOUT_STOP",
                    "reason": f"Stop loss triggered: {price:.2f} vs stop {position['stop_loss']:.2f}, P&L: {pnl:.2f} after {holding_days} days"
                })

                positions_to_remove.append(i)

        # Remove closed positions
        for i in reversed(positions_to_remove):
            self.positions.pop(i)

    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get strategy signals for analysis.

        Args:
            data: Historical price data

        Returns:
            Dictionary with analysis results
        """
        signals = {
            "strategy_name": f"Breakout ({self.lookback_period}d)",
            "signals": [],
            "active_positions": len(self.positions),
            "total_trades": self.trade_count,
            "current_resistance": 0.0,
            "current_support": 0.0,
            "price_history_length": len(self.price_history)
        }

        if len(self.price_history) >= self.lookback_period:
            recent_prices = pd.Series(self.price_history[-self.lookback_period:])
            signals["current_resistance"] = recent_prices.max()
            signals["current_support"] = recent_prices.min()

        return signals

    def reset(self) -> None:
        """Reset strategy state for new backtest."""
        super().reset()
        self.price_history = []
        self.highs = []
        self.lows = []
        self.positions = []
        self.trade_count = 0
