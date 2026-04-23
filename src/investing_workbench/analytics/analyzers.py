"""Composable analyzers for backtest metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(slots=True)
class MetricsInput:
    """Normalized input shared by all analyzers."""

    equity: pd.Series
    trades: pd.DataFrame
    initial_capital: float
    benchmark: pd.Series | None = None
    total_interest_earned: float = 0.0

    @property
    def daily_returns(self) -> pd.Series:
        """Daily returns derived from the equity curve."""
        return self.equity.pct_change().dropna()


class Analyzer(Protocol):
    """Contract for metric analyzers."""

    def analyze(self, context: MetricsInput) -> dict[str, Any]:
        """Return a partial metrics dictionary."""


class ReturnsAnalyzer:
    """Basic return and volatility calculations."""

    def analyze(self, context: MetricsInput) -> dict[str, Any]:
        total_return = (context.equity.iloc[-1] - context.initial_capital) / context.initial_capital
        daily_returns = context.daily_returns

        days = (context.equity.index[-1] - context.equity.index[0]).days
        years = days / 365.25
        if years > 0 and context.equity.iloc[0] > 0:
            cagr = (context.equity.iloc[-1] / context.equity.iloc[0]) ** (1 / years) - 1
        else:
            cagr = 0.0

        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0.0
        return {
            "total_return": total_return,
            "total_return_pct": total_return,
            "cagr": cagr,
            "cagr_pct": cagr,
            "volatility": volatility,
        }


class DrawdownAnalyzer:
    """Equity drawdown and MAR calculations."""

    def analyze(self, context: MetricsInput) -> dict[str, Any]:
        peak = context.equity.expanding().max()
        drawdown = (context.equity - peak) / peak
        max_drawdown = drawdown.min()

        days = (context.equity.index[-1] - context.equity.index[0]).days
        years = days / 365.25
        if years > 0 and context.equity.iloc[0] > 0:
            cagr = (context.equity.iloc[-1] / context.equity.iloc[0]) ** (1 / years) - 1
        else:
            cagr = 0.0

        mar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0.0
        return {
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown,
            "mar_ratio": mar_ratio,
        }


class RiskAdjustedAnalyzer:
    """Sharpe, Sortino, beta and alpha calculations."""

    risk_free_rate: float = 0.05

    def analyze(self, context: MetricsInput) -> dict[str, Any]:
        daily_returns = context.daily_returns

        if len(daily_returns) > 1 and daily_returns.std() != 0:
            sharpe_ratio = (daily_returns.mean() * 252 - self.risk_free_rate) / (
                daily_returns.std() * np.sqrt(252)
            )
        else:
            sharpe_ratio = 0.0

        negative_returns = daily_returns[daily_returns < 0]
        if len(negative_returns) > 0 and negative_returns.std() != 0:
            sortino_ratio = (daily_returns.mean() * 252 - self.risk_free_rate) / (
                negative_returns.std() * np.sqrt(252)
            )
        else:
            sortino_ratio = 0.0

        beta = None
        alpha = None
        if context.benchmark is not None and len(context.benchmark) == len(context.equity):
            benchmark_returns = context.benchmark.pct_change().dropna()
            if len(benchmark_returns) > 1:
                aligned_returns = pd.DataFrame(
                    {"strategy": daily_returns, "benchmark": benchmark_returns}
                ).dropna()
                if len(aligned_returns) > 10:
                    try:
                        beta, alpha, _, _, _ = stats.linregress(
                            aligned_returns["benchmark"].values,
                            aligned_returns["strategy"].values,
                        )
                        alpha = alpha * 252
                    except (TypeError, ValueError):
                        beta = None
                        alpha = None

        return {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "beta": beta,
            "alpha": alpha,
        }


class TradeStatisticsAnalyzer:
    """Trade-level statistics including layer PnL."""

    def analyze(self, context: MetricsInput) -> dict[str, Any]:
        trades = context.trades
        if len(trades) == 0:
            return {
                "hit_rate": 0.0,
                "win_rate_pct": 0.0,
                "avg_trade_pnl": 0.0,
                "profit_factor": 0.0,
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "layer_pnl": {},
                "total_interest_earned": context.total_interest_earned,
            }

        buy_trades = trades[trades["action"] == "BUY"]
        sell_trades = trades[trades["action"] == "SELL"]

        winning_trades = (
            sell_trades[sell_trades["pnl"] > 0] if "pnl" in sell_trades.columns else pd.DataFrame()
        )
        hit_rate = len(winning_trades) / len(sell_trades) if len(sell_trades) > 0 else 0.0
        avg_pnl = (
            sell_trades["pnl"].mean()
            if "pnl" in sell_trades.columns and len(sell_trades) > 0
            else 0.0
        )
        gross_profit = (
            sell_trades[sell_trades["pnl"] > 0]["pnl"].sum()
            if "pnl" in sell_trades.columns
            else 0.0
        )
        gross_loss = (
            abs(sell_trades[sell_trades["pnl"] < 0]["pnl"].sum())
            if "pnl" in sell_trades.columns
            else 0.0
        )
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.99
        layer_pnl = (
            sell_trades.groupby("layer")["pnl"].sum().to_dict()
            if "layer" in sell_trades.columns
            else {}
        )

        return {
            "hit_rate": hit_rate,
            "win_rate_pct": hit_rate,
            "avg_trade_pnl": avg_pnl,
            "profit_factor": profit_factor,
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "layer_pnl": layer_pnl,
            "total_interest_earned": context.total_interest_earned,
        }


DEFAULT_ANALYZERS: tuple[Analyzer, ...] = (
    ReturnsAnalyzer(),
    DrawdownAnalyzer(),
    RiskAdjustedAnalyzer(),
    TradeStatisticsAnalyzer(),
)
