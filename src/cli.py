"""Command line interface for backtesting."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from .benchmarks import get_benchmark_data, get_selic_benchmark
from .bitcoin_martingale.application.optimizations import OptimizationPlanningService
from .bitcoin_martingale.application.runs import RunBacktestService
from .bitcoin_martingale.domain.optimizations import OptimizationMode, OptimizationRequest
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

    args = parser.parse_args()
    service = RunBacktestService()

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

    elif args.command == "runs-list":
        try:
            runs = service.list_runs()[: args.limit]
            for run in runs:
                print(
                    f"{run['run_id']} | {run['created_at']} | "
                    f"{run['config_path']} | strategies={len(run['strategy_names'])}"
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
            space_path = Path(args.space_file)
            if not space_path.exists():
                print(f"Search-space file not found: {space_path}")
                sys.exit(1)

            raw_space = yaml.safe_load(space_path.read_text(encoding="utf-8")) or {}
            if not isinstance(raw_space, dict):
                print("Search-space file must deserialize to a mapping")
                sys.exit(1)

            global_space = raw_space.get("global", raw_space)
            strategy_spaces = raw_space.get("strategies", {})

            request = OptimizationRequest(
                config_path=args.config,
                strategy_names=args.strategies,
                parameter_space=global_space,
                strategy_parameter_spaces=strategy_spaces,
                mode=OptimizationMode(args.mode),
                max_trials=args.max_trials,
                random_seed=args.seed,
            )

            plan = planner.build_plan(request)
            print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        except Exception as e:
            print(f"Failed to build optimization plan: {e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
