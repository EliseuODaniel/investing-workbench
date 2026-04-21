"""System and status CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TypedDict, cast

from src.bitcoin_martingale.interfaces.cli.services import CliServices

COMMANDS = {"system-status"}


class ArtifactCountsPayload(TypedDict):
    runs: int
    optimizations: int
    walkforward: int
    montecarlo: int
    research_workspaces: int
    allocation_workspaces: int


class SystemStatusPayload(TypedDict):
    status: str
    config_count: int
    dataset_count: int
    due_dataset_count: int
    artifact_counts: ArtifactCountsPayload
    job_counts: dict[str, int]
    job_runtime: dict[str, object]
    latest_backtest_job_id: str | None
    latest_run_id: str | None
    latest_research_workspace_id: str | None
    warnings: list[str]


def handle(args: argparse.Namespace, services: CliServices) -> None:
    """Dispatch system-level commands."""
    try:
        if args.command != "system-status":
            return

        payload = cast(SystemStatusPayload, services.system_status_service.get_status())
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True))
            return

        artifact_counts = payload["artifact_counts"]
        print(
            f"status={payload['status']} | configs={payload['config_count']} | "
            f"datasets={payload['dataset_count']} | due_datasets={payload['due_dataset_count']}"
        )
        print(
            "artifacts="
            f"runs:{artifact_counts['runs']} "
            f"opt:{artifact_counts['optimizations']} "
            f"wf:{artifact_counts['walkforward']} "
            f"mc:{artifact_counts['montecarlo']} "
            f"research_ws:{artifact_counts['research_workspaces']} "
            f"allocation_ws:{artifact_counts['allocation_workspaces']}"
        )
        job_counts = payload["job_counts"]
        job_runtime = payload["job_runtime"]
        print(
            "jobs="
            f"queued:{job_counts['queued']} "
            f"running:{job_counts['running']} "
            f"completed:{job_counts['completed']} "
            f"failed:{job_counts['failed']} "
            f"cancelled:{job_counts['cancelled']}"
        )
        print(
            "job_runtime="
            f"mode:{job_runtime.get('execution_mode', 'inline')} "
            f"active:{job_runtime.get('active_futures', 0)} "
            f"max_workers:{job_runtime.get('max_workers', 0)}"
        )
        if payload.get("latest_backtest_job_id"):
            print(f"latest_job={payload['latest_backtest_job_id']}")
        if payload.get("latest_run_id"):
            print(f"latest_run={payload['latest_run_id']}")
        if payload.get("latest_research_workspace_id"):
            print(f"latest_research_workspace={payload['latest_research_workspace_id']}")
        for warning in payload["warnings"]:
            print(f"warning={warning}")
    except Exception as exc:
        print(f"Failed to process system command: {exc}")
        sys.exit(1)
