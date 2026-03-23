"""Command line interface for backtesting."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, cast

import pandas as pd
import yaml

from .benchmarks import get_benchmark_data, get_selic_benchmark
from .bitcoin_martingale.application.datasets import DatasetCatalogService
from .bitcoin_martingale.application.montecarlo import MonteCarloSimulationService
from .bitcoin_martingale.application.optimizations import (
    OptimizationExecutionService,
    OptimizationPlanningService,
)
from .bitcoin_martingale.application.runs import RunBacktestService
from .bitcoin_martingale.application.walkforward import WalkForwardValidationService
from .bitcoin_martingale.domain.montecarlo import MonteCarloMethod, MonteCarloRequest
from .bitcoin_martingale.domain.optimizations import (
    OptimizationDirection,
    OptimizationMode,
    OptimizationRequest,
)
from .bitcoin_martingale.domain.walkforward import WalkForwardRequest
from .config import AppConfig, create_default_config, load_strategy
from .data import get_data
from .engine import BacktestEngine
from .metrics import calculate_metrics, compare_strategies, print_metrics
from .plots import create_strategy_report


def run_backtest(
    config: AppConfig,
    strategy_names: Optional[list] = None,
    plot: bool = True,
    verbose: bool = True,
) -> dict:
    """Run backtest for configured strategies.

    Args:
        config: Application configuration
        strategy_names: List of strategy names to run (None = all)
        plot: Whether to generate plots
        verbose: Whether to print progress

    Returns:
        Dictionary with results for all strategies
    """
    # Filter strategies if specified
    strategies_to_run = config.strategies
    if strategy_names:
        strategies_to_run = [s for s in config.strategies if s.name in strategy_names]

    if not strategies_to_run:
        print("No strategies to run")
        return {}

    if verbose:
        end_date = config.backtest.end_date or "today"
        print(f"Loading data from {config.backtest.start_date} to {end_date}")

    # Load data
    try:
        data = get_data(
            start=config.backtest.start_date,
            end=config.backtest.end_date,
            cache_path=config.backtest.cache_path,
        )
        if verbose:
            print(f"Loaded {len(data)} days of data")
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

    # Run backtest for each strategy
    results = {}

    for strategy_config in strategies_to_run:
        if verbose:
            print(f"\nRunning {strategy_config.name}...")

        try:
            # Load and instantiate strategy
            strategy = load_strategy(strategy_config)

            # Create backtest engine
            engine = BacktestEngine(
                initial_cash=config.backtest.initial_capital,
                apply_cash_yield=config.backtest.apply_cash_yield,
                selic_rate_annual=config.backtest.selic_rate_annual,
                yield_frequency=config.backtest.yield_frequency,
                use_real_selic=config.backtest.use_real_selic,
                selic_path=config.backtest.selic_path,
                selic_fallback_rate=config.backtest.selic_fallback_rate,
            )

            # Run backtest
            result = engine.run(data, strategy)

            # Add metadata
            result["strategy_name"] = strategy_config.name
            result["start_price"] = data.iloc[0]["Close"]
            result["end_price"] = data.iloc[-1]["Close"]

            results[strategy_config.name] = result

            if verbose:
                # Calculate and print metrics
                metrics = calculate_metrics(
                    result["equity"]["equity"],
                    result["trades"],
                    config.backtest.initial_capital,
                    total_interest_earned=result.get("total_interest_earned", 0.0),
                )
                print_metrics(metrics, strategy_config.name)

        except Exception as e:
            print(f"Error running {strategy_config.name}: {e}")
            continue

    # Generate comparison if multiple strategies
    if len(results) > 1 and verbose:
        print("\n" + "=" * 60)
        print("STRATEGY COMPARISON")
        print("=" * 60)

        comparison = compare_strategies(results, config.backtest.initial_capital)

        if not comparison.empty:
            # Select key metrics for display
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

    # Generate plots if requested
    if plot and results:
        output_dir = Path(config.backtest.output_dir)
        try:
            create_strategy_report(results, data, output_dir)
            if verbose:
                print(f"\nPlots and reports saved to {output_dir}")
        except Exception as e:
            print(f"Error generating plots: {e}")

    return results


def process_benchmarks(config: AppConfig, data: pd.DataFrame, verbose: bool = True) -> dict:
    """Process benchmarks for the backtest period.

    Args:
        config: Application configuration
        data: Price data used for backtest
        verbose: Whether to print progress

    Returns:
        Dictionary with benchmark results
    """
    benchmarks = {}
    start_date = config.backtest.start_date
    end_date = config.backtest.end_date or datetime.now().strftime("%Y-%m-%d")
    initial_capital = config.backtest.initial_capital

    # Process market benchmarks
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

                for ticker, data in benchmark_data.items():
                    benchmark_config = next(b for b in enabled_benchmarks if b.ticker == ticker)
                    benchmarks[benchmark_config.name] = {
                        "equity_curve": data["equity_curve"],
                        "metrics": data["metrics"],
                        "ticker": ticker,
                        "name": benchmark_config.name,
                    }

                    if verbose:
                        total_return = data["metrics"]["total_return"]
                        print(f"✓ {benchmark_config.name}: {total_return:.2%} return")

            except Exception as e:
                if verbose:
                    print(f"Error processing benchmarks: {e}")

    # Process SELIC benchmark
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

        except Exception as e:
            if verbose:
                print(f"Error processing SELIC benchmark: {e}")

    # Process Buy & Hold benchmark (already included in results)
    # This will be handled separately in the comparison

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
        random_seed=args.seed,
        objective=args.objective,
        direction=OptimizationDirection(args.direction),
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bitcoin Martingale Backtesting Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run backtest strategies")
    run_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file path",
    )
    run_parser.add_argument(
        "--strategies",
        "-s",
        nargs="+",
        help="Specific strategies to run (default: all)",
    )
    run_parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip plot generation",
    )
    run_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress verbose output",
    )
    run_parser.add_argument(
        "--apply-cash-yield",
        action="store_true",
        help="Enable cash yield based on SELIC rate",
    )
    run_parser.add_argument(
        "--selic-rate",
        type=float,
        default=None,
        help="Annual SELIC rate (default: 0.13)",
    )
    run_parser.add_argument(
        "--use-real-selic",
        action="store_true",
        help="Use real monthly SELIC rates from file/download",
    )
    run_parser.add_argument(
        "--selic-path",
        type=str,
        default=None,
        help="Path to SELIC data file (default: data/selic.csv)",
    )
    run_parser.add_argument(
        "--selic-fallback-rate",
        type=float,
        default=None,
        help="Annual fallback rate when real data unavailable (default: 0.13)",
    )

    # Benchmark arguments
    run_parser.add_argument(
        "--benchmarks",
        nargs="+",
        default=None,
        help="Benchmark tickers to include (e.g., '^BVSP' 'SPY' 'ETH-USD')",
    )
    run_parser.add_argument(
        "--include-selic-benchmark",
        action="store_true",
        help="Include SELIC as a benchmark",
    )
    run_parser.add_argument(
        "--exclude-buy-hold-benchmark",
        action="store_true",
        help="Exclude BTC Buy & Hold benchmark (included by default)",
    )

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize configuration")
    init_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file path to create",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file to validate",
    )

    datasets_list_parser = subparsers.add_parser(
        "datasets-list",
        help="List discovered local datasets",
    )
    datasets_list_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of datasets to display",
    )

    datasets_show_parser = subparsers.add_parser(
        "datasets-show",
        help="Show detailed metadata for one dataset",
    )
    datasets_show_parser.add_argument("--dataset-id", required=True, help="Dataset identifier")

    datasets_import_parser = subparsers.add_parser(
        "datasets-import",
        help="Import a local CSV or Parquet file into data/",
    )
    datasets_import_parser.add_argument("--source-path", required=True, help="Source dataset path")
    datasets_import_parser.add_argument(
        "--dataset-name",
        default=None,
        help="Optional destination filename or stem inside data/",
    )
    datasets_import_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing dataset if it already exists",
    )

    datasets_refresh_parser = subparsers.add_parser(
        "datasets-refresh",
        help="Refresh a supported cached dataset in place",
    )
    datasets_refresh_parser.add_argument("--dataset-id", required=True, help="Dataset identifier")
    datasets_refresh_parser.add_argument(
        "--start-date",
        default="2020-01-01",
        help="Refresh start date in YYYY-MM-DD",
    )
    datasets_refresh_parser.add_argument(
        "--end-date",
        default=None,
        help="Optional refresh end date in YYYY-MM-DD",
    )

    datasets_policy_parser = subparsers.add_parser(
        "datasets-set-refresh-policy",
        help="Persist a refresh policy for a supported dataset",
    )
    datasets_policy_parser.add_argument("--dataset-id", required=True, help="Dataset identifier")
    datasets_policy_parser.add_argument(
        "--enabled",
        dest="enabled",
        action="store_true",
        help="Enable scheduled refresh checks",
    )
    datasets_policy_parser.add_argument(
        "--disabled",
        dest="enabled",
        action="store_false",
        help="Disable scheduled refresh checks",
    )
    datasets_policy_parser.set_defaults(enabled=True)
    datasets_policy_parser.add_argument(
        "--interval-days",
        type=int,
        default=7,
        help="Days between refreshes",
    )
    datasets_policy_parser.add_argument(
        "--start-date",
        default="2020-01-01",
        help="Refresh start date in YYYY-MM-DD",
    )
    datasets_policy_parser.add_argument(
        "--end-date",
        default=None,
        help="Optional refresh end date in YYYY-MM-DD",
    )

    datasets_due_parser = subparsers.add_parser(
        "datasets-refresh-due",
        help="List or execute refreshes for datasets whose policy is due",
    )
    datasets_due_parser.add_argument(
        "--execute",
        action="store_true",
        help="Refresh due datasets instead of only listing them",
    )
    datasets_due_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on due datasets to display or refresh",
    )

    runs_list_parser = subparsers.add_parser("runs-list", help="List persisted runs")
    runs_list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of runs to display",
    )

    runs_show_parser = subparsers.add_parser("runs-show", help="Show a persisted run manifest")
    runs_show_parser.add_argument("--run-id", required=True, help="Run identifier")

    runs_config_parser = subparsers.add_parser(
        "runs-config",
        help="Show the resolved config snapshot for a persisted run",
    )
    runs_config_parser.add_argument("--run-id", required=True, help="Run identifier")

    runs_profile_parser = subparsers.add_parser(
        "runs-data-profile",
        help="Show the dataset profile for a persisted run",
    )
    runs_profile_parser.add_argument("--run-id", required=True, help="Run identifier")

    runs_export_parser = subparsers.add_parser(
        "runs-export-csv",
        help="Export persisted strategy trades to CSV",
    )
    runs_export_parser.add_argument("--run-id", required=True, help="Run identifier")
    runs_export_parser.add_argument("--strategy", required=True, help="Strategy name")
    runs_export_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output file path; defaults to stdout",
    )

    optimize_plan_parser = subparsers.add_parser(
        "optimize-plan",
        help="Preview a reproducible optimization trial plan from a JSON or YAML search space",
    )
    optimize_plan_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file path",
    )
    optimize_plan_parser.add_argument(
        "--strategies",
        "-s",
        nargs="+",
        help="Specific strategies to include in the trial plan",
    )
    optimize_plan_parser.add_argument(
        "--space-file",
        required=True,
        help="Path to a JSON or YAML file describing the search space",
    )
    optimize_plan_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in OptimizationMode],
        default=OptimizationMode.GRID.value,
        help="Whether to generate a grid or random trial plan",
    )
    optimize_plan_parser.add_argument(
        "--max-trials",
        type=int,
        default=None,
        help="Optional cap on the number of generated trials",
    )
    optimize_plan_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for random planning mode",
    )
    optimize_plan_parser.add_argument(
        "--objective",
        type=str,
        default="sharpe_ratio",
        help="Metric name used later for ranking trials",
    )
    optimize_plan_parser.add_argument(
        "--direction",
        choices=[direction.value for direction in OptimizationDirection],
        default=OptimizationDirection.MAXIMIZE.value,
        help="Whether the objective should be maximized or minimized",
    )

    optimize_run_parser = subparsers.add_parser(
        "optimize-run",
        help="Execute a persisted optimization job from a JSON or YAML search space",
    )
    optimize_run_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file path",
    )
    optimize_run_parser.add_argument(
        "--strategies",
        "-s",
        nargs="+",
        help="Specific strategies to include in the optimization job",
    )
    optimize_run_parser.add_argument(
        "--space-file",
        required=True,
        help="Path to a JSON or YAML file describing the search space",
    )
    optimize_run_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in OptimizationMode],
        default=OptimizationMode.GRID.value,
        help="Whether to generate a grid or random trial plan",
    )
    optimize_run_parser.add_argument(
        "--max-trials",
        type=int,
        default=None,
        help="Optional cap on the number of generated trials",
    )
    optimize_run_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for random planning mode",
    )
    optimize_run_parser.add_argument(
        "--objective",
        type=str,
        default="sharpe_ratio",
        help="Metric name used to rank completed trials",
    )
    optimize_run_parser.add_argument(
        "--direction",
        choices=[direction.value for direction in OptimizationDirection],
        default=OptimizationDirection.MAXIMIZE.value,
        help="Whether the objective should be maximized or minimized",
    )

    optimizations_list_parser = subparsers.add_parser(
        "optimizations-list",
        help="List persisted optimization jobs",
    )
    optimizations_list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of optimizations to display",
    )

    optimizations_show_parser = subparsers.add_parser(
        "optimizations-show",
        help="Show a persisted optimization manifest",
    )
    optimizations_show_parser.add_argument(
        "--optimization-id",
        required=True,
        help="Optimization identifier",
    )

    optimizations_results_parser = subparsers.add_parser(
        "optimizations-results",
        help="Show persisted optimization results",
    )
    optimizations_results_parser.add_argument(
        "--optimization-id",
        required=True,
        help="Optimization identifier",
    )

    walkforward_run_parser = subparsers.add_parser(
        "walkforward-run",
        help="Execute persisted walk-forward validation with rolling train/test windows",
    )
    walkforward_run_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file path",
    )
    walkforward_run_parser.add_argument(
        "--strategies",
        "-s",
        nargs="+",
        help="Specific strategies to include in validation",
    )
    walkforward_run_parser.add_argument(
        "--train-days",
        type=int,
        default=90,
        help="Number of rows in each training window",
    )
    walkforward_run_parser.add_argument(
        "--test-days",
        type=int,
        default=30,
        help="Number of rows in each test window",
    )
    walkforward_run_parser.add_argument(
        "--step-days",
        type=int,
        default=30,
        help="Rows to advance between windows",
    )

    walkforward_list_parser = subparsers.add_parser(
        "walkforward-list",
        help="List persisted walk-forward validations",
    )
    walkforward_list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of validations to display",
    )

    walkforward_show_parser = subparsers.add_parser(
        "walkforward-show",
        help="Show a persisted walk-forward manifest",
    )
    walkforward_show_parser.add_argument("--walkforward-id", required=True, help="Walk-forward id")

    walkforward_results_parser = subparsers.add_parser(
        "walkforward-results",
        help="Show persisted walk-forward results",
    )
    walkforward_results_parser.add_argument(
        "--walkforward-id",
        required=True,
        help="Walk-forward id",
    )

    montecarlo_run_parser = subparsers.add_parser(
        "montecarlo-run",
        help="Execute persisted Monte Carlo robustness analysis over trade outcomes",
    )
    montecarlo_source = montecarlo_run_parser.add_mutually_exclusive_group(required=True)
    montecarlo_source.add_argument(
        "--config",
        "-c",
        type=str,
        help="Configuration file path used to generate a fresh persisted run",
    )
    montecarlo_source.add_argument(
        "--run-id",
        type=str,
        help="Existing persisted run to analyze",
    )
    montecarlo_run_parser.add_argument(
        "--strategies",
        "-s",
        nargs="+",
        help="Specific strategies to include in the analysis",
    )
    montecarlo_run_parser.add_argument(
        "--simulations",
        type=int,
        default=500,
        help="Number of Monte Carlo simulations to run",
    )
    montecarlo_run_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic sampling",
    )
    montecarlo_run_parser.add_argument(
        "--method",
        choices=[method.value for method in MonteCarloMethod],
        default=MonteCarloMethod.BOOTSTRAP.value,
        help="Sampling method: bootstrap or shuffle",
    )
    montecarlo_run_parser.add_argument(
        "--ruin-threshold-pct",
        type=float,
        default=0.30,
        help="Drawdown threshold used to flag ruin probability",
    )

    montecarlo_list_parser = subparsers.add_parser(
        "montecarlo-list",
        help="List persisted Monte Carlo analyses",
    )
    montecarlo_list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of analyses to display",
    )

    montecarlo_show_parser = subparsers.add_parser(
        "montecarlo-show",
        help="Show a persisted Monte Carlo manifest",
    )
    montecarlo_show_parser.add_argument(
        "--montecarlo-id",
        required=True,
        help="Monte Carlo identifier",
    )

    montecarlo_results_parser = subparsers.add_parser(
        "montecarlo-results",
        help="Show persisted Monte Carlo results",
    )
    montecarlo_results_parser.add_argument(
        "--montecarlo-id",
        required=True,
        help="Monte Carlo identifier",
    )

    args = parser.parse_args()
    service = RunBacktestService()
    dataset_service = DatasetCatalogService()
    optimization_service = OptimizationExecutionService()
    walkforward_service = WalkForwardValidationService()
    montecarlo_service = MonteCarloSimulationService(run_service=service)

    if args.command == "run":
        # Load configuration
        try:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"Configuration file not found: {config_path}")
                print("Use 'init' command to create a default configuration")
                sys.exit(1)

            config = AppConfig.from_file(args.config)

            # Override config with CLI arguments
            if args.apply_cash_yield:
                config.backtest.apply_cash_yield = True
            if args.selic_rate is not None:
                config.backtest.selic_rate_annual = args.selic_rate
            if args.use_real_selic:
                config.backtest.use_real_selic = True
            if args.selic_path is not None:
                config.backtest.selic_path = args.selic_path
            if args.selic_fallback_rate is not None:
                config.backtest.selic_fallback_rate = args.selic_fallback_rate

            # Override benchmark settings with CLI arguments
            if args.benchmarks:
                from .config import BenchmarkConfig

                # Create benchmark configs from CLI arguments
                cli_benchmarks = []
                for ticker in args.benchmarks:
                    cli_benchmarks.append(
                        BenchmarkConfig(
                            ticker=ticker, name=ticker, enabled=True  # Use ticker as name for CLI
                        )
                    )
                config.backtest.benchmarks = cli_benchmarks

            if args.include_selic_benchmark:
                config.backtest.include_selic_benchmark = True

            if args.exclude_buy_hold_benchmark:
                config.backtest.include_buy_hold_benchmark = False

        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)

        # Run backtest
        results = run_backtest(
            config=config,
            strategy_names=args.strategies,
            plot=not args.no_plot,
            verbose=not args.quiet,
        )

        if not results:
            print("No strategies executed successfully")
            sys.exit(1)

        # Process benchmarks if any are configured
        benchmarks = {}
        if (
            config.backtest.benchmarks
            or config.backtest.include_selic_benchmark
            or config.backtest.include_buy_hold_benchmark
        ):

            # Load data for benchmark processing
            data = get_data(
                start=config.backtest.start_date,
                end=config.backtest.end_date,
                cache_path=config.backtest.cache_path,
            )

            benchmarks = process_benchmarks(config, data, verbose=not args.quiet)

            # Include benchmarks in comparison if enabled
            if benchmarks and not args.quiet and len(results) > 1:
                print("\n" + "=" * 60)
                print("BENCHMARK COMPARISON")
                print("=" * 60)

                for name, benchmark_data in benchmarks.items():
                    metrics = benchmark_data["metrics"]
                    print(
                        f"{name:15} | Return: {metrics['total_return']:+.2%} | "
                        f"CAGR: {metrics['cagr']:+.2%} | "
                        f"Max DD: {metrics['max_drawdown']:+.2%} | "
                        f"Sharpe: {metrics['sharpe_ratio']:.2f}"
                    )

    elif args.command == "init":
        # Create default configuration
        config_path = Path(args.config)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        default_config = create_default_config()
        default_config.to_file(args.config)

        print(f"Default configuration created at {args.config}")
        print("Edit the configuration file to customize strategies and parameters")

    elif args.command == "validate":
        # Validate configuration
        try:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"Configuration file not found: {config_path}")
                sys.exit(1)

            config = AppConfig.from_file(args.config)

            # Validate strategies can be loaded
            for strategy_config in config.strategies:
                try:
                    load_strategy(strategy_config)
                    print(f"✓ {strategy_config.name}: OK")
                except Exception as e:
                    print(f"✗ {strategy_config.name}: {e}")

            print("\nConfiguration is valid!")

        except Exception as e:
            print(f"Configuration validation failed: {e}")
            sys.exit(1)

    elif args.command == "datasets-list":
        try:
            datasets = dataset_service.list_datasets()[: args.limit]
            for dataset in datasets:
                print(
                    f"{dataset['dataset_id']} | {dataset['category']} | "
                    f"{dataset['format']} | rows={dataset['row_count']} | {dataset['path']}"
                )
        except Exception as e:
            print(f"Failed to list datasets: {e}")
            sys.exit(1)

    elif args.command == "datasets-show":
        try:
            dataset = dataset_service.get_dataset(args.dataset_id)
            print(json.dumps(dataset, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load dataset metadata: {e}")
            sys.exit(1)

    elif args.command == "datasets-import":
        try:
            dataset = dataset_service.import_dataset(
                source_path=args.source_path,
                dataset_name=args.dataset_name,
                overwrite=args.overwrite,
            )
            print(json.dumps(dataset, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to import dataset: {e}")
            sys.exit(1)

    elif args.command == "datasets-refresh":
        try:
            dataset = dataset_service.refresh_dataset(
                args.dataset_id,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            print(json.dumps(dataset, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to refresh dataset: {e}")
            sys.exit(1)

    elif args.command == "datasets-set-refresh-policy":
        try:
            dataset = dataset_service.set_refresh_policy(
                args.dataset_id,
                enabled=args.enabled,
                interval_days=args.interval_days,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            print(json.dumps(dataset, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to set dataset refresh policy: {e}")
            sys.exit(1)

    elif args.command == "datasets-refresh-due":
        try:
            if args.execute:
                refreshed = dataset_service.refresh_due_datasets(limit=args.limit)
                print(json.dumps(refreshed, indent=2, sort_keys=True))
            else:
                due_datasets = dataset_service.list_due_datasets()
                if args.limit is not None:
                    due_datasets = due_datasets[: args.limit]
                print(json.dumps(due_datasets, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to process due datasets: {e}")
            sys.exit(1)

    elif args.command == "runs-list":
        try:
            runs = service.list_runs()[: args.limit]
            for run in runs:
                strategy_names = cast(list[object], run.get("strategy_names", []))
                print(
                    f"{run['run_id']} | {run['created_at']} | "
                    f"{run['config_path']} | strategies={len(strategy_names)}"
                )
        except Exception as e:
            print(f"Failed to list runs: {e}")
            sys.exit(1)

    elif args.command == "runs-show":
        try:
            manifest = service.get_run_manifest(args.run_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load run manifest: {e}")
            sys.exit(1)

    elif args.command == "runs-config":
        try:
            config_snapshot = service.get_run_config_snapshot(args.run_id)
            print(json.dumps(config_snapshot, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load run config snapshot: {e}")
            sys.exit(1)

    elif args.command == "runs-data-profile":
        try:
            data_profile = service.get_run_data_profile(args.run_id)
            print(json.dumps(data_profile, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load run data profile: {e}")
            sys.exit(1)

    elif args.command == "runs-export-csv":
        try:
            csv_content = service.get_trades_csv(args.run_id, args.strategy)
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(csv_content, encoding="utf-8")
                print(f"CSV exported to {output_path}")
            else:
                print(csv_content, end="")
        except Exception as e:
            print(f"Failed to export trades CSV: {e}")
            sys.exit(1)

    elif args.command == "optimize-plan":
        try:
            planner = OptimizationPlanningService()
            request = build_optimization_request(args)
            plan = planner.build_plan(request)
            print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to build optimization plan: {e}")
            sys.exit(1)

    elif args.command == "optimize-run":
        try:
            request = build_optimization_request(args)
            result = optimization_service.execute(request)
            print(json.dumps(result.results_dict(), indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to execute optimization: {e}")
            sys.exit(1)

    elif args.command == "optimizations-list":
        try:
            optimizations = optimization_service.list_optimizations()[: args.limit]
            for optimization in optimizations:
                strategy_names = cast(list[object], optimization.get("strategy_names", []))
                print(
                    f"{optimization['optimization_id']} | {optimization['created_at']} | "
                    f"objective={optimization['objective']} | "
                    "completed="
                    f"{optimization['completed_trial_count']}/{optimization['trial_count']} | "
                    f"strategies={len(strategy_names)}"
                )
        except Exception as e:
            print(f"Failed to list optimizations: {e}")
            sys.exit(1)

    elif args.command == "optimizations-show":
        try:
            manifest = optimization_service.get_manifest(args.optimization_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load optimization manifest: {e}")
            sys.exit(1)

    elif args.command == "optimizations-results":
        try:
            results = optimization_service.get_results(args.optimization_id)
            print(json.dumps(results, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load optimization results: {e}")
            sys.exit(1)

    elif args.command == "walkforward-run":
        try:
            walkforward_request = WalkForwardRequest(
                config_path=args.config,
                strategy_names=args.strategies,
                train_window_days=args.train_days,
                test_window_days=args.test_days,
                step_days=args.step_days,
            )
            walkforward_results = walkforward_service.execute(walkforward_request)
            print(json.dumps(walkforward_results.results_dict(), indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to execute walk-forward validation: {e}")
            sys.exit(1)

    elif args.command == "walkforward-list":
        try:
            executions = walkforward_service.list_executions()[: args.limit]
            for execution in executions:
                strategy_names = cast(list[object], execution.get("strategy_names", []))
                print(
                    f"{execution['walkforward_id']} | {execution['created_at']} | "
                    f"windows={execution['window_count']} | "
                    f"strategies={len(strategy_names)}"
                )
        except Exception as e:
            print(f"Failed to list walk-forward validations: {e}")
            sys.exit(1)

    elif args.command == "walkforward-show":
        try:
            manifest = walkforward_service.get_manifest(args.walkforward_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load walk-forward manifest: {e}")
            sys.exit(1)

    elif args.command == "walkforward-results":
        try:
            results = walkforward_service.get_results(args.walkforward_id)
            print(json.dumps(results, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load walk-forward results: {e}")
            sys.exit(1)

    elif args.command == "montecarlo-run":
        try:
            montecarlo_request = MonteCarloRequest(
                config_path=args.config,
                run_id=args.run_id,
                strategy_names=args.strategies,
                simulation_count=args.simulations,
                random_seed=args.seed,
                method=MonteCarloMethod(args.method),
                ruin_threshold_pct=args.ruin_threshold_pct,
            )
            montecarlo_results = montecarlo_service.execute(montecarlo_request)
            print(json.dumps(montecarlo_results.results_dict(), indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to execute Monte Carlo analysis: {e}")
            sys.exit(1)

    elif args.command == "montecarlo-list":
        try:
            executions = montecarlo_service.list_executions()[: args.limit]
            for execution in executions:
                strategy_names = cast(list[object], execution.get("strategy_names", []))
                print(
                    f"{execution['montecarlo_id']} | {execution['created_at']} | "
                    f"simulations={execution['simulation_count']} | "
                    f"strategies={len(strategy_names)}"
                )
        except Exception as e:
            print(f"Failed to list Monte Carlo analyses: {e}")
            sys.exit(1)

    elif args.command == "montecarlo-show":
        try:
            manifest = montecarlo_service.get_manifest(args.montecarlo_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load Monte Carlo manifest: {e}")
            sys.exit(1)

    elif args.command == "montecarlo-results":
        try:
            results = montecarlo_service.get_results(args.montecarlo_id)
            print(json.dumps(results, indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to load Monte Carlo results: {e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
