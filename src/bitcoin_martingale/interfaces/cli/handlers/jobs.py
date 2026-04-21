"""Async backtest job CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys

from src.bitcoin_martingale.interfaces.cli.services import CliServices

COMMANDS = {"backtest-jobs-list", "backtest-jobs-show", "backtest-jobs-worker"}


def handle(args: argparse.Namespace, services: CliServices) -> None:
    """Dispatch async backtest job commands."""
    try:
        if args.command == "backtest-jobs-list":
            jobs = services.backtest_job_service.list_jobs(
                status=args.status,
                limit=args.limit,
            )
            print(json.dumps(jobs, indent=2, sort_keys=True))
            return

        if args.command == "backtest-jobs-show":
            job = services.backtest_job_service.get_job(args.job_id)
            print(json.dumps(job, indent=2, sort_keys=True))
            return

        if args.command == "backtest-jobs-worker":
            summary = services.backtest_job_service.run_worker_loop(
                worker_id=args.worker_id,
                once=args.once,
                poll_interval_seconds=args.poll_interval,
                max_jobs=args.max_jobs,
            )
            print(json.dumps(summary, indent=2, sort_keys=True))
            return
    except KeyboardInterrupt:
        print("Backtest job worker stopped by user.")
        sys.exit(130)
    except Exception as exc:
        print(f"Failed to process backtest job command: {exc}")
        sys.exit(1)
