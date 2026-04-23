"""Allocation planning CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.investing_workbench.domain.allocations import RebalancePlanRequest
from src.investing_workbench.interfaces.cli.services import CliServices

COMMANDS = {
    "allocations-plan",
}


def handle(args: argparse.Namespace, services: CliServices) -> None:
    """Dispatch allocation commands."""
    try:
        if args.command != "allocations-plan":
            return

        input_payload = _read_payload(args.input)
        plan = services.allocation_service.build_plan(RebalancePlanRequest.from_dict(input_payload))
        serialized = json.dumps(plan.to_dict(), indent=2, sort_keys=True)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(serialized, encoding="utf-8")
        else:
            print(serialized)
    except Exception as exc:
        print(f"Failed to process allocation command: {exc}")
        sys.exit(1)


def _read_payload(input_path: str) -> dict[str, object]:
    if input_path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(input_path).read_text(encoding="utf-8"))
