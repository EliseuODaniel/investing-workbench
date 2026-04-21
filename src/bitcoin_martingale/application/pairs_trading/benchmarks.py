"""Benchmark helpers for pairs-trading workflows."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.data import get_data
from src.selic import get_daily_rate, get_or_create_daily_selic_data

from .contracts import PairsContext


class PairsBenchmarkService:
    """Build and normalize benchmark series used by pairs workflows."""

    def default_benchmark_ids(self, preset_metadata: dict[str, Any] | None) -> list[str]:
        """Return the default benchmark IDs for one resolved preset."""
        configured = (
            list(preset_metadata.get("benchmark_tickers", []))
            if preset_metadata is not None
            else []
        )
        default_ids = [*configured, "equal_weight", "selic_cash"]
        return list(dict.fromkeys(default_ids))

    def build_benchmarks(
        self,
        *,
        benchmark_ids: list[str],
        start_date: str,
        end_date: str | None,
        common_index: pd.DatetimeIndex,
        data_by_ticker: dict[str, pd.DataFrame],
        initial_capital: float,
        use_real_selic: bool,
        selic_path: str,
        selic_fallback_rate: float,
        force_download: bool,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Build aligned benchmark equity curves for the requested period."""
        warnings: list[str] = []
        benchmarks: list[dict[str, Any]] = []
        for benchmark_id in benchmark_ids:
            try:
                if benchmark_id == "equal_weight":
                    series = self.equal_weight_benchmark(
                        data_by_ticker=data_by_ticker,
                        tickers=sorted(data_by_ticker),
                        initial_capital=initial_capital,
                        index=common_index,
                    )
                    if series.empty:
                        raise ValueError("Equal-weight benchmark could not be computed")
                    benchmarks.append(
                        {
                            "benchmark_id": benchmark_id,
                            "label": "Equal-weight B3 universe",
                            "equity_curve": self.serialize_series(series),
                        }
                    )
                    continue

                if benchmark_id == "selic_cash":
                    series = self.cash_proxy_benchmark(
                        index=common_index,
                        initial_capital=initial_capital,
                        use_real_selic=use_real_selic,
                        selic_path=selic_path,
                        selic_fallback_rate=selic_fallback_rate,
                    )
                    benchmarks.append(
                        {
                            "benchmark_id": benchmark_id,
                            "label": "SELIC cash proxy",
                            "equity_curve": self.serialize_series(series),
                        }
                    )
                    continue

                cache_path = self.benchmark_cache_path(benchmark_id)
                dataframe = get_data(
                    start=start_date,
                    end=end_date,
                    cache_path=cache_path,
                    force_download=force_download,
                    data_source=benchmark_id,
                    include_actions=True,
                )
                close = dataframe["Adj Close"] if "Adj Close" in dataframe else dataframe["Close"]
                series = self.buy_hold_equity(close, initial_capital, common_index)
                if series.empty:
                    raise ValueError("Benchmark series returned no aligned observations")
                benchmarks.append(
                    {
                        "benchmark_id": benchmark_id,
                        "label": benchmark_id,
                        "equity_curve": self.serialize_series(series),
                    }
                )
            except Exception as exc:  # pragma: no cover - benchmark cache/download variability
                warnings.append(f"Benchmark '{benchmark_id}' could not be loaded: {exc}")
        return benchmarks, warnings

    def benchmark_dataframe_for_regime(self, *, context: PairsContext) -> pd.DataFrame | None:
        """Load a benchmark frame used by regime filters when available."""
        try:
            return get_data(
                start=str(context.common_index.min().date()),
                end=str(context.common_index.max().date()),
                cache_path="data/bova11_sa.parquet",
                force_download=False,
                data_source="BOVA11.SA",
                include_actions=True,
            )
        except Exception:
            return None

    def benchmark_reference_equity(
        self,
        benchmark_series: list[dict[str, Any]],
        index: pd.Index,
    ) -> pd.Series | None:
        """Return the main benchmark equity aligned to one scenario index."""
        for benchmark in benchmark_series:
            if benchmark["benchmark_id"] in {"BOVA11.SA", "^BVSP", "equal_weight"}:
                series = pd.Series(
                    [point["equity"] for point in benchmark["equity_curve"]],
                    index=pd.to_datetime([point["date"] for point in benchmark["equity_curve"]]),
                    dtype=float,
                )
                return series.reindex(index).ffill()
        return None

    def series_from_equity_curve(
        self,
        equity_curve: list[dict[str, Any]],
        *,
        value_key: str,
    ) -> pd.Series:
        """Convert a serialized equity curve back into a Series."""
        if not equity_curve:
            return pd.Series(dtype=float)
        return pd.Series(
            [float(point[value_key]) for point in equity_curve],
            index=pd.to_datetime([point["date"] for point in equity_curve]),
            dtype=float,
        )

    def concat_series_segments(self, segments: list[pd.Series]) -> pd.Series:
        """Merge segmented benchmark Series keeping the latest value per date."""
        if not segments:
            return pd.Series(dtype=float)
        merged = pd.concat(segments).sort_index()
        return merged[~merged.index.duplicated(keep="last")]

    def concat_equity_frames(self, frames: list[pd.DataFrame]) -> pd.DataFrame:
        """Merge scenario equity frames keeping the latest point per date."""
        if not frames:
            return pd.DataFrame(
                columns=[
                    "cash",
                    "cash_yield_base",
                    "unrealized_pnl",
                    "gross_exposure",
                    "net_exposure",
                    "open_positions",
                    "regime_ok",
                    "equity",
                ]
            )
        merged = pd.concat(frames).sort_index()
        return merged[~merged.index.duplicated(keep="last")]

    def concat_tabular_frames(self, frames: list[pd.DataFrame]) -> pd.DataFrame:
        """Concatenate tabular scenario artifacts such as trades or selections."""
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    def buy_hold_equity(
        self,
        series: pd.Series,
        initial_capital: float,
        index: pd.Index,
    ) -> pd.Series:
        """Build one buy-and-hold equity series aligned to the requested index."""
        aligned = pd.Series(series, dtype=float).reindex(index).ffill().dropna()
        if aligned.empty:
            return pd.Series(dtype=float)
        return (aligned / aligned.iloc[0]) * initial_capital

    def equal_weight_benchmark(
        self,
        *,
        data_by_ticker: dict[str, pd.DataFrame],
        tickers: list[str],
        initial_capital: float,
        index: pd.Index,
    ) -> pd.Series:
        """Build an equal-weight benchmark from the current universe."""
        components: list[pd.Series] = []
        for ticker in tickers:
            series = (
                pd.Series(data_by_ticker[ticker]["Adj Close"], dtype=float)
                .reindex(index)
                .ffill()
                .dropna()
            )
            if series.empty:
                continue
            components.append(series / series.iloc[0])
        if not components:
            return pd.Series(dtype=float)
        combined = pd.concat(components, axis=1).dropna()
        return combined.mean(axis=1) * initial_capital

    def cash_proxy_benchmark(
        self,
        *,
        index: pd.DatetimeIndex,
        initial_capital: float,
        use_real_selic: bool,
        selic_path: str,
        selic_fallback_rate: float,
    ) -> pd.Series:
        """Build a cash benchmark using either SELIC history or a fallback rate."""
        if len(index) == 0:
            return pd.Series(dtype=float)
        equity = pd.Series(index=index, dtype=float)
        equity.iloc[0] = initial_capital
        selic_data = None
        if use_real_selic:
            selic_data = get_or_create_daily_selic_data(
                path=selic_path,
                use_download=True,
                start_date=str(index.min().date()),
                end_date=str(index.max().date()),
            )
        for idx in range(1, len(index)):
            day = index[idx]
            previous = float(equity.iloc[idx - 1])
            if use_real_selic and selic_data is not None and not selic_data.empty:
                daily_rate = get_daily_rate(
                    selic_data,
                    day,
                    fallback_rate_annual=selic_fallback_rate,
                )
            else:
                daily_rate = (1.0 + selic_fallback_rate) ** (1.0 / 252.0) - 1.0
            equity.iloc[idx] = previous * (1.0 + daily_rate)
        return equity.ffill()

    def benchmark_cache_path(self, benchmark_id: str) -> str:
        """Return the local cache path used for one benchmark ticker."""
        if benchmark_id == "BOVA11.SA":
            return "data/bova11_sa.parquet"
        if benchmark_id == "^BVSP":
            return "data/BVSP_benchmark.parquet"
        safe_name = benchmark_id.replace("^", "").replace("/", "_").lower()
        return f"data/{safe_name}_benchmark.parquet"

    def serialize_equity_curve(self, equity_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Serialize one equity DataFrame into API-friendly records."""
        curve = equity_df.reset_index().rename(columns={"index": "date"})
        curve["date"] = curve["date"].astype(str)
        return curve.to_dict(orient="records")

    def serialize_series(self, series: pd.Series) -> list[dict[str, Any]]:
        """Serialize one benchmark Series into API-friendly records."""
        return [
            {
                "date": (
                    str(timestamp.date()) if isinstance(timestamp, pd.Timestamp) else str(timestamp)
                ),
                "equity": float(value),
            }
            for timestamp, value in series.items()
        ]
