"""Proxy market-series builders for investment simulations."""

from __future__ import annotations

from typing import Callable

import pandas as pd

from .catalog import InvestmentInstrument


def build_market_proxy_price_series(
    *,
    instrument: InvestmentInstrument,
    start_date: str,
    end_date: str,
    series_cache: dict[str, pd.Series],
    selic_path: str,
    inflation_path: str,
    fallback_rate_annual: float,
    inflation_fallback_rate_annual: float,
    get_or_create_daily_selic_data: Callable[..., pd.DataFrame],
    get_daily_rate: Callable[..., float],
    get_or_create_ipca_data: Callable[..., pd.DataFrame],
    get_monthly_ipca_rate: Callable[..., float],
) -> pd.Series:
    """Build synthetic proxy series with monthly/day basis business-day accumulation."""

    cached_series = series_cache.get(instrument.instrument_id)
    if cached_series is not None:
        return cached_series.copy()

    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()
    index = pd.date_range(start=start, end=end, freq="B")
    if index.empty:
        raise ValueError(f"Nao ha dias uteis para construir a curva de {instrument.label}.")

    values: list[float] = []
    price = 1.0
    month_lengths = pd.Series(1, index=index).groupby(index.to_period("M")).sum()
    selic_data = None
    ipca_data = None
    real_daily_spread = (1.0 + float(instrument.spread_rate_annual or 0.0)) ** (1.0 / 252.0) - 1.0
    fixed_daily_rate = (1.0 + float(instrument.fixed_rate_annual or 0.0)) ** (1.0 / 252.0) - 1.0

    for timestamp in index:
        daily_rate = 0.0
        if instrument.proxy_kind in {"selic_daily", "cdi_like_daily"}:
            if selic_data is None:
                selic_data = get_or_create_daily_selic_data(
                    path=selic_path,
                    use_download=True,
                    start_date=start_date,
                    end_date=end_date,
                )
            daily_rate = float(
                get_daily_rate(
                    selic_data,
                    timestamp,
                    fallback_rate_annual=fallback_rate_annual,
                )
            )
            if instrument.proxy_kind == "cdi_like_daily":
                daily_rate *= 0.955
        elif instrument.proxy_kind == "fixed_rate":
            daily_rate = fixed_daily_rate
        elif instrument.proxy_kind in {"ipca_monthly", "ipca_plus"}:
            if ipca_data is None:
                ipca_data = get_or_create_ipca_data(
                    path=inflation_path,
                    use_download=True,
                    start_date=start_date,
                    end_date=end_date,
                )
            monthly_rate = get_monthly_ipca_rate(
                ipca_data,
                timestamp.year,
                timestamp.month,
                fallback_rate_annual=inflation_fallback_rate_annual,
            )
            business_days = int(month_lengths.loc[timestamp.to_period("M")])
            inflation_daily = (1.0 + monthly_rate) ** (1.0 / business_days) - 1.0
            if instrument.proxy_kind == "ipca_plus":
                daily_rate = (1.0 + inflation_daily) * (1.0 + real_daily_spread) - 1.0
            else:
                daily_rate = inflation_daily
        else:
            raise ValueError(f"Proxy de investimento ainda nao suportado: {instrument.label}")

        price *= 1.0 + float(daily_rate)
        values.append(price)

    series = pd.Series(values, index=index, dtype=float)
    series_cache[instrument.instrument_id] = series
    return series.copy()
