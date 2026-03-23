"""Trend Following Strategy - Moving Average Crossover."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base import BaseStrategy


class TrendMACrossStrategy(BaseStrategy):
    """Trend following strategy using moving average crossover.

    Goes long when short MA crosses above long MA.
    Exits (sells entire position) when short MA crosses below long MA.
    Uses position sizing based on available capital.
    """

    def __init__(
        self,
        initial_capital: float = 30000.0,
        short_ma_period: int = 10,
        long_ma_period: int = 50,
        position_size_pct: float = 1.0,  # Use 100% of available cash by default
        min_cash_reserve: float = 1000.0  # Keep minimum cash reserve
    ):
        """Initialize Trend MA Cross strategy.

        Args:
            initial_capital: Starting capital amount
            short_ma_period: Period for short moving average
            long_ma_period: Period for long moving average
            position_size_pct: Percentage of available cash to use (0.0 to 1.0)
            min_cash_reserve: Minimum cash to keep in reserve
        """
        super().__init__(f"MA Cross ({short_ma_period}/{long_ma_period})", initial_capital)
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        self.position_size_pct = position_size_pct
        self.min_cash_reserve = min_cash_reserve

        # Track state
        self.in_position = False
        self.position_size = 0.0
        self.entry_price = 0.0
        self.entry_date = None
        self.ma_history = []

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process each bar for MA crossover logic.

        Args:
            row: Current OHLCV data row
            engine: Backtest engine instance
        """
        current_date = row.name
        current_price = float(row["Close"])

        # Store price for MA calculation
        self.price_history.append(current_price)

        # Need enough data for both MAs
        if len(self.price_history) < self.long_ma_period:
            return

        # Calculate moving averages
        prices = pd.Series(self.price_history)
        short_ma = prices.tail(self.short_ma_period).mean()
        long_ma = prices.tail(self.long_ma_period).mean()

        # Store MA history for analysis
        self.ma_history.append({
            "timestamp": current_date,
            "price": current_price,
            "short_ma": short_ma,
            "long_ma": long_ma
        })

        # Generate signals
        ma_diff = short_ma - long_ma
        prev_ma_diff = self.ma_history[-2]["short_ma"] - self.ma_history[-2]["long_ma"] if len(self.ma_history) >= 2 else 0

        # Check for crossover signals
        if not self.in_position:
            # Buy signal: short MA crosses above long MA
            if prev_ma_diff <= 0 and ma_diff > 0:
                self._enter_position(current_date, current_price, engine)
        else:
            # Sell signal: short MA crosses below long MA
            if prev_ma_diff >= 0 and ma_diff < 0:
                self._exit_position(current_date, current_price, engine)

    def _enter_position(self, timestamp, price, engine):
        """Enter long position."""
        available_cash = max(engine.state.cash - self.min_cash_reserve, 0)
        cash_to_use = available_cash * self.position_size_pct

        if cash_to_use > 0:
            quantity = cash_to_use / price
            engine.buy(timestamp=timestamp, price=price, quantity=quantity, layer_id=1)

            self.in_position = True
            self.position_size = quantity
            self.entry_price = price
            self.entry_date = timestamp

            self.trades.append({
                "timestamp": timestamp,
                "action": "BUY",
                "price": price,
                "quantity": quantity,
                "layer": 1,
                "signal": "MA_CROSSOVER_BUY",
                "reason": f"MA{self.short_ma_period} crossed above MA{self.long_ma_period} at {price:.2f}"
            })

    def _exit_position(self, timestamp, price, engine):
        """Exit entire position."""
        if self.position_size > 0:
            # For non-Martingale strategies, use layer_id=1 as default
            engine.sell(timestamp=timestamp, price=price, quantity=self.position_size, layer_id=1)

            pnl = (price - self.entry_price) * self.position_size
            holding_days = (timestamp - self.entry_date).days

            self.in_position = False
            old_position_size = self.position_size
            self.position_size = 0.0

            self.trades.append({
                "timestamp": timestamp,
                "action": "SELL",
                "price": price,
                "quantity": old_position_size,
                "layer": 1,
                "pnl": pnl,
                "signal": "MA_CROSSOVER_SELL",
                "reason": f"MA{self.short_ma_period} crossed below MA{self.long_ma_period} at {price:.2f} after {holding_days} days"
            })

    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get strategy signals for analysis.

        Args:
            data: Historical price data

        Returns:
            Dictionary with analysis results
        """
        signals = {
            "strategy_name": f"MA Cross ({self.short_ma_period}/{self.long_ma_period})",
            "signals": [],
            "ma_history": self.ma_history,
            "current_ma_short": 0.0,
            "current_ma_long": 0.0,
            "in_position": self.in_position,
            "position_size": self.position_size,
            "entry_price": self.entry_price
        }

        if len(self.ma_history) > 0:
            signals["current_ma_short"] = self.ma_history[-1]["short_ma"]
            signals["current_ma_long"] = self.ma_history[-1]["long_ma"]

            # Current signal
            ma_diff = signals["current_ma_short"] - signals["current_ma_long"]
            if not self.in_position and ma_diff > 0:
                signals["current_signal"] = "BUY"
            elif self.in_position and ma_diff < 0:
                signals["current_signal"] = "SELL"
            else:
                signals["current_signal"] = "HOLD"

        return signals

    def reset(self) -> None:
        """Reset strategy state for new backtest."""
        super().reset()
        self.in_position = False
        self.position_size = 0.0
        self.entry_price = 0.0
        self.entry_date = None
        self.ma_history = []