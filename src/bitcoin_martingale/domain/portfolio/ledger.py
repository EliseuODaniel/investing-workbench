"""Portfolio ledger that powers the refactored backtest engine."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.bitcoin_martingale.domain.backtest.models import Layer, State, Trade
from src.bitcoin_martingale.domain.execution import OrderFill, OrderSide
from src.bitcoin_martingale.domain.portfolio.models import PortfolioSnapshot, Position


class PortfolioLedger:
    """Mutates cash, layers, and trade history from normalized fills."""

    def __init__(self, *, asset: str, initial_cash: float) -> None:
        self.asset = asset
        self.initial_cash = initial_cash
        self.state = State(cash=initial_cash, max_equity=initial_cash)

    def reset(self) -> None:
        """Reset the ledger for a fresh run."""
        self.state = State(cash=self.initial_cash, max_equity=self.initial_cash)

    def total_quantity(self) -> float:
        """Total open quantity across all layers."""
        return sum(layer.quantity for layer in self.state.layers)

    def record_snapshot(self, *, timestamp: pd.Timestamp, market_price: float) -> PortfolioSnapshot:
        """Record an equity snapshot and return the normalized view."""
        position = self.build_position()
        total_equity = self.state.cash + (position.quantity * market_price)

        self.state.equity_history.append(total_equity)
        self.state.cash_history.append(self.state.cash)
        self.state.timestamp_history.append(timestamp)
        self.state.max_equity = max(self.state.max_equity, total_equity)

        positions = [position] if position.quantity > 0 else []
        return PortfolioSnapshot(
            timestamp=timestamp.to_pydatetime(),
            cash=self.state.cash,
            total_equity=total_equity,
            positions=positions,
        )

    def apply_buy(self, *, fill: OrderFill, layer_id: int) -> Layer:
        """Apply a buy fill and open a new layer."""
        cost = fill.gross_value + fill.fees
        self.state.cash -= cost

        layer = Layer(
            entry_price=fill.fill_price,
            quantity=fill.quantity,
            cost=cost,
            timestamp=pd.Timestamp(fill.filled_at),
            layer_id=layer_id,
        )
        self.state.layers.append(layer)
        self.state.trades.append(
            Trade(
                timestamp=pd.Timestamp(fill.filled_at),
                action="BUY",
                price=fill.fill_price,
                quantity=fill.quantity,
                cost=cost,
                layer=layer_id,
            )
        )
        return layer

    def apply_sell(self, *, fill: OrderFill, layer_id: int) -> bool:
        """Apply a sell fill to an existing layer."""
        layer_index = next(
            (index for index, layer in enumerate(self.state.layers) if layer.layer_id == layer_id),
            None,
        )
        if layer_index is None:
            return False

        layer = self.state.layers[layer_index]
        sell_quantity = min(fill.quantity, layer.quantity)
        revenue = (sell_quantity * fill.fill_price) - fill.fees
        cost_basis = layer.cost * (sell_quantity / layer.quantity)
        pnl = revenue - cost_basis

        self.state.cash += revenue

        remaining_quantity = layer.quantity - sell_quantity
        remaining_cost = layer.cost - cost_basis

        if remaining_quantity <= 0.000001:
            self.state.layers.pop(layer_index)
        else:
            self.state.layers[layer_index] = replace(
                layer,
                quantity=remaining_quantity,
                cost=remaining_cost,
            )

        self.state.trades.append(
            Trade(
                timestamp=pd.Timestamp(fill.filled_at),
                action="SELL",
                price=fill.fill_price,
                quantity=sell_quantity,
                cost=cost_basis,
                pnl=pnl,
                layer=layer_id,
            )
        )
        return True

    def build_position(self) -> Position:
        """Aggregate open layers into a single normalized position."""
        total_quantity = self.total_quantity()
        if total_quantity <= 0:
            return Position(
                asset=self.asset,
                quantity=0.0,
                average_entry_price=0.0,
                cost_basis=0.0,
            )

        total_cost = sum(layer.cost for layer in self.state.layers)
        average_entry_price = total_cost / total_quantity
        return Position(
            asset=self.asset,
            quantity=total_quantity,
            average_entry_price=average_entry_price,
            cost_basis=total_cost,
        )

    def apply_fill(self, *, fill: OrderFill, layer_id: int) -> bool:
        """Apply a normalized fill to the ledger."""
        if fill.side == OrderSide.BUY:
            self.apply_buy(fill=fill, layer_id=layer_id)
            return True
        return self.apply_sell(fill=fill, layer_id=layer_id)
