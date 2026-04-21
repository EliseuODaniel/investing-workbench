"""Configuration helpers for async backtest job execution."""

from __future__ import annotations

import os
from dataclasses import dataclass

VALID_EXECUTION_MODES = {"inline", "detached"}


@dataclass(frozen=True)
class BacktestJobSettings:
    """Settings that control how async backtest jobs are executed."""

    execution_mode: str = "inline"
    max_workers: int = 2
    resume_interrupted_jobs: bool = True


def load_backtest_job_settings_from_env() -> BacktestJobSettings:
    """Load async backtest job settings from environment variables."""
    execution_mode = (
        os.getenv(
            "BITCOIN_MARTINGALE_BACKTEST_JOB_EXECUTION_MODE",
            "inline",
        )
        .strip()
        .lower()
    )
    if execution_mode not in VALID_EXECUTION_MODES:
        raise ValueError(
            "BITCOIN_MARTINGALE_BACKTEST_JOB_EXECUTION_MODE must be 'inline' or 'detached'"
        )

    max_workers = _read_int_env("BITCOIN_MARTINGALE_BACKTEST_JOB_MAX_WORKERS", default=2)
    resume_interrupted_jobs = _read_bool_env(
        "BITCOIN_MARTINGALE_BACKTEST_JOB_RESUME_INTERRUPTED",
        default=True,
    )

    return BacktestJobSettings(
        execution_mode=execution_mode,
        max_workers=max_workers,
        resume_interrupted_jobs=resume_interrupted_jobs,
    )


def _read_int_env(name: str, *, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    value = int(raw)
    return max(1, value)


def _read_bool_env(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}
