"""Refactored backtest engine built on normalized domain models."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from src.bitcoin_martingale.domain.backtest.models import Layer, State, Trade
from src.bitcoin_martingale.domain.execution import OrderFill, OrderRequest, OrderSide
from src.bitcoin_martingale.domain.market_data import MarketBar
from src.bitcoin_martingale.domain.portfolio import PortfolioLedger
from src.selic import get_monthly_rate, get_or_create_selic_data


class BacktestCoreEngine:
    """Engine for backtesting strategies while preserving the legacy interface."""

    def __init__(
        self,
        initial_cash: float = 30000.0,
        apply_cash_yield: bool = False,
        selic_rate_annual: float = 0.13,
        yield_frequency: str = "monthly",
        use_real_selic: bool = False,
        selic_path: str = "data/selic.csv",
        selic_fallback_rate: float = 0.13,
        asset: str = "BTC-BRL",
        timeframe: str = "1d",
    ) -> None:
        self.initial_cash = initial_cash
        self.apply_cash_yield = apply_cash_yield
        self.selic_rate_annual = selic_rate_annual
        self.yield_frequency = yield_frequency
        self.use_real_selic = use_real_selic
        self.selic_path = selic_path
        self.selic_fallback_rate = selic_fallback_rate
        self.asset = asset
        self.timeframe = timeframe

        self.ledger = PortfolioLedger(asset=asset, initial_cash=initial_cash)
        self.state = self.ledger.state
        self._last_yield_month: tuple[int, int] | None = None
        self.selic_data = None

        if self.apply_cash_yield and self.use_real_selic:
            self._load_selic_data()

    def _load_selic_data(self) -> None:
        """Load SELIC data from file or download if needed."""
        try:
            self.selic_data = get_or_create_selic_data(
                path=self.selic_path,
                use_download=True,
                fallback_rate_annual=self.selic_fallback_rate,
            )
            if self.selic_data is not None and not self.selic_data.empty:
                print(f"Loaded {len(self.selic_data)} monthly SELIC rates from {self.selic_path}")
            else:
                print("Failed to load SELIC data, will use fallback rates")
        except Exception as exc:
            print(f"Error loading SELIC data: {exc}")
            self.selic_data = None

    @property
    def cash(self) -> float:
        """Current cash balance."""
        return self.state.cash

    @property
    def layers(self) -> list[Layer]:
        """Current open layers."""
        return self.state.layers

    def run(self, data: pd.DataFrame, strategy) -> dict[str, Any]:
        """Run a strategy against OHLCV data."""
        self.ledger.reset()
        self.state = self.ledger.state
        self._last_yield_month = None

        for timestamp, row in data.iterrows():
            bar = MarketBar.from_series(row, asset=self.asset, timeframe=self.timeframe)
            self._apply_cash_yield(timestamp)
            self.ledger.record_snapshot(timestamp=timestamp, market_price=bar.close)
            strategy.on_bar(row, self)

        if data.shape[0] > 0:
            self._close_all_positions(data.index[-1], float(data.iloc[-1]["Close"]))

        return self._get_results()

    def _apply_cash_yield(self, timestamp: pd.Timestamp) -> None:
        """Apply cash yield based on SELIC rate if enabled."""
        if not self.apply_cash_yield or self.yield_frequency != "monthly":
            return

        current_month = timestamp.month
        current_year = timestamp.year

        if self._last_yield_month is not None:
            if (
                current_month == self._last_yield_month[0]
                and current_year == self._last_yield_month[1]
            ):
                return

        if self.use_real_selic and self.selic_data is not None:
            monthly_rate = get_monthly_rate(
                self.selic_data, current_year, current_month, self.selic_fallback_rate
            )
        else:
            monthly_rate = self.selic_rate_annual / 12

        interest_earned = self.state.cash * monthly_rate
        self.state.cash += interest_earned
        self.state.total_interest_earned += interest_earned

        month_key = f"{current_year}-{current_month:02d}"
        self.state.selic_rates_used[month_key] = monthly_rate
        self._last_yield_month = (current_month, current_year)

    def buy(
        self,
        timestamp: pd.Timestamp,
        price: float,
        quantity: float,
        layer_id: Optional[int] = None,
    ) -> bool:
        """Execute a buy order using the normalized ledger."""
        if quantity <= 0:
            return False

        cost = price * quantity
        if self.state.cash < cost:
            return False

        resolved_layer_id = layer_id if layer_id is not None else len(self.state.layers)
        order = OrderRequest(
            order_id=f"buy-{timestamp.isoformat()}-{resolved_layer_id}",
            asset=self.asset,
            side=OrderSide.BUY,
            quantity=quantity,
            submitted_at=timestamp.to_pydatetime(),
            requested_price=price,
            metadata={"layer_id": resolved_layer_id},
        )
        fill = self._fill_order(order=order, fill_price=price)
        self.ledger.apply_buy(fill=fill, layer_id=resolved_layer_id)
        self.state = self.ledger.state
        return True

    def sell(self, timestamp: pd.Timestamp, price: float, quantity: float, layer_id: int) -> bool:
        """Sell a specific layer quantity."""
        if quantity <= 0:
            return False

        order = OrderRequest(
            order_id=f"sell-{timestamp.isoformat()}-{layer_id}",
            asset=self.asset,
            side=OrderSide.SELL,
            quantity=quantity,
            submitted_at=timestamp.to_pydatetime(),
            requested_price=price,
            metadata={"layer_id": layer_id},
        )
        fill = self._fill_order(order=order, fill_price=price)
        result = self.ledger.apply_sell(fill=fill, layer_id=layer_id)
        self.state = self.ledger.state
        return result

    def _fill_order(self, *, order: OrderRequest, fill_price: float) -> OrderFill:
        """Create a market fill for an order."""
        return OrderFill(
            order_id=order.order_id,
            asset=order.asset,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            filled_at=order.submitted_at,
            fees=0.0,
            slippage=0.0,
        )

    def _close_all_positions(self, timestamp: pd.Timestamp, price: float) -> None:
        """Force close all open positions using LIFO order."""
        layers_to_close = self.state.layers.copy()
        for layer in reversed(layers_to_close):
            if layer.quantity > 0:
                self.sell(timestamp, price, layer.quantity, layer.layer_id)

    def _get_results(self) -> dict[str, Any]:
        """Serialize results in the legacy engine format."""
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
            "final_equity": (
                self.state.equity_history[-1] if self.state.equity_history else self.initial_cash
            ),
            "final_cash": self.state.cash,
            "total_trades": len(self.state.trades),
            "open_layers": len(self.state.layers),
            "total_interest_earned": self.state.total_interest_earned,
            "cash_yield_enabled": self.apply_cash_yield,
            "selic_rate_annual": self.selic_rate_annual,
            "use_real_selic": self.use_real_selic,
            "selic_rates_used": (
                self.state.selic_rates_used.copy() if self.state.selic_rates_used else {}
            ),
        }


__all__ = ["BacktestCoreEngine", "Layer", "State", "Trade"]
