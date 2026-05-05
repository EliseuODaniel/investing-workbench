"""Market-level simulation helpers for investments comparisons."""

from __future__ import annotations

from typing import Callable

import pandas as pd


def build_contribution_schedule(
    *,
    index: pd.DatetimeIndex,
    initial_capital: float,
    monthly_contribution: float,
) -> dict[pd.Timestamp, float]:
    schedule: dict[pd.Timestamp, float] = {}
    first_timestamp = index[0]
    schedule[first_timestamp] = float(initial_capital)
    if monthly_contribution <= 0:
        return schedule

    first_period = first_timestamp.to_period("M")
    seen_periods = {first_period}
    for timestamp in index[1:]:
        period = timestamp.to_period("M")
        if period in seen_periods:
            continue
        schedule[timestamp] = schedule.get(timestamp, 0.0) + float(monthly_contribution)
        seen_periods.add(period)
    return schedule


def simulate_buy_and_hold_with_aportes(
    *,
    price_series: pd.Series,
    start_date: str,
    initial_capital: float,
    monthly_contribution: float,
) -> tuple[pd.Series, pd.Series]:
    if price_series.empty:
        raise ValueError("Serie de precos vazia para simulacao.")
    filtered = price_series.loc[pd.Timestamp(start_date) :]
    if filtered.empty:
        raise ValueError("Nao ha sessoes disponiveis para o periodo escolhido.")

    schedule = build_contribution_schedule(
        index=filtered.index,
        initial_capital=initial_capital,
        monthly_contribution=monthly_contribution,
    )
    units = 0.0
    equity_values: list[float] = []
    flow_values: list[float] = []
    for timestamp, price in filtered.items():
        flow = float(schedule.get(timestamp, 0.0))
        if flow > 0:
            units += flow / float(price)
        equity_values.append(units * float(price))
        flow_values.append(flow)
    return (
        pd.Series(equity_values, index=filtered.index, dtype=float),
        pd.Series(flow_values, index=filtered.index, dtype=float),
    )


def simulate_selic_proxy(
    *,
    start_date: str,
    end_date: str,
    initial_capital: float,
    monthly_contribution: float,
    selic_path: str,
    fallback_rate_annual: float,
    get_or_create_daily_selic_data: Callable[..., pd.DataFrame],
    get_daily_rate: Callable[..., float],
) -> tuple[pd.Series, pd.Series]:
    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()
    index = pd.date_range(start=start, end=end, freq="B")
    if index.empty:
        raise ValueError("Nao ha dias uteis para o periodo solicitado.")
    selic_data = get_or_create_daily_selic_data(
        path=selic_path,
        use_download=True,
        start_date=start_date,
        end_date=end_date,
    )
    schedule = build_contribution_schedule(
        index=index,
        initial_capital=initial_capital,
        monthly_contribution=monthly_contribution,
    )
    equity_values: list[float] = []
    flow_values: list[float] = []
    equity = 0.0
    for timestamp in index:
        flow = float(schedule.get(timestamp, 0.0))
        if flow > 0:
            equity += flow
        daily_rate = get_daily_rate(
            selic_data,
            timestamp,
            fallback_rate_annual=fallback_rate_annual,
        )
        equity *= 1.0 + float(daily_rate)
        equity_values.append(equity)
        flow_values.append(flow)
    return (
        pd.Series(equity_values, index=index, dtype=float),
        pd.Series(flow_values, index=index, dtype=float),
    )
