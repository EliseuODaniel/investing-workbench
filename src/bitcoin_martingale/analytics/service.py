"""Metric orchestration built on plugable analyzers."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .analyzers import DEFAULT_ANALYZERS, Analyzer, MetricsInput


class MetricsService:
    """Compose analyzers into the legacy metrics payload."""

    def __init__(self, analyzers: tuple[Analyzer, ...] = DEFAULT_ANALYZERS) -> None:
        self.analyzers = analyzers

    def calculate(
        self,
        *,
        equity: pd.Series,
        trades: pd.DataFrame,
        initial_capital: float,
        benchmark: pd.Series | None = None,
        total_interest_earned: float | None = None,
    ) -> dict[str, Any]:
        """Calculate metrics for a single strategy or benchmark."""
        if len(equity) == 0:
            return {"error": "No equity data"}

        context = MetricsInput(
            equity=equity,
            trades=trades,
            initial_capital=initial_capital,
            benchmark=benchmark,
            total_interest_earned=total_interest_earned or 0.0,
        )

        metrics: dict[str, Any] = {}
        for analyzer in self.analyzers:
            metrics.update(analyzer.analyze(context))

        return metrics

    def compare(
        self, *, results: dict[str, dict[str, Any]], initial_capital: float
    ) -> pd.DataFrame:
        """Compare multiple strategies side by side."""
        comparison_data: list[dict[str, Any]] = []

        for strategy_name, result in results.items():
            if "equity" not in result or len(result["equity"]) == 0:
                continue

            equity = result["equity"]["equity"]
            trades = result["trades"]

            if len(equity) > 0:
                start_price = result.get("start_price", 1.0)
                end_price = result.get("end_price", 1.0)
                buy_hold_return = (end_price - start_price) / start_price
                buy_hold_equity = initial_capital * (1 + buy_hold_return)
            else:
                buy_hold_equity = initial_capital

            benchmark = pd.Series([buy_hold_equity] * len(equity), index=equity.index)
            metrics = self.calculate(
                equity=equity,
                trades=trades,
                initial_capital=initial_capital,
                benchmark=benchmark,
            )

            row = {"Strategy": strategy_name}
            row.update(metrics)
            comparison_data.append(row)

        if not comparison_data:
            return pd.DataFrame()

        comparison_df = pd.DataFrame(comparison_data)
        return comparison_df.sort_values("total_return", ascending=False)
