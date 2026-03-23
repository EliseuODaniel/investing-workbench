"""Mean Reversion Strategy - Trade based on price returning to mean/bands."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy implementation.

    Buys when price drops below moving mean/bands by threshold.
    Sells when price returns to mean or above mean by profit target.
    Can use simple moving average or Bollinger Bands.
    """

    def __init__(
        self,
        initial_capital: float = 30000.0,
        ma_period: int = 20,  # Moving average period
        use_bollinger: bool = False,  # Use Bollinger Bands instead of simple MA
        bb_std_dev: float = 2.0,  # Standard deviations for Bollinger Bands
        entry_threshold: float = 0.05,  # Entry threshold (5% below mean)
        profit_target: float = 0.03,  # Profit target (3% above mean)
        position_size_pct: float = 0.3,  # Use 30% of available cash
        min_cash_reserve: float = 1000.0,
        max_positions: int = 3,  # Max concurrent reversion positions
        slippage: float = 0.0005
    ):
        """Initialize Mean Reversion strategy.

        Args:
            initial_capital: Initial capital
            ma_period: Moving average period
            use_bollinger: Use Bollinger Bands instead of simple MA
            bb_std_dev: Standard deviations for Bollinger Bands
            entry_threshold: Entry threshold as percentage below mean/bands
            profit_target: Profit target as percentage above mean
            position_size_pct: Percentage of cash to use per position
            min_cash_reserve: Minimum cash to keep in reserve
            max_positions: Maximum concurrent positions
        """
        super().__init__(f"Mean Reversion ({ma_period}d {'BB' if use_bollinger else 'MA'})", initial_capital)
        self.ma_period = ma_period
        self.use_bollinger = use_bollinger
        self.bb_std_dev = bb_std_dev
        self.entry_threshold = entry_threshold
        self.profit_target = profit_target
        self.position_size_pct = position_size_pct
        self.min_cash_reserve = min_cash_reserve
        self.max_positions = max_positions
        self.slippage = slippage

        # Track state
        self.price_history = []
        self.positions = []  # Track multiple reversion positions
        self.trade_count = 0
        self.indicators_history = []

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process each bar for mean reversion logic.

        Args:
            row: Current OHLCV data row
            engine: Backtest engine instance
        """
        current_date = row.name
        current_price = float(row["Close"])

        # Store price data
        self.price_history.append(current_price)

        # Need enough data for MA calculation
        if len(self.price_history) < self.ma_period:
            return

        # Calculate indicators
        prices = pd.Series(self.price_history)
        sma = prices.tail(self.ma_period).mean()
        std_dev = prices.tail(self.ma_period).std()

        if self.use_bollinger:
            upper_band = sma + (self.bb_std_dev * std_dev)
            lower_band = sma - (self.bb_std_dev * std_dev)
            mean_level = lower_band  # Entry when below lower band
            exit_level = sma  # Exit when returning to mean
        else:
            upper_band = sma * (1 + self.profit_target)  # Simple profit target
            lower_band = sma * (1 - self.entry_threshold)  # Entry threshold
            mean_level = sma
            exit_level = upper_band

        # Store indicators for analysis
        self.indicators_history.append({
            "timestamp": current_date,
            "price": current_price,
            "sma": sma,
            "std_dev": std_dev,
            "upper_band": upper_band,
            "lower_band": lower_band if self.use_bollinger else None
        })

        # Manage existing positions
        self._check_exits(current_date, current_price, exit_level, engine)

        # Check for new entry opportunities
        self._check_entries(current_date, current_price, lower_band, mean_level, engine)

    def _check_entries(self, timestamp, price, entry_level, mean_level, engine):
        """Check for new mean reversion entry opportunities."""
        if len(self.positions) >= self.max_positions:
            return

        # Check if we have enough cash
        available_cash = max(engine.state.cash - self.min_cash_reserve, 0)
        if available_cash <= 0:
            return

        # Check if price is sufficiently below entry level
        if price < entry_level:
            # Calculate how far below entry (stronger signal = bigger position)
            deviation_pct = (entry_level - price) / entry_level
            position_boost = min(1.5, 1 + deviation_pct)  # Boost position size for strong deviations

            cash_to_use = available_cash * self.position_size_pct * position_boost
            exec_price = price * (1 + self.slippage)
            quantity = cash_to_use / exec_price

            if quantity > 0:
                # Execute buy
                engine.buy(timestamp=timestamp, price=exec_price, quantity=quantity, layer_id=len(self.positions) + 1)

                # Set profit target
                if self.use_bollinger:
                    profit_target_price = mean_level  # Exit at mean
                else:
                    profit_target_price = mean_level * (1 + self.profit_target)

                # Track position
                position = {
                    "entry_price": exec_price,
                    "quantity": quantity,
                    "entry_date": timestamp,
                    "profit_target": profit_target_price,
                    "entry_level": entry_level,
                    "mean_level": mean_level,
                    "layer": len(self.positions) + 1
                }
                self.positions.append(position)
                self.trade_count += 1

                strategy_type = "Bollinger Bands" if self.use_bollinger else "Simple MA"
                self.trades.append({
                    "timestamp": timestamp,
                    "action": "BUY",
                    "price": exec_price,
                    "quantity": quantity,
                    "layer": position["layer"],
                    "signal": "MEAN_REVERSION_BUY",
                    "reason": f"{strategy_type} - Price {price:.2f} below entry {entry_level:.2f} (deviation: {deviation_pct:.2%}), Target: {profit_target_price:.2f}"
                })

    def _check_exits(self, timestamp, price, exit_level, engine):
        """Check for mean reversion exits."""
        positions_to_remove = []

        for i, position in enumerate(self.positions):
            # Exit when price reaches mean or profit target
            if price >= exit_level:
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

                # Calculate return to mean
                return_to_mean_pct = (price - position["entry_level"]) / position["entry_level"]

                self.trades.append({
                    "timestamp": timestamp,
                    "action": "SELL",
                    "price": price,
                    "quantity": position["quantity"],
                    "layer": position["layer"],
                    "pnl": pnl,
                    "signal": "MEAN_REVERSION_SELL",
                    "reason": f"Mean reversion exit: {price:.2f} (target: {position['profit_target']:.2f}), P&L: {pnl:.2f} after {holding_days} days, Return to mean: {return_to_mean_pct:.2%}"
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
            "strategy_name": f"Mean Reversion ({self.ma_period}d {'BB' if self.use_bollinger else 'MA'})",
            "signals": [],
            "active_positions": len(self.positions),
            "total_trades": self.trade_count,
            "current_sma": 0.0,
            "current_upper_band": 0.0,
            "current_lower_band": 0.0,
            "price_history_length": len(self.price_history)
        }

        if len(self.indicators_history) > 0:
            latest = self.indicators_history[-1]
            signals["current_sma"] = latest["sma"]
            signals["current_upper_band"] = latest["upper_band"]
            signals["current_lower_band"] = latest.get("lower_band")

        return signals

    def reset(self) -> None:
        """Reset strategy state for new backtest."""
        super().reset()
        self.price_history = []
        self.positions = []
        self.trade_count = 0
        self.indicators_history = []
