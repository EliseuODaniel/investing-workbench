"""Simple DCA Strategy - Dollar Cost Averaging with periodic fixed purchases."""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseStrategy


class SimpleDCAStrategy(BaseStrategy):
    """Simple DCA strategy implementation.

    Makes periodic fixed-amount purchases (weekly/monthly) regardless of price.
    No sells, just consistent accumulation.
    """

    def __init__(
        self,
        initial_capital: float = 30000.0,
        dca_amount: float = 500.0,
        dca_frequency: str = "weekly",  # "weekly", "monthly", "daily"
        start_immediately: bool = True
    ):
        """Initialize Simple DCA strategy.

        Args:
            initial_capital: Starting capital amount
            dca_amount: Fixed amount to invest each period
            dca_frequency: Frequency of investments ("daily", "weekly", "monthly")
            start_immediately: Whether to invest immediately or wait for first period
        """
        super().__init__(f"Simple DCA ({dca_frequency})", initial_capital)
        self.dca_amount = dca_amount
        self.dca_frequency = dca_frequency
        self.start_immediately = start_immediately

        # Track purchase schedule
        self.last_purchase_date = None
        self.purchase_count = 0
        self.total_invested = 0.0
        self.total_btc = 0.0

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process each bar for DCA logic.

        Args:
            row: Current OHLCV data row
            engine: Backtest engine instance
        """
        current_date = row.name
        current_price = float(row["Close"])

        # Check if it's time for next purchase
        if self._should_purchase(current_date, engine):
            # Calculate how much we can buy with available cash
            available_cash = min(self.dca_amount, engine.state.cash)

            if available_cash > 0:
                quantity = available_cash / current_price

                # Execute buy order
                engine.buy(
                    timestamp=current_date,
                    price=current_price,
                    quantity=quantity,
                    layer_id=self.purchase_count + 1
                )

                # Track purchase
                self.last_purchase_date = current_date
                self.purchase_count += 1
                self.total_invested += available_cash
                self.total_btc += quantity

                self.trades.append({
                    "timestamp": current_date,
                    "action": "BUY",
                    "price": current_price,
                    "quantity": quantity,
                    "layer": self.purchase_count,
                    "signal": "DCA_PURCHASE",
                    "reason": f"DCA {self.dca_frequency} purchase #{self.purchase_count}: {available_cash:.2f} at {current_price:.2f} = {quantity:.6f} BTC"
                })

    def _should_purchase(self, current_date, engine) -> bool:
        """Check if we should make a purchase on this date."""
        if engine.state.cash < self.dca_amount:
            return False

        # If starting immediately and no purchases yet, buy on first day
        if self.start_immediately and self.last_purchase_date is None:
            return True

        # For subsequent purchases, check frequency
        if self.last_purchase_date is None:
            return False

        days_since_last = (current_date - self.last_purchase_date).days

        if self.dca_frequency == "daily":
            return days_since_last >= 1
        elif self.dca_frequency == "weekly":
            return days_since_last >= 7
        elif self.dca_frequency == "monthly":
            return days_since_last >= 30  # Approximate month
        else:
            return False

    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get strategy signals for analysis.

        Args:
            data: Historical price data

        Returns:
            Dictionary with analysis results
        """
        signals = {
            "strategy_name": f"Simple DCA ({self.dca_frequency})",
            "signals": [],
            "purchase_count": self.purchase_count,
            "total_invested": self.total_invested,
            "total_btc": self.total_btc,
            "avg_purchase_price": 0.0,
            "current_value": 0.0
        }

        if self.total_btc > 0 and len(data) > 0:
            signals["avg_purchase_price"] = self.total_invested / self.total_btc
            current_price = data.iloc[-1]["Close"]
            signals["current_value"] = self.total_btc * current_price
            signals["unrealized_pnl"] = signals["current_value"] - self.total_invested
            signals["unrealized_pnl_pct"] = signals["unrealized_pnl"] / self.total_invested

        return signals

    def reset(self) -> None:
        """Reset strategy state for new backtest."""
        super().reset()
        self.last_purchase_date = None
        self.purchase_count = 0
        self.total_invested = 0.0
        self.total_btc = 0.0