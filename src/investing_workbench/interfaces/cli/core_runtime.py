"""Core CLI runtime helpers shared by compatibility and handler layers."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.benchmarks import get_benchmark_data, get_selic_benchmark
from src.config import AppConfig, load_strategy
from src.data import get_data
from src.engine import BacktestEngine
from src.investing_workbench.domain.optimizations import (
    OptimizationDirection,
    OptimizationMode,
    OptimizationRequest,
)
from src.metrics import calculate_metrics, compare_strategies, print_metrics
from src.plots import create_strategy_report


def run_backtest(
    config: AppConfig,
    strategy_names: Optional[list] = None,
    plot: bool = True,
    verbose: bool = True,
) -> dict:
    """Run backtest for configured strategies."""
    strategies_to_run = config.strategies
    if strategy_names:
        strategies_to_run = [s for s in config.strategies if s.name in strategy_names]

    if not strategies_to_run:
        print("No strategies to run")
        return {}

    if verbose:
        end_date = config.backtest.end_date or "today"
        print(f"Loading data from {config.backtest.start_date} to {end_date}")

    try:
        data = get_data(
            start=config.backtest.start_date,
            end=config.backtest.end_date,
            cache_path=config.backtest.cache_path,
            data_source=config.backtest.data_source,
        )
        if verbose:
            print(f"Loaded {len(data)} days of data")
    except Exception as exc:
        print(f"Error loading data: {exc}")
        return {}

    results = {}
    for strategy_config in strategies_to_run:
        if verbose:
            print(f"\nRunning {strategy_config.name}...")

        try:
            strategy = load_strategy(strategy_config)
            engine = BacktestEngine(
                initial_cash=config.backtest.initial_capital,
                apply_cash_yield=config.backtest.apply_cash_yield,
                selic_rate_annual=config.backtest.selic_rate_annual,
                yield_frequency=config.backtest.yield_frequency,
                use_real_selic=config.backtest.use_real_selic,
                selic_path=config.backtest.selic_path,
                selic_fallback_rate=config.backtest.selic_fallback_rate,
                fee_rate=config.backtest.fee_rate,
                fixed_fee=config.backtest.fixed_fee,
                buy_slippage=config.backtest.buy_slippage,
                sell_slippage=config.backtest.sell_slippage,
                max_volume_participation=config.backtest.max_volume_participation,
                allow_partial_fills=config.backtest.allow_partial_fills,
                min_fill_quantity=config.backtest.min_fill_quantity,
            )
            result = engine.run(data, strategy)
            result["strategy_name"] = strategy_config.name
            result["start_price"] = data.iloc[0]["Close"]
            result["end_price"] = data.iloc[-1]["Close"]
            results[strategy_config.name] = result

            if verbose:
                metrics = calculate_metrics(
                    result["equity"]["equity"],
                    result["trades"],
                    config.backtest.initial_capital,
                    total_interest_earned=result.get("total_interest_earned", 0.0),
                )
                print_metrics(metrics, strategy_config.name)
                execution_summary = result.get("execution_summary", {})
                if execution_summary.get("liquidity_constrained"):
                    print(
                        "Execution: "
                        f"partial_fills={execution_summary.get('partial_fill_count', 0)} | "
                        f"rejected_orders={execution_summary.get('rejected_order_count', 0)}"
                    )
                for warning in result.get("warnings", []):
                    print(f"Warning: {warning}")
        except Exception as exc:
            print(f"Error running {strategy_config.name}: {exc}")
            continue

    if len(results) > 1 and verbose:
        print("\n" + "=" * 60)
        print("STRATEGY COMPARISON")
        print("=" * 60)
        comparison = compare_strategies(results, config.backtest.initial_capital)
        if not comparison.empty:
            key_columns = [
                "Strategy",
                "total_return",
                "cagr",
                "max_drawdown",
                "sharpe_ratio",
                "total_trades",
                "hit_rate",
            ]
            display_df = comparison[key_columns].copy()
            display_df.loc[:, "total_return"] = display_df["total_return"].apply(
                lambda x: f"{x:.2%}"
            )
            display_df.loc[:, "cagr"] = display_df["cagr"].apply(lambda x: f"{x:.2%}")
            display_df.loc[:, "max_drawdown"] = display_df["max_drawdown"].apply(
                lambda x: f"{x:.2%}"
            )
            display_df.loc[:, "hit_rate"] = display_df["hit_rate"].apply(lambda x: f"{x:.2%}")
            print(display_df.to_string(index=False))

    if plot and results:
        output_dir = Path(config.backtest.output_dir)
        try:
            create_strategy_report(results, data, output_dir)
            if verbose:
                print(f"\nPlots and reports saved to {output_dir}")
        except Exception as exc:
            print(f"Error generating plots: {exc}")

    return results


def process_benchmarks(config: AppConfig, data: pd.DataFrame, verbose: bool = True) -> dict:
    """Process benchmarks for the backtest period."""
    benchmarks = {}
    start_date = config.backtest.start_date
    end_date = config.backtest.end_date or datetime.now().strftime("%Y-%m-%d")
    initial_capital = config.backtest.initial_capital

    if config.backtest.benchmarks:
        enabled_benchmarks = [b for b in config.backtest.benchmarks if b.enabled]
        if enabled_benchmarks:
            tickers = [b.ticker for b in enabled_benchmarks]
            if verbose:
                print(f"\nDownloading benchmark data for: {', '.join(tickers)}")
            try:
                benchmark_data = get_benchmark_data(
                    tickers=tickers,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    cache_dir=config.backtest.cache_path.replace("/btc_brl.parquet", ""),
                )
                for ticker, benchmark_frame in benchmark_data.items():
                    benchmark_config = next(b for b in enabled_benchmarks if b.ticker == ticker)
                    benchmarks[benchmark_config.name] = {
                        "equity_curve": benchmark_frame["equity_curve"],
                        "metrics": benchmark_frame["metrics"],
                        "ticker": ticker,
                        "name": benchmark_config.name,
                    }
                    if verbose:
                        total_return = benchmark_frame["metrics"]["total_return"]
                        print(f"✓ {benchmark_config.name}: {total_return:.2%} return")
            except Exception as exc:
                if verbose:
                    print(f"Error processing benchmarks: {exc}")

    if config.backtest.include_selic_benchmark:
        if verbose:
            print("\nProcessing SELIC benchmark...")
        try:
            selic_data = get_selic_benchmark(
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                use_real_selic=config.backtest.use_real_selic,
                selic_path=config.backtest.selic_path,
                selic_fallback_rate=config.backtest.selic_fallback_rate,
                cache_dir=config.backtest.cache_path.replace("/btc_brl.parquet", ""),
            )
            benchmarks["SELIC"] = {
                "equity_curve": selic_data["equity_curve"],
                "metrics": selic_data["metrics"],
                "ticker": "SELIC",
                "name": "SELIC",
            }
            if verbose:
                print(f"✓ SELIC: {selic_data['metrics']['total_return']:.2%} return")
        except Exception as exc:
            if verbose:
                print(f"Error processing SELIC benchmark: {exc}")

    return benchmarks


def build_optimization_request(args: argparse.Namespace) -> OptimizationRequest:
    """Build an optimization request from CLI arguments."""
    space_path = Path(args.space_file)
    if not space_path.exists():
        raise FileNotFoundError(f"Search-space file not found: {space_path}")

    raw_space = yaml.safe_load(space_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw_space, dict):
        raise ValueError("Search-space file must deserialize to a mapping")

    global_space = raw_space.get("global", raw_space)
    strategy_spaces = raw_space.get("strategies", {})

    return OptimizationRequest(
        config_path=args.config,
        strategy_names=args.strategies,
        parameter_space=global_space,
        strategy_parameter_spaces=strategy_spaces,
        mode=OptimizationMode(args.mode),
        max_trials=args.max_trials,
        random_seed=args.random_seed,
        objective=args.objective,
        direction=OptimizationDirection(args.direction),
    )
