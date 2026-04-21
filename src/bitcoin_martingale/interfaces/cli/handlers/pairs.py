"""CLI handlers for B3 pairs-trading workflows."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.bitcoin_martingale.interfaces.cli.services import CliServices

COMMANDS = {
    "pairs-universes",
    "pairs-ibov-snapshots",
    "pairs-ibov-snapshot-show",
    "pairs-ibov-snapshots-backfill",
    "pairs-universe-resolve",
    "pairs-screen",
    "pairs-backtest",
    "pairs-backtest-batch",
    "pairs-backtest-job",
    "pairs-backtest-job-batch",
    "pairs-backtest-jobs-list",
    "pairs-backtest-jobs-show",
    "pairs-backtest-jobs-worker",
    "pairs-backtests-list",
    "pairs-backtests-show",
    "pairs-backtests-results",
}


def handle(args: argparse.Namespace, services: CliServices) -> None:
    """Dispatch pairs-trading CLI commands."""
    try:
        payload: Any
        if args.command == "pairs-universes":
            payload = services.pairs_trading_service.list_universe_presets()
            if args.format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                for item in payload:
                    print(
                        f"{item['preset_id']} | tickers={item['ticker_count']} | "
                        f"{item['label']}"
                    )
        elif args.command == "pairs-ibov-snapshots":
            payload = services.pairs_trading_service.list_ibov_snapshots()
            if args.format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                for item in payload:
                    print(
                        f"{item['as_of_date']} | tickers={item['ticker_count']} | "
                        f"{item.get('validity_label') or 'n/a'}"
                    )
        elif args.command == "pairs-ibov-snapshot-show":
            payload = services.pairs_trading_service.get_ibov_snapshot(as_of_date=args.as_of_date)
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-ibov-snapshots-backfill":
            payload = services.pairs_trading_service.backfill_ibov_snapshots(
                start_date=args.start_date,
                end_date=args.end_date,
                force_refresh=args.force_refresh,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-universe-resolve":
            payload = services.pairs_trading_service.resolve_universe(
                **_pairs_common_kwargs(args),
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-screen":
            payload = services.pairs_trading_service.screen_pairs(
                **_pairs_screen_kwargs(args),
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtest":
            payload = services.pairs_trading_service.run_backtest(
                **_pairs_backtest_kwargs(args),
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtest-batch":
            payload = services.pairs_trading_service.run_batch(
                **_pairs_backtest_kwargs(args),
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtest-job":
            payload = services.pairs_backtest_job_service.create_job(
                _pairs_backtest_kwargs(args),
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtest-job-batch":
            payload = services.pairs_backtest_job_service.create_job(
                _pairs_backtest_kwargs(args),
                batch_mode=True,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtest-jobs-list":
            payload = services.pairs_backtest_job_service.list_jobs(
                status=args.status,
                limit=args.limit,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtest-jobs-show":
            payload = services.pairs_backtest_job_service.get_job(args.job_id)
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtest-jobs-worker":
            payload = services.pairs_backtest_job_service.run_worker_loop(
                worker_id=args.worker_id,
                once=args.once,
                poll_interval_seconds=args.poll_interval,
                max_jobs=args.max_jobs,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtests-list":
            payload = services.pairs_trading_service.list_backtests()[: args.limit]
            if args.format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                for item in payload:
                    print(
                        f"{item['pairs_backtest_id']} | {item['created_at']} | "
                        f"scenarios={item['scenario_count']} | preset={item['preset_id']}"
                    )
        elif args.command == "pairs-backtests-show":
            payload = services.pairs_trading_service.get_manifest(args.pairs_backtest_id)
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "pairs-backtests-results":
            payload = services.pairs_trading_service.get_results(args.pairs_backtest_id)
            print(json.dumps(payload, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"Failed to process pairs command: {exc}")
        sys.exit(1)


def _pairs_common_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "preset_id": args.preset_id,
        "tickers": args.tickers,
        "as_of_date": args.as_of_date,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "force_download": args.force_download,
        "min_price": args.min_price,
        "min_median_notional_brl": args.min_median_notional_brl,
        "use_proxy_short_borrow": args.use_proxy_short_borrow,
        "proxy_min_short_score": args.proxy_min_short_score,
        "proxy_borrow_base_rate_annual": args.proxy_borrow_base_rate_annual,
        "proxy_borrow_max_rate_annual": args.proxy_borrow_max_rate_annual,
        "borrow_snapshot_path": args.borrow_snapshot_path,
    }


def _pairs_screen_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    payload = _pairs_common_kwargs(args)
    payload.update(
        {
            "formation_window": args.formation_window,
            "test_window": args.test_window,
            "max_pairs": args.max_pairs,
            "top_n": args.top_n,
            "min_return_corr": args.min_return_corr,
            "max_coint_pvalue": args.max_coint_pvalue,
            "min_half_life": args.min_half_life,
            "max_half_life": args.max_half_life,
            "require_cointegration": args.require_cointegration,
        }
    )
    return payload


def _pairs_backtest_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    payload = _pairs_screen_kwargs(args)
    payload.update(
        {
            "step_window": args.step_window,
            "entry_zscore": args.entry_zscore,
            "exit_zscore": args.exit_zscore,
            "stop_zscore": args.stop_zscore,
            "max_holding_days": args.max_holding_days,
            "pair_allocation_pct": args.pair_allocation_pct,
            "initial_capital": args.initial_capital,
            "zscore_window": args.zscore_window,
            "fee_rate": args.fee_rate,
            "slippage": args.slippage,
            "short_borrow_rate_annual": args.short_borrow_rate_annual,
            "apply_cash_yield": args.apply_cash_yield,
            "use_real_selic": args.use_real_selic,
            "selic_path": args.selic_path,
            "selic_fallback_rate": args.selic_fallback_rate,
            "cash_collateral_ratio": args.cash_collateral_ratio,
            "explicit_margin_model": args.explicit_margin_model,
            "short_margin_haircut": args.short_margin_haircut,
            "dynamic_beta": args.dynamic_beta,
            "rolling_beta_window": args.rolling_beta_window,
            "regime_filter": args.regime_filter,
            "regime_ma_window": args.regime_ma_window,
            "regime_max_deviation": args.regime_max_deviation,
            "regime_vol_window": args.regime_vol_window,
            "regime_vol_lookback": args.regime_vol_lookback,
            "regime_vol_quantile": args.regime_vol_quantile,
            "portfolio_construction": args.portfolio_construction,
            "target_pair_volatility_annual": args.target_pair_volatility_annual,
            "max_gross_exposure_pct": args.max_gross_exposure_pct,
            "max_net_exposure_pct": args.max_net_exposure_pct,
            "max_sector_pairs": args.max_sector_pairs,
            "benchmark_ids": args.benchmark_ids,
        }
    )
    return payload
