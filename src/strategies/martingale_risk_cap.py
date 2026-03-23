"""Risk-Cap Martingale Strategy - Martingale with risk management and position limits."""

import pandas as pd
from typing import Optional
from ..engine import Trade
from .base import MartingaleStrategy


class MartingaleRiskCapStrategy(MartingaleStrategy):
    """Risk-cap Martingale strategy with position size limits and risk management.

    Implements classic Martingale with enhanced risk controls:
    - Maximum total position size as % of portfolio
    - Drawdown-based position sizing
    - Stop-loss for total position
    - Capital preservation during severe downturns
    """

    def __init__(
        self,
        base_bet: float = 500.0,
        multiplier: float = 2.0,
        drop_step: float = 0.10,
        take_profit: float = 0.15,
        max_layers: int = 10,
        max_position_pct: float = 0.8,  # Max 80% of portfolio in position
        max_total_exposure: float = 10000.0,  # Maximum total exposure in USD
        stop_loss_pct: float = 0.30,  # Stop loss at 30% total loss
        drawdown_threshold: float = 0.25,  # Reduce position size after 25% drawdown
        position_size_reduction: float = 0.5,  # Reduce position size by 50% when threshold hit
        emergency_stop: bool = True,  # Enable emergency stop on severe losses
        **kwargs
    ):
        """Initialize Risk-cap Martingale strategy.

        Args:
            base_bet: Initial bet amount
            multiplier: Position size multiplier for each layer
            drop_step: Price drop percentage to trigger new layer
            take_profit: Profit target percentage for layer exits
            max_layers: Maximum number of concurrent layers
            max_position_pct: Maximum position size as % of total portfolio value
            max_total_exposure: Maximum total exposure in USD
            stop_loss_pct: Stop loss percentage for total position
            drawdown_threshold: Drawdown threshold for position size reduction
            position_size_reduction: Percentage to reduce position size when threshold hit
            emergency_stop: Enable emergency stop on severe losses
            **kwargs: Additional parameters
        """
        super().__init__("Risk Cap Martingale", base_bet, multiplier, drop_step, take_profit, max_layers, **kwargs)
        self.max_position_pct = max_position_pct
        self.max_total_exposure = max_total_exposure
        self.stop_loss_pct = stop_loss_pct
        self.drawdown_threshold = drawdown_threshold
        self.position_size_reduction = position_size_reduction
        self.emergency_stop = emergency_stop

        # Track risk metrics
        self.peak_portfolio_value = 0.0
        self.total_exposure = 0.0
        self.position_size_reduced = False
        self.emergency_stopped = False
        self.risk_metrics_history = []
        self.last_buy_price: Optional[float] = None

    def calculate_total_exposure(self, engine, current_price: float) -> float:
        """Calculate current total exposure in USD.

        Args:
            engine: Backtest engine instance
            current_price: Current asset price

        Returns:
            Total exposure in USD
        """
        btc_held = sum(layer.quantity for layer in engine.state.layers)
        return btc_held * current_price

    def calculate_drawdown(self, current_portfolio_value: float) -> float:
        """Calculate current drawdown from peak.

        Args:
            current_portfolio_value: Current total portfolio value

        Returns:
            Drawdown as percentage (0.0 to 1.0)
        """
        if self.peak_portfolio_value == 0:
            self.peak_portfolio_value = current_portfolio_value
            return 0.0

        if current_portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_portfolio_value
            return 0.0

        return (self.peak_portfolio_value - current_portfolio_value) / self.peak_portfolio_value

    def should_reduce_position_size(self) -> bool:
        """Check if position size should be reduced due to drawdown.

        Returns:
            True if position size should be reduced
        """
        return not self.position_size_reduced  # Only reduce once

    def should_emergency_stop(self, engine, current_price: float) -> bool:
        """Check if emergency stop should be triggered.

        Args:
            engine: Backtest engine instance
            current_price: Current asset price

        Returns:
            True if emergency stop should be triggered
        """
        if not self.emergency_stop or self.emergency_stopped:
            return False

        # Calculate total loss
        current_portfolio_value = engine.state.cash + (sum(layer.quantity for layer in engine.state.layers) * current_price)
        total_invested = sum(layer.quantity * layer.entry_price for layer in engine.state.layers)
        current_value = sum(layer.quantity for layer in engine.state.layers) * current_price
        total_loss = (total_invested - current_value) / total_invested if total_invested > 0 else 0

        return total_loss >= self.stop_loss_pct

    def can_add_layer(self, engine) -> bool:
        """Check if new layer can be added with risk constraints.

        Args:
            engine: Backtest engine instance

        Returns:
            True if new layer can be added
        """
        # Check basic layer limit
        if len(engine.state.layers) >= self.max_layers:
            return False

        # Check emergency stop
        if self.emergency_stopped:
            return False

        return True

    def calculate_risk_adjusted_bet_size(self, base_bet_amount: float, engine, current_price: float) -> float:
        """Calculate risk-adjusted bet size.

        Args:
            base_bet_amount: Base bet amount before adjustments
            engine: Backtest engine instance
            current_price: Current asset price

        Returns:
            Risk-adjusted bet amount
        """
        adjusted_bet = base_bet_amount

        # Check position size limits
        current_portfolio_value = engine.state.cash + (sum(layer.quantity for layer in engine.state.layers) * current_price)
        max_position_value = current_portfolio_value * self.max_position_pct
        current_total_exposure = self.calculate_total_exposure(engine, current_price)

        if current_total_exposure >= max_position_value:
            return 0.0  # Can't add more position

        # Reduce bet size if approaching max position
        remaining_capacity = max_position_value - current_total_exposure
        if adjusted_bet > remaining_capacity:
            adjusted_bet = remaining_capacity

        # Check max total exposure limit
        if current_total_exposure + adjusted_bet > self.max_total_exposure:
            adjusted_bet = max(0, self.max_total_exposure - current_total_exposure)

        # Apply drawdown-based reduction
        current_portfolio_value = engine.state.cash + (sum(layer.quantity for layer in engine.state.layers) * current_price)
        drawdown = self.calculate_drawdown(current_portfolio_value)

        if drawdown >= self.drawdown_threshold and self.should_reduce_position_size():
            adjusted_bet *= self.position_size_reduction
            self.position_size_reduced = True

        return max(0, adjusted_bet)

    def on_bar(self, row: pd.Series, engine) -> None:
        """Process current bar and generate trading signals with risk management.

        Args:
            row: Current OHLCV bar
            engine: Backtest engine instance
        """
        close_price = float(row["Close"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        timestamp = row.name

        # Track portfolio metrics
        current_portfolio_value = engine.state.cash + (sum(layer.quantity for layer in engine.state.layers) * close_price)
        self.total_exposure = self.calculate_total_exposure(engine, close_price)
        drawdown = self.calculate_drawdown(current_portfolio_value)

        # Store risk metrics for analysis
        self.risk_metrics_history.append({
            "timestamp": timestamp,
            "portfolio_value": current_portfolio_value,
            "total_exposure": self.total_exposure,
            "exposure_pct": self.total_exposure / current_portfolio_value if current_portfolio_value > 0 else 0,
            "drawdown": drawdown,
            "peak_value": self.peak_portfolio_value,
            "emergency_stopped": self.emergency_stopped,
            "position_size_reduced": self.position_size_reduced
        })

        # Check for emergency stop
        if self.should_emergency_stop(engine, close_price):
            self._execute_emergency_stop(timestamp, close_price, engine)
            return

        # Initial buy if no positions
        if not engine.state.layers:
            self._execute_initial_buy(timestamp, close_price, engine)
            return

        # Update reference to last layer
        last_layer = engine.state.layers[-1] if engine.state.layers else None
        if last_layer is None:
            return

        # Check for layer addition (buy signal) with risk-adjusted sizing
        if self.can_add_layer(engine):
            target_buy_price = self.get_next_buy_price(last_layer.entry_price)
            if low_price <= target_buy_price:
                self._execute_layer_buy(timestamp, close_price, engine)

        # Check for layer exit (sell signal)
        target_sell_price = self.get_target_sell_price(last_layer.entry_price)
        if high_price >= target_sell_price:
            self._execute_layer_sell(timestamp, close_price, last_layer, engine)

    def _execute_initial_buy(self, timestamp, price: float, engine) -> None:
        """Execute initial position entry with risk adjustments.

        Args:
            timestamp: Trade timestamp
            price: Execution price
            engine: Backtest engine instance
        """
        exec_price = price * (1 + self.slippage)
        risk_adjusted_bet = self.calculate_risk_adjusted_bet_size(self.base_bet, engine, exec_price)

        if risk_adjusted_bet > 0 and engine.state.cash >= risk_adjusted_bet:
            quantity = self.calculate_position_size(risk_adjusted_bet, exec_price)
            if engine.buy(timestamp, exec_price, quantity):
                self.last_buy_price = exec_price

    def _execute_layer_buy(self, timestamp, price: float, engine) -> None:
        """Execute additional layer buy with risk-adjusted sizing.

        Args:
            timestamp: Trade timestamp
            price: Target buy price
            engine: Backtest engine instance
        """
        current_layers = len(engine.state.layers)
        base_bet_amount = self.calculate_next_bet_size(current_layers)
        exec_price = price * (1 + self.slippage)
        risk_adjusted_bet = self.calculate_risk_adjusted_bet_size(base_bet_amount, engine, exec_price)

        if risk_adjusted_bet > 0 and engine.state.cash >= risk_adjusted_bet:
            quantity = self.calculate_position_size(risk_adjusted_bet, exec_price)
            if engine.buy(timestamp, exec_price, quantity):
                self.last_buy_price = exec_price

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

            # Reset position size reduction if all layers closed
            if len(engine.state.layers) == 0:
                self.position_size_reduced = False

    def _execute_emergency_stop(self, timestamp, price: float, engine) -> None:
        """Execute emergency stop - close all positions.

        Args:
            timestamp: Trade timestamp
            price: Current price
            engine: Backtest engine instance
        """
        self.emergency_stopped = True

        # Close all layers
        exec_price = price * (1 - self.slippage)
        for layer in engine.state.layers[:]:  # Copy list to avoid modification during iteration
            engine.sell(timestamp, exec_price, layer.quantity, layer.layer_id)

        # Add emergency stop record to trades
        emergency_trade = Trade(
            timestamp=timestamp,
            action="EMERGENCY_STOP",
            price=price,
            quantity=0.0,
            cost=0.0,
            pnl=0.0,
            layer=None
        )
        engine.state.trades.append(emergency_trade)

    def get_signals(self, data: pd.DataFrame) -> dict:
        """Get strategy signals for analysis.

        Args:
            data: Historical price data

        Returns:
            Dictionary with analysis results
        """
        signals = {
            "strategy_name": "Risk Cap Martingale",
            "risk_metrics_history": self.risk_metrics_history,
            "current_exposure": self.total_exposure,
            "emergency_stopped": self.emergency_stopped,
            "position_size_reduced": self.position_size_reduced,
            "peak_portfolio_value": self.peak_portfolio_value,
            "signals": []
        }

        if len(self.risk_metrics_history) > 0:
            latest = self.risk_metrics_history[-1]
            signals["current_drawdown"] = latest["drawdown"]
            signals["exposure_pct"] = latest["exposure_pct"]

        return signals

    def reset(self) -> None:
        """Reset strategy state for new backtest."""
        self.peak_portfolio_value = 0.0
        self.total_exposure = 0.0
        self.position_size_reduced = False
        self.emergency_stopped = False
        self.risk_metrics_history = []
        self.last_buy_price = None
