"""Didactic cross-asset comparison service for B3-listed investments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data import get_data
from src.selic import get_daily_rate, get_or_create_daily_selic_data

from .catalog import (
    BENCHMARK_OPTIONS,
    INSTRUMENTS,
    PRESETS,
    InvestmentInstrument,
    build_catalog_payload,
)


@dataclass(frozen=True)
class _SimulationResult:
    instrument: InvestmentInstrument
    equity_curve: pd.Series
    flow_curve: pd.Series
    invested_total: float
    final_value: float
    net_profit: float
    twr_total: float
    cagr: float
    annual_volatility: float
    max_drawdown: float
    availability_start: str
    availability_end: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument.instrument_id,
            "label": self.instrument.label,
            "ticker": self.instrument.ticker,
            "category_id": self.instrument.category_id,
            "category_label": self.instrument.category_label,
            "description": self.instrument.description,
            "rationale": self.instrument.rationale,
            "risk_label": self.instrument.risk_label,
            "region_label": self.instrument.region_label,
            "source_kind": self.instrument.source_kind,
            "invested_total": float(self.invested_total),
            "final_value": float(self.final_value),
            "net_profit": float(self.net_profit),
            "total_return_on_invested": (
                float(self.final_value / self.invested_total - 1.0)
                if self.invested_total > 0
                else 0.0
            ),
            "time_weighted_return": float(self.twr_total),
            "cagr": float(self.cagr),
            "annual_volatility": float(self.annual_volatility),
            "max_drawdown": float(self.max_drawdown),
            "availability_start": self.availability_start,
            "availability_end": self.availability_end,
        }


class InvestmentComparisonService:
    """Compare historical B3 investment alternatives using one cash-flow schedule."""

    def __init__(
        self,
        *,
        data_dir: str | Path = "data/investments",
        selic_path: str = "data/selic_daily.csv",
        fallback_rate_annual: float = 0.13,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.selic_path = selic_path
        self.fallback_rate_annual = fallback_rate_annual
        self.instrument_map = {item.instrument_id: item for item in INSTRUMENTS}

    def list_catalog(self) -> dict[str, Any]:
        payload = build_catalog_payload()
        payload["generated_at"] = datetime.now(UTC)
        payload["sources"] = [
            {
                "label": "B3",
                "url": "https://www.b3.com.br/",
            },
            {
                "label": "Yahoo Finance via yfinance",
                "url": "https://finance.yahoo.com/",
            },
            {
                "label": "Banco Central do Brasil",
                "url": "https://www.bcb.gov.br/",
            },
        ]
        return payload

    def compare(
        self,
        *,
        asset_ids: list[str],
        start_date: str = "2021-01-01",
        end_date: str | None = None,
        initial_capital: float = 10000.0,
        monthly_contribution: float = 0.0,
        benchmark_ids: list[str] | None = None,
        force_download: bool = False,
    ) -> dict[str, Any]:
        if not asset_ids:
            raise ValueError("Selecione pelo menos um investimento para comparar.")
        if initial_capital <= 0:
            raise ValueError("O capital inicial precisa ser maior do que zero.")
        if monthly_contribution < 0:
            raise ValueError("O aporte mensal nao pode ser negativo.")

        generated_at = datetime.now(UTC)
        end_date_resolved = end_date or generated_at.strftime("%Y-%m-%d")
        benchmark_keys = benchmark_ids or [item["benchmark_id"] for item in BENCHMARK_OPTIONS]
        warnings: list[str] = []

        selected_instruments: list[InvestmentInstrument] = []
        for asset_id in asset_ids:
            instrument = self.instrument_map.get(asset_id)
            if instrument is None:
                warnings.append(f"Ativo desconhecido ignorado: {asset_id}")
                continue
            selected_instruments.append(instrument)
        if not selected_instruments:
            raise ValueError("Nenhum ativo selecionado foi reconhecido pelo catalogo.")

        results: list[_SimulationResult] = []
        chart_series: list[dict[str, Any]] = []
        chart_curves: dict[str, pd.Series] = {}

        for instrument in selected_instruments:
            try:
                result = self._simulate_instrument(
                    instrument=instrument,
                    start_date=start_date,
                    end_date=end_date_resolved,
                    initial_capital=initial_capital,
                    monthly_contribution=monthly_contribution,
                    force_download=force_download,
                )
            except ValueError as exc:
                warnings.append(str(exc))
                continue

            results.append(result)
            chart_curves[result.instrument.instrument_id] = result.equity_curve
            chart_series.append(
                {
                    "id": result.instrument.instrument_id,
                    "label": result.instrument.label,
                    "color": self._series_color(result.instrument.instrument_id),
                }
            )

        if not results:
            raise ValueError("Nenhum ativo teve historico suficiente para o comparativo pedido.")

        benchmark_payloads: list[dict[str, Any]] = []
        benchmark_reference_id = None
        for benchmark_id in benchmark_keys:
            benchmark_curve = self._build_benchmark_curve(
                benchmark_id=benchmark_id,
                start_date=start_date,
                end_date=end_date_resolved,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                force_download=force_download,
            )
            if benchmark_curve is None:
                continue
            chart_curves[benchmark_id] = benchmark_curve["equity_curve"]
            chart_series.append(
                {
                    "id": benchmark_id,
                    "label": benchmark_curve["label"],
                    "color": self._series_color(benchmark_id),
                    "dashed": benchmark_id == "selic_cash",
                }
            )
            benchmark_payloads.append(benchmark_curve)
            if benchmark_reference_id is None and benchmark_id == "selic_cash":
                benchmark_reference_id = "selic_cash"
        if benchmark_reference_id is None and benchmark_payloads:
            benchmark_reference_id = str(benchmark_payloads[0]["benchmark_id"])

        union_index = self._union_index(
            [item.equity_curve for item in results]
            + [item["equity_curve"] for item in benchmark_payloads]
        )
        chart_points = self._build_chart_points(union_index, chart_curves)
        class_summary = self._build_class_summary(results)
        highlight_summary = self._build_highlights(results, benchmark_payloads)

        return {
            "generated_at": generated_at,
            "request": {
                "asset_ids": [item.instrument_id for item in selected_instruments],
                "start_date": start_date,
                "end_date": end_date_resolved,
                "initial_capital": initial_capital,
                "monthly_contribution": monthly_contribution,
                "benchmark_ids": benchmark_keys,
                "force_download": force_download,
            },
            "catalog_snapshot": {
                "categories": build_catalog_payload()["categories"],
                "selected_assets": [item.to_payload() for item in selected_instruments],
                "presets": [item.to_payload() for item in PRESETS],
            },
            "assumptions": [
                "A comparacao usa a mesma agenda de aportes para todos os investimentos.",
                (
                    "Acoes, ETFs, FIIs e BDRs usam serie ajustada para aproximar "
                    "rendimento total historico."
                ),
                (
                    "O comparador trata o Tesouro Selic como proxy por taxa diaria, "
                    "nao como um titulo especifico marcado a mercado."
                ),
                (
                    "Aporte mensal entra no primeiro dia util ou de negociacao "
                    "disponivel de cada mes, apos o inicio."
                ),
            ],
            "results": [
                item.to_payload()
                for item in sorted(results, key=lambda row: row.final_value, reverse=True)
            ],
            "benchmarks": [
                {
                    **{key: value for key, value in item.items() if key != "equity_curve"},
                    "equity_curve": self._serialize_curve(item["equity_curve"]),
                }
                for item in benchmark_payloads
            ],
            "chart": {
                "reference_series_id": benchmark_reference_id,
                "series": chart_series,
                "points": chart_points,
            },
            "class_summary": class_summary,
            "highlights": highlight_summary,
            "warnings": warnings,
        }

    def _simulate_instrument(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
    ) -> _SimulationResult:
        if instrument.source_kind == "selic_proxy":
            equity_curve, flow_curve = self._simulate_selic_proxy(
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
            )
            return self._finalize_result(
                instrument=instrument,
                equity_curve=equity_curve,
                flow_curve=flow_curve,
            )

        price_series = self._load_adjusted_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
        )
        equity_curve, flow_curve = self._simulate_buy_and_hold_with_aportes(
            price_series=price_series,
            start_date=start_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
        )
        return self._finalize_result(
            instrument=instrument,
            equity_curve=equity_curve,
            flow_curve=flow_curve,
        )

    def _load_adjusted_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        force_download: bool,
    ) -> pd.Series:
        if instrument.ticker is None:
            raise ValueError(f"{instrument.label} nao possui ticker de mercado configurado.")
        cache_path = self.data_dir / f"{instrument.instrument_id.lower()}.parquet"
        data = get_data(
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
        if series.index.min() > requested_start + pd.Timedelta(days=10):
            raise ValueError(
                f"{instrument.label} so possui historico a partir de {series.index.min().date()}."
            )
        return series

    def _simulate_buy_and_hold_with_aportes(
        self,
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

        schedule = self._build_contribution_schedule(
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

    def _simulate_selic_proxy(
        self,
        *,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
    ) -> tuple[pd.Series, pd.Series]:
        start = pd.Timestamp(start_date).normalize()
        end = pd.Timestamp(end_date).normalize()
        index = pd.date_range(start=start, end=end, freq="B")
        if index.empty:
            raise ValueError("Nao ha dias uteis para o periodo solicitado.")
        selic_data = get_or_create_daily_selic_data(
            path=self.selic_path,
            use_download=True,
            start_date=start_date,
            end_date=end_date,
        )
        schedule = self._build_contribution_schedule(
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
                fallback_rate_annual=self.fallback_rate_annual,
            )
            equity *= 1.0 + float(daily_rate)
            equity_values.append(equity)
            flow_values.append(flow)
        return (
            pd.Series(equity_values, index=index, dtype=float),
            pd.Series(flow_values, index=index, dtype=float),
        )

    def _build_contribution_schedule(
        self,
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

    def _finalize_result(
        self,
        *,
        instrument: InvestmentInstrument,
        equity_curve: pd.Series,
        flow_curve: pd.Series,
    ) -> _SimulationResult:
        invested_total = float(flow_curve.sum())
        final_value = float(equity_curve.iloc[-1])
        net_profit = final_value - invested_total
        returns = self._time_weighted_returns(equity_curve, flow_curve)
        twr_total = float((1.0 + returns).prod() - 1.0) if not returns.empty else 0.0
        cagr = (
            float((1.0 + twr_total) ** (252.0 / len(returns)) - 1.0)
            if not returns.empty and 1.0 + twr_total > 0
            else 0.0
        )
        annual_volatility = (
            float(returns.std(ddof=0) * np.sqrt(252.0)) if len(returns) > 1 else 0.0
        )
        drawdown = equity_curve / equity_curve.cummax() - 1.0
        max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
        return _SimulationResult(
            instrument=instrument,
            equity_curve=equity_curve,
            flow_curve=flow_curve,
            invested_total=invested_total,
            final_value=final_value,
            net_profit=net_profit,
            twr_total=twr_total,
            cagr=cagr,
            annual_volatility=annual_volatility,
            max_drawdown=max_drawdown,
            availability_start=str(equity_curve.index.min().date()),
            availability_end=str(equity_curve.index.max().date()),
        )

    def _time_weighted_returns(self, equity_curve: pd.Series, flow_curve: pd.Series) -> pd.Series:
        previous_equity = equity_curve.shift(1)
        adjusted_equity = equity_curve - flow_curve
        returns = adjusted_equity.divide(previous_equity).subtract(1.0)
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        return returns.astype(float)

    def _build_benchmark_curve(
        self,
        *,
        benchmark_id: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
    ) -> dict[str, Any] | None:
        if benchmark_id == "selic_cash":
            instrument = self.instrument_map["SELIC_PROXY"]
            result = self._simulate_instrument(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                force_download=force_download,
            )
            payload = result.to_payload()
            payload["benchmark_id"] = benchmark_id
            payload["label"] = "SELIC / caixa"
            payload["equity_curve"] = result.equity_curve
            return payload

        if benchmark_id == "bova11":
            instrument = self.instrument_map["BOVA11"]
            result = self._simulate_instrument(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                force_download=force_download,
            )
            payload = result.to_payload()
            payload["benchmark_id"] = benchmark_id
            payload["label"] = "BOVA11 (referencia)"
            payload["equity_curve"] = result.equity_curve
            return payload
        return None

    def _build_chart_points(
        self,
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

    def _build_class_summary(self, results: list[_SimulationResult]) -> list[dict[str, Any]]:
        grouped: dict[str, list[_SimulationResult]] = {}
        for result in results:
            grouped.setdefault(result.instrument.category_label, []).append(result)

        summary: list[dict[str, Any]] = []
        for category_label, items in grouped.items():
            summary.append(
                {
                    "category_label": category_label,
                    "asset_count": len(items),
                    "average_final_value": float(np.mean([item.final_value for item in items])),
                    "average_cagr": float(np.mean([item.cagr for item in items])),
                    "average_max_drawdown": float(
                        np.mean([item.max_drawdown for item in items])
                    ),
                    "leader_label": max(items, key=lambda item: item.final_value).instrument.label,
                }
            )
        return sorted(summary, key=lambda item: item["average_final_value"], reverse=True)

    def _build_highlights(
        self,
        results: list[_SimulationResult],
        benchmarks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ordered = sorted(results, key=lambda item: item.final_value, reverse=True)
        best = ordered[0]
        defensive = max(results, key=lambda item: item.max_drawdown)
        selic = next((item for item in benchmarks if item["benchmark_id"] == "selic_cash"), None)
        bova11 = next((item for item in benchmarks if item["benchmark_id"] == "bova11"), None)

        def _count_beating(benchmark: dict[str, Any] | None) -> int | None:
            if benchmark is None:
                return None
            return sum(1 for item in results if item.final_value > float(benchmark["final_value"]))

        insights = [
            f"{best.instrument.label} foi o melhor comparativo em valor final no periodo.",
            (
                f"{defensive.instrument.label} teve a queda maxima menos dolorosa "
                "entre os ativos escolhidos."
            ),
        ]
        if selic is not None:
            beat_count = _count_beating(selic)
            insights.append(
                f"{beat_count} de {len(results)} investimentos terminaram acima da "
                "referencia de SELIC."
            )
        if bova11 is not None:
            beat_count = _count_beating(bova11)
            insights.append(
                f"{beat_count} de {len(results)} investimentos superaram o BOVA11 "
                "no mesmo fluxo de aportes."
            )

        return {
            "best_final_value": best.to_payload(),
            "most_defensive": defensive.to_payload(),
            "beats_selic_count": _count_beating(selic),
            "beats_bova11_count": _count_beating(bova11),
            "insights": insights,
        }

    def _serialize_curve(self, curve: pd.Series) -> list[dict[str, Any]]:
        return [
            {"date": str(timestamp.date()), "equity": float(value)}
            for timestamp, value in curve.items()
        ]

    def _union_index(self, series_list: list[pd.Series]) -> pd.DatetimeIndex:
        index = pd.DatetimeIndex([])
        for series in series_list:
            index = index.union(series.index)
        return index.sort_values()

    def _series_color(self, series_id: str) -> str:
        palette = {
            "SELIC_PROXY": "#10b981",
            "selic_cash": "#10b981",
            "bova11": "#3b82f6",
            "BOVA11": "#3b82f6",
            "IVVB11": "#06b6d4",
            "PETR4": "#f97316",
            "VALE3": "#ef4444",
            "ITUB4": "#8b5cf6",
            "WEGE3": "#f59e0b",
            "HGLG11": "#22c55e",
            "KNRI11": "#84cc16",
            "XPLG11": "#14b8a6",
            "MXRF11": "#ec4899",
            "IMAB11": "#6366f1",
            "SMAL11": "#f43f5e",
            "DIVO11": "#eab308",
            "AAPL34": "#38bdf8",
            "MSFT34": "#0ea5e9",
            "GOGL34": "#60a5fa",
        }
        return palette.get(series_id, "#94a3b8")
