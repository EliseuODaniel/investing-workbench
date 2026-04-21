"""Persisted run CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from src.bitcoin_martingale.interfaces.cli.services import CliServices

COMMANDS = {
    "runs-list",
    "runs-show",
    "runs-config",
    "runs-data-profile",
    "runs-export-csv",
}


def handle(args: argparse.Namespace, services: CliServices) -> None:
    """Dispatch persisted run commands."""
    try:
        if args.command == "runs-list":
            runs = services.run_service.list_runs()[: args.limit]
            for run in runs:
                strategy_names = cast(list[object], run.get("strategy_names", []))
                print(
                    f"{run['run_id']} | {run['created_at']} | "
                    f"{run['config_path']} | strategies={len(strategy_names)}"
                )
        elif args.command == "runs-show":
            manifest = services.run_service.get_run_manifest(args.run_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        elif args.command == "runs-config":
            config_snapshot = services.run_service.get_run_config_snapshot(args.run_id)
            print(json.dumps(config_snapshot, indent=2, sort_keys=True))
        elif args.command == "runs-data-profile":
            data_profile = services.run_service.get_run_data_profile(args.run_id)
            print(json.dumps(data_profile, indent=2, sort_keys=True))
        elif args.command == "runs-export-csv":
            csv_content = services.run_service.get_trades_csv(args.run_id, args.strategy)
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(csv_content, encoding="utf-8")
                print(f"CSV exported to {output_path}")
            else:
                print(csv_content, end="")
    except Exception as exc:
        print(f"Failed to process run command: {exc}")
        sys.exit(1)
