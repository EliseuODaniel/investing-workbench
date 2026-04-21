"""Core CLI handlers for run/init/validate commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.bitcoin_martingale.interfaces.cli.core_runtime import process_benchmarks, run_backtest
from src.config import (
    AppConfig,
    BenchmarkConfig,
    create_default_config,
    load_strategy,
)
from src.data import get_data

COMMANDS = {"run", "init", "validate"}


def handle(args: argparse.Namespace) -> None:
    """Dispatch core commands."""
    if args.command == "run":
        _handle_run(args)
    elif args.command == "init":
        _handle_init(args)
    elif args.command == "validate":
        _handle_validate(args)


def _handle_run(args: argparse.Namespace) -> None:
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Configuration file not found: {config_path}")
            print("Use 'init' command to create a default configuration")
            sys.exit(1)

        config = AppConfig.from_file(args.config)

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

        if args.benchmarks:
            cli_benchmarks = [
                BenchmarkConfig(ticker=ticker, name=ticker, enabled=True)
                for ticker in args.benchmarks
            ]
            config.backtest.benchmarks = cli_benchmarks

        if args.include_selic_benchmark:
            config.backtest.include_selic_benchmark = True

        if args.exclude_buy_hold_benchmark:
            config.backtest.include_buy_hold_benchmark = False

    except Exception as exc:
        print(f"Error loading configuration: {exc}")
        sys.exit(1)

    results = run_backtest(
        config=config,
        strategy_names=args.strategies,
        plot=not args.no_plot,
        verbose=not args.quiet,
    )

    if not results:
        print("No strategies executed successfully")
        sys.exit(1)

    if not (
        config.backtest.benchmarks
        or config.backtest.include_selic_benchmark
        or config.backtest.include_buy_hold_benchmark
    ):
        return

    data = get_data(
        start=config.backtest.start_date,
        end=config.backtest.end_date,
        cache_path=config.backtest.cache_path,
        data_source=config.backtest.data_source,
    )
    benchmarks = process_benchmarks(config, data, verbose=not args.quiet)

    if not (benchmarks and not args.quiet and len(results) > 1):
        return

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


def _handle_init(args: argparse.Namespace) -> None:
    config_path = Path(args.config)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = create_default_config()
    default_config.to_file(args.config)

    print(f"Default configuration created at {args.config}")
    print("Edit the configuration file to customize strategies and parameters")


def _handle_validate(args: argparse.Namespace) -> None:
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Configuration file not found: {config_path}")
            sys.exit(1)

        config = AppConfig.from_file(args.config)

        for strategy_config in config.strategies:
            try:
                load_strategy(strategy_config)
                print(f"✓ {strategy_config.name}: OK")
            except Exception as exc:
                print(f"✗ {strategy_config.name}: {exc}")

        print("\nConfiguration is valid!")

    except Exception as exc:
        print(f"Configuration validation failed: {exc}")
        sys.exit(1)
