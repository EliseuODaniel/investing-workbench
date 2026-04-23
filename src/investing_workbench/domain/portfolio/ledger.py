"""Portfolio ledger that powers the refactored backtest engine."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.investing_workbench.domain.backtest.models import Layer, State, Trade
from src.investing_workbench.domain.execution import OrderFill, OrderSide
from src.investing_workbench.domain.portfolio.models import PortfolioSnapshot, Position


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
        self.state.total_fees_paid += fill.fees

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
                notional=cost,
                layer=layer_id,
                cash_after=self.state.cash,
                position_after=self._position_quantity(),
                reference_after=fill.fill_price,
                requested_quantity=fill.requested_quantity,
                fill_ratio=(
                    (fill.quantity / fill.requested_quantity)
                    if fill.requested_quantity and fill.requested_quantity > 0
                    else None
                ),
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
        self.state.total_fees_paid += fill.fees

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
                notional=revenue,
                cash_after=self.state.cash,
                position_after=self._position_quantity(),
                reference_after=fill.fill_price,
                requested_quantity=fill.requested_quantity,
                fill_ratio=(
                    (sell_quantity / fill.requested_quantity)
                    if fill.requested_quantity and fill.requested_quantity > 0
                    else None
                ),
            )
        )
        return True

    def apply_stock_split(self, *, split_factor: float, timestamp: pd.Timestamp) -> bool:
        """Scale every open layer to account for a stock split.

        Parameters
        ----------
        split_factor: float
            Ratio implied by the split event (e.g. 2.0 for 2-for-1).
        timestamp: pd.Timestamp
            Event timestamp.

        Returns
        -------
        bool
            True when at least one layer was scaled.
        """
        if split_factor <= 0:
            return False

        if not self.state.layers:
            self.state.corporate_actions_log.append(
                {
                    "timestamp": pd.Timestamp(timestamp),
                    "type": "stock_split",
                    "split_factor": split_factor,
                    "cash_delta": 0.0,
                    "affected_layers": 0,
                    "notes": "Split with no open position",
                }
            )
            return False

        scaled_layers = []
        for layer in self.state.layers:
            scaled_layers.append(
                replace(
                    layer,
                    quantity=layer.quantity * split_factor,
                    entry_price=layer.entry_price / split_factor,
                )
            )

        self.state.layers = scaled_layers

        self.state.corporate_actions_log.append(
            {
                "timestamp": pd.Timestamp(timestamp),
                "type": "stock_split",
                "split_factor": split_factor,
                "cash_delta": 0.0,
                "affected_layers": len(self.state.layers),
                "notes": "Adjusted open layers and entry prices",
            }
        )
        return True

    def apply_dividend(self, *, dividend_per_share: float, timestamp: pd.Timestamp) -> None:
        """Credit dividends for current open position.

        Parameters
        ----------
        dividend_per_share: float
            Cash amount paid per share.
        timestamp: pd.Timestamp
            Event timestamp.
        """
        if dividend_per_share <= 0:
            return

        total_quantity = self.total_quantity()
        if total_quantity <= 0:
            self.state.corporate_actions_log.append(
                {
                    "timestamp": pd.Timestamp(timestamp),
                    "type": "dividend",
                    "dividend_per_share": dividend_per_share,
                    "cash_delta": 0.0,
                    "total_shares": 0.0,
                    "notes": "Dividend with no open shares",
                }
            )
            return

        cash_credit = dividend_per_share * total_quantity
        self.state.cash += cash_credit
        self.state.total_dividends_received += cash_credit

        self.state.corporate_actions_log.append(
            {
                "timestamp": pd.Timestamp(timestamp),
                "type": "dividend",
                "dividend_per_share": dividend_per_share,
                "cash_delta": cash_credit,
                "total_shares": total_quantity,
                "notes": "Dividend credited to cash",
            }
        )

    def get_last_layer_id(self) -> int | None:
        """Return the most recently opened layer id with remaining quantity."""
        for layer in reversed(self.state.layers):
            if layer.quantity > 0:
                return layer.layer_id
        return None

    def total_position_value(self, market_price: float) -> float:
        """Return total market value of open position."""
        return self.total_quantity() * market_price

    def total_cost_basis(self) -> float:
        """Return total cost basis of all open layers."""
        return sum(layer.cost for layer in self.state.layers)

    def _position_quantity(self) -> float:
        """Return current total open quantity."""
        return sum(layer.quantity for layer in self.state.layers)

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
