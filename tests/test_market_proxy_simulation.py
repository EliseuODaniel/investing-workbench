"""Unit tests for synthetic market-proxy series builders."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from src.investing_workbench.application.investments.catalog import (
    INSTRUMENTS,
)
from src.investing_workbench.application.investments.market_proxy_simulation import (
    build_market_proxy_price_series,
)


def _instrument_by_id(instrument_id: str):
    return next(item for item in INSTRUMENTS if item.instrument_id == instrument_id)


def test_build_market_proxy_fixed_rate_uses_constant_daily_rate() -> None:
    instrument = _instrument_by_id("PREFIXADO_11_PROXY")
    series = build_market_proxy_price_series(
        instrument=instrument,
        start_date="2024-01-02",
        end_date="2024-01-05",
        series_cache={},
        selic_path="ignore.csv",
        inflation_path="ignore.csv",
        fallback_rate_annual=0.13,
        inflation_fallback_rate_annual=0.045,
        get_or_create_daily_selic_data=lambda **kwargs: pd.DataFrame(),
        get_daily_rate=lambda *_args, **_kwargs: 0.001,
        get_or_create_ipca_data=lambda **kwargs: pd.DataFrame(),
        get_monthly_ipca_rate=lambda *_args, **_kwargs: 0.0,
    )

    index = pd.date_range(start="2024-01-02", end="2024-01-05", freq="B")
    daily_rate = (1.0 + 0.11) ** (1.0 / 252.0) - 1.0
    expected_final = (1.0 + daily_rate) ** len(index)
    expected_first = 1.0 + daily_rate
    assert len(series) == len(index)
    assert index.equals(series.index)
    assert series.iloc[0] == pytest.approx(expected_first)
    assert series.iloc[-1] == pytest.approx(expected_final)


def test_build_market_proxy_caches_series_before_returning() -> None:
    instrument = _instrument_by_id("SELIC_PROXY")
    cache: dict[str, pd.Series] = {}
    first = build_market_proxy_price_series(
        instrument=instrument,
        start_date="2024-02-01",
        end_date="2024-02-05",
        series_cache=cache,
        selic_path="ignore.csv",
        inflation_path="ignore.csv",
        fallback_rate_annual=0.13,
        inflation_fallback_rate_annual=0.045,
        get_or_create_daily_selic_data=lambda **kwargs: pd.DataFrame(
            {
                "date": pd.date_range("2024-02-01", "2024-02-05", freq="B"),
                "rate": [0.0002] * 3,
            }
        ),
        get_daily_rate=lambda *_args, **_kwargs: 0.0002,
        get_or_create_ipca_data=lambda **kwargs: pd.DataFrame(),
        get_monthly_ipca_rate=lambda *_args, **_kwargs: 0.0,
    )

    second = build_market_proxy_price_series(
        instrument=instrument,
        start_date="2024-02-01",
        end_date="2024-02-05",
        series_cache=cache,
        selic_path="ignore.csv",
        inflation_path="ignore.csv",
        fallback_rate_annual=0.13,
        inflation_fallback_rate_annual=0.045,
        get_or_create_daily_selic_data=lambda **_: (_ for _ in ()).throw(
            RuntimeError("should not be called when cache hit")
        ),
        get_daily_rate=lambda *_args, **_kwargs: 999.0,
        get_or_create_ipca_data=lambda **_: (_ for _ in ()).throw(
            RuntimeError("should not be called when cache hit")
        ),
        get_monthly_ipca_rate=lambda *_args, **_kwargs: 999.0,
    )

    pd.testing.assert_series_equal(first, second)
    assert first is not second


def test_build_market_proxy_ipca_and_ipca_plus_use_monthly_rates() -> None:
    ipca_data = pd.DataFrame({"year": [2024, 2024], "month": [1, 2], "rate": [0.01, 0.004]})

    ipca_instrument = _instrument_by_id("IPCA_PROXY")
    ipca_plus_instrument = _instrument_by_id("IPCA_PLUS_6_PROXY")

    ipca_series = build_market_proxy_price_series(
        instrument=ipca_instrument,
        start_date="2024-01-02",
        end_date="2024-01-06",
        series_cache={},
        selic_path="ignore.csv",
        inflation_path="ignore.csv",
        fallback_rate_annual=0.13,
        inflation_fallback_rate_annual=0.045,
        get_or_create_daily_selic_data=lambda **kwargs: pd.DataFrame(),
        get_daily_rate=lambda *_args, **_kwargs: 0.0,
        get_or_create_ipca_data=lambda **kwargs: ipca_data,
        get_monthly_ipca_rate=lambda df, year, month, **kwargs: float(
            df.loc[df["year"] == year].loc[df["month"] == month, "rate"].iloc[-1]
        ),
    )
    ipca_plus_series = build_market_proxy_price_series(
        instrument=ipca_plus_instrument,
        start_date="2024-01-02",
        end_date="2024-01-06",
        series_cache={},
        selic_path="ignore.csv",
        inflation_path="ignore.csv",
        fallback_rate_annual=0.13,
        inflation_fallback_rate_annual=0.045,
        get_or_create_daily_selic_data=lambda **kwargs: pd.DataFrame(),
        get_daily_rate=lambda *_args, **_kwargs: 0.0,
        get_or_create_ipca_data=lambda **kwargs: ipca_data,
        get_monthly_ipca_rate=lambda df, year, month, **kwargs: float(
            df.loc[df["year"] == year].loc[df["month"] == month, "rate"].iloc[-1]
        ),
    )

    assert len(ipca_plus_series) == len(ipca_series)
    assert float(ipca_plus_series.iloc[-1]) > float(ipca_series.iloc[-1]) >= 1.0


def test_build_market_proxy_rejects_unknown_proxy_kind() -> None:
    instrument = replace(INSTRUMENTS[0], proxy_kind="unknown_kind")
    with pytest.raises(ValueError, match="nao suportado"):
        build_market_proxy_price_series(
            instrument=instrument,
            start_date="2024-01-02",
            end_date="2024-01-03",
            series_cache={},
            selic_path="ignore.csv",
            inflation_path="ignore.csv",
            fallback_rate_annual=0.13,
            inflation_fallback_rate_annual=0.045,
            get_or_create_daily_selic_data=lambda **kwargs: pd.DataFrame(),
            get_daily_rate=lambda *_args, **_kwargs: 0.0,
            get_or_create_ipca_data=lambda **kwargs: pd.DataFrame(),
            get_monthly_ipca_rate=lambda *_args, **_kwargs: 0.0,
        )
