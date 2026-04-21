"""CLI entrypoint for the next-generation interface layer."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence

from src.bitcoin_martingale.infrastructure.logging import configure_logging
from src.bitcoin_martingale.interfaces.cli.handlers import (
    allocations,
    core,
    datasets,
    jobs,
    pairs,
    research,
    runs,
    system,
)
from src.bitcoin_martingale.interfaces.cli.parser import build_parser
from src.bitcoin_martingale.interfaces.cli.services import CliServices, build_services


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entry point."""
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    services = build_services()

    if _dispatch_core(args.command, args):
        return
    if _dispatch_services(args.command, args, services):
        return

    parser.print_help()


def _dispatch_core(command: str | None, args: argparse.Namespace) -> bool:
    if command not in core.COMMANDS:
        return False
    core.handle(args)
    return True


def _dispatch_services(
    command: str | None,
    args: argparse.Namespace,
    services: CliServices,
) -> bool:
    handler_map: dict[str, Callable[[argparse.Namespace, CliServices], None]] = {
        **{name: system.handle for name in system.COMMANDS},
        **{name: datasets.handle for name in datasets.COMMANDS},
        **{name: runs.handle for name in runs.COMMANDS},
        **{name: jobs.handle for name in jobs.COMMANDS},
        **{name: research.handle for name in research.COMMANDS},
        **{name: pairs.handle for name in pairs.COMMANDS},
        **{name: allocations.handle for name in allocations.COMMANDS},
    }
    handler = handler_map.get(command or "")
    if handler is None:
        return False
    handler(args, services)
    return True
