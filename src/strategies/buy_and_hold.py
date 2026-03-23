"""Buy & Hold Strategy - compra todo capital no primeiro dia e mantém até o fim."""

import pandas as pd
from typing import Dict, Any, Optional
from .base import BaseStrategy


class BuyAndHoldStrategy(BaseStrategy):
    """Buy & Hold strategy implementation.

    Buys the maximum possible position on the first day and holds until the end.
    No sells, no rebalancing, just pure buy and hold.
    """

    def __init__(self, initial_capital: float = 30000.0):
        """Initialize Buy & Hold strategy.

        Args:
            initial_capital: Starting capital amount
        """
        super().__init__("Buy & Hold", initial_capital)
        self.position_opened = False
        self.position_size = 0.0
        self.entry_price = 0.0

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process each bar for buy & hold logic.

        Args:
            row: Current OHLCV data row
            engine: Backtest engine instance
        """
        current_date = row.name

        if not self.position_opened:
            # Buy maximum possible position on first day
            entry_price = float(row["Close"])
            cash_available = engine.state.cash

            # Calculate position size (use all available cash)
            self.position_size = cash_available / entry_price
            self.entry_price = entry_price

            # Execute buy order
            if self.position_size > 0:
                engine.buy(
                    timestamp=current_date,
                    price=entry_price,
                    quantity=self.position_size,
                    layer_id=1  # Single layer for buy & hold
                )
                self.position_opened = True

                self.trades.append({
                    "timestamp": current_date,
                    "action": "BUY",
                    "price": entry_price,
                    "quantity": self.position_size,
                    "layer": 1,
                    "signal": "BUY_AND_HOLD_INITIAL",
                    "reason": f"Buy & Hold - Initial position of {self.position_size:.6f} BTC at {entry_price:.2f}"
                })

    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get strategy signals for analysis.

        Args:
            data: Historical price data

        Returns:
            Dictionary with analysis results
        """
        signals = {
            "strategy_name": "Buy & Hold",
            "signals": [],
            "position_opened": self.position_opened,
            "entry_price": self.entry_price,
            "position_size": self.position_size,
            "total_return": 0.0
        }

        if self.position_opened and len(data) > 0:
            current_price = data.iloc[-1]["Close"]
            total_return = (current_price - self.entry_price) / self.entry_price
            signals["total_return"] = total_return

        return signals

    def reset(self) -> None:
        """Reset strategy state for new backtest."""
        super().reset()
        self.position_opened = False
        self.position_size = 0.0
        self.entry_price = 0.0