"""Portfolio-level simulations for model and custom investment portfolios."""

from __future__ import annotations

from typing import Callable

import pandas as pd

from .catalog import InvestmentInstrument

LoadComponentSeries = Callable[
    [InvestmentInstrument, str, str, bool, dict[str, pd.Series]],
    pd.Series,
]
PickComponentSeries = Callable[[str], InvestmentInstrument | None]


def _normalize_portfolio_weights(
    weights_by_component: dict[str, float],
) -> dict[str, float]:
    if not weights_by_component:
        raise ValueError("Carteira nao possui componentes.")

    total_weight = sum(weights_by_component.values())
    if total_weight <= 0:
        raise ValueError("Carteira nao possui pesos validos.")

    return {
        component_id: float(weight) / total_weight
        for component_id, weight in weights_by_component.items()
    }


def simulate_model_portfolio(
    *,
    instrument: InvestmentInstrument,
    start_date: str,
    end_date: str,
    initial_capital: float,
    monthly_contribution: float,
    force_download: bool,
    series_cache: dict[str, pd.Series],
    load_component_series: LoadComponentSeries,
    build_contribution_schedule: Callable[..., dict[pd.Timestamp, float]],
    pick_component_series: PickComponentSeries,
) -> tuple[pd.Series, pd.Series, dict[str, float]]:
    if not instrument.components:
        raise ValueError(f"{instrument.label} nao possui componentes configurados.")

    components = {component_id: weight for component_id, weight in instrument.components}
    normalized_weights = _normalize_portfolio_weights(components)

    component_series: dict[str, pd.Series] = {}
    for component_id in normalized_weights:
        component = pick_component_series(component_id)
        if component is None:
            raise ValueError(
                f"{instrument.label} referencia um componente desconhecido: {component_id}."
            )
        component_series[component_id] = load_component_series(
            component,
            start_date,
            end_date,
            force_download,
            series_cache,
        )

    if not component_series:
        raise ValueError(f"{instrument.label} nao possui componentes com historico suficiente.")

    first_series = next(iter(component_series.values()))
    common_index = first_series.index
    for series in component_series.values():
        common_index = common_index.intersection(series.index)

    if common_index.empty:
        raise ValueError(
            f"{instrument.label} nao encontrou intersecao de historico suficiente "
            "entre os componentes."
        )

    try:
        schedule = build_contribution_schedule(common_index, initial_capital, monthly_contribution)
    except TypeError:
        schedule = build_contribution_schedule(
            index=common_index,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
        )

    units = {component_id: 0.0 for component_id in normalized_weights}
    equity_values: list[float] = []
    flow_values: list[float] = []
    last_period = None
    last_prices: dict[str, float] = {}

    for timestamp in common_index:
        prices = {
            component_id: float(series.loc[timestamp])
            for component_id, series in component_series.items()
        }
        total_equity = sum(units[component_id] * prices[component_id] for component_id in units)
        flow = float(schedule.get(timestamp, 0.0))
        if flow > 0:
            total_equity += flow

        period = timestamp.to_period("M")
        should_rebalance = last_period is None or period != last_period
        if should_rebalance:
            units = {
                component_id: (total_equity * weight) / prices[component_id]
                for component_id, weight in normalized_weights.items()
            }
            total_equity = sum(units[component_id] * prices[component_id] for component_id in units)
            last_period = period

        equity_values.append(total_equity)
        flow_values.append(flow)
        last_prices = prices

    component_values = {
        component_id: float(units[component_id] * last_prices[component_id])
        for component_id in units
    }

    return (
        pd.Series(equity_values, index=common_index, dtype=float),
        pd.Series(flow_values, index=common_index, dtype=float),
        component_values,
    )
