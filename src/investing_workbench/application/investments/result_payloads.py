"""Helpers for investment result payload construction and chart math."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_models import SimulationResult


def build_result_payload(
    *,
    result: SimulationResult,
    inflation_curve: pd.Series,
    instrument_map: dict[str, Any],
) -> dict[str, Any]:
    """Build a normalized result payload with nominal and real variants."""

    payload = result.to_payload()
    real_equity_curve = deflate_curve(result.equity_curve, inflation_curve)
    real_flow_curve = deflate_curve(result.flow_curve, inflation_curve)
    real_metrics = summarize_curves(real_equity_curve, real_flow_curve)
    net_curve = result.net_liquidation_curve
    net_metrics = summarize_curves(net_curve, result.flow_curve) if net_curve is not None else None
    real_net_metrics = (
        summarize_curves(deflate_curve(net_curve, inflation_curve), real_flow_curve)
        if net_curve is not None
        else None
    )
    component_breakdown = build_component_breakdown(
        result=result,
        instrument_map=instrument_map,
    )
    payload.update(
        {
            "invested_total_real": real_metrics["invested_total"],
            "final_value_real": real_metrics["final_value"],
            "net_profit_real": real_metrics["net_profit"],
            "real_total_return_on_invested": (
                float(real_metrics["final_value"] / real_metrics["invested_total"] - 1.0)
                if real_metrics["invested_total"] > 0
                else 0.0
            ),
            "real_time_weighted_return": real_metrics["time_weighted_return"],
            "real_cagr": real_metrics["cagr"],
            "final_value_net": (
                net_metrics["final_value"] if net_metrics is not None else result.final_value
            ),
            "net_profit_net": (
                net_metrics["net_profit"] if net_metrics is not None else result.net_profit
            ),
            "cagr_net": net_metrics["cagr"] if net_metrics is not None else result.cagr,
            "final_value_real_net": (
                real_net_metrics["final_value"]
                if real_net_metrics is not None
                else real_metrics["final_value"]
            ),
            "net_profit_real_net": (
                real_net_metrics["net_profit"]
                if real_net_metrics is not None
                else real_metrics["net_profit"]
            ),
            "real_cagr_net": (
                real_net_metrics["cagr"] if real_net_metrics is not None else real_metrics["cagr"]
            ),
            "component_breakdown": component_breakdown,
            "category_breakdown": build_category_breakdown(
                component_breakdown=component_breakdown,
                total_value=result.final_value,
            ),
        }
    )
    return payload


def build_benchmark_payload(
    benchmark_entry: dict[str, Any],
    inflation_curve: pd.Series,
    instrument_map: dict[str, Any],
) -> dict[str, Any]:
    """Build benchmark payload with chart serialization."""

    result: SimulationResult = benchmark_entry["result"]
    payload = build_result_payload(
        result=result,
        inflation_curve=inflation_curve,
        instrument_map=instrument_map,
    )
    payload["benchmark_id"] = benchmark_entry["benchmark_id"]
    payload["label"] = benchmark_entry["label"]
    payload["equity_curve"] = serialize_curve(result.equity_curve)
    return payload


def build_component_breakdown(
    *,
    result: SimulationResult,
    instrument_map: dict[str, Any],
) -> list[dict[str, Any]]:
    if not result.instrument.components or not result.component_values:
        return []

    total_value = max(result.final_value, 1e-9)
    total_target = sum(weight for _, weight in result.instrument.components) or 1.0
    breakdown: list[dict[str, Any]] = []
    for component_id, weight in result.instrument.components:
        component_meta = instrument_map.get(component_id)
        if component_meta is None:
            continue
        component_value = float(result.component_values.get(component_id, 0.0))
        breakdown.append(
            {
                "component_id": component_id,
                "label": component_meta.label,
                "category_id": component_meta.category_id,
                "category_label": component_meta.category_label,
                "target_weight": float(weight / total_target),
                "ending_weight": float(component_value / total_value),
                "final_value": component_value,
            }
        )
    return sorted(breakdown, key=lambda item: item["final_value"], reverse=True)


def build_category_breakdown(
    *,
    component_breakdown: list[dict[str, Any]],
    total_value: float,
) -> list[dict[str, Any]]:
    if not component_breakdown:
        return []

    grouped: dict[str, dict[str, Any]] = {}
    safe_total_value = max(total_value, 1e-9)
    for item in component_breakdown:
        category_id = str(item["category_id"])
        bucket = grouped.setdefault(
            category_id,
            {
                "category_id": category_id,
                "category_label": item["category_label"],
                "target_weight": 0.0,
                "final_value": 0.0,
            },
        )
        bucket["target_weight"] += float(item["target_weight"])
        bucket["final_value"] += float(item["final_value"])

    summary = []
    for bucket in grouped.values():
        summary.append(
            {
                **bucket,
                "ending_weight": float(bucket["final_value"] / safe_total_value),
            }
        )
    return sorted(summary, key=lambda item: item["final_value"], reverse=True)


def build_inflation_summary(inflation_curve: pd.Series) -> dict[str, Any]:
    final_factor = float(inflation_curve.iloc[-1]) if not inflation_curve.empty else 1.0
    return {
        "label": "IPCA acumulado",
        "accumulated_rate": final_factor - 1.0,
        "purchasing_power_loss": 1.0 - (1.0 / final_factor if final_factor > 0 else 1.0),
        "availability_start": str(inflation_curve.index.min().date()),
        "availability_end": str(inflation_curve.index.max().date()),
        "source_label": "Banco Central do Brasil / SGS 433",
    }


def build_chart_points(
    index: pd.DatetimeIndex,
    curves: dict[str, pd.Series],
) -> list[dict[str, Any]]:
    normalized = {
        key: series.reindex(index).ffill().where(series.reindex(index).notna())
        for key, series in curves.items()
    }
    points: list[dict[str, Any]] = []
    for timestamp in index:
        row: dict[str, Any] = {"date": str(timestamp.date())}
        for series_id, series in normalized.items():
            value = series.loc[timestamp]
            row[series_id] = float(value) if pd.notna(value) else None
        points.append(row)
    return points


def serialize_curve(curve: pd.Series) -> list[dict[str, Any]]:
    return [
        {"date": str(timestamp.date()), "equity": float(value)}
        for timestamp, value in curve.items()
    ]


def union_index(series_list: list[pd.Series]) -> pd.DatetimeIndex:
    index = pd.DatetimeIndex([])
    for series in series_list:
        index = index.union(series.index)
    return index.sort_values()


def intersection_index(series_list: list[pd.Series]) -> pd.DatetimeIndex:
    """Return the common trading dates across multiple series."""

    if not series_list:
        return pd.DatetimeIndex([])
    index = series_list[0].index
    for series in series_list[1:]:
        index = index.intersection(series.index)
    return index.sort_values()


def summarize_curves(
    equity_curve: pd.Series,
    flow_curve: pd.Series,
) -> dict[str, float]:
    invested_total = float(flow_curve.sum())
    final_value = float(equity_curve.iloc[-1])
    net_profit = final_value - invested_total
    returns = time_weighted_returns(equity_curve, flow_curve)
    twr_total = float((1.0 + returns).prod() - 1.0) if not returns.empty else 0.0
    periods_per_year_value = periods_per_year(equity_curve.index)
    cagr = (
        float((1.0 + twr_total) ** (periods_per_year_value / len(returns)) - 1.0)
        if not returns.empty and 1.0 + twr_total > 0
        else 0.0
    )
    annual_volatility = (
        float(returns.std(ddof=0) * np.sqrt(periods_per_year_value)) if len(returns) > 1 else 0.0
    )
    drawdown = equity_curve / equity_curve.cummax() - 1.0
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
    return {
        "invested_total": invested_total,
        "final_value": final_value,
        "net_profit": net_profit,
        "time_weighted_return": twr_total,
        "cagr": cagr,
        "annual_volatility": annual_volatility,
        "max_drawdown": max_drawdown,
    }


def deflate_curve(curve: pd.Series, inflation_curve: pd.Series) -> pd.Series:
    aligned_inflation = inflation_curve.reindex(curve.index).ffill().bfill()
    aligned_inflation = aligned_inflation.where(aligned_inflation > 0, 1.0)
    real_curve = curve.divide(aligned_inflation)
    return real_curve.astype(float)


def periods_per_year(index: pd.DatetimeIndex) -> float:
    if len(index) < 2:
        return 252.0
    day_deltas = pd.Series(index).diff().dropna().dt.days
    if day_deltas.empty:
        return 252.0
    median_delta = float(day_deltas.median())
    if median_delta <= 3:
        return 252.0
    if median_delta <= 10:
        return 52.0
    if median_delta <= 40:
        return 12.0
    if median_delta <= 100:
        return 4.0
    return max(1.0, 365.25 / median_delta)


def time_weighted_returns(
    equity_curve: pd.Series,
    flow_curve: pd.Series,
) -> pd.Series:
    previous_equity = equity_curve.shift(1)
    adjusted_equity = equity_curve - flow_curve
    returns = adjusted_equity.divide(previous_equity).subtract(1.0)
    return returns.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
