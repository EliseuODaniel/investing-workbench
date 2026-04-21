"""Parser assembly for the CLI interface layer."""

from __future__ import annotations

import argparse

from src.bitcoin_martingale.domain.montecarlo import MonteCarloMethod
from src.bitcoin_martingale.domain.optimizations import OptimizationDirection, OptimizationMode


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for all supported commands."""
    parser = argparse.ArgumentParser(
        description="Bitcoin Martingale Backtesting Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    _add_core_commands(subparsers)
    _add_system_commands(subparsers)
    _add_dataset_commands(subparsers)
    _add_run_commands(subparsers)
    _add_job_commands(subparsers)
    _add_research_commands(subparsers)
    _add_pairs_commands(subparsers)
    _add_allocation_commands(subparsers)

    return parser


def _add_core_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
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

    init_parser = subparsers.add_parser("init", help="Initialize configuration")
    init_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file path to create",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="configs/martingale.yaml",
        help="Configuration file to validate",
    )


def _add_system_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    status_parser = subparsers.add_parser(
        "system-status",
        help="Show local platform status and persisted artifact counts",
    )
    status_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )


def _add_dataset_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
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


def _add_run_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
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


def _add_job_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    jobs_list_parser = subparsers.add_parser(
        "backtest-jobs-list",
        help="List persisted async backtest jobs",
    )
    jobs_list_parser.add_argument(
        "--status",
        choices=("queued", "running", "completed", "failed", "cancelled"),
        default=None,
        help="Optional status filter",
    )
    jobs_list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of jobs to display",
    )

    jobs_show_parser = subparsers.add_parser(
        "backtest-jobs-show",
        help="Show one persisted async backtest job manifest",
    )
    jobs_show_parser.add_argument("--job-id", required=True, help="Async backtest job identifier")

    jobs_worker_parser = subparsers.add_parser(
        "backtest-jobs-worker",
        help="Run a dedicated async backtest worker loop",
    )
    jobs_worker_parser.add_argument(
        "--worker-id",
        default=None,
        help="Optional explicit worker identifier",
    )
    jobs_worker_parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds to wait between queue polls when idle",
    )
    jobs_worker_parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Optional cap on jobs processed before exiting",
    )
    jobs_worker_parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one queued job and exit",
    )


def _add_research_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    experiments_list_parser = subparsers.add_parser(
        "experiments-list",
        help="List normalized experiment records across runs and research jobs",
    )
    experiments_list_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of experiment records to display",
    )
    experiments_list_parser.add_argument(
        "--type",
        dest="experiment_type",
        choices=["run", "optimization", "walkforward", "montecarlo"],
        default=None,
        help="Optional experiment type filter",
    )
    experiments_list_parser.add_argument(
        "--strategy",
        dest="strategy_name",
        default=None,
        help="Optional strategy-name filter",
    )

    experiments_show_parser = subparsers.add_parser(
        "experiments-show",
        help="Show the normalized detail payload for one persisted experiment",
    )
    experiments_show_parser.add_argument(
        "--type",
        dest="experiment_type",
        choices=["run", "optimization", "walkforward", "montecarlo"],
        required=True,
        help="Experiment type",
    )
    experiments_show_parser.add_argument(
        "--id",
        dest="experiment_id",
        required=True,
        help="Experiment identifier",
    )

    workspaces_list_parser = subparsers.add_parser(
        "research-workspaces-list",
        help="List saved research workspaces",
    )
    workspaces_list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of workspaces to display",
    )

    workspaces_show_parser = subparsers.add_parser(
        "research-workspaces-show",
        help="Show a saved research workspace manifest",
    )
    workspaces_show_parser.add_argument("--workspace-id", required=True, help="Workspace ID")

    workspaces_export_parser = subparsers.add_parser(
        "research-workspaces-export",
        help="Export one saved research workspace as markdown, html, or json",
    )
    workspaces_export_parser.add_argument("--workspace-id", required=True, help="Workspace ID")
    workspaces_export_parser.add_argument(
        "--format",
        choices=("markdown", "html", "json"),
        default="markdown",
        help="Export format",
    )
    workspaces_export_parser.add_argument(
        "--output",
        default=None,
        help="Optional file path; defaults to stdout",
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


def _add_allocation_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    allocation_plan_parser = subparsers.add_parser(
        "allocations-plan",
        help="Build a rebalance plan from a JSON allocation payload",
    )
    allocation_plan_parser.add_argument(
        "--input",
        required=True,
        help="Input JSON payload path, or '-' to read from stdin",
    )
    allocation_plan_parser.add_argument(
        "--output",
        default=None,
        help="Optional output path; defaults to stdout",
    )


def _add_pairs_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--preset",
        dest="preset_id",
        default="ibov_proxy",
        help="Curated universe preset id",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=None,
        help="Optional custom B3 tickers to use instead of the preset",
    )
    parser.add_argument(
        "--start-date",
        default="2021-01-01",
        help="Start date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Optional end date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--as-of-date",
        default=None,
        help="Optional logical as-of date for universe resolution",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force B3 data refresh before screening or backtesting",
    )
    parser.add_argument(
        "--min-price",
        type=float,
        default=5.0,
        help="Minimum acceptable asset price",
    )
    parser.add_argument(
        "--min-median-notional-brl",
        type=float,
        default=90000000.0,
        help="Minimum median daily notional in BRL",
    )
    parser.add_argument(
        "--use-proxy-short-borrow",
        dest="use_proxy_short_borrow",
        action="store_true",
        help="Filter with proxy short-borrow heuristics",
    )
    parser.add_argument(
        "--disable-proxy-short-borrow",
        dest="use_proxy_short_borrow",
        action="store_false",
        help="Disable proxy short-borrow heuristics",
    )
    parser.set_defaults(use_proxy_short_borrow=True)
    parser.add_argument(
        "--proxy-min-short-score",
        type=float,
        default=0.35,
        help="Minimum proxy short score",
    )
    parser.add_argument(
        "--proxy-borrow-base-rate",
        dest="proxy_borrow_base_rate_annual",
        type=float,
        default=0.03,
        help="Base annual proxy borrow rate",
    )
    parser.add_argument(
        "--proxy-borrow-max-rate",
        dest="proxy_borrow_max_rate_annual",
        type=float,
        default=0.12,
        help="Max annual proxy borrow rate",
    )
    parser.add_argument(
        "--borrow-snapshot-path",
        default=None,
        help="Optional local CSV with ticker borrow overrides",
    )


def _add_pairs_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    universes_parser = subparsers.add_parser(
        "pairs-universes",
        help="List curated B3 pairs-trading universe presets",
    )
    universes_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )

    snapshots_list_parser = subparsers.add_parser(
        "pairs-ibov-snapshots",
        help="List cached official IBOV snapshots",
    )
    snapshots_list_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )

    snapshots_show_parser = subparsers.add_parser(
        "pairs-ibov-snapshot-show",
        help="Show one cached official IBOV snapshot",
    )
    snapshots_show_parser.add_argument("--as-of-date", required=True)

    snapshots_backfill_parser = subparsers.add_parser(
        "pairs-ibov-snapshots-backfill",
        help="Backfill official IBOV snapshots around rebalance dates",
    )
    snapshots_backfill_parser.add_argument("--start-date", required=True)
    snapshots_backfill_parser.add_argument("--end-date", required=True)
    snapshots_backfill_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Refresh cached snapshots even when they already exist",
    )

    universe_resolve_parser = subparsers.add_parser(
        "pairs-universe-resolve",
        help="Resolve one B3 universe and print quality diagnostics",
    )
    _add_pairs_common_args(universe_resolve_parser)

    screener_parser = subparsers.add_parser(
        "pairs-screen",
        help="Screen candidate B3 pairs by cointegration, half-life, and liquidity",
    )
    _add_pairs_common_args(screener_parser)
    screener_parser.add_argument("--formation-window", type=int, default=252)
    screener_parser.add_argument("--test-window", type=int, default=21)
    screener_parser.add_argument("--max-pairs", type=int, default=3)
    screener_parser.add_argument("--top-n", type=int, default=20)
    screener_parser.add_argument("--min-return-corr", type=float, default=0.25)
    screener_parser.add_argument("--max-coint-pvalue", type=float, default=0.10)
    screener_parser.add_argument("--min-half-life", type=float, default=2.0)
    screener_parser.add_argument("--max-half-life", type=float, default=60.0)
    screener_parser.add_argument(
        "--require-cointegration",
        dest="require_cointegration",
        action="store_true",
    )
    screener_parser.add_argument(
        "--allow-non-coint",
        dest="require_cointegration",
        action="store_false",
    )
    screener_parser.set_defaults(require_cointegration=True)

    backtest_parser = subparsers.add_parser(
        "pairs-backtest",
        help="Execute and persist one B3 pairs-trading scenario",
    )
    _add_pairs_common_args(backtest_parser)
    _add_pairs_backtest_args(backtest_parser)

    batch_parser = subparsers.add_parser(
        "pairs-backtest-batch",
        help="Execute and persist a default multi-scenario B3 pairs batch",
    )
    _add_pairs_common_args(batch_parser)
    _add_pairs_backtest_args(batch_parser)

    backtest_job_parser = subparsers.add_parser(
        "pairs-backtest-job",
        help="Queue one async B3 pairs-trading scenario",
    )
    _add_pairs_common_args(backtest_job_parser)
    _add_pairs_backtest_args(backtest_job_parser)

    batch_job_parser = subparsers.add_parser(
        "pairs-backtest-job-batch",
        help="Queue one async B3 pairs-trading batch",
    )
    _add_pairs_common_args(batch_job_parser)
    _add_pairs_backtest_args(batch_job_parser)

    jobs_list_parser = subparsers.add_parser(
        "pairs-backtest-jobs-list",
        help="List persisted async pairs backtest jobs",
    )
    jobs_list_parser.add_argument(
        "--status",
        choices=("queued", "running", "completed", "failed", "cancelled"),
        default=None,
        help="Optional status filter",
    )
    jobs_list_parser.add_argument("--limit", type=int, default=10)

    jobs_show_parser = subparsers.add_parser(
        "pairs-backtest-jobs-show",
        help="Show one persisted async pairs backtest job manifest",
    )
    jobs_show_parser.add_argument("--job-id", required=True)

    jobs_worker_parser = subparsers.add_parser(
        "pairs-backtest-jobs-worker",
        help="Run a dedicated async pairs backtest worker loop",
    )
    jobs_worker_parser.add_argument("--worker-id", default=None)
    jobs_worker_parser.add_argument("--poll-interval", type=float, default=2.0)
    jobs_worker_parser.add_argument("--max-jobs", type=int, default=None)
    jobs_worker_parser.add_argument("--once", action="store_true")

    list_parser = subparsers.add_parser(
        "pairs-backtests-list",
        help="List persisted B3 pairs-trading manifests",
    )
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )

    show_parser = subparsers.add_parser(
        "pairs-backtests-show",
        help="Show one persisted B3 pairs-trading manifest",
    )
    show_parser.add_argument("--pairs-backtest-id", required=True)

    results_parser = subparsers.add_parser(
        "pairs-backtests-results",
        help="Show one persisted B3 pairs-trading result set",
    )
    results_parser.add_argument("--pairs-backtest-id", required=True)


def _add_pairs_backtest_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--formation-window", type=int, default=252)
    parser.add_argument("--test-window", type=int, default=21)
    parser.add_argument("--step-window", type=int, default=21)
    parser.add_argument("--entry-zscore", type=float, default=2.0)
    parser.add_argument("--exit-zscore", type=float, default=0.5)
    parser.add_argument("--stop-zscore", type=float, default=4.0)
    parser.add_argument("--max-holding-days", type=int, default=30)
    parser.add_argument("--max-pairs", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--pair-allocation-pct", type=float, default=0.30)
    parser.add_argument("--initial-capital", type=float, default=100000.0)
    parser.add_argument("--min-return-corr", type=float, default=0.25)
    parser.add_argument("--max-coint-pvalue", type=float, default=0.10)
    parser.add_argument("--min-half-life", type=float, default=2.0)
    parser.add_argument("--max-half-life", type=float, default=60.0)
    parser.add_argument("--zscore-window", type=int, default=60)
    parser.add_argument("--fee-rate", type=float, default=0.0003)
    parser.add_argument("--slippage", type=float, default=0.0005)
    parser.add_argument("--short-borrow-rate-annual", type=float, default=0.05)
    parser.add_argument("--apply-cash-yield", action="store_true")
    parser.add_argument("--use-real-selic", action="store_true")
    parser.add_argument("--selic-path", default="data/selic_daily.csv")
    parser.add_argument("--selic-fallback-rate", type=float, default=0.13)
    parser.add_argument("--cash-collateral-ratio", type=float, default=1.0)
    parser.add_argument("--explicit-margin-model", action="store_true")
    parser.add_argument("--short-margin-haircut", type=float, default=0.50)
    parser.add_argument("--dynamic-beta", action="store_true")
    parser.add_argument("--rolling-beta-window", type=int, default=60)
    parser.add_argument(
        "--regime-filter",
        choices=("none", "ma_deviation_and_vol"),
        default="none",
    )
    parser.add_argument("--regime-ma-window", type=int, default=63)
    parser.add_argument("--regime-max-deviation", type=float, default=0.08)
    parser.add_argument("--regime-vol-window", type=int, default=21)
    parser.add_argument("--regime-vol-lookback", type=int, default=252)
    parser.add_argument("--regime-vol-quantile", type=float, default=0.75)
    parser.add_argument(
        "--portfolio-construction",
        choices=("equal_notional", "risk_parity"),
        default="equal_notional",
    )
    parser.add_argument("--target-pair-volatility-annual", type=float, default=0.18)
    parser.add_argument("--max-gross-exposure-pct", type=float, default=1.50)
    parser.add_argument("--max-net-exposure-pct", type=float, default=0.20)
    parser.add_argument("--max-sector-pairs", type=int, default=1)
    parser.add_argument(
        "--benchmark-ids",
        nargs="+",
        default=None,
        help="Optional benchmark ids such as BOVA11.SA ^BVSP equal_weight selic_cash",
    )
    parser.add_argument(
        "--require-cointegration",
        dest="require_cointegration",
        action="store_true",
    )
    parser.add_argument(
        "--allow-non-coint",
        dest="require_cointegration",
        action="store_false",
    )
    parser.set_defaults(require_cointegration=True)
