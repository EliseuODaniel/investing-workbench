"""Compatibility facade for performance metrics and strategy comparisons."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.investing_workbench.analytics import MetricsService

_metrics_service = MetricsService()


def calculate_metrics(
    equity: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
    benchmark: pd.Series | None = None,
    total_interest_earned: float | None = None,
) -> dict[str, Any]:
    """Calculate comprehensive performance metrics."""
    return _metrics_service.calculate(
        equity=equity,
        trades=trades,
        initial_capital=initial_capital,
        benchmark=benchmark,
        total_interest_earned=total_interest_earned,
    )


def print_metrics(metrics: dict[str, Any], strategy_name: str = "Strategy") -> None:
    """Print formatted metrics to console."""
    print(f"\n=== {strategy_name} Performance ===")
    print(f"Total Return: {metrics['total_return']:.2%}")
    print(f"CAGR: {metrics['cagr']:.2%}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"MAR Ratio: {metrics['mar_ratio']:.2f}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"Volatility: {metrics['volatility']:.2%}")
    print(f"Hit Rate: {metrics['hit_rate']:.2%}")
    print(f"Average Trade PnL: ${metrics['avg_trade_pnl']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Total Trades: {metrics['total_trades']}")
    if metrics.get("total_interest_earned", 0) > 0:
        print(f"Total Interest Earned: ${metrics['total_interest_earned']:.2f}")
    if metrics["beta"] is not None:
        print(f"Beta: {metrics['beta']:.2f}")
        print(f"Alpha: {metrics['alpha']:.2%}")


def compare_strategies(results: dict[str, dict[str, Any]], initial_capital: float) -> pd.DataFrame:
    """Compare multiple strategies side by side."""
    return _metrics_service.compare(results=results, initial_capital=initial_capital)
