"""Compatibility CLI adapter for the next-generation interface layer."""

from __future__ import annotations

from src.investing_workbench.interfaces.cli.core_runtime import (
    build_optimization_request,
    process_benchmarks,
    run_backtest,
)
from src.investing_workbench.interfaces.cli.main import main

__all__ = [
    "build_optimization_request",
    "main",
    "process_benchmarks",
    "run_backtest",
]
