"""Enhanced B3 cointegration pairs-trading scenario.

Includes cash-yield, regime, margin, and financing variants.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from src.data import get_data
from src.investing_workbench.application.scenarios.b3_cointegration_pairs import (
    REQUESTED_UNIVERSE,
    SECTOR_MAP,
    _buy_hold_equity,
    _equal_weight_benchmark,
    _load_universe,
    _pair_selection_summary,
    _performance_summary,
)
from src.investing_workbench.domain.pairs_trading import (
    CointegrationPairsBacktester,
    PairsTradingConfig,
)
from src.selic import get_daily_rate, get_or_create_daily_selic_data


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run enhanced B3 cointegration pairs-trading scenario"
    )
    parser.add_argument("--start-date", default="2021-01-01")
    parser.add_argument("--end-date", default=pd.Timestamp.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--output-dir", default="reports/b3_cointegration_pairs_enhanced")
    return parser


def _run_one_scenario(
    *,
    name: str,
    data_by_ticker: dict[str, pd.DataFrame],
    benchmark_data: pd.DataFrame,
    config: PairsTradingConfig,
    require_cointegration: bool,
) -> dict[str, Any]:
    backtester = CointegrationPairsBacktester(
        data_by_ticker=data_by_ticker,
        sector_map={k: SECTOR_MAP[k] for k in data_by_ticker},
        config=config,
        benchmark_data=benchmark_data,
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
        "cash_yield_total": result["cash_yield_total"],
        "regime_blocked_entries": result["regime_blocked_entries"],
    }


def _scenario_metrics(
    *,
    scenario: dict[str, Any],
    initial_capital: float,
    benchmark_equity: pd.Series,
) -> dict[str, Any]:
    equity_df = scenario["equity"]
    metrics = _performance_summary(
        equity_df=equity_df,
        trades_df=scenario["trades"],
        initial_capital=initial_capital,
        benchmark_equity=benchmark_equity.reindex(equity_df.index).ffill(),
    )
    metrics["cash_yield_total"] = float(scenario["cash_yield_total"])
    metrics["regime_blocked_entries"] = int(scenario["regime_blocked_entries"])
    metrics["avg_cash_yield_base"] = float(equity_df["cash_yield_base"].mean())
    metrics["avg_open_positions"] = float(equity_df["open_positions"].mean())
    metrics["regime_active_ratio"] = float(equity_df["regime_ok"].mean())
    metrics["eligible_universe_size"] = int(len(scenario["eligible_universe"]))
    metrics["selection_count"] = int(len(scenario["selections"]))
    if not scenario["trades"].empty and "short_borrow_rate_annual" in scenario["trades"]:
        metrics["avg_trade_short_borrow_rate"] = float(
            scenario["trades"]["short_borrow_rate_annual"].mean()
        )
    else:
        metrics["avg_trade_short_borrow_rate"] = 0.0
    metrics["first_trade_date"] = scenario["first_trade_date"]
    metrics["last_date"] = str(equity_df.index[-1].date())
    return metrics


def _selic_only_equity(
    *,
    index: pd.Index,
    initial_capital: float,
    selic_path: str,
    fallback_rate_annual: float,
) -> pd.Series:
    if len(index) == 0:
        return pd.Series(dtype=float)
    start_date = str(pd.Timestamp(index[0]).date())
    end_date = str(pd.Timestamp(index[-1]).date())
    selic_data = get_or_create_daily_selic_data(
        path=selic_path,
        use_download=True,
        start_date=start_date,
        end_date=end_date,
    )
    equity: list[float] = []
    capital = float(initial_capital)
    for date in pd.Index(index):
        if equity:
            capital *= 1.0 + get_daily_rate(
                selic_data,
                pd.Timestamp(date),
                fallback_rate_annual=fallback_rate_annual,
            )
        equity.append(capital)
    return pd.Series(equity, index=index, dtype=float)


def _scenario_export_name(name: str) -> str:
    return (
        name.replace("cointegration_", "")
        .replace("with_", "")
        .replace("no_", "no_")
        .replace("explicit_", "explicit_")
    )


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

    bova11 = get_data(
        start=args.start_date,
        end=args.end_date,
        cache_path="data/bova11_sa.parquet",
        force_download=args.force_download,
        data_source="BOVA11.SA",
        include_actions=True,
    )

    baseline_config = PairsTradingConfig(min_return_corr=0.5)
    enhanced_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=True,
        use_real_selic=True,
        selic_path="data/selic_daily.csv",
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
    )
    enhanced_no_costs_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=True,
        use_real_selic=True,
        selic_path="data/selic_daily.csv",
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
    )
    explicit_margin_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=True,
        use_real_selic=True,
        selic_path="data/selic_daily.csv",
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
        explicit_margin_model=True,
        short_margin_haircut=0.5,
    )
    explicit_margin_no_costs_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=True,
        use_real_selic=True,
        selic_path="data/selic_daily.csv",
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
        explicit_margin_model=True,
        short_margin_haircut=0.5,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
    )
    explicit_margin_no_cash_yield_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=False,
        use_real_selic=False,
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
        explicit_margin_model=True,
        short_margin_haircut=0.5,
    )
    explicit_margin_stressed_financing_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=True,
        use_real_selic=True,
        selic_path="data/selic_daily.csv",
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
        explicit_margin_model=True,
        short_margin_haircut=1.0,
        short_borrow_rate_annual=0.10,
    )
    explicit_margin_proxy_borrow_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=True,
        use_real_selic=True,
        selic_path="data/selic_daily.csv",
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
        explicit_margin_model=True,
        short_margin_haircut=0.5,
        use_proxy_short_borrow=True,
        proxy_borrow_base_rate_annual=0.03,
        proxy_borrow_max_rate_annual=0.12,
        proxy_min_short_score=0.40,
    )
    explicit_margin_proxy_borrow_no_cash_yield_config = PairsTradingConfig(
        min_return_corr=0.5,
        apply_cash_yield=False,
        use_real_selic=False,
        dynamic_beta=True,
        rolling_beta_window=60,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=63,
        regime_max_deviation=0.08,
        regime_vol_window=21,
        regime_vol_lookback=252,
        regime_vol_quantile=0.75,
        explicit_margin_model=True,
        short_margin_haircut=0.5,
        use_proxy_short_borrow=True,
        proxy_borrow_base_rate_annual=0.03,
        proxy_borrow_max_rate_annual=0.12,
        proxy_min_short_score=0.40,
    )

    scenarios = [
        ("baseline_with_costs", baseline_config),
        ("enhanced_with_costs", enhanced_config),
        ("enhanced_no_costs", enhanced_no_costs_config),
        ("enhanced_explicit_margin_with_costs", explicit_margin_config),
        ("enhanced_explicit_margin_no_costs", explicit_margin_no_costs_config),
        ("enhanced_explicit_margin_no_cash_yield_with_costs", explicit_margin_no_cash_yield_config),
        (
            "enhanced_explicit_margin_stressed_financing_with_costs",
            explicit_margin_stressed_financing_config,
        ),
        ("enhanced_explicit_margin_proxy_borrow_with_costs", explicit_margin_proxy_borrow_config),
        (
            "enhanced_explicit_margin_proxy_borrow_no_cash_yield_with_costs",
            explicit_margin_proxy_borrow_no_cash_yield_config,
        ),
    ]
    scenario_results: dict[str, dict[str, Any]] = {}
    for name, config in scenarios:
        scenario_results[name] = _run_one_scenario(
            name=name,
            data_by_ticker=loaded_data,
            benchmark_data=bova11,
            config=config,
            require_cointegration=True,
        )

    proxy_margin = scenario_results["enhanced_explicit_margin_proxy_borrow_with_costs"]

    eligible_tickers = proxy_margin["eligible_universe"]["ticker"].tolist()
    ineligible_tickers = sorted(set(loaded_data) - set(eligible_tickers))

    strategy_index = proxy_margin["equity"].index
    benchmark_a_equity = _buy_hold_equity(
        bova11["Adj Close"], enhanced_config.initial_capital, strategy_index
    )
    benchmark_b_equity = _equal_weight_benchmark(
        loaded_data, eligible_tickers, enhanced_config.initial_capital, strategy_index
    )
    benchmark_c_selic_equity = _selic_only_equity(
        index=strategy_index,
        initial_capital=enhanced_config.initial_capital,
        selic_path="data/selic_daily.csv",
        fallback_rate_annual=0.13,
    )

    scenario_metrics = {
        name: _scenario_metrics(
            scenario=result,
            initial_capital=scenarios[idx][1].initial_capital,
            benchmark_equity=benchmark_a_equity,
        )
        for idx, (name, _config) in enumerate(scenarios)
        for result in [scenario_results[name]]
    }

    benchmark_a_metrics = _performance_summary(
        equity_df=pd.DataFrame({"equity": benchmark_a_equity, "gross_exposure": 0.0}),
        trades_df=pd.DataFrame(),
        initial_capital=enhanced_config.initial_capital,
    )
    benchmark_b_metrics = _performance_summary(
        equity_df=pd.DataFrame({"equity": benchmark_b_equity, "gross_exposure": 0.0}),
        trades_df=pd.DataFrame(),
        initial_capital=enhanced_config.initial_capital,
    )
    benchmark_c_metrics = _performance_summary(
        equity_df=pd.DataFrame({"equity": benchmark_c_selic_equity, "gross_exposure": 0.0}),
        trades_df=pd.DataFrame(),
        initial_capital=enhanced_config.initial_capital,
    )

    selection_summary = _pair_selection_summary(proxy_margin["selections"])
    pnl_by_pair = (
        proxy_margin["trades"]
        .groupby("pair_label", as_index=False)["net_pnl"]
        .sum()
        .sort_values("net_pnl", ascending=False)
        if not proxy_margin["trades"].empty
        else pd.DataFrame(columns=["pair_label", "net_pnl"])
    )

    scenario_comparison = []
    for name, metrics in scenario_metrics.items():
        row = {
            "scenario": name,
            "final_equity": metrics["final_equity"],
            "return_total": metrics["return_total"],
            "cagr": metrics["cagr"],
            "sharpe": metrics["sharpe"],
            "max_drawdown": metrics["max_drawdown"],
            "trade_count": metrics["trade_count"],
            "cash_yield_total": metrics["cash_yield_total"],
            "trade_pnl_total": metrics["avg_trade_pnl"] * metrics["trade_count"],
            "short_borrow_cost_total": metrics["short_borrow_cost_total"],
            "fees_total": metrics["fees_total"],
            "slippage_total": metrics["slippage_total"],
            "eligible_universe_size": metrics["eligible_universe_size"],
            "avg_trade_short_borrow_rate": metrics["avg_trade_short_borrow_rate"],
        }
        scenario_comparison.append(row)
    scenario_comparison_df = pd.DataFrame(scenario_comparison).sort_values(
        "final_equity", ascending=False
    )

    for name, result in scenario_results.items():
        slug = name.replace("enhanced_", "").replace("baseline_", "").replace("__", "_")
        (output_dir / f"{slug}_trades.csv").write_text(
            result["trades"].to_csv(index=False), encoding="utf-8"
        )
        (output_dir / f"{slug}_equity.csv").write_text(
            result["equity"].reset_index().to_csv(index=False), encoding="utf-8"
        )
    (output_dir / "proxy_margin_pair_selections.csv").write_text(
        proxy_margin["selections"].to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "proxy_margin_pair_selection_summary.csv").write_text(
        selection_summary.to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "proxy_margin_universe_eligible.csv").write_text(
        proxy_margin["eligible_universe"].to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "proxy_margin_pnl_by_pair.csv").write_text(
        pnl_by_pair.to_csv(index=False), encoding="utf-8"
    )
    (output_dir / "scenario_comparison.csv").write_text(
        scenario_comparison_df.to_csv(index=False), encoding="utf-8"
    )

    summary = {
        "premises": {
            "initial_capital": enhanced_config.initial_capital,
            "requested_universe": REQUESTED_UNIVERSE,
            "available_universe": sorted(loaded_data.keys()),
            "unavailable_universe": unavailable,
            "eligible_universe": eligible_tickers,
            "excluded_after_liquidity_filter": ineligible_tickers,
            "proxy_borrow_threshold": explicit_margin_proxy_borrow_config.proxy_min_short_score,
            "frequency": "daily",
            "formation_window_days": enhanced_config.formation_window,
            "test_window_days": enhanced_config.test_window,
            "rebalance_step_days": enhanced_config.step_window,
            "entry_zscore": enhanced_config.entry_zscore,
            "exit_zscore": enhanced_config.exit_zscore,
            "stop_zscore": enhanced_config.stop_zscore,
            "max_holding_days": enhanced_config.max_holding_days,
            "max_pairs": enhanced_config.max_pairs,
            "pair_allocation_pct": enhanced_config.pair_allocation_pct,
            "selection_method": (
                "same-sector candidates, return correlation >= 0.50, OLS hedge ratio, "
                "Engle-Granger, ADF residual, half-life filter, greedy unique-asset ranking"
            ),
            "enhancements": {
                "cash_yield": (
                    "Selic diária oficial sobre caixa elegível líquido do colateral estimado"
                ),
                "dynamic_beta": (
                    f"rolling OLS hedge ratio com janela " f"{enhanced_config.rolling_beta_window}"
                ),
                "regime_filter": (
                    "bloqueia novas entradas e encerra posições quando BOVA11 "
                    "está distante demais da média móvel de 63d ou com vol acima "
                    "do percentil 75 da janela móvel"
                ),
                "explicit_margin_model": (
                    "long consome caixa, provento do short fica segregado e a ponta "
                    "vendida exige haircut adicional"
                ),
                "stressed_financing": (
                    "cenário de estresse com haircut de 100% sobre o short e "
                    "borrow proxy de 10% a.a."
                ),
                "alpha_only_variant": (
                    "mesma estratégia com margem explícita, mas sem remuneração "
                    "de caixa para isolar o alpha operacional"
                ),
                "proxy_short_borrow": (
                    "borrow proxy por ativo calibrado por liquidez e volatilidade, "
                    "com taxa anual entre 3% e 12% e filtro mínimo de short score"
                ),
            },
            "costs_enhanced": {
                "fee_rate": enhanced_config.fee_rate,
                "slippage_per_side": enhanced_config.slippage,
                "short_borrow_rate_annual": enhanced_config.short_borrow_rate_annual,
            },
            "signal_price_series": (
                "split-adjusted OHLC built from raw OHLC and Stock Splits only; "
                "dividends kept separate in P&L"
            ),
        },
        "results": scenario_metrics,
        "benchmarks": {
            "benchmark_a_bova11_buy_hold": benchmark_a_metrics,
            "benchmark_b_equal_weight_universe": benchmark_b_metrics,
            "benchmark_c_selic_only": benchmark_c_metrics,
        },
        "selected_pairs_summary": selection_summary.to_dict(orient="records"),
        "trade_audit": {
            "explicit_margin_trade_log_csv": str(
                output_dir / "explicit_margin_with_costs_trades.csv"
            ),
            "proxy_margin_trade_log_csv": str(
                output_dir / "explicit_margin_proxy_borrow_with_costs_trades.csv"
            ),
            "proxy_margin_selection_log_csv": str(output_dir / "proxy_margin_pair_selections.csv"),
            "universe_csv": str(output_dir / "proxy_margin_universe_eligible.csv"),
            "pnl_by_pair_csv": str(output_dir / "proxy_margin_pnl_by_pair.csv"),
            "scenario_comparison_csv": str(output_dir / "scenario_comparison.csv"),
        },
        "artifacts": {
            "summary_json": str(output_dir / "b3_cointegration_pairs_enhanced_summary.json"),
            "scenario_comparison_csv": str(output_dir / "scenario_comparison.csv"),
            "explicit_margin_equity_with_costs_csv": str(
                output_dir / "explicit_margin_with_costs_equity.csv"
            ),
            "proxy_margin_equity_with_costs_csv": str(
                output_dir / "explicit_margin_proxy_borrow_with_costs_equity.csv"
            ),
            "proxy_margin_no_cash_yield_equity_csv": str(
                output_dir / "explicit_margin_proxy_borrow_no_cash_yield_with_costs_equity.csv"
            ),
            "explicit_margin_no_cash_yield_equity_csv": str(
                output_dir / "explicit_margin_no_cash_yield_with_costs_equity.csv"
            ),
            "stressed_financing_equity_csv": str(
                output_dir / "explicit_margin_stressed_financing_with_costs_equity.csv"
            ),
        },
    }

    summary_path = output_dir / "b3_cointegration_pairs_enhanced_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    summary = run_scenario(argv)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
