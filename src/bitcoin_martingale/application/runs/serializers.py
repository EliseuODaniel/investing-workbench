"""Serialization helpers for run orchestration outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.api.models import (
    BacktestResponse,
    BenchmarkResult,
    ConfigInfo,
    EquityPoint,
    ExecutionEvent,
    ExecutionSummary,
    StrategyMetrics,
    StrategyResult,
    Trade,
)
from src.config import AppConfig
from src.metrics import calculate_metrics


def build_config_info(config_file: Path, config_data: dict[str, Any]) -> ConfigInfo:
    """Build the API-facing config descriptor from a YAML file payload."""
    display_name = config_data.get("name", config_file.stem)
    strategy_names = [strategy.get("name", "") for strategy in config_data.get("strategies", [])]
    return ConfigInfo(
        name=config_file.stem,
        path=str(config_file),
        display_name=display_name,
        strategies=strategy_names,
    )


class RunResponseSerializer:
    """Convert raw engine outputs into the stable API response contract."""

    def build_response(
        self,
        *,
        config: AppConfig,
        strategies_to_run: list[Any],
        data: pd.DataFrame,
        strategy_runner: Any,
        benchmark_loader: Any,
    ) -> BacktestResponse:
        buy_hold_equity = self.build_buy_hold_curve(data, config.backtest.initial_capital)
        results = strategy_runner(config, strategies_to_run, data)
        benchmarks = benchmark_loader(config)
        return BacktestResponse(
            results=results,
            buy_hold_equity=buy_hold_equity,
            benchmarks=benchmarks if benchmarks else None,
            data_info={
                "start_date": data.index[0].isoformat(),
                "end_date": data.index[-1].isoformat(),
                "total_days": len(data),
                "initial_price": float(data.iloc[0]["Close"]),
                "final_price": float(data.iloc[-1]["Close"]),
            },
            run_info={},
            warnings=self._collect_response_warnings(results),
        )

    def build_buy_hold_curve(self, data: pd.DataFrame, initial_capital: float) -> list[EquityPoint]:
        initial_price = float(data.iloc[0]["Close"])
        curve: list[EquityPoint] = []
        for timestamp, row in data.iterrows():
            current_price = float(row["Close"])
            buy_hold_value = initial_capital * (current_price / initial_price)
            curve.append(
                EquityPoint(
                    timestamp=timestamp.isoformat(),
                    equity=buy_hold_value,
                    cash=initial_capital,
                )
            )
        return curve

    def build_strategy_result(
        self,
        *,
        strategy_name: str,
        result: dict[str, Any],
        initial_capital: float,
        data: pd.DataFrame,
    ) -> StrategyResult:
        equity_points = [
            EquityPoint(
                timestamp=timestamp.isoformat(),
                equity=row["equity"],
                cash=row["cash"],
            )
            for timestamp, row in result["equity"].iterrows()
        ]
        trades = [self.serialize_trade(trade_row) for _, trade_row in result["trades"].iterrows()]
        metrics = calculate_metrics(
            result["equity"]["equity"],
            result["trades"],
            initial_capital,
            total_interest_earned=result.get("total_interest_earned", 0.0),
        )
        selic_rates_used = self._serialize_selic_rates(result.get("selic_rates_used", {}))
        return StrategyResult(
            strategy_name=strategy_name,
            equity=equity_points,
            trades=trades,
            metrics=StrategyMetrics(
                total_return=metrics["total_return"],
                cagr=metrics["cagr"],
                sharpe_ratio=metrics["sharpe_ratio"],
                sortino_ratio=metrics["sortino_ratio"],
                max_drawdown=metrics["max_drawdown"],
                hit_rate=metrics["hit_rate"],
                profit_factor=metrics["profit_factor"],
                total_trades=metrics["total_trades"],
                avg_trade_pnl=metrics["avg_trade_pnl"],
                volatility=metrics["volatility"],
                total_interest_earned=metrics["total_interest_earned"],
                total_fees_paid=float(result.get("total_fees_paid", 0.0)),
                total_dividends_received=float(result.get("total_dividends_received", 0.0)),
                selic_rates_used=selic_rates_used,
            ),
            start_price=float(data.iloc[0]["Close"]),
            end_price=float(data.iloc[-1]["Close"]),
            execution_log=self.serialize_execution_log(result.get("execution_log", [])),
            execution_summary=self.serialize_execution_summary(result.get("execution_summary", {})),
            warnings=self._serialize_warnings(result.get("warnings", [])),
        )

    def serialize_trade(self, trade_row: pd.Series) -> Trade:
        """Serialize one trade row from the engine result dataframe."""

        def _optional_number(value: Any) -> float | None:
            if pd.isna(value):
                return None
            return float(value)

        layer_value = trade_row.get("layer")
        if pd.isna(layer_value):
            layer_value = None
        elif isinstance(layer_value, float) and layer_value.is_integer():
            layer_value = int(layer_value)

        pnl_value = trade_row.get("pnl")
        if pd.isna(pnl_value):
            pnl_value = None

        return Trade(
            timestamp=trade_row["timestamp"].isoformat(),
            action=trade_row["action"],
            price=trade_row["price"],
            quantity=trade_row["quantity"],
            cost=_optional_number(trade_row.get("cost")),
            pnl=pnl_value,
            layer=layer_value,
            requested_quantity=_optional_number(trade_row.get("requested_quantity")),
            fill_ratio=_optional_number(trade_row.get("fill_ratio")),
        )

    def serialize_execution_log(self, events: list[dict[str, Any]]) -> list[ExecutionEvent]:
        """Serialize raw execution events from the engine output."""
        serialized_events: list[ExecutionEvent] = []
        for event in events:
            serialized_events.append(
                ExecutionEvent(
                    timestamp=pd.Timestamp(event["timestamp"]).isoformat(),
                    event_type=str(event["event_type"]),
                    side=str(event["side"]),
                    requested_quantity=float(event["requested_quantity"]),
                    filled_quantity=float(event["filled_quantity"]),
                    fill_ratio=float(event["fill_ratio"]),
                    requested_price=float(event["requested_price"]),
                    fill_price=(
                        float(event["fill_price"]) if event.get("fill_price") is not None else None
                    ),
                    fees=float(event.get("fees", 0.0)),
                    slippage=float(event.get("slippage", 0.0)),
                    message=str(event["message"]),
                )
            )
        return serialized_events

    def serialize_execution_summary(self, payload: dict[str, Any]) -> ExecutionSummary:
        """Serialize aggregate execution diagnostics."""
        return ExecutionSummary(
            fill_count=int(payload.get("fill_count", 0)),
            partial_fill_count=int(payload.get("partial_fill_count", 0)),
            rejected_buy_count=int(payload.get("rejected_buy_count", 0)),
            rejected_sell_count=int(payload.get("rejected_sell_count", 0)),
            rejected_order_count=int(payload.get("rejected_order_count", 0)),
            liquidity_constrained=bool(payload.get("liquidity_constrained", False)),
            requested_quantity_total=float(payload.get("requested_quantity_total", 0.0)),
            filled_quantity_total=float(payload.get("filled_quantity_total", 0.0)),
        )

    def serialize_benchmark(
        self, *, name: str, ticker: str, benchmark_data: dict[str, Any]
    ) -> BenchmarkResult:
        """Serialize one benchmark dataset into the API-facing response shape."""
        equity_points = [
            EquityPoint(
                timestamp=timestamp.isoformat(),
                equity=row["equity"],
                cash=0.0,
            )
            for timestamp, row in benchmark_data["equity_curve"].iterrows()
        ]
        metrics = benchmark_data["metrics"]
        return BenchmarkResult(
            name=name,
            ticker=ticker,
            equity=equity_points,
            metrics=StrategyMetrics(
                total_return=metrics["total_return"],
                cagr=metrics["cagr"],
                sharpe_ratio=metrics["sharpe_ratio"],
                sortino_ratio=0.0,
                max_drawdown=metrics["max_drawdown"],
                hit_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                avg_trade_pnl=0.0,
                volatility=metrics["volatility"],
                total_interest_earned=0.0,
                selic_rates_used=None,
            ),
        )

    def _collect_response_warnings(self, results: dict[str, StrategyResult]) -> list[str]:
        warnings: list[str] = []
        for strategy_name, result in results.items():
            warnings.extend(f"{strategy_name}: {warning}" for warning in result.warnings if warning)
        return warnings

    def _serialize_selic_rates(self, payload: dict[str, Any]) -> list[dict[str, Any]] | None:
        if not payload:
            return None

        serialized_rates: list[dict[str, Any]] = []
        for period, rate in payload.items():
            serialized_rates.append({"period": str(period), "rate": float(rate)})
        return serialized_rates

    def _serialize_warnings(self, warnings: list[Any]) -> list[str]:
        return [str(warning) for warning in warnings if warning is not None]
