"""ATR-based Martingale Strategy - Dynamic step sizing based on volatility."""

import pandas as pd
import numpy as np
from typing import Optional
from .base import MartingaleStrategy


class MartingaleATRStrategy(MartingaleStrategy):
    """ATR-based Martingale strategy with dynamic drop steps.

    Uses Average True Range (ATR) to adjust drop steps based on market volatility:
    - Larger drop steps during high volatility periods
    - Smaller drop steps during low volatility periods
    - Prevents over-trading in choppy markets
    - More responsive to market conditions
    """

    def __init__(
        self,
        base_bet: float = 500.0,
        multiplier: float = 2.0,
        drop_step: float = 0.10,  # Base drop step (will be adjusted by ATR)
        take_profit: float = 0.15,
        max_layers: int = 10,
        atr_period: int = 14,  # ATR calculation period
        atr_multiplier: float = 2.0,  # Multiplier for ATR-based drops
        min_drop_step: float = 0.05,  # Minimum drop step (5%)
        max_drop_step: float = 0.25,  # Maximum drop step (25%)
        **kwargs
    ):
        """Initialize ATR-based Martingale strategy.

        Args:
            base_bet: Initial bet amount
            multiplier: Position size multiplier for each layer
            drop_step: Base drop step percentage (will be dynamically adjusted)
            take_profit: Profit target percentage for layer exits
            max_layers: Maximum number of concurrent layers
            atr_period: Period for ATR calculation
            atr_multiplier: Multiplier for ATR-based drop adjustments
            min_drop_step: Minimum allowed drop step
            max_drop_step: Maximum allowed drop step
            **kwargs: Additional parameters
        """
        super().__init__("ATR Martingale", base_bet, multiplier, drop_step, take_profit, max_layers, **kwargs)
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.min_drop_step = min_drop_step
        self.max_drop_step = max_drop_step

        # Track ATR history for analysis
        self.atr_history = []
        self.current_atr = 0.0
        self.last_buy_price: Optional[float] = None

    def calculate_atr(self, high_prices: pd.Series, low_prices: pd.Series, close_prices: pd.Series) -> float:
        """Calculate Average True Range.

        Args:
            high_prices: Series of high prices
            low_prices: Series of low prices
            close_prices: Series of close prices

        Returns:
            Current ATR value
        """
        if len(high_prices) < self.atr_period + 1:
            return 0.0

        # Calculate True Range
        tr1 = high_prices - low_prices
        tr2 = abs(high_prices - close_prices.shift(1))
        tr3 = abs(low_prices - close_prices.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR using exponential moving average
        atr = true_range.ewm(span=self.atr_period, adjust=False).mean()

        return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0

    def get_dynamic_drop_step(self, current_price: float) -> float:
        """Calculate dynamic drop step based on ATR.

        Args:
            current_price: Current asset price

        Returns:
            Adjusted drop step percentage
        """
        if self.current_atr == 0.0:
            return self.drop_step  # Fall back to base drop step

        # Calculate ATR as percentage of price
        atr_pct = (self.current_atr / current_price) * 100

        # Adjust drop step based on ATR
        # Higher volatility (higher ATR) = larger drop steps
        # Lower volatility (lower ATR) = smaller drop steps
        adjusted_step = atr_pct * self.atr_multiplier / 100

        # Clamp to min/max bounds
        adjusted_step = max(self.min_drop_step, min(self.max_drop_step, adjusted_step))

        return adjusted_step

    def get_next_buy_price(self, last_layer_price: float, current_price: float = 0.0) -> float:
        """Calculate price target for next layer buy using dynamic ATR-based steps.

        Args:
            last_layer_price: Entry price of last layer
            current_price: Current market price (for ATR calculation)

        Returns:
            Target buy price for next layer
        """
        if current_price == 0.0:
            current_price = last_layer_price

        dynamic_drop = self.get_dynamic_drop_step(current_price)
        return last_layer_price * (1 - dynamic_drop)

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process current bar and generate trading signals with ATR-based adjustments.

        Args:
            row: Current OHLCV bar
            engine: Backtest engine instance
        """
        close_price = float(row["Close"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        timestamp = row.name

        # Store price history for ATR calculation
        if not hasattr(self, 'price_history'):
            self.price_history = []
        if not hasattr(self, 'high_history'):
            self.high_history = []
        if not hasattr(self, 'low_history'):
            self.low_history = []

        self.price_history.append(close_price)
        self.high_history.append(high_price)
        self.low_history.append(low_price)

        # Calculate current ATR
        if len(self.price_history) >= self.atr_period + 1:
            prices_series = pd.Series(self.price_history)
            highs_series = pd.Series(self.high_history)
            lows_series = pd.Series(self.low_history)

            self.current_atr = self.calculate_atr(highs_series, lows_series, prices_series)

            # Store ATR for analysis
            self.atr_history.append({
                "timestamp": timestamp,
                "atr": self.current_atr,
                "atr_pct": (self.current_atr / close_price) * 100 if close_price > 0 else 0,
                "price": close_price
            })

        # Initial buy if no positions
        if not engine.state.layers:
            self._execute_initial_buy(timestamp, close_price, engine)
            return

        # Update reference to last layer
        last_layer = engine.state.layers[-1] if engine.state.layers else None
        if last_layer is None:
            return

        # Check for layer addition (buy signal) with dynamic ATR-based pricing
        if self.can_add_layer(engine):
            target_buy_price = self.get_next_buy_price(last_layer.entry_price, close_price)
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
        """Execute additional layer buy with ATR-based sizing.

        Args:
            timestamp: Trade timestamp
            price: Target buy price
            engine: Backtest engine instance
        """
        current_layers = len(engine.state.layers)
        bet_amount = self.calculate_next_bet_size(current_layers)

        # Optional: Reduce bet size during high volatility periods
        if self.current_atr > 0:
            atr_pct = (self.current_atr / price) * 100
            volatility_factor = max(0.5, 1.0 - (atr_pct / 20))  # Reduce size in high volatility
            bet_amount *= volatility_factor

        exec_price = price * (1 + self.slippage)
        if engine.state.cash >= bet_amount:
            quantity = self.calculate_position_size(bet_amount, exec_price)
            if engine.buy(timestamp, exec_price, quantity):
                self.last_buy_price = price

    def _execute_layer_sell(self, timestamp, price: float, layer, engine) -> None:
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

    def get_signals(self, data: pd.DataFrame) -> dict:
        """Get strategy signals for analysis.

        Args:
            data: Historical price data

        Returns:
            Dictionary with analysis results
        """
        signals = {
            "strategy_name": f"ATR Martingale ({self.atr_period}d)",
            "atr_history": self.atr_history,
            "current_atr": self.current_atr,
            "current_drop_step": self.get_dynamic_drop_step(data.iloc[-1]["Close"]) if len(data) > 0 else self.drop_step,
            "signals": []
        }

        if len(self.atr_history) > 0:
            latest_atr = self.atr_history[-1]
            signals["current_atr_pct"] = latest_atr["atr_pct"]
            signals["atr_trend"] = "rising" if len(self.atr_history) >= 2 and latest_atr["atr"] > self.atr_history[-2]["atr"] else "falling"

        return signals

    def reset(self) -> None:
        """Reset strategy state for new backtest."""
        if hasattr(self, 'price_history'):
            self.price_history = []
        if hasattr(self, 'high_history'):
            self.high_history = []
        if hasattr(self, 'low_history'):
            self.low_history = []
        self.atr_history = []
        self.current_atr = 0.0
        self.last_buy_price = None
