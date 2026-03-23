"""Backtest engine for running trading strategies."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import pandas as pd
from .selic import get_or_create_selic_data, get_monthly_rate


@dataclass
class Trade:
    """Record of a single trade."""
    timestamp: pd.Timestamp
    action: str  # BUY or SELL
    price: float
    quantity: float
    cost: float
    pnl: Optional[float] = None
    layer: Optional[int] = None


@dataclass
class Layer:
    """Open position layer."""
    entry_price: float
    quantity: float
    cost: float
    timestamp: pd.Timestamp
    layer_id: int


@dataclass
class State:
    """Current backtest state."""
    cash: float
    layers: List[Layer] = field(default_factory=list)
    equity_history: List[float] = field(default_factory=list)
    cash_history: List[float] = field(default_factory=list)
    timestamp_history: List[pd.Timestamp] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    max_equity: float = field(default_factory=lambda: 0.0)
    total_interest_earned: float = field(default_factory=lambda: 0.0)
    selic_rates_used: Dict[str, float] = field(default_factory=dict)  # Track rates used


class BacktestEngine:
    """Engine for backtesting trading strategies."""

    def __init__(self, initial_cash: float = 30000.0, apply_cash_yield: bool = False,
                 selic_rate_annual: float = 0.13, yield_frequency: str = "monthly",
                 use_real_selic: bool = False, selic_path: str = "data/selic.csv",
                 selic_fallback_rate: float = 0.13):
        self.initial_cash = initial_cash
        self.apply_cash_yield = apply_cash_yield
        self.selic_rate_annual = selic_rate_annual
        self.yield_frequency = yield_frequency
        self.use_real_selic = use_real_selic
        self.selic_path = selic_path
        self.selic_fallback_rate = selic_fallback_rate

        # Initialize state
        self.state = State(cash=initial_cash, max_equity=initial_cash)
        self._last_yield_month = None

        # Load SELIC data if real rates are enabled
        self.selic_data = None
        if self.apply_cash_yield and self.use_real_selic:
            self._load_selic_data()

    def _load_selic_data(self) -> None:
        """Load SELIC data from file or download if needed."""
        try:
            self.selic_data = get_or_create_selic_data(
                path=self.selic_path,
                use_download=True,  # Attempt download
                fallback_rate_annual=self.selic_fallback_rate
            )
            if self.selic_data is not None and not self.selic_data.empty:
                print(f"Loaded {len(self.selic_data)} monthly SELIC rates from {self.selic_path}")
            else:
                print("Failed to load SELIC data, will use fallback rates")
        except Exception as e:
            print(f"Error loading SELIC data: {e}")
            self.selic_data = None

    @property
    def cash(self) -> float:
        """Get current cash balance for compatibility.

        Returns:
            Current cash from state
        """
        return self.state.cash

    @property
    def layers(self) -> List[Layer]:
        """Get current layers for compatibility.

        Returns:
            Current layers from state
        """
        return self.state.layers

    def run(self, data: pd.DataFrame, strategy) -> Dict[str, Any]:
        """Run backtest on data with given strategy.

        Args:
            data: OHLCV DataFrame
            strategy: Strategy instance with on_bar method

        Returns:
            Results dictionary with trades and equity history
        """
        self.state = State(cash=self.initial_cash, max_equity=self.initial_cash)
        self._last_yield_month = None

        for timestamp, row in data.iterrows():
            # Apply cash yield at the beginning of each month (before any operations)
            self._apply_cash_yield(timestamp)

            # Update equity history
            total_btc = sum(layer.quantity for layer in self.state.layers)
            close_price = float(row["Close"])
            current_equity = self.state.cash + (total_btc * close_price)
            self.state.equity_history.append(current_equity)
            self.state.cash_history.append(self.state.cash)
            self.state.timestamp_history.append(timestamp)

            # Update max equity for drawdown calculation
            if current_equity > self.state.max_equity:
                self.state.max_equity = current_equity

            # Process strategy signals
            strategy.on_bar(row, self)

        # Close any remaining positions at the end
        if data.shape[0] > 0:
            last_price = float(data.iloc[-1]["Close"])
            self._close_all_positions(data.index[-1], last_price)

        return self._get_results()

    def _apply_cash_yield(self, timestamp: pd.Timestamp) -> None:
        """Apply cash yield based on SELIC rate if enabled.

        Args:
            timestamp: Current timestamp for yield application
        """
        if not self.apply_cash_yield:
            return

        if self.yield_frequency != "monthly":
            return  # Currently only monthly is supported

        current_month = timestamp.month
        current_year = timestamp.year

        # Check if we've already applied yield for this month
        if self._last_yield_month is not None:
            if current_month == self._last_yield_month[0] and current_year == self._last_yield_month[1]:
                return

        # Get monthly rate
        if self.use_real_selic and self.selic_data is not None:
            # Use real monthly SELIC rate
            monthly_rate = get_monthly_rate(
                self.selic_data, current_year, current_month, self.selic_fallback_rate
            )
        else:
            # Use fixed annual rate converted to monthly
            monthly_rate = self.selic_rate_annual / 12

        # Apply monthly yield
        interest_earned = self.state.cash * monthly_rate

        # Update cash and track total interest
        self.state.cash += interest_earned
        self.state.total_interest_earned += interest_earned

        # Track the rate used for debugging/metrics
        month_key = f"{current_year}-{current_month:02d}"
        self.state.selic_rates_used[month_key] = monthly_rate

        # Record that we've applied yield for this month
        self._last_yield_month = (current_month, current_year)

    def buy(self, timestamp: pd.Timestamp, price: float, quantity: float, layer_id: Optional[int] = None) -> bool:
        """Execute buy order.

        Args:
            timestamp: Trade timestamp
            price: Execution price
            quantity: Quantity to buy
            layer_id: Optional layer identifier

        Returns:
            True if trade executed successfully
        """
        cost = price * quantity
        if self.state.cash < cost:
            return False

        self.state.cash -= cost

        # Add new layer
        if layer_id is None:
            layer_id = len(self.state.layers)

        layer = Layer(
            entry_price=price,
            quantity=quantity,
            cost=cost,
            timestamp=timestamp,
            layer_id=layer_id,
        )
        self.state.layers.append(layer)

        # Record trade
        trade = Trade(
            timestamp=timestamp,
            action="BUY",
            price=price,
            quantity=quantity,
            cost=cost,
            layer=layer_id,
        )
        self.state.trades.append(trade)

        return True

    def sell(self, timestamp: pd.Timestamp, price: float, quantity: float, layer_id: int) -> bool:
        """Sell specific layer quantity (LIFO).

        Args:
            timestamp: Trade timestamp
            price: Execution price
            quantity: Quantity to sell
            layer_id: Layer identifier to sell from

        Returns:
            True if trade executed successfully
        """
        # Find the layer
        layer_idx = None
        for i, layer in enumerate(self.state.layers):
            if layer.layer_id == layer_id:
                layer_idx = i
                break

        if layer_idx is None:
            return False

        layer = self.state.layers[layer_idx]
        sell_qty = min(quantity, layer.quantity)

        revenue = price * sell_qty
        cost_basis = layer.cost * (sell_qty / layer.quantity)
        pnl = revenue - cost_basis

        self.state.cash += revenue

        # Update or remove layer
        layer.quantity -= sell_qty
        layer.cost -= cost_basis

        if layer.quantity <= 0.000001:  # Remove empty layers
            self.state.layers.pop(layer_idx)

        # Record trade
        trade = Trade(
            timestamp=timestamp,
            action="SELL",
            price=price,
            quantity=sell_qty,
            cost=cost_basis,
            pnl=pnl,
            layer=layer_id,
        )
        self.state.trades.append(trade)

        return True

    def _close_all_positions(self, timestamp: pd.Timestamp, price: float):
        """Force close all open positions."""
        layers_to_close = self.state.layers.copy()
        for layer in reversed(layers_to_close):  # LIFO
            if layer.quantity > 0:
                self.sell(timestamp, price, layer.quantity, layer.layer_id)

    def _get_results(self) -> Dict[str, Any]:
        """Get backtest results."""
        equity_df = pd.DataFrame(
            {
                "timestamp": self.state.timestamp_history,
                "equity": self.state.equity_history,
                "cash": self.state.cash_history,
            }
        ).set_index("timestamp")

        trades_df = pd.DataFrame([vars(trade) for trade in self.state.trades])

        return {
            "equity": equity_df,
            "trades": trades_df,
            "final_equity": self.state.equity_history[-1] if self.state.equity_history else self.initial_cash,
            "final_cash": self.state.cash,
            "total_trades": len(self.state.trades),
            "open_layers": len(self.state.layers),
            "total_interest_earned": self.state.total_interest_earned,
            "cash_yield_enabled": self.apply_cash_yield,
            "selic_rate_annual": self.selic_rate_annual,
            "use_real_selic": self.use_real_selic,
            "selic_rates_used": self.state.selic_rates_used.copy() if self.state.selic_rates_used else {},
        }