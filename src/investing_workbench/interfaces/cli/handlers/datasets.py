"""Dataset-related CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys

from src.investing_workbench.interfaces.cli.services import CliServices

COMMANDS = {
    "datasets-list",
    "datasets-show",
    "datasets-import",
    "datasets-refresh",
    "datasets-set-refresh-policy",
    "datasets-refresh-due",
}


def handle(args: argparse.Namespace, services: CliServices) -> None:
    """Dispatch dataset commands."""
    try:
        if args.command == "datasets-list":
            datasets = services.dataset_service.list_datasets()[: args.limit]
            for dataset in datasets:
                print(
                    f"{dataset['dataset_id']} | {dataset['category']} | "
                    f"{dataset['format']} | rows={dataset['row_count']} | {dataset['path']}"
                )
        elif args.command == "datasets-show":
            dataset = services.dataset_service.get_dataset(args.dataset_id)
            print(json.dumps(dataset, indent=2, sort_keys=True))
        elif args.command == "datasets-import":
            dataset = services.dataset_service.import_dataset(
                source_path=args.source_path,
                dataset_name=args.dataset_name,
                overwrite=args.overwrite,
            )
            print(json.dumps(dataset, indent=2, sort_keys=True))
        elif args.command == "datasets-refresh":
            dataset = services.dataset_service.refresh_dataset(
                args.dataset_id,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            print(json.dumps(dataset, indent=2, sort_keys=True))
        elif args.command == "datasets-set-refresh-policy":
            dataset = services.dataset_service.set_refresh_policy(
                args.dataset_id,
                enabled=args.enabled,
                interval_days=args.interval_days,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            print(json.dumps(dataset, indent=2, sort_keys=True))
        elif args.command == "datasets-refresh-due":
            if args.execute:
                refreshed = services.dataset_service.refresh_due_datasets(limit=args.limit)
                print(json.dumps(refreshed, indent=2, sort_keys=True))
            else:
                due_datasets = services.dataset_service.list_due_datasets()
                if args.limit is not None:
                    due_datasets = due_datasets[: args.limit]
                print(json.dumps(due_datasets, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"Failed to process dataset command: {exc}")
        sys.exit(1)
