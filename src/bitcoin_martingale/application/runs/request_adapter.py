"""Adapters for transport-specific backtest requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .dto import BacktestRunInput


def to_backtest_run_input(
    request: BacktestRunInput | Mapping[str, Any] | object,
) -> BacktestRunInput:
    """Normalize transport payloads into the application input DTO."""
    if isinstance(request, BacktestRunInput):
        return request

    payload = _to_payload(request)

    return BacktestRunInput(
        config_path=str(payload.get("config_path") or "configs/martingale.yaml"),
        strategies=_list_or_none(payload.get("strategies")),
        start_date=_str_or_none(payload.get("start_date")),
        end_date=_str_or_none(payload.get("end_date")),
        initial_capital=_float_or_none(payload.get("initial_capital")),
        base_bet=_float_or_none(payload.get("base_bet")),
        multiplier=_float_or_none(payload.get("multiplier")),
        drop_step=_float_or_none(payload.get("drop_step")),
        take_profit=_float_or_none(payload.get("take_profit")),
        max_layers=_int_or_none(payload.get("max_layers")),
        data_source=_str_or_none(payload.get("data_source")),
        cache_path=_str_or_none(payload.get("cache_path")),
        force_download=bool(payload.get("force_download", False)),
        apply_cash_yield=_bool_or_none(payload.get("apply_cash_yield")),
        selic_rate_annual=_float_or_none(payload.get("selic_rate_annual")),
        use_real_selic=_bool_or_none(payload.get("use_real_selic")),
        selic_path=_str_or_none(payload.get("selic_path")),
        selic_fallback_rate=_float_or_none(payload.get("selic_fallback_rate")),
        fee_rate=_float_or_none(payload.get("fee_rate")),
        fixed_fee=_float_or_none(payload.get("fixed_fee")),
        buy_slippage=_float_or_none(payload.get("buy_slippage")),
        sell_slippage=_float_or_none(payload.get("sell_slippage")),
        max_volume_participation=_float_or_none(payload.get("max_volume_participation")),
        allow_partial_fills=_bool_or_none(payload.get("allow_partial_fills")),
        min_fill_quantity=_float_or_none(payload.get("min_fill_quantity")),
        benchmarks=_list_or_none(payload.get("benchmarks")),
        include_selic_benchmark=_bool_or_none(payload.get("include_selic_benchmark")),
        include_buy_hold_benchmark=_bool_or_none(payload.get("include_buy_hold_benchmark")),
    )


def _to_payload(request: Mapping[str, Any] | object) -> dict[str, Any]:
    if isinstance(request, Mapping):
        return dict(request)

    model_dump = getattr(request, "model_dump", None)
    if callable(model_dump):
        payload = model_dump()
        if isinstance(payload, Mapping):
            return dict(payload)

    raise TypeError("Unsupported run request payload")


def _list_or_none(value: Any) -> list[str] | None:
    if value is None:
        return None
    return [str(item) for item in value]


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)
