"""Reporting helpers for pairs-trading scenarios."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.investing_workbench.domain.pairs_trading import PairsTradingConfig
from src.metrics import calculate_metrics

from .catalog import SECTOR_RATIONALE


class PairsReportingService:
    """Build summaries and analytics for pairs scenario outputs."""

    def performance_summary(
        self,
        *,
        equity_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        initial_capital: float,
        benchmark_equity: pd.Series | None,
    ) -> dict[str, Any]:
        """Build top-level performance metrics for one scenario."""
        metrics = calculate_metrics(
            equity=equity_df["equity"],
            trades=self.normalize_trade_metrics_input(trades_df),
            initial_capital=initial_capital,
            benchmark=benchmark_equity,
        )
        avg_exposure = float(
            (equity_df["gross_exposure"] / equity_df["equity"].replace(0, np.nan))
            .fillna(0.0)
            .mean()
        )
        turnover = 0.0
        if not trades_df.empty:
            turnover = float(
                (trades_df["gross_exposure_entry"].sum() + trades_df["gross_exposure_exit"].sum())
                / max(float(equity_df["equity"].mean()), 1e-9)
            )
        win_rate = float((trades_df["net_pnl"] > 0).mean()) if not trades_df.empty else 0.0
        return {
            "return_total": float(metrics["total_return"]),
            "cagr": float(metrics["cagr"]),
            "volatility": float(metrics["volatility"]),
            "sharpe": float(metrics["sharpe_ratio"]),
            "sortino": float(metrics["sortino_ratio"]),
            "max_drawdown": float(metrics["max_drawdown"]),
            "mar_ratio": float(metrics["mar_ratio"]),
            "trade_count": int(len(trades_df)),
            "win_rate": win_rate,
            "profit_factor": float(metrics["profit_factor"]),
            "avg_trade_pnl": float(trades_df["net_pnl"].mean()) if not trades_df.empty else 0.0,
            "final_equity": float(equity_df["equity"].iloc[-1]),
            "avg_gross_exposure_pct": avg_exposure,
            "turnover": turnover,
            "short_borrow_cost_total": (
                float(trades_df["short_borrow_cost"].sum()) if not trades_df.empty else 0.0
            ),
            "fees_total": float(trades_df["fees_paid"].sum()) if not trades_df.empty else 0.0,
            "slippage_total": (
                float(trades_df["slippage_cost"].sum()) if not trades_df.empty else 0.0
            ),
        }

    def pair_selection_summary(self, selections_df: pd.DataFrame) -> pd.DataFrame:
        """Summarize pair selection frequency and stability across the run."""
        if selections_df.empty:
            return pd.DataFrame(columns=["pair_label"])
        grouped = (
            selections_df.groupby(
                ["pair_label", "y_ticker", "x_ticker", "sector_group"],
                as_index=False,
            )
            .agg(
                selection_count=("pair_label", "size"),
                avg_return_corr=("return_corr", "mean"),
                avg_coint_pvalue=("coint_pvalue", "mean"),
                avg_beta=("beta", "mean"),
                avg_half_life=("half_life", "mean"),
            )
            .sort_values(["selection_count", "avg_coint_pvalue"], ascending=[False, True])
        )
        grouped["rationale"] = grouped["sector_group"].map(SECTOR_RATIONALE)
        return grouped

    def pair_pnl_summary(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """Summarize cumulative PnL per pair."""
        if trades_df.empty:
            return pd.DataFrame(columns=["pair_label", "net_pnl"])
        return (
            trades_df.groupby("pair_label", as_index=False)["net_pnl"]
            .sum()
            .sort_values("net_pnl", ascending=False)
        )

    def build_portfolio_summary(
        self,
        *,
        equity_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        selections_df: pd.DataFrame,
        config: PairsTradingConfig,
    ) -> dict[str, Any]:
        """Build portfolio construction diagnostics for one scenario."""
        sector_counts: list[dict[str, Any]] = []
        if not selections_df.empty:
            sector_counts = (
                selections_df.groupby("sector_group", as_index=False)
                .agg(selection_count=("pair_label", "size"))
                .sort_values("selection_count", ascending=False)
                .to_dict(orient="records")
            )
        top_pair_share = 0.0
        if not trades_df.empty:
            pnl = trades_df.groupby("pair_label")["net_pnl"].sum().abs()
            denominator = float(pnl.sum())
            if denominator > 0:
                top_pair_share = float(pnl.max() / denominator)
        unique_assets: set[str] = set()
        if not selections_df.empty:
            unique_assets |= set(selections_df["y_ticker"].tolist())
            unique_assets |= set(selections_df["x_ticker"].tolist())
        borrow_source_mix: list[dict[str, Any]] = []
        if not trades_df.empty and "short_borrow_source" in trades_df:
            borrow_source_mix = (
                trades_df.groupby("short_borrow_source", as_index=False)
                .agg(trade_count=("pair_label", "size"))
                .sort_values("trade_count", ascending=False)
                .to_dict(orient="records")
            )
        return {
            "construction": config.portfolio_construction,
            "target_pair_volatility_annual": config.target_pair_volatility_annual,
            "max_sector_pairs": config.max_sector_pairs,
            "max_gross_exposure_pct": config.max_gross_exposure_pct,
            "max_net_exposure_pct": config.max_net_exposure_pct,
            "gross_exposure_peak": (
                float(equity_df["gross_exposure"].max()) if not equity_df.empty else 0.0
            ),
            "gross_exposure_average": (
                float(equity_df["gross_exposure"].mean()) if not equity_df.empty else 0.0
            ),
            "net_exposure_abs_average": (
                float(equity_df["net_exposure"].abs().mean()) if not equity_df.empty else 0.0
            ),
            "open_positions_peak": (
                int(equity_df["open_positions"].max()) if not equity_df.empty else 0
            ),
            "unique_pairs_traded": (
                int(trades_df["pair_label"].nunique()) if not trades_df.empty else 0
            ),
            "unique_assets_used": int(len(unique_assets)),
            "allocation_pct_average": (
                float(trades_df["allocation_pct"].mean()) if not trades_df.empty else 0.0
            ),
            "allocation_pct_max": (
                float(trades_df["allocation_pct"].max()) if not trades_df.empty else 0.0
            ),
            "top_pair_concentration_pct": top_pair_share,
            "sector_mix": sector_counts,
            "borrow_source_mix": borrow_source_mix,
        }

    def build_robustness_report(self, scenario_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Summarize dispersion across scenarios in one batch run."""
        if not scenario_results:
            return {"rankings": [], "dispersion": {}}
        summary_frame = pd.DataFrame(
            [
                {
                    "scenario_id": scenario["scenario_id"],
                    "label": scenario["label"],
                    "return_total": scenario["metrics"]["return_total"],
                    "sharpe": scenario["metrics"]["sharpe"],
                    "max_drawdown": scenario["metrics"]["max_drawdown"],
                    "trade_count": scenario["metrics"]["trade_count"],
                }
                for scenario in scenario_results
            ]
        )
        rankings = summary_frame.sort_values(
            ["sharpe", "return_total"], ascending=[False, False]
        ).to_dict(orient="records")
        return {
            "rankings": rankings,
            "dispersion": {
                "return_total_range": float(
                    summary_frame["return_total"].max() - summary_frame["return_total"].min()
                ),
                "sharpe_range": float(
                    summary_frame["sharpe"].max() - summary_frame["sharpe"].min()
                ),
                "max_drawdown_range": float(
                    summary_frame["max_drawdown"].max() - summary_frame["max_drawdown"].min()
                ),
            },
        }

    def build_alpha_decomposition(
        self,
        *,
        equity_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        initial_capital: float,
        cash_yield_total: float,
        benchmark_series: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Split total result into trade sleeve, cash carry, frictions, and benchmark gaps."""
        final_equity = (
            float(equity_df["equity"].iloc[-1]) if not equity_df.empty else initial_capital
        )
        total_pnl = final_equity - initial_capital
        trade_gross_pnl_total = float(trades_df["gross_pnl"].sum()) if not trades_df.empty else 0.0
        trade_net_pnl_total = float(trades_df["net_pnl"].sum()) if not trades_df.empty else 0.0
        dividend_pnl_total = float(trades_df["dividend_pnl"].sum()) if not trades_df.empty else 0.0
        short_borrow_cost_total = (
            float(trades_df["short_borrow_cost"].sum()) if not trades_df.empty else 0.0
        )
        fees_total = float(trades_df["fees_paid"].sum()) if not trades_df.empty else 0.0
        slippage_total = float(trades_df["slippage_cost"].sum()) if not trades_df.empty else 0.0
        explained_pnl_total = trade_net_pnl_total + cash_yield_total
        residual_pnl_total = total_pnl - explained_pnl_total

        benchmark_comparison: list[dict[str, Any]] = []
        primary_benchmark_id: str | None = None
        for benchmark in benchmark_series:
            equity_curve = benchmark.get("equity_curve", [])
            if not equity_curve:
                continue
            last_point = equity_curve[-1]
            benchmark_equity = float(last_point.get("equity", initial_capital))
            if not np.isfinite(benchmark_equity):
                continue
            benchmark_return_total = (benchmark_equity / initial_capital) - 1.0
            comparison = {
                "benchmark_id": str(benchmark.get("benchmark_id", "")),
                "label": str(benchmark.get("label", benchmark.get("benchmark_id", ""))),
                "final_equity": benchmark_equity,
                "equity_gap": final_equity - benchmark_equity,
                "return_total": benchmark_return_total,
                "excess_return_total": (
                    (final_equity / initial_capital) - 1.0 - benchmark_return_total
                ),
            }
            benchmark_comparison.append(comparison)
            if primary_benchmark_id is None and comparison["benchmark_id"] != "selic_cash":
                primary_benchmark_id = str(comparison["benchmark_id"])

        if primary_benchmark_id is None and benchmark_comparison:
            primary_benchmark_id = str(benchmark_comparison[0]["benchmark_id"])
        primary_benchmark = next(
            (item for item in benchmark_comparison if item["benchmark_id"] == primary_benchmark_id),
            None,
        )

        total_pnl_denominator = max(abs(total_pnl), 1e-9)
        return {
            "initial_capital": float(initial_capital),
            "final_equity": final_equity,
            "total_pnl": total_pnl,
            "trade_gross_pnl_total": trade_gross_pnl_total,
            "trade_net_pnl_total": trade_net_pnl_total,
            "dividend_pnl_total": dividend_pnl_total,
            "cash_yield_total": float(cash_yield_total),
            "short_borrow_cost_total": short_borrow_cost_total,
            "fees_total": fees_total,
            "slippage_total": slippage_total,
            "explained_pnl_total": explained_pnl_total,
            "residual_pnl_total": residual_pnl_total,
            "trade_return_total": trade_net_pnl_total / initial_capital,
            "cash_return_total": float(cash_yield_total) / initial_capital,
            "trade_share_of_total_pnl": trade_net_pnl_total / total_pnl_denominator,
            "cash_share_of_total_pnl": float(cash_yield_total) / total_pnl_denominator,
            "primary_benchmark_id": primary_benchmark_id,
            "primary_benchmark_equity_gap": (
                float(primary_benchmark["equity_gap"]) if primary_benchmark is not None else None
            ),
            "primary_benchmark_excess_return": (
                float(primary_benchmark["excess_return_total"])
                if primary_benchmark is not None
                else None
            ),
            "benchmark_comparison": benchmark_comparison,
        }

    def normalize_trade_metrics_input(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize pairs trades into the generic metrics input schema."""
        if trades_df.empty:
            return pd.DataFrame(columns=["action", "pnl", "layer"])
        metrics_df = trades_df.copy()
        metrics_df["action"] = "SELL"
        metrics_df["pnl"] = metrics_df["net_pnl"]
        metrics_df["layer"] = metrics_df["pair_label"]
        return metrics_df
