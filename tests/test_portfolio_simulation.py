from __future__ import annotations

import pandas as pd
import pytest

from src.investing_workbench.application.investments.market_simulation import (
    build_contribution_schedule,
)
from src.investing_workbench.application.investments.portfolio_simulation import (
    simulate_model_portfolio,
)


class _MiniInstrument:
    def __init__(self, instrument_id: str, label: str, components: list[tuple[str, float]]):
        self.instrument_id = instrument_id
        self.label = label
        self.components = components


def _build_series(start: str, scale: float) -> pd.Series:
    index = pd.date_range(start=start, end="2021-01-15", freq="B")
    return pd.Series([scale + i for i in range(len(index))], index=index, dtype=float)


def test_simulate_model_portfolio_builds_weights_and_flow_values() -> None:
    instrument = _MiniInstrument(
        instrument_id="MODEL",
        label="Carteira exemplo",
        components=[("A", 2.0), ("B", 1.0)],
    )
    series_by_asset = {
        "A": _build_series("2021-01-04", 100.0),
        "B": _build_series("2021-01-04", 200.0),
    }

    def load_component_series(
        component: _MiniInstrument,
        _start: str,
        _end: str,
        _force_download: bool,
        _series_cache: dict[str, pd.Series],
    ) -> pd.Series:
        assert isinstance(component, _MiniInstrument)
        return series_by_asset[component.instrument_id]

    equity_curve, flow_curve, component_values = simulate_model_portfolio(
        instrument=instrument,
        start_date="2021-01-04",
        end_date="2021-01-15",
        initial_capital=3000.0,
        monthly_contribution=1000.0,
        force_download=False,
        series_cache={},
        load_component_series=load_component_series,
        build_contribution_schedule=build_contribution_schedule,
        pick_component_series=lambda component_id: _MiniInstrument(
            instrument_id=component_id,
            label=component_id,
            components=[],
        ),
    )

    expected_index = pd.date_range(start="2021-01-04", end="2021-01-15", freq="B")
    assert set(equity_curve.index) == set(expected_index)
    assert set(flow_curve.index) == set(expected_index)
    assert flow_curve.iloc[0] == 3000.0
    assert any(index.month == 2 for index in flow_curve.index) is False
    assert abs(sum(component_values.values()) - equity_curve.iloc[-1]) < 1e-6


def test_simulate_model_portfolio_rejects_unknown_component() -> None:
    instrument = _MiniInstrument(
        instrument_id="MODEL",
        label="Carteira inválida",
        components=[("UNKNOWN", 1.0)],
    )

    with pytest.raises(ValueError, match="referencia um componente desconhecido"):
        simulate_model_portfolio(
            instrument=instrument,
            start_date="2021-01-04",
            end_date="2021-01-15",
            initial_capital=3000.0,
            monthly_contribution=0.0,
            force_download=False,
            series_cache={},
            load_component_series=lambda *_args, **_kwargs: pd.Series(dtype=float),
            build_contribution_schedule=build_contribution_schedule,
            pick_component_series=lambda component_id: None,
        )


def test_simulate_model_portfolio_accepts_positional_contribution_schedule_callback() -> None:
    instrument = _MiniInstrument(
        instrument_id="MODEL",
        label="Carteira positional",
        components=[("A", 1.0)],
    )
    series_by_asset = {
        "A": _build_series("2021-01-04", 100.0),
    }
    called = {"value": 0}

    def positional_schedule(
        index: pd.DatetimeIndex, initial_cash: float, contribution: float
    ) -> dict:
        called["value"] += 1
        assert initial_cash == 500.0
        assert contribution == 100.0
        assert len(index) > 0
        return {index[0]: 500.0}

    simulate_model_portfolio(
        instrument=instrument,
        start_date="2021-01-04",
        end_date="2021-01-15",
        initial_capital=500.0,
        monthly_contribution=100.0,
        force_download=False,
        series_cache={},
        load_component_series=lambda *_args, **_kwargs: series_by_asset["A"],
        build_contribution_schedule=positional_schedule,
        pick_component_series=lambda component_id: _MiniInstrument(
            instrument_id=component_id,
            label=component_id,
            components=[],
        ),
    )
    assert called["value"] == 1
