"""Data loading helpers for investment simulations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.data import get_data

from .fixed_income import get_or_create_fixed_income_quotes
from .tesouro_direto import get_or_create_tesouro_direto_history


class InvestmentDataLoader:
    """Load historical series used by investment simulations."""

    def __init__(
        self,
        *,
        data_dir: str | Path,
        fixed_income_dir: str | Path,
        tesouro_direto_dir: str | Path,
        selic_path: str,
        inflation_path: str,
        get_data_func: Callable[..., pd.DataFrame] = get_data,
        get_fixed_income_quotes_func: Callable[..., pd.DataFrame] = (
            get_or_create_fixed_income_quotes
        ),
        get_tesouro_direto_history_func: Callable[..., pd.DataFrame] = (
            get_or_create_tesouro_direto_history
        ),
    ) -> None:
        self.data_dir = Path(data_dir)
        self.fixed_income_dir = Path(fixed_income_dir)
        self.tesouro_direto_dir = Path(tesouro_direto_dir)
        self.selic_path = selic_path
        self.inflation_path = inflation_path
        self._get_data = get_data_func
        self._get_fixed_income_quotes = get_fixed_income_quotes_func
        self._get_tesouro_direto_history = get_tesouro_direto_history_func
        self._tesouro_direto_history_cache: pd.DataFrame | None = None
        self._tesouro_direto_prepared_cache: dict[tuple[str, str, str], dict[str, Any]] = {}

    def clear_cache(self) -> None:
        """Clear persisted runtime caches and force next load from disk or API."""

        self._tesouro_direto_history_cache = None
        self._tesouro_direto_prepared_cache.clear()

    def load_adjusted_series(
        self,
        *,
        instrument,
        start_date: str,
        end_date: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
        strict_start: bool = True,
    ) -> pd.Series:
        cached_series = series_cache.get(instrument.instrument_id)
        if cached_series is not None:
            return cached_series.copy()

        if instrument.ticker is None:
            raise ValueError(f"{instrument.label} nao possui ticker de mercado configurado.")

        cache_path = self.data_dir / f"{instrument.instrument_id.lower()}.parquet"
        data = self._get_data(
            start=start_date,
            end=end_date,
            cache_path=str(cache_path),
            force_download=force_download,
            data_source=instrument.ticker,
            include_actions=True,
        )
        if data.empty:
            raise ValueError(f"{instrument.label} nao retornou dados para o periodo escolhido.")

        price_column = "Adj Close" if "Adj Close" in data.columns else "Close"
        series = data[price_column].dropna().astype(float)
        series.index = pd.to_datetime(series.index).tz_localize(None)
        series = series.sort_index()
        requested_start = pd.Timestamp(start_date)
        if strict_start and series.index.min() > requested_start + pd.Timedelta(days=10):
            raise ValueError(
                f"{instrument.label} so possui historico a partir de {series.index.min().date()}."
            )

        series_cache[instrument.instrument_id] = series
        return series.copy()

    def load_fixed_income_index_series(
        self,
        *,
        instrument,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
        strict_start: bool = True,
    ) -> pd.Series:
        cached_series = series_cache.get(instrument.instrument_id)
        if cached_series is not None:
            return cached_series.copy()

        quotes = self._get_fixed_income_quotes(
            instrument.instrument_id,
            cache_dir=self.fixed_income_dir,
            use_download=True,
            start_date=start_date,
            end_date=end_date,
        )
        series = quotes.set_index("date")["close"].astype(float).sort_index()
        requested_start = pd.Timestamp(start_date)
        if strict_start and series.index.min() > requested_start + pd.Timedelta(days=5):
            raise ValueError(
                f"{instrument.label} so possui historico a partir de {series.index.min().date()}."
            )
        series_cache[instrument.instrument_id] = series
        return series.copy()

    def load_tesouro_direto_history(
        self,
        *,
        start_date: str,
        end_date: str,
        force_download: bool,
    ) -> pd.DataFrame:
        should_refresh = force_download or self._tesouro_direto_history_cache is None
        if not should_refresh and self._tesouro_direto_history_cache is not None:
            cached = self._tesouro_direto_history_cache
            cache_start = pd.Timestamp(cached["date"].min())
            cache_end = pd.Timestamp(cached["date"].max())
            should_refresh = cache_start > pd.Timestamp(start_date) or cache_end < pd.Timestamp(
                end_date
            )
        if should_refresh:
            self._tesouro_direto_history_cache = self._get_tesouro_direto_history(
                cache_dir=self.tesouro_direto_dir,
                use_download=True,
                start_date=start_date,
                end_date=end_date,
            )
            self._tesouro_direto_prepared_cache.clear()

        history = self._tesouro_direto_history_cache
        if history is None or history.empty:
            raise ValueError("Nao foi possivel carregar o historico do Tesouro Direto.")
        filtered = history[
            (history["date"] >= pd.Timestamp(start_date))
            & (history["date"] <= pd.Timestamp(end_date))
        ].copy()
        if filtered.empty:
            raise ValueError("O Tesouro Direto nao possui historico para o periodo pedido.")
        return filtered

    def prepare_tesouro_family_history(
        self,
        *,
        start_date: str,
        end_date: str,
        title_type: str,
        force_download: bool,
    ) -> dict[str, Any]:
        cache_key = (start_date, end_date, title_type)
        cached = self._tesouro_direto_prepared_cache.get(cache_key)
        if cached is not None:
            return cached

        history = self.load_tesouro_direto_history(
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
        )
        family_history = history[history["title_type"] == title_type].copy()
        if family_history.empty:
            raise ValueError(f"{title_type} nao possui historico oficial suficiente.")

        prepared = {
            "family_history": family_history,
            "grouped_quotes": {
                timestamp: frame.reset_index(drop=True)
                for timestamp, frame in family_history.groupby("date", sort=True)
            },
            "last_available_by_title": family_history.groupby("title_key")["date"].max().to_dict(),
            "candidate_cache": {},
        }
        prepared["quotes_by_title"] = {
            timestamp: {str(row["title_key"]): row for _, row in frame.iterrows()}
            for timestamp, frame in prepared["grouped_quotes"].items()
        }
        prepared["dates"] = pd.DatetimeIndex(sorted(prepared["grouped_quotes"].keys()))
        self._tesouro_direto_prepared_cache[cache_key] = prepared
        return prepared
