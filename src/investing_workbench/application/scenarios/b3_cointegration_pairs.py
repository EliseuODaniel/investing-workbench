"""Reproducible B3 cointegration pairs-trading scenario."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data import get_data
from src.investing_workbench.domain.pairs_trading import (
    CointegrationPairsBacktester,
    PairsTradingConfig,
)
from src.metrics import calculate_metrics

REQUESTED_UNIVERSE = [
    "PETR4",
    "PETR3",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "BBAS3",
    "ABEV3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "SUZB3",
    "PRIO3",
    "GGBR4",
    "CSNA3",
    "ELET3",
    "ENEV3",
    "RADL3",
    "RAIL3",
    "JBSS3",
    "CMIG4",
]

SECTOR_MAP = {
    "PETR4": "oil_gas",
    "PETR3": "oil_gas",
    "PRIO3": "oil_gas",
    "ITUB4": "banks",
    "BBDC4": "banks",
    "BBAS3": "banks",
    "VALE3": "metals_mining",
    "GGBR4": "metals_mining",
    "CSNA3": "metals_mining",
    "SUZB3": "pulp_paper",
    "ABEV3": "consumer_defensive",
    "RADL3": "consumer_defensive",
    "LREN3": "consumer_discretionary",
    "RENT3": "consumer_discretionary",
    "ENEV3": "utilities",
    "CMIG4": "utilities",
    "WEGE3": "industrials",
    "RAIL3": "industrials",
    "ELET3": "utilities",
    "JBSS3": "protein",
}

SECTOR_RATIONALE = {
    "oil_gas": "mesma cadeia de óleo e gás / exploração e refino",
    "banks": "bancos grandes domésticos com drivers macro parecidos",
    "metals_mining": "mineração e aço expostos ao mesmo ciclo de commodities metálicas",
    "pulp_paper": "celulose e papel; grupo isolado neste universo",
    "consumer_defensive": "consumo defensivo doméstico com drivers locais de renda e juros",
    "consumer_discretionary": "consumo discricionário doméstico sensível a renda, crédito e juros",
    "utilities": "utilities/energia com sensibilidade a juros e regulação",
    "industrials": "indústria e logística/infra com ciclo doméstico parecido",
    "protein": "proteína animal; grupo isolado neste universo",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run B3 cointegration pairs-trading scenario")
    parser.add_argument("--start-date", default="2021-01-01")
    parser.add_argument("--end-date", default=pd.Timestamp.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--output-dir", default="reports/b3_cointegration_pairs")
    return parser


def _load_universe(
    *, start_date: str, end_date: str | None, force_download: bool
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    data_by_ticker: dict[str, pd.DataFrame] = {}
    exclusions: dict[str, str] = {}
    for ticker in REQUESTED_UNIVERSE:
        try:
            data_by_ticker[ticker] = get_data(
                start=start_date,
                end=end_date,
                cache_path=f"data/{ticker.lower()}_sa.parquet",
                force_download=force_download,
                data_source=ticker,
                include_actions=True,
            )
        except Exception as exc:
            exclusions[ticker] = str(exc)
    return data_by_ticker, exclusions


def _normalize_trade_metrics_input(trades_df: pd.DataFrame) -> pd.DataFrame:
    if trades_df.empty:
        return pd.DataFrame(columns=["action", "pnl", "layer"])
    metrics_df = trades_df.copy()
    metrics_df["action"] = "SELL"
    metrics_df["pnl"] = metrics_df["net_pnl"]
    metrics_df["layer"] = metrics_df["pair_label"]
    return metrics_df


def _performance_summary(
    *,
    equity_df: pd.DataFrame,
    trades_df: pd.DataFrame,
    initial_capital: float,
    benchmark_equity: pd.Series | None = None,
) -> dict[str, Any]:
    metrics = calculate_metrics(
        equity=equity_df["equity"],
        trades=_normalize_trade_metrics_input(trades_df),
        initial_capital=initial_capital,
        benchmark=benchmark_equity,
    )
    avg_exposure = float(
        (equity_df["gross_exposure"] / equity_df["equity"].replace(0, np.nan)).fillna(0.0).mean()
    )
    turnover = 0.0
    if not trades_df.empty:
        turnover = float(
            (trades_df["gross_exposure_entry"].sum() + trades_df["gross_exposure_exit"].sum())
            / equity_df["equity"].mean()
        )
    win_rate = float((trades_df["net_pnl"] > 0).mean()) if not trades_df.empty else 0.0
    avg_win = (
        float(trades_df.loc[trades_df["net_pnl"] > 0, "net_pnl"].mean())
        if (not trades_df.empty and (trades_df["net_pnl"] > 0).any())
        else 0.0
    )
    avg_loss = (
        float(trades_df.loc[trades_df["net_pnl"] < 0, "net_pnl"].mean())
        if (not trades_df.empty and (trades_df["net_pnl"] < 0).any())
        else 0.0
    )
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
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": float(metrics["profit_factor"]),
        "avg_trade_pnl": float(trades_df["net_pnl"].mean()) if not trades_df.empty else 0.0,
        "final_equity": float(equity_df["equity"].iloc[-1]),
        "exposure_avg_gross": avg_exposure,
        "turnover": turnover,
        "short_borrow_cost_total": (
            float(trades_df["short_borrow_cost"].sum()) if not trades_df.empty else 0.0
        ),
        "fees_total": float(trades_df["fees_paid"].sum()) if not trades_df.empty else 0.0,
        "slippage_total": float(trades_df["slippage_cost"].sum()) if not trades_df.empty else 0.0,
    }


def _buy_hold_equity(series: pd.Series, initial_capital: float, index: pd.Index) -> pd.Series:
    aligned = series.reindex(index).ffill().dropna()
    if aligned.empty:
        return pd.Series(dtype=float)
    return (aligned / aligned.iloc[0]) * initial_capital


def _equal_weight_benchmark(
    data_by_ticker: dict[str, pd.DataFrame],
    tickers: list[str],
    initial_capital: float,
    index: pd.Index,
) -> pd.Series:
    components = []
    for ticker in tickers:
        series = data_by_ticker[ticker]["Adj Close"].reindex(index).ffill().dropna()
        if series.empty:
            continue
        components.append(series / series.iloc[0])
    if not components:
        return pd.Series(dtype=float)
    combined = pd.concat(components, axis=1).dropna()
    return combined.mean(axis=1) * initial_capital


def _pair_selection_summary(selections_df: pd.DataFrame) -> pd.DataFrame:
    if selections_df.empty:
        return pd.DataFrame(columns=["pair_label"])

    grouped = (
        selections_df.groupby(
            ["pair_label", "y_ticker", "x_ticker", "sector_group"], as_index=False
        )
        .agg(
            selection_count=("pair_label", "size"),
            avg_return_corr=("return_corr", "mean"),
            avg_coint_pvalue=("coint_pvalue", "mean"),
            avg_beta=("beta", "mean"),
            avg_half_life=("half_life", "mean"),
            periods=("trade_start", lambda s: ", ".join(sorted(set(s.tolist()))[:8])),
        )
        .sort_values(["selection_count", "avg_coint_pvalue"], ascending=[False, True])
    )
    grouped["rationale"] = grouped["sector_group"].map(SECTOR_RATIONALE)
    return grouped


def _run_one_scenario(
    *,
    name: str,
    data_by_ticker: dict[str, pd.DataFrame],
    config: PairsTradingConfig,
    require_cointegration: bool,
) -> dict[str, Any]:
    backtester = CointegrationPairsBacktester(
        data_by_ticker=data_by_ticker,
        sector_map={k: SECTOR_MAP[k] for k in data_by_ticker},
        config=config,
    )
    result = backtester.run(require_cointegration=require_cointegration)
    return {
        "name": name,
        "config": asdict(config),
        "equity": result["equity"],
        "trades": result["trades"],
        "selections": result["selections"],
        "eligible_universe": result["eligible_universe"],
        "first_trade_date": result["first_trade_date"],
        "common_index": result["common_index"],
    }


def run_scenario(argv: list[str] | None = None) -> dict[str, Any]:
    parser = _build_parser()
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    loaded_data, unavailable = _load_universe(
        start_date=args.start_date,
        end_date=args.end_date,
        force_download=args.force_download,
    )

    cost_config = PairsTradingConfig(min_return_corr=0.5)
    no_cost_config = PairsTradingConfig(
        min_return_corr=0.5, fee_rate=0.0, slippage=0.0, short_borrow_rate_annual=0.0
    )

    main = _run_one_scenario(
        name="cointegration_with_costs",
        data_by_ticker=loaded_data,
        config=cost_config,
        require_cointegration=True,
    )
    academic = _run_one_scenario(
        name="cointegration_no_costs",
        data_by_ticker=loaded_data,
        config=no_cost_config,
        require_cointegration=True,
    )
    no_filter = _run_one_scenario(
        name="no_cointegration_filter",
        data_by_ticker=loaded_data,
        config=cost_config,
        require_cointegration=False,
    )

    eligible_tickers = main["eligible_universe"]["ticker"].tolist()
    eligible_set = set(eligible_tickers)
    ineligible_tickers = sorted(set(loaded_data) - eligible_set)

    strategy_index = main["equity"].index
    bova11 = get_data(
        start=args.start_date,
        end=args.end_date,
        cache_path="data/bova11_sa.parquet",
        force_download=args.force_download,
        data_source="BOVA11.SA",
        include_actions=True,
    )
    benchmark_a_equity = _buy_hold_equity(
        bova11["Adj Close"], cost_config.initial_capital, strategy_index
    )
    benchmark_b_equity = _equal_weight_benchmark(
        loaded_data, eligible_tickers, cost_config.initial_capital, strategy_index
    )

    main_metrics = _performance_summary(
        equity_df=main["equity"],
        trades_df=main["trades"],
        initial_capital=cost_config.initial_capital,
        benchmark_equity=benchmark_a_equity.reindex(main["equity"].index).ffill(),
    )
    academic_metrics = _performance_summary(
        equity_df=academic["equity"],
        trades_df=academic["trades"],
        initial_capital=no_cost_config.initial_capital,
        benchmark_equity=benchmark_a_equity.reindex(academic["equity"].index).ffill(),
    )
    no_filter_metrics = _performance_summary(
        equity_df=no_filter["equity"],
        trades_df=no_filter["trades"],
        initial_capital=cost_config.initial_capital,
        benchmark_equity=benchmark_a_equity.reindex(no_filter["equity"].index).ffill(),
    )
    benchmark_a_metrics = _performance_summary(
        equity_df=pd.DataFrame({"equity": benchmark_a_equity, "gross_exposure": 0.0}),
        trades_df=pd.DataFrame(),
        initial_capital=cost_config.initial_capital,
    )
    benchmark_b_metrics = _performance_summary(
        equity_df=pd.DataFrame({"equity": benchmark_b_equity, "gross_exposure": 0.0}),
        trades_df=pd.DataFrame(),
        initial_capital=cost_config.initial_capital,
    )

    pair_selection_summary = _pair_selection_summary(main["selections"])
    pnl_by_pair = (
        main["trades"]
        .groupby("pair_label", as_index=False)["net_pnl"]
        .sum()
        .sort_values("net_pnl", ascending=False)
        if not main["trades"].empty
        else pd.DataFrame(columns=["pair_label", "net_pnl"])
    )

    (output_dir / "b3_pairs_trades_with_costs.csv").write_text(
        main["trades"].to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_trades_no_costs.csv").write_text(
        academic["trades"].to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_trades_no_coint_filter.csv").write_text(
        no_filter["trades"].to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_pair_selections.csv").write_text(
        main["selections"].to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_pair_selection_summary.csv").write_text(
        pair_selection_summary.to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_universe_eligible.csv").write_text(
        main["eligible_universe"].to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_equity_with_costs.csv").write_text(
        main["equity"].reset_index().to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_equity_no_costs.csv").write_text(
        academic["equity"].reset_index().to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "b3_pairs_pnl_by_pair.csv").write_text(
        pnl_by_pair.to_csv(index=False), encoding="utf-8"
    )

    summary = {
        "premises": {
            "initial_capital": cost_config.initial_capital,
            "requested_universe": REQUESTED_UNIVERSE,
            "available_universe": sorted(loaded_data.keys()),
            "unavailable_universe": unavailable,
            "eligible_universe": eligible_tickers,
            "excluded_after_liquidity_filter": ineligible_tickers,
            "frequency": "daily",
            "formation_window_days": cost_config.formation_window,
            "test_window_days": cost_config.test_window,
            "rebalance_step_days": cost_config.step_window,
            "entry_zscore": cost_config.entry_zscore,
            "exit_zscore": cost_config.exit_zscore,
            "stop_zscore": cost_config.stop_zscore,
            "max_holding_days": cost_config.max_holding_days,
            "max_pairs": cost_config.max_pairs,
            "pair_allocation_pct": cost_config.pair_allocation_pct,
            "selection_method": "same-sector candidates, return correlation pre-filter, OLS hedge ratio, Engle-Granger cointegration, ADF residual, half-life filter, greedy unique-asset ranking",
            "short_proxy": "short eligibility approximated by liquidity; no real BTC/borrow availability dataset",
            "costs_main": {
                "fee_rate": cost_config.fee_rate,
                "slippage_per_side": cost_config.slippage,
                "short_borrow_rate_annual": cost_config.short_borrow_rate_annual,
            },
            "costs_secondary": {
                "fee_rate": 0.0,
                "slippage_per_side": 0.0,
                "short_borrow_rate_annual": 0.0,
            },
            "signal_price_series": "split-adjusted OHLC built from raw Close/Open and Stock Splits only; dividends kept separate in P&L",
        },
        "results": {
            "main_with_costs": main_metrics,
            "secondary_no_costs": academic_metrics,
            "benchmark_without_cointegration_filter": no_filter_metrics,
        },
        "benchmarks": {
            "benchmark_a_bova11_buy_hold": benchmark_a_metrics,
            "benchmark_b_equal_weight_universe": benchmark_b_metrics,
            "benchmark_c_no_cointegration_filter": no_filter_metrics,
        },
        "selected_pairs_summary": pair_selection_summary.to_dict(orient="records"),
        "trade_audit": {
            "trade_log_csv": str(output_dir / "b3_pairs_trades_with_costs.csv"),
            "selection_log_csv": str(output_dir / "b3_pairs_pair_selections.csv"),
            "universe_csv": str(output_dir / "b3_pairs_universe_eligible.csv"),
            "pnl_by_pair_csv": str(output_dir / "b3_pairs_pnl_by_pair.csv"),
        },
        "artifacts": {
            "summary_json": str(output_dir / "b3_cointegration_pairs_summary.json"),
            "equity_with_costs_csv": str(output_dir / "b3_pairs_equity_with_costs.csv"),
            "equity_no_costs_csv": str(output_dir / "b3_pairs_equity_no_costs.csv"),
        },
    }

    summary_path = output_dir / "b3_cointegration_pairs_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    summary = run_scenario(argv)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
