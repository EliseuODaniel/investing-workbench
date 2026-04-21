"""Quality checks for persisted run artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def inspect_run_quality(
    *,
    config_snapshot: Mapping[str, Any] | None,
    response_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Return a quality issue for persisted runs that should not be trusted."""
    if not config_snapshot or not response_payload:
        return None

    backtest = config_snapshot.get("backtest")
    if not isinstance(backtest, Mapping):
        return None

    if not backtest.get("apply_cash_yield") or not backtest.get("use_real_selic"):
        return None

    results = response_payload.get("results")
    if not isinstance(results, Mapping):
        return None

    highest_monthly_rate = 0.0
    rate_sample_count = 0
    for strategy_payload in results.values():
        if not isinstance(strategy_payload, Mapping):
            continue
        metrics = strategy_payload.get("metrics")
        if not isinstance(metrics, Mapping):
            continue
        rates_used = metrics.get("selic_rates_used")
        if not isinstance(rates_used, list):
            continue
        for entry in rates_used:
            if not isinstance(entry, Mapping):
                continue
            try:
                monthly_rate = float(entry.get("rate", 0.0) or 0.0)
            except (TypeError, ValueError):
                continue
            highest_monthly_rate = max(highest_monthly_rate, monthly_rate)
            rate_sample_count += 1

    if rate_sample_count == 0 or highest_monthly_rate <= 0.03:
        return None

    return {
        "status": "legacy_invalid",
        "code": "selic_monthly_cache_bug",
        "title": "Run legado invalidado",
        "message": (
            "Este resultado foi gerado com uma versao antiga da SELIC mensal real, "
            "o que inflou o rendimento do caixa e distorceu as metricas. Reexecute "
            "o estudo com o modelo atual antes de comparar estrategias."
        ),
        "details": {
            "max_monthly_selic_rate": highest_monthly_rate,
            "sample_count": rate_sample_count,
        },
    }
