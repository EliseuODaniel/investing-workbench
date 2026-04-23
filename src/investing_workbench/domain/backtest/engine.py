"""Refactored backtest engine built on normalized domain models."""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from src.investing_workbench.domain.backtest.models import Layer, State, Trade
from src.investing_workbench.domain.execution import OrderFill, OrderRequest, OrderSide
from src.investing_workbench.domain.market_data import MarketBar
from src.investing_workbench.domain.portfolio import PortfolioLedger
from src.selic import (
    get_daily_rate,
    get_monthly_rate,
    get_or_create_daily_selic_data,
    get_or_create_selic_data,
)

logger = logging.getLogger(__name__)


class BacktestCoreEngine:
    """Engine for backtesting strategies while preserving the legacy interface."""

    def __init__(
        self,
        initial_cash: float = 30000.0,
        apply_cash_yield: bool = False,
        selic_rate_annual: float = 0.13,
        yield_frequency: str = "monthly",
        cash_yield_timing: str = "start_of_bar",
        use_real_selic: bool = False,
        selic_path: str = "data/selic.csv",
        selic_fallback_rate: float = 0.13,
        asset: str = "BTC-BRL",
        timeframe: str = "1d",
        close_positions_at_end: bool = True,
        fee_rate: float = 0.0,
        fixed_fee: float = 0.0,
        buy_slippage: float = 0.0,
        sell_slippage: float = 0.0,
        max_volume_participation: float | None = None,
        allow_partial_fills: bool = True,
        min_fill_quantity: float = 0.0,
    ) -> None:
        self.initial_cash = initial_cash
        self.apply_cash_yield = apply_cash_yield
        self.selic_rate_annual = selic_rate_annual
        self.yield_frequency = yield_frequency
        self.cash_yield_timing = cash_yield_timing
        self.use_real_selic = use_real_selic
        self.selic_path = selic_path
        self.selic_fallback_rate = selic_fallback_rate
        self.asset = asset
        self.timeframe = timeframe
        self.close_positions_at_end = close_positions_at_end
        self.fee_rate = fee_rate
        self.fixed_fee = fixed_fee
        self.buy_slippage = buy_slippage
        self.sell_slippage = sell_slippage
        self.max_volume_participation = max_volume_participation
        self.allow_partial_fills = allow_partial_fills
        self.min_fill_quantity = min_fill_quantity

        self.ledger = PortfolioLedger(asset=asset, initial_cash=initial_cash)
        self.state = self.ledger.state
        self._last_yield_month: tuple[int, int] | None = None
        self._last_yield_day: tuple[int, int, int] | None = None
        self._last_market_price: float | None = None
        self._current_bar: MarketBar | None = None
        self._current_bar_timestamp: pd.Timestamp | None = None
        self._bar_volume_limit: float | None = None
        self._bar_volume_used: float = 0.0
        self.selic_data = None

        if self.cash_yield_timing not in {"start_of_bar", "end_of_bar"}:
            raise ValueError("cash_yield_timing must be either 'start_of_bar' or 'end_of_bar'")

        if self.apply_cash_yield and self.use_real_selic:
            self._load_selic_data()

    def _load_selic_data(self) -> None:
        """Load SELIC data from file or download if needed."""
        try:
            if self.yield_frequency == "daily":
                self.selic_data = get_or_create_daily_selic_data(
                    path=self.selic_path,
                    use_download=True,
                )
                if self.selic_data is not None and not self.selic_data.empty:
                    logger.info(
                        "Loaded %s daily SELIC rates from %s",
                        len(self.selic_data),
                        self.selic_path,
                    )
                else:
                    logger.warning("Failed to load daily SELIC data, will use fallback rates")
                return

            self.selic_data = get_or_create_selic_data(
                path=self.selic_path,
                use_download=True,
                fallback_rate_annual=self.selic_fallback_rate,
            )
            if self.selic_data is not None and not self.selic_data.empty:
                logger.info(
                    "Loaded %s monthly SELIC rates from %s",
                    len(self.selic_data),
                    self.selic_path,
                )
            else:
                logger.warning("Failed to load monthly SELIC data, will use fallback rates")
        except Exception:
            logger.exception("Error loading SELIC data from %s", self.selic_path)
            self.selic_data = None

    def _ensure_selic_data_coverage(self, *, start: pd.Timestamp, end: pd.Timestamp) -> None:
        """Refresh the SELIC cache so it covers the run window when possible."""
        if not self.apply_cash_yield or not self.use_real_selic:
            return

        start_date = pd.Timestamp(start).strftime("%Y-%m-%d")
        end_date = pd.Timestamp(end).strftime("%Y-%m-%d")

        try:
            if self.yield_frequency == "daily":
                self.selic_data = get_or_create_daily_selic_data(
                    path=self.selic_path,
                    use_download=True,
                    start_date=start_date,
                    end_date=end_date,
                )
                if self.selic_data is not None and not self.selic_data.empty:
                    logger.info(
                        "Daily SELIC coverage refreshed for %s to %s using %s rows",
                        start_date,
                        end_date,
                        len(self.selic_data),
                    )
                else:
                    logger.warning(
                        "Daily SELIC coverage refresh returned no data for %s to %s; "
                        "falling back to configured rate",
                        start_date,
                        end_date,
                    )
                return

            self.selic_data = get_or_create_selic_data(
                path=self.selic_path,
                use_download=True,
                start_date=start_date,
                end_date=end_date,
                fallback_rate_annual=self.selic_fallback_rate,
            )
            if self.selic_data is not None and not self.selic_data.empty:
                logger.info(
                    "Monthly SELIC coverage refreshed for %s to %s using %s rows",
                    start_date,
                    end_date,
                    len(self.selic_data),
                )
            else:
                logger.warning(
                    "Monthly SELIC coverage refresh returned no data for %s to %s; "
                    "falling back to configured rate",
                    start_date,
                    end_date,
                )
        except Exception:
            logger.exception(
                "Failed to refresh SELIC coverage for %s to %s",
                start_date,
                end_date,
            )

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
        self._last_yield_day = None
        self._last_market_price = None
        self._current_bar = None
        self._current_bar_timestamp = None
        self._bar_volume_limit = None
        self._bar_volume_used = 0.0

        if data.empty:
            return self._get_results()

        self._ensure_selic_data_coverage(
            start=pd.Timestamp(data.index[0]),
            end=pd.Timestamp(data.index[-1]),
        )

        for timestamp, row in data.iterrows():
            bar = MarketBar.from_series(row, asset=self.asset, timeframe=self.timeframe)
            self._set_current_bar(timestamp=timestamp, bar=bar)
            if self.cash_yield_timing == "start_of_bar":
                self._apply_cash_yield(timestamp)
            self._apply_corporate_actions(timestamp=timestamp, row=row)
            strategy.on_bar(row, self)
            if self.cash_yield_timing == "end_of_bar":
                self._apply_cash_yield(timestamp)
            self._record_snapshot(timestamp=timestamp, market_price=bar.close)

        if data.shape[0] > 0 and self.close_positions_at_end:
            last_timestamp = data.index[-1]
            last_price = float(data.iloc[-1]["Close"])
            self._close_all_positions(last_timestamp, last_price)
            self._sync_last_snapshot(timestamp=last_timestamp, market_price=last_price)

        return self._get_results()

    def _apply_corporate_actions(self, timestamp: pd.Timestamp, row: pd.Series) -> None:
        """Apply stock splits and dividends for the current bar."""
        split_factor = float(row.get("Stock Splits", 0.0) or 0.0)
        if split_factor > 0:
            self.ledger.apply_stock_split(
                split_factor=split_factor,
                timestamp=timestamp,
            )

        dividend_per_share = float(row.get("Dividends", 0.0) or 0.0)
        if dividend_per_share > 0:
            self.ledger.apply_dividend(
                dividend_per_share=dividend_per_share,
                timestamp=timestamp,
            )

    def _record_snapshot(self, *, timestamp: pd.Timestamp, market_price: float) -> None:
        """Persist position and equity history for this bar."""
        self._last_market_price = market_price
        self.ledger.record_snapshot(timestamp=timestamp, market_price=market_price)

    def _sync_last_snapshot(self, *, timestamp: pd.Timestamp, market_price: float) -> None:
        """Overwrite the final snapshot so it reflects the post-trade portfolio state."""
        self._last_market_price = market_price
        total_equity = self.state.cash + (self.ledger.total_quantity() * market_price)

        if self.state.timestamp_history and self.state.timestamp_history[-1] == timestamp:
            self.state.timestamp_history[-1] = timestamp
            self.state.cash_history[-1] = self.state.cash
            self.state.equity_history[-1] = total_equity
            self.state.max_equity = max(self.state.max_equity, total_equity)
            return

        self.ledger.record_snapshot(timestamp=timestamp, market_price=market_price)

    def _apply_cash_yield(self, timestamp: pd.Timestamp) -> None:
        """Apply cash yield based on SELIC rate if enabled."""
        if not self.apply_cash_yield:
            return

        if self.yield_frequency == "daily":
            self._apply_daily_cash_yield(timestamp)
            return

        if self.yield_frequency != "monthly":
            return

        current_month = int(timestamp.month)
        current_year = int(timestamp.year)

        if self._last_yield_month is not None:
            if (
                current_month == self._last_yield_month[0]
                and current_year == self._last_yield_month[1]
            ):
                return

        monthly_rate = self._resolve_monthly_rate(timestamp)
        interest_earned = self.state.cash * monthly_rate
        self.state.cash += interest_earned
        self.state.total_interest_earned += interest_earned

        month_key = f"{current_year}-{current_month:02d}"
        self.state.selic_rates_used[month_key] = monthly_rate
        self._last_yield_month = (current_month, current_year)
        self._last_yield_day = (timestamp.year, timestamp.month, timestamp.day)

    def _apply_daily_cash_yield(self, timestamp: pd.Timestamp) -> None:
        current_day = (timestamp.year, timestamp.month, timestamp.day)
        if self._last_yield_day == current_day:
            return

        if self.use_real_selic and self.selic_data is not None:
            daily_rate = get_daily_rate(
                self.selic_data,
                timestamp,
                fallback_rate_annual=self.selic_fallback_rate,
            )
        else:
            daily_rate = (1 + self.selic_rate_annual) ** (1.0 / 252.0) - 1

        interest_earned = self.state.cash * daily_rate
        self.state.cash += interest_earned
        self.state.total_interest_earned += interest_earned
        day_key = pd.Timestamp(timestamp).strftime("%Y-%m-%d")
        self.state.selic_rates_used[day_key] = daily_rate
        self._last_yield_day = current_day
        self._last_yield_month = (timestamp.month, timestamp.year)

    def _resolve_monthly_rate(self, timestamp: pd.Timestamp) -> float:
        if self.use_real_selic and self.selic_data is not None:
            return get_monthly_rate(
                self.selic_data,
                int(timestamp.year),
                int(timestamp.month),
                self.selic_fallback_rate,
            )
        return self.selic_rate_annual / 12

    def buy(
        self,
        timestamp: pd.Timestamp,
        price: float,
        quantity: float,
        layer_id: Optional[int] = None,
        market_volume: float | None = None,
    ) -> bool:
        """Execute a buy order using the normalized ledger."""
        if quantity <= 0:
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
        fill = self._fill_order(order=order, fill_price=price, market_volume=market_volume)
        if fill is None:
            self._log_execution_event(
                timestamp=timestamp,
                event_type="buy_rejected",
                side=OrderSide.BUY,
                requested_quantity=quantity,
                filled_quantity=0.0,
                requested_price=price,
                message="Order was not executable under current cash or liquidity limits.",
            )
            return False
        self.ledger.apply_buy(fill=fill, layer_id=resolved_layer_id)
        self.state = self.ledger.state
        self._log_fill_event(fill=fill, requested_price=price)
        return True

    def sell(
        self,
        timestamp: pd.Timestamp,
        price: float,
        quantity: float,
        layer_id: int,
        market_volume: float | None = None,
    ) -> bool:
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
        fill = self._fill_order(order=order, fill_price=price, market_volume=market_volume)
        if fill is None:
            self._log_execution_event(
                timestamp=timestamp,
                event_type="sell_rejected",
                side=OrderSide.SELL,
                requested_quantity=quantity,
                filled_quantity=0.0,
                requested_price=price,
                message="Order was not executable under current liquidity limits.",
            )
            return False
        result = self.ledger.apply_sell(fill=fill, layer_id=layer_id)
        self.state = self.ledger.state
        if result:
            self._log_fill_event(fill=fill, requested_price=price)
        return result

    def _fill_order(
        self,
        *,
        order: OrderRequest,
        fill_price: float,
        market_volume: float | None = None,
    ) -> OrderFill | None:
        """Create a market fill for an order."""
        executable_quantity = self._resolve_executable_quantity(
            requested_quantity=order.quantity,
            market_volume=market_volume,
        )
        if executable_quantity <= 0:
            return None

        effective_fill_price = self._resolve_fill_price(order.side, fill_price)
        if order.side == OrderSide.BUY:
            gross_value = effective_fill_price * executable_quantity
            total_cost = gross_value + self._calculate_fees(gross_value)
            if self.state.cash + 1e-12 < total_cost:
                return None

        gross_value = effective_fill_price * executable_quantity
        fees = self._calculate_fees(gross_value)
        slippage = abs(effective_fill_price - fill_price)
        self._consume_bar_liquidity(executable_quantity)
        return OrderFill(
            order_id=order.order_id,
            asset=order.asset,
            side=order.side,
            quantity=executable_quantity,
            fill_price=effective_fill_price,
            filled_at=order.submitted_at,
            fees=fees,
            slippage=slippage,
            requested_quantity=order.quantity,
        )

    def _set_current_bar(self, *, timestamp: pd.Timestamp, bar: MarketBar) -> None:
        self._current_bar = bar
        self._current_bar_timestamp = timestamp
        self._bar_volume_used = 0.0
        if self.max_volume_participation is None:
            self._bar_volume_limit = None
            return

        participation = min(max(self.max_volume_participation, 0.0), 1.0)
        self._bar_volume_limit = max(bar.volume, 0.0) * participation

    def _resolve_executable_quantity(
        self,
        *,
        requested_quantity: float,
        market_volume: float | None = None,
    ) -> float:
        if requested_quantity <= 0:
            return 0.0

        if market_volume is not None and self.max_volume_participation is not None:
            volume_cap = max(market_volume, 0.0) * min(max(self.max_volume_participation, 0.0), 1.0)
            available_quantity = max(volume_cap, 0.0)
        elif self._bar_volume_limit is not None:
            available_quantity = max(self._bar_volume_limit - self._bar_volume_used, 0.0)
        else:
            return requested_quantity

        if available_quantity <= 0:
            return 0.0
        if requested_quantity <= available_quantity:
            return requested_quantity
        if not self.allow_partial_fills:
            return 0.0

        partial_quantity = available_quantity
        if partial_quantity < self.min_fill_quantity:
            return 0.0
        return partial_quantity

    def _consume_bar_liquidity(self, quantity: float) -> None:
        if self._bar_volume_limit is None:
            return
        self._bar_volume_used = min(self._bar_volume_used + quantity, self._bar_volume_limit)

    def _log_fill_event(self, *, fill: OrderFill, requested_price: float) -> None:
        requested_quantity = fill.requested_quantity or fill.quantity
        event_type = "fill"
        message = "Order filled in full."
        if fill.quantity + 1e-12 < requested_quantity:
            event_type = "partial_fill"
            message = "Order partially filled due to liquidity limits."

        self._log_execution_event(
            timestamp=pd.Timestamp(fill.filled_at),
            event_type=event_type,
            side=fill.side,
            requested_quantity=requested_quantity,
            filled_quantity=fill.quantity,
            requested_price=requested_price,
            fill_price=fill.fill_price,
            fees=fill.fees,
            slippage=fill.slippage,
            message=message,
        )

    def _log_execution_event(
        self,
        *,
        timestamp: pd.Timestamp,
        event_type: str,
        side: OrderSide,
        requested_quantity: float,
        filled_quantity: float,
        requested_price: float,
        fill_price: float | None = None,
        fees: float = 0.0,
        slippage: float = 0.0,
        message: str,
    ) -> None:
        fill_ratio = (filled_quantity / requested_quantity) if requested_quantity > 0 else 0.0
        self.state.execution_log.append(
            {
                "timestamp": pd.Timestamp(timestamp),
                "event_type": event_type,
                "side": side.value,
                "requested_quantity": requested_quantity,
                "filled_quantity": filled_quantity,
                "fill_ratio": fill_ratio,
                "requested_price": requested_price,
                "fill_price": fill_price,
                "fees": fees,
                "slippage": slippage,
                "message": message,
            }
        )

    def _resolve_fill_price(self, side: OrderSide, requested_price: float) -> float:
        if side == OrderSide.BUY:
            return requested_price * (1.0 + self.buy_slippage)
        return requested_price * (1.0 - self.sell_slippage)

    def _calculate_fees(self, gross_value: float) -> float:
        if gross_value <= 0:
            return 0.0
        return gross_value * self.fee_rate + self.fixed_fee

    def estimate_buy_total_cost(self, requested_price: float, quantity: float) -> float:
        fill_price = self._resolve_fill_price(OrderSide.BUY, requested_price)
        gross_value = fill_price * quantity
        return gross_value + self._calculate_fees(gross_value)

    def estimate_sell_net_proceeds(self, requested_price: float, quantity: float) -> float:
        fill_price = self._resolve_fill_price(OrderSide.SELL, requested_price)
        gross_value = fill_price * quantity
        return gross_value - self._calculate_fees(gross_value)

    def quantity_for_buy_budget(self, requested_price: float, budget: float) -> float:
        if budget <= 0:
            return 0.0
        fill_price = self._resolve_fill_price(OrderSide.BUY, requested_price)
        denominator = fill_price * (1.0 + self.fee_rate)
        if denominator <= 0:
            return 0.0
        safety_margin = max(1e-9, budget * 1e-12)
        usable_budget = max(budget - self.fixed_fee - safety_margin, 0.0)
        return usable_budget / denominator

    def _build_execution_summary(self) -> dict[str, Any]:
        events = self.state.execution_log
        fills = sum(1 for event in events if event["event_type"] == "fill")
        partial_fills = sum(1 for event in events if event["event_type"] == "partial_fill")
        rejected_buys = sum(1 for event in events if event["event_type"] == "buy_rejected")
        rejected_sells = sum(1 for event in events if event["event_type"] == "sell_rejected")
        total_requested = sum(float(event["requested_quantity"]) for event in events)
        total_filled = sum(float(event["filled_quantity"]) for event in events)

        return {
            "fill_count": fills,
            "partial_fill_count": partial_fills,
            "rejected_buy_count": rejected_buys,
            "rejected_sell_count": rejected_sells,
            "rejected_order_count": rejected_buys + rejected_sells,
            "liquidity_constrained": partial_fills > 0 or rejected_sells > 0 or rejected_buys > 0,
            "requested_quantity_total": total_requested,
            "filled_quantity_total": total_filled,
        }

    def _build_execution_warnings(self, summary: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        if summary["partial_fill_count"] > 0:
            warnings.append(
                "One or more orders were partially filled due to configured liquidity limits."
            )
        if summary["rejected_buy_count"] > 0:
            warnings.append(
                "One or more buy orders were rejected because cash or liquidity was insufficient."
            )
        if summary["rejected_sell_count"] > 0:
            warnings.append(
                "One or more sell orders were rejected because liquidity was insufficient."
            )
        return warnings

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
        last_market_price = self._last_market_price or 0.0
        execution_summary = self._build_execution_summary()

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
            "yield_frequency": self.yield_frequency,
            "cash_yield_timing": self.cash_yield_timing,
            "selic_rate_annual": self.selic_rate_annual,
            "use_real_selic": self.use_real_selic,
            "selic_rates_used": (
                self.state.selic_rates_used.copy() if self.state.selic_rates_used else {}
            ),
            "total_dividends_received": self.state.total_dividends_received,
            "total_fees_paid": self.state.total_fees_paid,
            "fee_rate": self.fee_rate,
            "fixed_fee": self.fixed_fee,
            "buy_slippage": self.buy_slippage,
            "sell_slippage": self.sell_slippage,
            "max_volume_participation": self.max_volume_participation,
            "allow_partial_fills": self.allow_partial_fills,
            "min_fill_quantity": self.min_fill_quantity,
            "execution_log": self.state.execution_log,
            "execution_summary": execution_summary,
            "warnings": self._build_execution_warnings(execution_summary),
            "corporate_actions_log": self.state.corporate_actions_log,
            "position_quantity": self.ledger.total_quantity(),
            "position_value": self.ledger.total_position_value(last_market_price),
            "last_market_price": last_market_price,
            "close_positions_at_end": self.close_positions_at_end,
        }


__all__ = ["BacktestCoreEngine", "Layer", "State", "Trade"]
