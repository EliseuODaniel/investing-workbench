"""Base strategy interface for trading strategies."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd

from ..engine import State


class Strategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, name: str, **kwargs):
        """Initialize strategy with configuration.

        Args:
            name: Strategy name for identification
            **kwargs: Strategy-specific parameters
        """
        self.name = name
        self.config = kwargs

    @abstractmethod
    def on_bar(self, row: pd.Series, engine) -> None:
        """Process a single bar/candle.

        Args:
            row: OHLCV data for current bar
            engine: Backtest engine instance
        """
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get strategy-specific metrics.

        Returns:
            Dictionary with strategy metrics
        """
        return {"name": self.name, "config": self.config}


class BaseStrategy(Strategy):
    """Base class for non-Martingale trading strategies with common state management."""

    def __init__(self, name: str, initial_capital: float = 30000.0, **kwargs):
        """Initialize base strategy with common state.

        Args:
            name: Strategy name for identification
            initial_capital: Starting capital amount
            **kwargs: Strategy-specific parameters
        """
        super().__init__(name, **kwargs)
        self.initial_capital = initial_capital

        # Common state for all strategies
        self.trades: List[Dict[str, Any]] = []
        self.price_history: List[float] = []
        self.equity_history: List[Dict[str, Any]] = []
        self.cash_history: List[Dict[str, Any]] = []
        self.position_history: List[Dict[str, Any]] = []

    def add_trade(self, timestamp, action: str, price: float, quantity: float,
                  layer: int = 1, signal: str = "", reason: str = "", pnl: float = 0.0):
        """Add a trade record.

        Args:
            timestamp: Trade timestamp
            action: 'BUY' or 'SELL'
            price: Trade price
            quantity: Trade quantity
            layer: Layer number
            signal: Signal that triggered the trade
            reason: Reason for the trade
            pnl: Profit/loss for the trade
        """
        trade = {
            "timestamp": timestamp,
            "action": action,
            "price": price,
            "quantity": quantity,
            "layer": layer,
            "signal": signal,
            "reason": reason,
            "pnl": pnl
        }
        self.trades.append(trade)

    def record_equity_state(self, timestamp, equity: float, cash: float, btc: float):
        """Record current equity state.

        Args:
            timestamp: Current timestamp
            equity: Total portfolio value
            cash: Available cash
            btc: Bitcoin holdings
        """
        self.equity_history.append({
            "timestamp": timestamp,
            "equity": equity,
            "cash": cash,
            "btc": btc
        })

    def reset(self):
        """Reset strategy state for new backtest."""
        self.trades = []
        self.price_history = []
        self.equity_history = []
        self.cash_history = []
        self.position_history = []

    def get_metrics(self) -> Dict[str, Any]:
        """Get strategy-specific metrics."""
        return {
            "name": self.name,
            "config": self.config,
            "total_trades": len(self.trades),
            "strategy": self.get_signals()
        }

    def get_signals(self, data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Get strategy signals for analysis.

        Args:
            data: Historical price data (optional)

        Returns:
            Dictionary with analysis results
        """
        return {
            "strategy_name": self.name,
            "signals": [],
            "total_trades": len(self.trades),
            "trades": self.trades,
            "price_history_length": len(self.price_history)
        }


class MartingaleStrategy(Strategy):
    """Base class for Martingale-type strategies."""

    def __init__(
        self,
        name: str = "Martingale",
        base_bet: float = 500.0,
        multiplier: float = 2.0,
        drop_step: float = 0.10,
        take_profit: float = 0.15,
        max_layers: int = 10,
        slippage: float = 0.0005,
        **kwargs
    ):
        """Initialize Martingale strategy.

        Args:
            name: Strategy name
            base_bet: Initial bet amount
            multiplier: Position size multiplier for each layer
            drop_step: Price drop percentage to trigger new layer
            take_profit: Profit target percentage for layer exits
            max_layers: Maximum number of concurrent layers
            slippage: Execution slippage applied to price (as fraction, e.g., 0.0005 = 5 bps)
            **kwargs: Additional parameters
        """
        super().__init__(name, **kwargs)
        self.base_bet = base_bet
        self.multiplier = multiplier
        self.drop_step = drop_step
        self.take_profit = take_profit
        self.max_layers = max_layers
        self.slippage = slippage

    def calculate_next_bet_size(self, current_layers: int) -> float:
        """Calculate bet size for next layer.

        Args:
            current_layers: Number of currently open layers

        Returns:
            Bet amount for next layer
        """
        return self.base_bet * (self.multiplier ** current_layers)

    def get_next_buy_price(self, last_layer_price: float) -> float:
        """Calculate price target for next layer buy.

        Args:
            last_layer_price: Entry price of last layer

        Returns:
            Target buy price for next layer
        """
        return last_layer_price * (1 - self.drop_step)

    def get_target_sell_price(self, layer_entry_price: float) -> float:
        """Calculate target sell price for a layer.

        Args:
            layer_entry_price: Entry price of the layer

        Returns:
            Target sell price (take profit)
        """
        return layer_entry_price * (1 + self.take_profit)

    def can_add_layer(self, engine) -> bool:
        """Check if new layer can be added.

        Args:
            engine: Backtest engine instance

        Returns:
            True if new layer can be added
        """
        return len(engine.state.layers) < self.max_layers

    def calculate_position_size(self, bet_amount: float, price: float) -> float:
        """Calculate position size in base asset.

        Args:
            bet_amount: Amount to invest in quote currency
            price: Asset price

        Returns:
            Quantity of base asset to buy
        """
        return bet_amount / price
