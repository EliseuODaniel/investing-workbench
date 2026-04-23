"""Didactic cross-asset comparison service for B3-listed investments."""

from __future__ import annotations

import re
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
    CATEGORY_LABELS,
    INSTRUMENTS,
    PRESETS,
    InvestmentInstrument,
    build_catalog_payload,
)
from .fixed_income import (
    build_fixed_income_cache_metadata,
    get_fixed_income_definition,
    get_or_create_fixed_income_quotes,
)
from .inflation import get_monthly_ipca_rate, get_or_create_ipca_data
from .tesouro_direto import (
    TESOURO_DIRETO_CSV_URL,
    build_tesouro_cache_metadata,
    get_or_create_tesouro_direto_history,
    get_tesouro_direto_strategy_definition,
)

_FIXED_INCOME_IOF_TABLE = {
    1: 0.96,
    2: 0.93,
    3: 0.90,
    4: 0.86,
    5: 0.83,
    6: 0.80,
    7: 0.76,
    8: 0.73,
    9: 0.70,
    10: 0.66,
    11: 0.63,
    12: 0.60,
    13: 0.56,
    14: 0.53,
    15: 0.50,
    16: 0.46,
    17: 0.43,
    18: 0.40,
    19: 0.36,
    20: 0.33,
    21: 0.30,
    22: 0.26,
    23: 0.23,
    24: 0.20,
    25: 0.16,
    26: 0.13,
    27: 0.10,
    28: 0.06,
    29: 0.03,
}


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
    component_values: dict[str, float] | None = None
    net_liquidation_curve: pd.Series | None = None
    taxes_paid_total: float = 0.0
    realized_taxes_paid: float = 0.0
    estimated_exit_taxes: float = 0.0
    strategy_metadata: dict[str, Any] | None = None

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
            "taxes_paid_total": float(self.taxes_paid_total),
            "realized_taxes_paid": float(self.realized_taxes_paid),
            "estimated_exit_taxes": float(self.estimated_exit_taxes),
            "strategy_metadata": self.strategy_metadata or {},
        }


@dataclass
class _TesouroLot:
    title_key: str
    quantity: float
    buy_date: pd.Timestamp
    buy_price: float


class InvestmentComparisonService:
    """Compare historical B3 investment alternatives using one cash-flow schedule."""

    def __init__(
        self,
        *,
        data_dir: str | Path = "data/investments",
        fixed_income_dir: str | Path = "data/fixed_income_indexes",
        tesouro_direto_dir: str | Path = "data/tesouro_direto",
        selic_path: str = "data/selic_daily.csv",
        inflation_path: str = "data/ipca_monthly.csv",
        fallback_rate_annual: float = 0.13,
        inflation_fallback_rate_annual: float = 0.045,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.fixed_income_dir = Path(fixed_income_dir)
        self.fixed_income_dir.mkdir(parents=True, exist_ok=True)
        self.tesouro_direto_dir = Path(tesouro_direto_dir)
        self.tesouro_direto_dir.mkdir(parents=True, exist_ok=True)
        self.selic_path = selic_path
        self.inflation_path = inflation_path
        self.fallback_rate_annual = fallback_rate_annual
        self.inflation_fallback_rate_annual = inflation_fallback_rate_annual
        self.instrument_map = {item.instrument_id: item for item in INSTRUMENTS}
        self._tesouro_direto_history_cache: pd.DataFrame | None = None
        self._tesouro_direto_prepared_cache: dict[tuple[str, str, str], dict[str, Any]] = {}

    def list_catalog(self) -> dict[str, Any]:
        payload = build_catalog_payload()
        payload["generated_at"] = datetime.now(UTC)
        payload["sources"] = [
            {
                "label": "B3",
                "url": "https://www.b3.com.br/",
            },
            {
                "label": "ANBIMA IDkA",
                "url": "https://www.anbima.com.br/informacoes/idka/default.asp",
            },
            {
                "label": "Yahoo Finance via yfinance",
                "url": "https://finance.yahoo.com/",
            },
            {
                "label": "Banco Central do Brasil",
                "url": "https://www.bcb.gov.br/",
            },
            {
                "label": "Mais Retorno API publica",
                "url": "https://api.maisretorno.com/v3/",
            },
            {
                "label": "Tesouro Transparente / Tesouro Direto",
                "url": TESOURO_DIRETO_CSV_URL,
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
        custom_portfolios: list[dict[str, Any]] | None = None,
        fixed_income_study_mode: str = "auto",
        fixed_income_tax_treatment: str = "gross",
        fixed_income_window_frequency: str = "monthly",
        force_download: bool = False,
    ) -> dict[str, Any]:
        if not asset_ids and not custom_portfolios:
            raise ValueError("Selecione pelo menos um investimento ou carteira para comparar.")
        if initial_capital <= 0:
            raise ValueError("O capital inicial precisa ser maior do que zero.")
        if monthly_contribution < 0:
            raise ValueError("O aporte mensal nao pode ser negativo.")
        if fixed_income_study_mode not in {"auto", "index_duration", "retail_treasury", "both"}:
            raise ValueError("Modo de estudo de renda fixa invalido.")
        if fixed_income_tax_treatment not in {"gross", "net", "both"}:
            raise ValueError("Tratamento tributario de renda fixa invalido.")
        if fixed_income_window_frequency not in {"monthly", "daily"}:
            raise ValueError("Frequencia de janelas de renda fixa invalida.")

        generated_at = datetime.now(UTC)
        end_date_resolved = end_date or generated_at.strftime("%Y-%m-%d")
        benchmark_keys = (
            benchmark_ids
            if benchmark_ids is not None
            else [item["benchmark_id"] for item in BENCHMARK_OPTIONS]
        )
        warnings: list[str] = []
        series_cache: dict[str, pd.Series] = {}

        selected_assets: list[InvestmentInstrument] = []
        for asset_id in asset_ids:
            instrument = self.instrument_map.get(asset_id)
            if instrument is None:
                warnings.append(f"Ativo desconhecido ignorado: {asset_id}")
                continue
            selected_assets.append(instrument)

        custom_instruments = self._build_custom_portfolio_instruments(
            custom_portfolios or [],
            warnings=warnings,
        )
        comparison_instruments = [*selected_assets, *custom_instruments]
        if not comparison_instruments:
            raise ValueError("Nenhum investimento valido foi reconhecido pelo comparador.")

        results: list[_SimulationResult] = []
        chart_series: list[dict[str, Any]] = []
        chart_curves: dict[str, pd.Series] = {}

        for instrument in comparison_instruments:
            try:
                result = self._simulate_instrument(
                    instrument=instrument,
                    start_date=start_date,
                    end_date=end_date_resolved,
                    initial_capital=initial_capital,
                    monthly_contribution=monthly_contribution,
                    force_download=force_download,
                    series_cache=series_cache,
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

        benchmark_entries: list[dict[str, Any]] = []
        benchmark_reference_id = None
        for benchmark_id in benchmark_keys:
            benchmark_entry = self._build_benchmark_entry(
                benchmark_id=benchmark_id,
                start_date=start_date,
                end_date=end_date_resolved,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                force_download=force_download,
                series_cache=series_cache,
            )
            if benchmark_entry is None:
                continue
            benchmark_entries.append(benchmark_entry)
            chart_curves[benchmark_id] = benchmark_entry["result"].equity_curve
            chart_series.append(
                {
                    "id": benchmark_id,
                    "label": benchmark_entry["label"],
                    "color": self._series_color(benchmark_id),
                    "dashed": benchmark_id == "selic_cash",
                }
            )
            if benchmark_reference_id is None and benchmark_id == "selic_cash":
                benchmark_reference_id = "selic_cash"

        if benchmark_reference_id is None and benchmark_entries:
            benchmark_reference_id = str(benchmark_entries[0]["benchmark_id"])

        inflation_curve = self._build_inflation_price_series(
            start_date=start_date,
            end_date=end_date_resolved,
            series_cache=series_cache,
        )

        ordered_results = sorted(results, key=lambda row: row.final_value, reverse=True)
        result_payloads = [
            self._build_result_payload(result, inflation_curve) for result in ordered_results
        ]
        benchmark_payloads = [
            self._build_benchmark_payload(entry, inflation_curve) for entry in benchmark_entries
        ]

        union_index = self._union_index(
            [item.equity_curve for item in results]
            + [item["result"].equity_curve for item in benchmark_entries]
        )
        chart_points = self._build_chart_points(union_index, chart_curves)
        real_chart_curves = {
            series_id: self._deflate_curve(curve, inflation_curve)
            for series_id, curve in chart_curves.items()
        }
        real_chart_points = self._build_chart_points(union_index, real_chart_curves)
        class_summary = self._build_class_summary(result_payloads)
        highlight_summary = self._build_highlights(result_payloads, benchmark_payloads)
        fixed_income_backtest = self._build_fixed_income_backtest(
            results=results,
            comparison_instruments=comparison_instruments,
            start_date=start_date,
            end_date=end_date_resolved,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            inflation_curve=inflation_curve,
            fixed_income_study_mode=fixed_income_study_mode,
            fixed_income_tax_treatment=fixed_income_tax_treatment,
            fixed_income_window_frequency=fixed_income_window_frequency,
            force_download=force_download,
            series_cache=series_cache,
        )

        return {
            "generated_at": generated_at,
            "request": {
                "asset_ids": [item.instrument_id for item in selected_assets],
                "custom_portfolios": [
                    self._serialize_custom_portfolio_request(item) for item in custom_instruments
                ],
                "start_date": start_date,
                "end_date": end_date_resolved,
                "initial_capital": initial_capital,
                "monthly_contribution": monthly_contribution,
                "benchmark_ids": benchmark_keys,
                "fixed_income_study_mode": fixed_income_study_mode,
                "fixed_income_tax_treatment": fixed_income_tax_treatment,
                "fixed_income_window_frequency": fixed_income_window_frequency,
                "force_download": force_download,
            },
            "catalog_snapshot": {
                "categories": build_catalog_payload()["categories"],
                "selected_assets": [item.to_payload() for item in comparison_instruments],
                "presets": [item.to_payload() for item in PRESETS],
            },
            "assumptions": [
                "A comparacao usa a mesma agenda de aportes para todos os investimentos.",
                (
                    "Acoes, ETFs, FIIs e BDRs usam serie ajustada para aproximar "
                    "rendimento total historico."
                ),
                (
                    "Proxies de SELIC, CDI, IPCA, IPCA+ e prefixado sao simplificacoes "
                    "didaticas, nao a simulacao de um titulo especifico."
                ),
                (
                    "Os indices historicos de CDI e IDkA usam cotacoes diarias para "
                    "comparar renda fixa por duration sem depender de um fundo especifico."
                ),
                (
                    "Retorno real deflaciona a curva pelo IPCA mensal para mostrar "
                    "poder de compra no inicio do periodo."
                ),
                (
                    "Aporte mensal entra no primeiro dia util ou de negociacao "
                    "disponivel de cada mes, apos o inicio."
                ),
            ],
            "results": result_payloads,
            "benchmarks": benchmark_payloads,
            "chart": {
                "reference_series_id": benchmark_reference_id,
                "series": chart_series,
                "points": chart_points,
            },
            "real_chart": {
                "reference_series_id": benchmark_reference_id,
                "series": chart_series,
                "points": real_chart_points,
            },
            "inflation": self._build_inflation_summary(inflation_curve),
            "class_summary": class_summary,
            "highlights": highlight_summary,
            "fixed_income_backtest": fixed_income_backtest,
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
        series_cache: dict[str, pd.Series],
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

        if instrument.source_kind in {"model_portfolio", "custom_portfolio"}:
            equity_curve, flow_curve, component_values = self._simulate_model_portfolio(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                force_download=force_download,
                series_cache=series_cache,
            )
            return self._finalize_result(
                instrument=instrument,
                equity_curve=equity_curve,
                flow_curve=flow_curve,
                component_values=component_values,
            )

        if instrument.source_kind == "tesouro_direct_strategy":
            equity_curve, flow_curve, net_curve, strategy_metadata = (
                self._simulate_tesouro_direto_strategy(
                    instrument=instrument,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    monthly_contribution=monthly_contribution,
                    force_download=force_download,
                )
            )
            return self._finalize_result(
                instrument=instrument,
                equity_curve=equity_curve,
                flow_curve=flow_curve,
                net_liquidation_curve=net_curve,
                taxes_paid_total=float(strategy_metadata.get("total_taxes", 0.0)),
                realized_taxes_paid=float(strategy_metadata.get("realized_taxes", 0.0)),
                estimated_exit_taxes=float(strategy_metadata.get("estimated_exit_taxes", 0.0)),
                strategy_metadata=strategy_metadata,
            )

        if instrument.source_kind == "fixed_income_index":
            price_series = self._load_fixed_income_index_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
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

        if instrument.proxy_kind is not None or instrument.source_kind in {
            "rate_proxy",
            "inflation_proxy",
        }:
            price_series = self._build_proxy_price_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
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

        price_series = self._load_adjusted_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
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
        series_cache: dict[str, pd.Series],
        strict_start: bool = True,
    ) -> pd.Series:
        cached_series = series_cache.get(instrument.instrument_id)
        if cached_series is not None:
            return cached_series.copy()
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
        if strict_start and series.index.min() > requested_start + pd.Timedelta(days=10):
            raise ValueError(
                f"{instrument.label} so possui historico a partir de {series.index.min().date()}."
            )
        series_cache[instrument.instrument_id] = series
        return series.copy()

    def _load_fixed_income_index_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
        strict_start: bool = True,
    ) -> pd.Series:
        cached_series = series_cache.get(instrument.instrument_id)
        if cached_series is not None:
            return cached_series.copy()

        quotes = get_or_create_fixed_income_quotes(
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

    def _load_tesouro_direto_history(
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
            self._tesouro_direto_history_cache = get_or_create_tesouro_direto_history(
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

    def _prepare_tesouro_family_history(
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

        history = self._load_tesouro_direto_history(
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

    def _simulate_tesouro_direto_strategy(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
    ) -> tuple[pd.Series, pd.Series, pd.Series, dict[str, Any]]:
        definition = get_tesouro_direto_strategy_definition(instrument.instrument_id)
        if definition is None:
            raise ValueError(
                f"Estrategia de Tesouro Direto desconhecida: {instrument.instrument_id}"
            )
        prepared = self._prepare_tesouro_family_history(
            start_date=start_date,
            end_date=end_date,
            title_type=definition.title_type,
            force_download=force_download,
        )
        quotes_by_title = prepared["quotes_by_title"]
        last_available_by_title = prepared["last_available_by_title"]
        dates = prepared["dates"]
        schedule = self._build_contribution_schedule(
            index=dates,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
        )

        active_title_key: str | None = None
        gross_cash = 0.0
        net_cash = 0.0
        gross_lots: list[_TesouroLot] = []
        net_lots: list[_TesouroLot] = []
        equity_values: list[float] = []
        net_liquidation_values: list[float] = []
        flow_values: list[float] = []
        realized_taxes = 0.0
        roll_count = 0
        last_estimated_exit_taxes = 0.0

        for timestamp in dates:
            flow = float(schedule.get(timestamp, 0.0))
            gross_cash += flow
            net_cash += flow

            current_quote = self._resolve_tesouro_quote_row(
                quotes_by_title[timestamp],
                active_title_key,
            )
            should_roll = False
            if active_title_key is None:
                should_roll = True
            elif current_quote is None:
                should_roll = True
            else:
                last_available = last_available_by_title.get(active_title_key)
                if (
                    last_available is not None
                    and timestamp == last_available
                    and timestamp != dates[-1]
                ):
                    should_roll = True
                elif not self._tesouro_quote_fits_strategy(current_quote, definition):
                    should_roll = True

            if should_roll:
                if current_quote is not None and gross_lots:
                    gross_cash += self._liquidate_tesouro_lots(
                        lots=gross_lots,
                        sell_price=float(current_quote["investor_sell_price"]),
                        sell_date=timestamp,
                        apply_taxes=False,
                    )[0]
                    net_proceeds, taxes_paid = self._liquidate_tesouro_lots(
                        lots=net_lots,
                        sell_price=float(current_quote["investor_sell_price"]),
                        sell_date=timestamp,
                        apply_taxes=True,
                    )
                    net_cash += net_proceeds
                    realized_taxes += taxes_paid
                    gross_lots = []
                    net_lots = []
                    if active_title_key is not None:
                        roll_count += 1

                candidate_quote = self._prepare_tesouro_candidate(
                    prepared=prepared,
                    definition=definition,
                    timestamp=timestamp,
                )
                active_title_key = (
                    str(candidate_quote["title_key"]) if candidate_quote is not None else None
                )
                if candidate_quote is not None:
                    gross_cash, gross_lots = self._buy_tesouro_with_cash(
                        cash=gross_cash,
                        lots=gross_lots,
                        buy_quote=candidate_quote,
                        buy_date=timestamp,
                    )
                    net_cash, net_lots = self._buy_tesouro_with_cash(
                        cash=net_cash,
                        lots=net_lots,
                        buy_quote=candidate_quote,
                        buy_date=timestamp,
                    )
                    current_quote = self._resolve_tesouro_quote_row(
                        quotes_by_title[timestamp],
                        active_title_key,
                    )

            elif flow > 0 and current_quote is not None:
                gross_cash, gross_lots = self._buy_tesouro_with_cash(
                    cash=gross_cash,
                    lots=gross_lots,
                    buy_quote=current_quote,
                    buy_date=timestamp,
                )
                net_cash, net_lots = self._buy_tesouro_with_cash(
                    cash=net_cash,
                    lots=net_lots,
                    buy_quote=current_quote,
                    buy_date=timestamp,
                )

            current_quote = self._resolve_tesouro_quote_row(
                quotes_by_title[timestamp],
                active_title_key,
            )
            if current_quote is None:
                gross_equity = gross_cash
                net_equity = net_cash
                estimated_exit_taxes = 0.0
            else:
                sell_price = float(
                    current_quote["investor_sell_price"]
                    if pd.notna(current_quote["investor_sell_price"])
                    else current_quote["base_price"]
                )
                gross_market_value = sum(lot.quantity * sell_price for lot in gross_lots)
                net_market_value = sum(lot.quantity * sell_price for lot in net_lots)
                estimated_exit_taxes = self._estimate_tesouro_exit_taxes(
                    lots=net_lots,
                    sell_price=sell_price,
                    sell_date=timestamp,
                )
                gross_equity = gross_cash + gross_market_value
                net_equity = net_cash + net_market_value - estimated_exit_taxes

            last_estimated_exit_taxes = float(estimated_exit_taxes)
            equity_values.append(float(gross_equity))
            net_liquidation_values.append(float(net_equity))
            flow_values.append(flow)

        gross_curve = pd.Series(equity_values, index=dates, dtype=float)
        flow_curve = pd.Series(flow_values, index=dates, dtype=float)
        net_curve = pd.Series(net_liquidation_values, index=dates, dtype=float)
        strategy_metadata = {
            "study_id": "retail_treasury",
            "title_type": definition.title_type,
            "family_id": definition.family_id,
            "family_label": definition.family_label,
            "target_duration_years": definition.target_duration_years,
            "selection_rule": definition.selection_rule,
            "roll_count": int(roll_count),
            "cash_drag_note": (
                "Quando um titulo deixa de ser ofertado e nao ha substituto imediato, o caixa "
                "fica parado ate surgir um papel compativel."
            ),
            "tax_model": "IR regressivo + IOF inferior a 30 dias",
            "realized_taxes": float(realized_taxes),
            "estimated_exit_taxes": float(last_estimated_exit_taxes),
            "total_taxes": float(realized_taxes + last_estimated_exit_taxes),
        }
        return gross_curve, flow_curve, net_curve, strategy_metadata

    def _prepare_tesouro_candidate(
        self,
        *,
        prepared: dict[str, Any],
        definition: Any,
        timestamp: pd.Timestamp,
    ) -> dict[str, Any] | None:
        cache_key = (definition.instrument_id, str(timestamp.date()))
        candidate_cache: dict[tuple[str, str], dict[str, Any] | None] = prepared["candidate_cache"]
        if cache_key in candidate_cache:
            return candidate_cache[cache_key]
        quotes = prepared["grouped_quotes"][timestamp]
        candidate = self._select_tesouro_candidate(quotes, definition)
        candidate_cache[cache_key] = candidate
        return candidate

    def _resolve_tesouro_quote_row(
        self,
        quotes: pd.DataFrame | dict[str, Any],
        title_key: str | None,
    ) -> Any | None:
        if title_key is None:
            return None
        if isinstance(quotes, dict):
            return quotes.get(title_key)
        matched = quotes[quotes["title_key"] == title_key]
        if matched.empty:
            return None
        return matched.iloc[0]

    def _tesouro_quote_fits_strategy(
        self,
        quote: pd.Series,
        definition: Any,
    ) -> bool:
        if definition.selection_rule == "shortest_maturity":
            return float(quote["years_to_maturity"]) > 0.25
        years_to_maturity = float(quote["years_to_maturity"])
        min_years = definition.min_years_to_maturity
        max_years = definition.max_years_to_maturity
        if min_years is not None and years_to_maturity < min_years:
            return False
        if max_years is not None and years_to_maturity > max_years:
            return False
        return True

    def _select_tesouro_candidate(
        self,
        quotes: pd.DataFrame,
        definition: Any,
    ) -> pd.Series | None:
        candidates = quotes.copy()
        if candidates.empty:
            return None
        if definition.selection_rule == "shortest_maturity":
            eligible = candidates[candidates["years_to_maturity"] > 0.25]
            if eligible.empty:
                return None
            return eligible.sort_values(["years_to_maturity", "maturity_date"]).iloc[0]

        eligible = candidates.copy()
        if definition.min_years_to_maturity is not None:
            eligible = eligible[eligible["years_to_maturity"] >= definition.min_years_to_maturity]
        if definition.max_years_to_maturity is not None:
            eligible = eligible[eligible["years_to_maturity"] <= definition.max_years_to_maturity]
        if eligible.empty:
            eligible = candidates.copy()
        eligible = eligible.assign(
            duration_gap=(
                eligible["years_to_maturity"] - float(definition.target_duration_years)
            ).abs()
        )
        return eligible.sort_values(["duration_gap", "years_to_maturity", "maturity_date"]).iloc[0]

    def _buy_tesouro_with_cash(
        self,
        *,
        cash: float,
        lots: list[_TesouroLot],
        buy_quote: pd.Series,
        buy_date: pd.Timestamp,
    ) -> tuple[float, list[_TesouroLot]]:
        buy_price = float(buy_quote["investor_buy_price"])
        if cash <= 0 or buy_price <= 0:
            return cash, lots
        quantity = float(cash / buy_price)
        if quantity <= 0:
            return cash, lots
        updated_lots = [
            *lots,
            _TesouroLot(
                title_key=str(buy_quote["title_key"]),
                quantity=quantity,
                buy_date=buy_date,
                buy_price=buy_price,
            ),
        ]
        return 0.0, updated_lots

    def _liquidate_tesouro_lots(
        self,
        *,
        lots: list[_TesouroLot],
        sell_price: float,
        sell_date: pd.Timestamp,
        apply_taxes: bool,
    ) -> tuple[float, float]:
        proceeds = 0.0
        taxes_paid = 0.0
        for lot in lots:
            gross_proceeds = float(lot.quantity * sell_price)
            taxes = (
                self._fixed_income_exit_taxes(
                    cost_basis=float(lot.quantity * lot.buy_price),
                    sale_value=gross_proceeds,
                    holding_days=max(1, int((sell_date - lot.buy_date).days)),
                )
                if apply_taxes
                else 0.0
            )
            proceeds += gross_proceeds - taxes
            taxes_paid += taxes
        return proceeds, taxes_paid

    def _estimate_tesouro_exit_taxes(
        self,
        *,
        lots: list[_TesouroLot],
        sell_price: float,
        sell_date: pd.Timestamp,
    ) -> float:
        return float(
            sum(
                self._fixed_income_exit_taxes(
                    cost_basis=float(lot.quantity * lot.buy_price),
                    sale_value=float(lot.quantity * sell_price),
                    holding_days=max(1, int((sell_date - lot.buy_date).days)),
                )
                for lot in lots
            )
        )

    def _fixed_income_ir_rate(self, holding_days: int) -> float:
        if holding_days <= 180:
            return 0.225
        if holding_days <= 360:
            return 0.20
        if holding_days <= 720:
            return 0.175
        return 0.15

    def _fixed_income_exit_taxes(
        self,
        *,
        cost_basis: float,
        sale_value: float,
        holding_days: int,
    ) -> float:
        gross_gain = max(0.0, float(sale_value - cost_basis))
        if gross_gain <= 0:
            return 0.0
        iof_rate = _FIXED_INCOME_IOF_TABLE.get(holding_days, 0.0) if holding_days < 30 else 0.0
        iof_tax = gross_gain * iof_rate
        ir_tax = max(0.0, gross_gain - iof_tax) * self._fixed_income_ir_rate(holding_days)
        return float(iof_tax + ir_tax)

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

    def _simulate_model_portfolio(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> tuple[pd.Series, pd.Series, dict[str, float]]:
        if not instrument.components:
            raise ValueError(f"{instrument.label} nao possui componentes configurados.")

        component_series: dict[str, pd.Series] = {}
        component_weights = {component_id: weight for component_id, weight in instrument.components}
        total_weight = sum(component_weights.values())
        if total_weight <= 0:
            raise ValueError(f"{instrument.label} nao possui pesos validos.")
        component_weights = {
            component_id: weight / total_weight
            for component_id, weight in component_weights.items()
        }

        for component_id in component_weights:
            component = self.instrument_map.get(component_id)
            if component is None:
                raise ValueError(
                    f"{instrument.label} referencia um componente desconhecido: {component_id}."
                )
            component_series[component_id] = self._load_component_series(
                instrument=component,
                start_date=start_date,
                end_date=end_date,
                force_download=force_download,
                series_cache=series_cache,
            )

        common_index = self._intersection_index(list(component_series.values()))
        if common_index.empty:
            raise ValueError(
                f"{instrument.label} nao encontrou intersecao de historico "
                "suficiente entre os componentes."
            )

        schedule = self._build_contribution_schedule(
            index=common_index,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
        )
        units = {component_id: 0.0 for component_id in component_weights}
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
                    for component_id, weight in component_weights.items()
                }
                total_equity = sum(
                    units[component_id] * prices[component_id] for component_id in units
                )
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

    def _load_component_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> pd.Series:
        if instrument.proxy_kind is not None or instrument.source_kind in {
            "selic_proxy",
            "rate_proxy",
            "inflation_proxy",
        }:
            return self._build_proxy_price_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
            )
        if instrument.source_kind == "fixed_income_index":
            return self._load_fixed_income_index_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
                strict_start=False,
            )
        return self._load_adjusted_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
            strict_start=False,
        )

    def _build_proxy_price_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
    ) -> pd.Series:
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
        real_daily_spread = (1.0 + float(instrument.spread_rate_annual or 0.0)) ** (
            1.0 / 252.0
        ) - 1.0
        fixed_daily_rate = (1.0 + float(instrument.fixed_rate_annual or 0.0)) ** (1.0 / 252.0) - 1.0

        for timestamp in index:
            daily_rate = 0.0
            if instrument.proxy_kind in {"selic_daily", "cdi_like_daily"}:
                if selic_data is None:
                    selic_data = get_or_create_daily_selic_data(
                        path=self.selic_path,
                        use_download=True,
                        start_date=start_date,
                        end_date=end_date,
                    )
                daily_rate = float(
                    get_daily_rate(
                        selic_data,
                        timestamp,
                        fallback_rate_annual=self.fallback_rate_annual,
                    )
                )
                if instrument.proxy_kind == "cdi_like_daily":
                    daily_rate *= 0.955
            elif instrument.proxy_kind == "fixed_rate":
                daily_rate = fixed_daily_rate
            elif instrument.proxy_kind in {"ipca_monthly", "ipca_plus"}:
                if ipca_data is None:
                    ipca_data = get_or_create_ipca_data(
                        path=self.inflation_path,
                        use_download=True,
                        start_date=start_date,
                        end_date=end_date,
                    )
                monthly_rate = get_monthly_ipca_rate(
                    ipca_data,
                    timestamp.year,
                    timestamp.month,
                    fallback_rate_annual=self.inflation_fallback_rate_annual,
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

    def _build_inflation_price_series(
        self,
        *,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
    ) -> pd.Series:
        inflation_instrument = self.instrument_map.get("IPCA_PROXY")
        if inflation_instrument is None:
            raise ValueError("O proxy de inflacao IPCA nao esta configurado no catalogo.")
        return self._build_proxy_price_series(
            instrument=inflation_instrument,
            start_date=start_date,
            end_date=end_date,
            series_cache=series_cache,
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
        component_values: dict[str, float] | None = None,
        net_liquidation_curve: pd.Series | None = None,
        taxes_paid_total: float = 0.0,
        realized_taxes_paid: float = 0.0,
        estimated_exit_taxes: float = 0.0,
        strategy_metadata: dict[str, Any] | None = None,
    ) -> _SimulationResult:
        metrics = self._summarize_curves(equity_curve, flow_curve)
        return _SimulationResult(
            instrument=instrument,
            equity_curve=equity_curve,
            flow_curve=flow_curve,
            invested_total=metrics["invested_total"],
            final_value=metrics["final_value"],
            net_profit=metrics["net_profit"],
            twr_total=metrics["time_weighted_return"],
            cagr=metrics["cagr"],
            annual_volatility=metrics["annual_volatility"],
            max_drawdown=metrics["max_drawdown"],
            availability_start=str(equity_curve.index.min().date()),
            availability_end=str(equity_curve.index.max().date()),
            component_values=component_values,
            net_liquidation_curve=net_liquidation_curve,
            taxes_paid_total=taxes_paid_total,
            realized_taxes_paid=realized_taxes_paid,
            estimated_exit_taxes=estimated_exit_taxes,
            strategy_metadata=strategy_metadata,
        )

    def _summarize_curves(
        self,
        equity_curve: pd.Series,
        flow_curve: pd.Series,
    ) -> dict[str, float]:
        invested_total = float(flow_curve.sum())
        final_value = float(equity_curve.iloc[-1])
        net_profit = final_value - invested_total
        returns = self._time_weighted_returns(equity_curve, flow_curve)
        twr_total = float((1.0 + returns).prod() - 1.0) if not returns.empty else 0.0
        periods_per_year = self._periods_per_year(equity_curve.index)
        cagr = (
            float((1.0 + twr_total) ** (periods_per_year / len(returns)) - 1.0)
            if not returns.empty and 1.0 + twr_total > 0
            else 0.0
        )
        annual_volatility = (
            float(returns.std(ddof=0) * np.sqrt(periods_per_year)) if len(returns) > 1 else 0.0
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

    def _time_weighted_returns(self, equity_curve: pd.Series, flow_curve: pd.Series) -> pd.Series:
        previous_equity = equity_curve.shift(1)
        adjusted_equity = equity_curve - flow_curve
        returns = adjusted_equity.divide(previous_equity).subtract(1.0)
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        return returns.astype(float)

    def _periods_per_year(self, index: pd.DatetimeIndex) -> float:
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

    def _build_benchmark_entry(
        self,
        *,
        benchmark_id: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
        series_cache: dict[str, pd.Series],
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
                series_cache=series_cache,
            )
            return {
                "benchmark_id": benchmark_id,
                "label": "SELIC / caixa",
                "result": result,
            }

        if benchmark_id == "bova11":
            instrument = self.instrument_map["BOVA11"]
            result = self._simulate_instrument(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                force_download=force_download,
                series_cache=series_cache,
            )
            return {
                "benchmark_id": benchmark_id,
                "label": "BOVA11 (referencia)",
                "result": result,
            }
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

    def _build_result_payload(
        self,
        result: _SimulationResult,
        inflation_curve: pd.Series,
    ) -> dict[str, Any]:
        payload = result.to_payload()
        real_equity_curve = self._deflate_curve(result.equity_curve, inflation_curve)
        real_flow_curve = self._deflate_curve(result.flow_curve, inflation_curve)
        real_metrics = self._summarize_curves(real_equity_curve, real_flow_curve)
        net_curve = result.net_liquidation_curve
        net_metrics = (
            self._summarize_curves(net_curve, result.flow_curve) if net_curve is not None else None
        )
        real_net_metrics = (
            self._summarize_curves(
                self._deflate_curve(net_curve, inflation_curve),
                real_flow_curve,
            )
            if net_curve is not None
            else None
        )
        component_breakdown = self._build_component_breakdown(result)
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
                    real_net_metrics["cagr"]
                    if real_net_metrics is not None
                    else real_metrics["cagr"]
                ),
                "component_breakdown": component_breakdown,
                "category_breakdown": self._build_category_breakdown(
                    component_breakdown,
                    total_value=result.final_value,
                ),
            }
        )
        return payload

    def _build_benchmark_payload(
        self,
        benchmark_entry: dict[str, Any],
        inflation_curve: pd.Series,
    ) -> dict[str, Any]:
        result: _SimulationResult = benchmark_entry["result"]
        payload = self._build_result_payload(result, inflation_curve)
        payload["benchmark_id"] = benchmark_entry["benchmark_id"]
        payload["label"] = benchmark_entry["label"]
        payload["equity_curve"] = self._serialize_curve(result.equity_curve)
        return payload

    def _build_fixed_income_backtest(
        self,
        *,
        results: list[_SimulationResult],
        comparison_instruments: list[InvestmentInstrument],
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        inflation_curve: pd.Series,
        fixed_income_study_mode: str,
        fixed_income_tax_treatment: str,
        fixed_income_window_frequency: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> dict[str, Any] | None:
        benchmark_result = self._ensure_fixed_income_benchmark_result(
            results=results,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
            series_cache=series_cache,
        )
        if benchmark_result is None:
            return None

        study_ids = self._resolve_fixed_income_study_ids(
            results=results,
            fixed_income_study_mode=fixed_income_study_mode,
        )
        if not study_ids:
            return None

        studies: list[dict[str, Any]] = []
        for study_id in study_ids:
            if study_id == "index_duration":
                study_payload = self._build_fixed_income_index_study(
                    results=results,
                    comparison_instruments=comparison_instruments,
                    benchmark_result=benchmark_result,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    monthly_contribution=monthly_contribution,
                    inflation_curve=inflation_curve,
                    fixed_income_tax_treatment=fixed_income_tax_treatment,
                    fixed_income_window_frequency=fixed_income_window_frequency,
                    force_download=force_download,
                    series_cache=series_cache,
                )
            else:
                study_payload = self._build_fixed_income_tesouro_study(
                    results=results,
                    comparison_instruments=comparison_instruments,
                    benchmark_result=benchmark_result,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    monthly_contribution=monthly_contribution,
                    inflation_curve=inflation_curve,
                    fixed_income_tax_treatment=fixed_income_tax_treatment,
                    fixed_income_window_frequency=fixed_income_window_frequency,
                    force_download=force_download,
                    series_cache=series_cache,
                )
            if study_payload is not None:
                studies.append(study_payload)

        if not studies:
            return None

        primary_study = studies[0]
        return {
            "requested_study_mode": fixed_income_study_mode,
            "tax_treatment": fixed_income_tax_treatment,
            "window_frequency": fixed_income_window_frequency,
            "selected_study_id": primary_study["study_id"],
            "selected_study_label": primary_study["study_label"],
            "study_count": len(studies),
            "studies": studies,
            "summary": {
                "available_study_ids": [item["study_id"] for item in studies],
                "takeaways": self._build_fixed_income_cross_study_takeaways(studies),
            },
            "methodology": primary_study["methodology"],
            "full_period": primary_study["full_period"],
            "rolling_windows": primary_study["rolling_windows"],
            "takeaways": primary_study["takeaways"],
        }

    def _ensure_fixed_income_benchmark_result(
        self,
        *,
        results: list[_SimulationResult],
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> _SimulationResult | None:
        benchmark_result = next(
            (item for item in results if item.instrument.instrument_id == "CDI_INDEX"),
            None,
        )
        if benchmark_result is not None:
            return benchmark_result

        benchmark_instrument = self.instrument_map.get("CDI_INDEX")
        if benchmark_instrument is None:
            return None
        return self._simulate_instrument(
            instrument=benchmark_instrument,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
            series_cache=series_cache,
        )

    def _resolve_fixed_income_study_ids(
        self,
        *,
        results: list[_SimulationResult],
        fixed_income_study_mode: str,
    ) -> list[str]:
        has_index_results = any(
            item.instrument.source_kind == "fixed_income_index" for item in results
        )
        has_treasury_results = any(
            item.instrument.source_kind == "tesouro_direct_strategy" for item in results
        )

        if fixed_income_study_mode == "index_duration":
            return ["index_duration"] if has_index_results else []
        if fixed_income_study_mode == "retail_treasury":
            return ["retail_treasury"] if has_treasury_results else []

        study_ids: list[str] = []
        if has_index_results:
            study_ids.append("index_duration")
        if has_treasury_results:
            study_ids.append("retail_treasury")
        return study_ids

    def _build_fixed_income_index_study(
        self,
        *,
        results: list[_SimulationResult],
        comparison_instruments: list[InvestmentInstrument],
        benchmark_result: _SimulationResult,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        inflation_curve: pd.Series,
        fixed_income_tax_treatment: str,
        fixed_income_window_frequency: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> dict[str, Any] | None:
        fixed_income_results = [
            item for item in results if item.instrument.source_kind == "fixed_income_index"
        ]
        if not fixed_income_results:
            return None

        all_results = list(fixed_income_results)
        if benchmark_result.instrument.instrument_id not in {
            item.instrument.instrument_id for item in all_results
        }:
            all_results.append(benchmark_result)

        benchmark_curve = self._load_fixed_income_index_series(
            instrument=benchmark_result.instrument,
            start_date=start_date,
            end_date=end_date,
            series_cache=series_cache,
            strict_start=False,
        )
        benchmark_row = self._build_fixed_income_result_row(
            result=benchmark_result,
            inflation_curve=inflation_curve,
            benchmark_result=benchmark_result,
            fixed_income_tax_treatment=fixed_income_tax_treatment,
        )

        rows = [
            self._build_fixed_income_result_row(
                result=result,
                inflation_curve=inflation_curve,
                benchmark_result=benchmark_result,
                fixed_income_tax_treatment=fixed_income_tax_treatment,
            )
            for result in all_results
        ]
        rows.sort(key=lambda item: float(item["display_value"]), reverse=True)

        rolling_windows: list[dict[str, Any]] = []
        for result in all_results:
            if result.instrument.instrument_id == benchmark_result.instrument.instrument_id:
                continue
            definition = get_fixed_income_definition(result.instrument.instrument_id)
            if definition is None:
                continue
            quote_curve = self._load_fixed_income_index_series(
                instrument=result.instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
                strict_start=False,
            )
            for window_years in (1, 2, 3, 5):
                stats = self._build_fixed_income_window_stats(
                    curve=quote_curve,
                    benchmark_curve=benchmark_curve,
                    window_years=window_years,
                    start_frequency=fixed_income_window_frequency,
                )
                if stats is None:
                    continue
                rolling_windows.append(
                    {
                        "study_id": "index_duration",
                        "instrument_id": result.instrument.instrument_id,
                        "label": result.instrument.label,
                        "source_kind": result.instrument.source_kind,
                        "family_id": definition.family_id,
                        "family_label": definition.family_label,
                        "duration_years": definition.duration_years,
                        **stats,
                    }
                )

        leaders = self._build_fixed_income_leaders(
            rows=rows,
            rolling_windows=rolling_windows,
        )
        selected_fixed_income = [
            item.instrument_id
            for item in comparison_instruments
            if item.source_kind == "fixed_income_index"
        ]
        methodology = {
            "study_id": "index_duration",
            "study_label": "Indices de duration constante",
            "benchmark_instrument_id": benchmark_result.instrument.instrument_id,
            "benchmark_label": benchmark_result.instrument.label,
            "series_source_label": "Mais Retorno API publica / indices de renda fixa",
            "series_source_url": "https://api.maisretorno.com/v3/",
            "index_methodology_label": "ANBIMA IDkA para durations constantes",
            "study_scope_label": "Indice rolante de duration constante",
            "what_it_measures": (
                "A dinamica das curvas de juros ao longo do tempo sem depender de um titulo "
                "especifico na prateleira do Tesouro."
            ),
            "what_it_does_not_measure": (
                "Nao replica exatamente um Tesouro IPCA+ ou Prefixado comprado no varejo e "
                "carregado ate o vencimento, nem impostos da pessoa fisica."
            ),
            "rolling_window_note": (
                "As janelas moveis usam cotacao historica dos indices para medir consistencia "
                "intrinseca de cada duration com inicios "
                f"{self._fixed_income_frequency_label(fixed_income_window_frequency)}."
            ),
            "full_period_note": (
                "O acumulado principal respeita o capital e os aportes do comparativo atual, "
                "mas a camada de indices continua sendo uma simplificacao didatica."
            ),
            "comparison_metric_label": self._fixed_income_metric_label(fixed_income_tax_treatment),
            "tax_treatment": fixed_income_tax_treatment,
            "window_frequency_requested": fixed_income_window_frequency,
            "window_frequency_effective": fixed_income_window_frequency,
            "selected_fixed_income_ids": selected_fixed_income,
            "video_reference_match": (
                start_date == "2005-12-30"
                and end_date == "2026-03-31"
                and initial_capital == 1000.0
                and monthly_contribution == 0.0
            ),
            "cache": build_fixed_income_cache_metadata(self.fixed_income_dir),
        }
        return {
            "study_id": "index_duration",
            "study_label": "Indices de duration constante",
            "methodology": methodology,
            "full_period": {
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": float(initial_capital),
                "monthly_contribution": float(monthly_contribution),
                "benchmark": benchmark_row,
                "results": rows,
                "leaders": leaders,
            },
            "rolling_windows": rolling_windows,
            "takeaways": self._build_fixed_income_takeaways(
                study_id="index_duration",
                rows=rows,
                benchmark_row=benchmark_row,
                leaders=leaders,
                rolling_windows=rolling_windows,
                initial_capital=initial_capital,
                fixed_income_tax_treatment=fixed_income_tax_treatment,
                requested_window_frequency=fixed_income_window_frequency,
                effective_window_frequency=fixed_income_window_frequency,
            ),
        }

    def _build_fixed_income_tesouro_study(
        self,
        *,
        results: list[_SimulationResult],
        comparison_instruments: list[InvestmentInstrument],
        benchmark_result: _SimulationResult,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        inflation_curve: pd.Series,
        fixed_income_tax_treatment: str,
        fixed_income_window_frequency: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> dict[str, Any] | None:
        treasury_results = [
            item for item in results if item.instrument.source_kind == "tesouro_direct_strategy"
        ]
        if not treasury_results:
            return None

        all_results = list(treasury_results)
        if benchmark_result.instrument.instrument_id not in {
            item.instrument.instrument_id for item in all_results
        }:
            all_results.append(benchmark_result)

        effective_window_frequency = (
            "monthly" if fixed_income_window_frequency == "daily" else fixed_income_window_frequency
        )
        benchmark_row = self._build_fixed_income_result_row(
            result=benchmark_result,
            inflation_curve=inflation_curve,
            benchmark_result=benchmark_result,
            fixed_income_tax_treatment=fixed_income_tax_treatment,
        )
        rows = [
            self._build_fixed_income_result_row(
                result=result,
                inflation_curve=inflation_curve,
                benchmark_result=benchmark_result,
                fixed_income_tax_treatment=fixed_income_tax_treatment,
            )
            for result in all_results
        ]
        rows.sort(key=lambda item: float(item["display_value"]), reverse=True)

        rolling_windows: list[dict[str, Any]] = []
        window_curve_cache: dict[str, pd.Series] = {}
        benchmark_window_curve = self._build_fixed_income_window_curve_for_instrument(
            instrument=benchmark_result.instrument,
            start_date=start_date,
            end_date=end_date,
            fixed_income_tax_treatment=fixed_income_tax_treatment,
            force_download=force_download,
            series_cache=series_cache,
            window_curve_cache=window_curve_cache,
        )
        for result in all_results:
            if result.instrument.instrument_id == benchmark_result.instrument.instrument_id:
                continue
            definition = get_tesouro_direto_strategy_definition(result.instrument.instrument_id)
            if definition is None:
                continue
            strategy_window_curve = self._build_fixed_income_window_curve_for_instrument(
                instrument=result.instrument,
                start_date=start_date,
                end_date=end_date,
                fixed_income_tax_treatment=fixed_income_tax_treatment,
                force_download=force_download,
                series_cache=series_cache,
                window_curve_cache=window_curve_cache,
            )
            for window_years in (1, 2, 3, 5):
                stats = self._build_fixed_income_window_stats(
                    curve=strategy_window_curve,
                    benchmark_curve=benchmark_window_curve,
                    window_years=window_years,
                    start_frequency=effective_window_frequency,
                )
                if stats is None:
                    continue
                rolling_windows.append(
                    {
                        "study_id": "retail_treasury",
                        "instrument_id": result.instrument.instrument_id,
                        "label": result.instrument.label,
                        "source_kind": result.instrument.source_kind,
                        "family_id": definition.family_id,
                        "family_label": definition.family_label,
                        "duration_years": definition.target_duration_years,
                        "window_frequency_requested": fixed_income_window_frequency,
                        **stats,
                    }
                )

        leaders = self._build_fixed_income_leaders(
            rows=rows,
            rolling_windows=rolling_windows,
        )
        selected_fixed_income = [
            item.instrument_id
            for item in comparison_instruments
            if item.source_kind == "tesouro_direct_strategy"
        ]
        methodology = {
            "study_id": "retail_treasury",
            "study_label": "Tesouro Direto historico oficial",
            "benchmark_instrument_id": benchmark_result.instrument.instrument_id,
            "benchmark_label": benchmark_result.instrument.label,
            "series_source_label": "Tesouro Transparente / Tesouro Direto",
            "series_source_url": TESOURO_DIRETO_CSV_URL,
            "index_methodology_label": (
                "Rolagem de titulos oficiais do Tesouro Direto por familia e duration alvo"
            ),
            "study_scope_label": "Produto real de varejo com compra, venda e rolagem",
            "what_it_measures": (
                "Uma aproximacao mais fiel da experiencia da pessoa fisica em Tesouro Selic, "
                "Tesouro Prefixado e Tesouro IPCA+, usando precos oficiais de compra e venda."
            ),
            "what_it_does_not_measure": (
                "Nao inclui LCI, LCA, CDB, taxas bancarias, debentures ou efeito de cupons. "
                "Tambem simplifica a rolagem para regras objetivas de duration alvo."
            ),
            "rolling_window_note": (
                "As janelas moveis usam uma curva normalizada sem aportes, derivada dos precos "
                "oficiais do Tesouro Direto, para medir consistencia da estrategia com impostos "
                "estimados e inicios "
                f"{self._fixed_income_frequency_label(effective_window_frequency)}."
            ),
            "full_period_note": (
                "O acumulado principal usa precos oficiais do Tesouro Direto, com visao bruta "
                "e liquidacao liquida estimada via IR regressivo e IOF inferior a 30 dias."
            ),
            "comparison_metric_label": self._fixed_income_metric_label(fixed_income_tax_treatment),
            "tax_treatment": fixed_income_tax_treatment,
            "window_frequency_requested": fixed_income_window_frequency,
            "window_frequency_effective": effective_window_frequency,
            "selected_fixed_income_ids": selected_fixed_income,
            "video_reference_match": False,
            "cache": build_tesouro_cache_metadata(self.tesouro_direto_dir),
            "benchmark_cache": build_fixed_income_cache_metadata(self.fixed_income_dir),
        }
        return {
            "study_id": "retail_treasury",
            "study_label": "Tesouro Direto historico oficial",
            "methodology": methodology,
            "full_period": {
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": float(initial_capital),
                "monthly_contribution": float(monthly_contribution),
                "benchmark": benchmark_row,
                "results": rows,
                "leaders": leaders,
            },
            "rolling_windows": rolling_windows,
            "takeaways": self._build_fixed_income_takeaways(
                study_id="retail_treasury",
                rows=rows,
                benchmark_row=benchmark_row,
                leaders=leaders,
                rolling_windows=rolling_windows,
                initial_capital=initial_capital,
                fixed_income_tax_treatment=fixed_income_tax_treatment,
                requested_window_frequency=fixed_income_window_frequency,
                effective_window_frequency=effective_window_frequency,
            ),
        }

    def _build_fixed_income_result_row(
        self,
        *,
        result: _SimulationResult,
        inflation_curve: pd.Series,
        benchmark_result: _SimulationResult,
        fixed_income_tax_treatment: str,
    ) -> dict[str, Any]:
        payload = self._build_result_payload(result, inflation_curve)
        benchmark_payload = (
            payload
            if result.instrument.instrument_id == benchmark_result.instrument.instrument_id
            else self._build_result_payload(benchmark_result, inflation_curve)
        )
        metric_fields = self._fixed_income_metric_fields(fixed_income_tax_treatment)
        definition_metadata = self._fixed_income_definition_metadata(result.instrument)
        benchmark_value = float(benchmark_payload[metric_fields["final_value"]])
        benchmark_real_value = float(benchmark_payload[metric_fields["final_value_real"]])
        display_value = float(payload[metric_fields["final_value"]])
        display_real_value = float(payload[metric_fields["final_value_real"]])
        row = {
            **payload,
            **definition_metadata,
            "display_value": display_value,
            "display_profit": float(payload[metric_fields["net_profit"]]),
            "display_cagr": float(payload[metric_fields["cagr"]]),
            "display_value_real": display_real_value,
            "display_profit_real": float(payload[metric_fields["net_profit_real"]]),
            "display_real_cagr": float(payload[metric_fields["real_cagr"]]),
            "comparison_metric_label": self._fixed_income_metric_label(fixed_income_tax_treatment),
            "relative_gap_vs_benchmark": (
                float(display_value / benchmark_value - 1.0) if benchmark_value > 0 else 0.0
            ),
            "value_gap_vs_benchmark": float(display_value - benchmark_value),
            "relative_gap_vs_benchmark_real": (
                float(display_real_value / benchmark_real_value - 1.0)
                if benchmark_real_value > 0
                else 0.0
            ),
            "value_gap_vs_benchmark_real": float(display_real_value - benchmark_real_value),
            "is_benchmark": (
                result.instrument.instrument_id == benchmark_result.instrument.instrument_id
            ),
        }
        return row

    def _fixed_income_definition_metadata(self, instrument: InvestmentInstrument) -> dict[str, Any]:
        if instrument.source_kind == "fixed_income_index":
            definition = get_fixed_income_definition(instrument.instrument_id)
            if definition is None:
                return {
                    "family_id": "unknown",
                    "family_label": "Renda fixa",
                    "duration_years": None,
                    "source_method_label": "Indice",
                }
            return {
                "family_id": definition.family_id,
                "family_label": definition.family_label,
                "duration_years": definition.duration_years,
                "source_method_label": "Indice de duration constante",
            }

        tesouro_definition = get_tesouro_direto_strategy_definition(instrument.instrument_id)
        if tesouro_definition is None:
            return {
                "family_id": "unknown",
                "family_label": "Renda fixa",
                "duration_years": None,
                "source_method_label": "Tesouro Direto",
            }
        return {
            "family_id": tesouro_definition.family_id,
            "family_label": tesouro_definition.family_label,
            "duration_years": tesouro_definition.target_duration_years,
            "title_type": tesouro_definition.title_type,
            "selection_rule": tesouro_definition.selection_rule,
            "source_method_label": "Rolagem oficial de Tesouro Direto",
        }

    def _fixed_income_metric_fields(self, tax_treatment: str) -> dict[str, str]:
        suffix = "_net" if tax_treatment in {"net", "both"} else ""
        return {
            "final_value": f"final_value{suffix}",
            "net_profit": f"net_profit{suffix}",
            "cagr": f"cagr{suffix}",
            "final_value_real": f"final_value_real{suffix}",
            "net_profit_real": f"net_profit_real{suffix}",
            "real_cagr": f"real_cagr{suffix}",
        }

    def _fixed_income_metric_label(self, tax_treatment: str) -> str:
        if tax_treatment == "gross":
            return "valor bruto"
        if tax_treatment == "net":
            return "valor liquido estimado"
        return "valor liquido estimado com bruto disponivel"

    def _fixed_income_frequency_label(self, frequency: str) -> str:
        return "mensais" if frequency == "monthly" else "diarios"

    def _build_fixed_income_leaders(
        self,
        *,
        rows: list[dict[str, Any]],
        rolling_windows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        leaders: dict[str, Any] = {}
        if rows:
            leaders["overall"] = max(rows, key=lambda item: float(item["display_value"]))
            leaders["best_real_cagr"] = max(
                rows,
                key=lambda item: float(item["display_real_cagr"]),
            )
        for family_id in {"post_fixed", "prefixado", "ipca_plus"}:
            family_rows = [row for row in rows if row["family_id"] == family_id]
            if family_rows:
                leaders[family_id] = max(
                    family_rows,
                    key=lambda item: float(item["display_value"]),
                )
        consistency_pool = [row for row in rolling_windows if row["window_years"] == 5]
        if consistency_pool:
            leaders["most_consistent"] = max(
                consistency_pool,
                key=lambda item: float(item["win_rate"]),
            )
        return leaders

    def _build_fixed_income_takeaways(
        self,
        *,
        study_id: str,
        rows: list[dict[str, Any]],
        benchmark_row: dict[str, Any],
        leaders: dict[str, Any],
        rolling_windows: list[dict[str, Any]],
        initial_capital: float,
        fixed_income_tax_treatment: str,
        requested_window_frequency: str,
        effective_window_frequency: str,
    ) -> list[str]:
        takeaways: list[str] = []
        comparison_label = self._fixed_income_metric_label(fixed_income_tax_treatment)
        overall_leader = leaders.get("overall")
        if overall_leader is not None:
            takeaways.append(
                f"Na visao de {comparison_label}, {overall_leader['label']} liderou o periodo "
                f"cheio com R$ {overall_leader['display_value']:.2f} para cada "
                f"R$ {initial_capital:.2f} de capital inicial."
            )
        takeaways.append(
            f"O benchmark {benchmark_row['label']} terminou em "
            f"R$ {benchmark_row['display_value']:.2f} na mesma agenda de aportes."
        )

        prefixado_leader = leaders.get("prefixado")
        if prefixado_leader is not None:
            takeaways.append(
                f"Entre os prefixados, {prefixado_leader['label']} foi o melhor no acumulado."
            )
        ipca_leader = leaders.get("ipca_plus")
        if ipca_leader is not None:
            takeaways.append(
                f"Entre os IPCA+, {ipca_leader['label']} foi o melhor no periodo cheio."
            )
        most_consistent = leaders.get("most_consistent")
        if most_consistent is not None:
            takeaways.append(
                f"Em janelas moveis de 5 anos, {most_consistent['label']} venceu o CDI em "
                f"{most_consistent['win_rate']:.2%} das vezes."
            )

        if study_id == "index_duration":
            short_ipca = self._pick_duration_row(rows, family_id="ipca_plus", side="min")
            long_ipca = self._pick_duration_row(rows, family_id="ipca_plus", side="max")
            if short_ipca is not None and long_ipca is not None and short_ipca != long_ipca:
                ipca_gap = float(long_ipca["display_value"] / short_ipca["display_value"] - 1.0)
                takeaways.append(
                    f"Nos IPCA+, alongar do curto para o longo mudou {ipca_gap:.2%} no acumulado, "
                    "reforcando a tese de premio relativamente pequeno para mais duration."
                )

            short_pre = self._pick_duration_row(rows, family_id="prefixado", side="min")
            long_pre = self._pick_duration_row(rows, family_id="prefixado", side="max")
            if short_pre is not None and long_pre is not None and short_pre != long_pre:
                pre_gap = float(long_pre["display_value"] / short_pre["display_value"] - 1.0)
                takeaways.append(
                    f"Nos prefixados, alongar do curto para o longo mudou {pre_gap:.2%}, "
                    "um salto bem mais visivel do que no bloco de IPCA+."
                )

        if study_id == "retail_treasury" and fixed_income_tax_treatment in {"net", "both"}:
            taxed_rows = [
                row
                for row in rows
                if not row["is_benchmark"] and float(row.get("taxes_paid_total", 0.0)) > 0
            ]
            if taxed_rows:
                heaviest_tax = max(taxed_rows, key=lambda item: float(item["taxes_paid_total"]))
                takeaways.append(
                    f"Na prateleira real do Tesouro, {heaviest_tax['label']} acumulou cerca de "
                    f"R$ {heaviest_tax['taxes_paid_total']:.2f} em impostos estimados."
                )
        if requested_window_frequency != effective_window_frequency:
            takeaways.append(
                "As janelas moveis foram reduzidas para inicios mensais porque a simulacao "
                "titulo a titulo do Tesouro Direto fica mais fiel e mais estavel nesse ritmo."
            )
        return takeaways

    def _pick_duration_row(
        self,
        rows: list[dict[str, Any]],
        *,
        family_id: str,
        side: str,
    ) -> dict[str, Any] | None:
        candidates = [
            row
            for row in rows
            if row["family_id"] == family_id
            and row.get("duration_years") is not None
            and not row.get("is_benchmark", False)
        ]
        if not candidates:
            return None
        if side == "min":
            return min(candidates, key=lambda item: float(item["duration_years"]))
        return max(candidates, key=lambda item: float(item["duration_years"]))

    def _build_fixed_income_cross_study_takeaways(
        self,
        studies: list[dict[str, Any]],
    ) -> list[str]:
        if len(studies) < 2:
            return []
        lookup = {item["study_id"]: item for item in studies}
        index_study = lookup.get("index_duration")
        treasury_study = lookup.get("retail_treasury")
        if index_study is None or treasury_study is None:
            return []

        index_leader = index_study["full_period"]["leaders"].get("overall")
        treasury_leader = treasury_study["full_period"]["leaders"].get("overall")
        if index_leader is None or treasury_leader is None:
            return []

        takeaways = [
            (
                f"No estudo por indice, {index_leader['label']} liderou; no estudo com Tesouro "
                f"Direto real, {treasury_leader['label']} liderou."
            )
        ]
        if index_leader["instrument_id"] != treasury_leader["instrument_id"]:
            takeaways.append(
                "A resposta muda quando saimos do indice teorico e entramos no produto real, "
                "porque impostos, disponibilidade de papeis e precos de compra e venda "
                "passam a importar."
            )
        return takeaways

    def _build_fixed_income_window_stats(
        self,
        *,
        curve: pd.Series,
        benchmark_curve: pd.Series,
        window_years: int,
        start_frequency: str,
    ) -> dict[str, Any] | None:
        index = curve.index.intersection(benchmark_curve.index)
        if index.empty:
            return None
        aligned_curve = curve.reindex(index)
        aligned_benchmark = benchmark_curve.reindex(index)
        start_dates = self._select_window_start_dates(index, start_frequency)
        excess_returns: list[float] = []
        wins = 0
        best_window: tuple[float, pd.Timestamp, pd.Timestamp] | None = None
        worst_window: tuple[float, pd.Timestamp, pd.Timestamp] | None = None

        for start_date in start_dates:
            target_date = start_date + pd.DateOffset(years=window_years)
            if target_date > index[-1]:
                continue
            end_position = index.searchsorted(target_date, side="right") - 1
            if end_position < 0:
                continue
            end_date = index[end_position]
            if end_date <= start_date:
                continue
            asset_return = float(aligned_curve.loc[end_date] / aligned_curve.loc[start_date] - 1.0)
            benchmark_return = float(
                aligned_benchmark.loc[end_date] / aligned_benchmark.loc[start_date] - 1.0
            )
            excess_return = asset_return - benchmark_return
            excess_returns.append(excess_return)
            if excess_return > 0:
                wins += 1
            if best_window is None or excess_return > best_window[0]:
                best_window = (excess_return, start_date, end_date)
            if worst_window is None or excess_return < worst_window[0]:
                worst_window = (excess_return, start_date, end_date)

        if not excess_returns:
            return None

        excess_array = np.asarray(excess_returns, dtype=float)
        return {
            "window_years": window_years,
            "window_frequency": start_frequency,
            "windows_count": int(len(excess_returns)),
            "win_rate": float(wins / len(excess_returns)),
            "average_excess_return": float(excess_array.mean()),
            "median_excess_return": float(np.median(excess_array)),
            "best_excess_return": float(excess_array.max()),
            "worst_excess_return": float(excess_array.min()),
            "best_window_start": (str(best_window[1].date()) if best_window is not None else None),
            "best_window_end": str(best_window[2].date()) if best_window is not None else None,
            "worst_window_start": (
                str(worst_window[1].date()) if worst_window is not None else None
            ),
            "worst_window_end": str(worst_window[2].date()) if worst_window is not None else None,
        }

    def _build_fixed_income_window_stats_from_simulations(
        self,
        *,
        instrument: InvestmentInstrument,
        benchmark_instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        window_years: int,
        initial_capital: float,
        monthly_contribution: float,
        inflation_curve: pd.Series,
        fixed_income_tax_treatment: str,
        requested_frequency: str,
        effective_frequency: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
        simulation_cache: dict[tuple[str, str, str], dict[str, Any]],
    ) -> dict[str, Any] | None:
        metric_fields = self._fixed_income_metric_fields(fixed_income_tax_treatment)
        asset_index = self._fixed_income_observation_index(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
        )
        benchmark_index = self._fixed_income_observation_index(
            instrument=benchmark_instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
        )
        common_index = asset_index.intersection(benchmark_index)
        if common_index.empty:
            return None
        start_dates = self._select_window_start_dates(common_index, effective_frequency)
        excess_returns: list[float] = []
        wins = 0
        best_window: tuple[float, pd.Timestamp, pd.Timestamp] | None = None
        worst_window: tuple[float, pd.Timestamp, pd.Timestamp] | None = None

        for candidate_start in start_dates:
            target_date = candidate_start + pd.DateOffset(years=window_years)
            if target_date > common_index[-1]:
                continue
            end_position = common_index.searchsorted(target_date, side="right") - 1
            if end_position < 0:
                continue
            candidate_end = common_index[end_position]
            if candidate_end <= candidate_start:
                continue

            asset_payload = self._simulate_fixed_income_window_payload(
                instrument=instrument,
                start_date=str(candidate_start.date()),
                end_date=str(candidate_end.date()),
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                inflation_curve=inflation_curve,
                force_download=force_download,
                series_cache=series_cache,
                simulation_cache=simulation_cache,
            )
            benchmark_payload = self._simulate_fixed_income_window_payload(
                instrument=benchmark_instrument,
                start_date=str(candidate_start.date()),
                end_date=str(candidate_end.date()),
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                inflation_curve=inflation_curve,
                force_download=force_download,
                series_cache=series_cache,
                simulation_cache=simulation_cache,
            )
            asset_invested = max(float(asset_payload["invested_total"]), 1e-9)
            benchmark_invested = max(float(benchmark_payload["invested_total"]), 1e-9)
            asset_return = float(asset_payload[metric_fields["final_value"]] / asset_invested - 1.0)
            benchmark_return = float(
                benchmark_payload[metric_fields["final_value"]] / benchmark_invested - 1.0
            )
            excess_return = asset_return - benchmark_return
            excess_returns.append(excess_return)
            if excess_return > 0:
                wins += 1
            if best_window is None or excess_return > best_window[0]:
                best_window = (excess_return, candidate_start, candidate_end)
            if worst_window is None or excess_return < worst_window[0]:
                worst_window = (excess_return, candidate_start, candidate_end)

        if not excess_returns:
            return None

        excess_array = np.asarray(excess_returns, dtype=float)
        return {
            "window_years": window_years,
            "window_frequency": effective_frequency,
            "window_frequency_requested": requested_frequency,
            "windows_count": int(len(excess_returns)),
            "win_rate": float(wins / len(excess_returns)),
            "average_excess_return": float(excess_array.mean()),
            "median_excess_return": float(np.median(excess_array)),
            "best_excess_return": float(excess_array.max()),
            "worst_excess_return": float(excess_array.min()),
            "best_window_start": (str(best_window[1].date()) if best_window is not None else None),
            "best_window_end": str(best_window[2].date()) if best_window is not None else None,
            "worst_window_start": (
                str(worst_window[1].date()) if worst_window is not None else None
            ),
            "worst_window_end": str(worst_window[2].date()) if worst_window is not None else None,
        }

    def _simulate_fixed_income_window_payload(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        inflation_curve: pd.Series,
        force_download: bool,
        series_cache: dict[str, pd.Series],
        simulation_cache: dict[tuple[str, str, str], dict[str, Any]],
    ) -> dict[str, Any]:
        cache_key = (instrument.instrument_id, start_date, end_date)
        cached = simulation_cache.get(cache_key)
        if cached is not None:
            return cached
        result = self._simulate_instrument(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
            series_cache=series_cache,
        )
        payload = self._build_result_payload(result, inflation_curve)
        simulation_cache[cache_key] = payload
        return payload

    def _fixed_income_observation_index(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> pd.DatetimeIndex:
        if instrument.source_kind == "fixed_income_index":
            curve = self._load_fixed_income_index_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
                strict_start=False,
            )
            return curve.index
        if instrument.source_kind == "tesouro_direct_strategy":
            definition = get_tesouro_direto_strategy_definition(instrument.instrument_id)
            if definition is None:
                return pd.DatetimeIndex([])
            prepared = self._prepare_tesouro_family_history(
                start_date=start_date,
                end_date=end_date,
                title_type=definition.title_type,
                force_download=force_download,
            )
            return prepared["dates"]
        return pd.DatetimeIndex([])

    def _select_window_start_dates(
        self,
        index: pd.DatetimeIndex,
        start_frequency: str,
    ) -> pd.DatetimeIndex:
        if start_frequency != "monthly" or len(index) <= 1:
            return index
        periods = index.to_period("M")
        mask: list[bool] = [True]
        if len(index) > 1:
            mask.extend((periods[1:] != periods[:-1]).tolist())
        return index[mask]

    def _build_fixed_income_window_curve_for_instrument(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        fixed_income_tax_treatment: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
        window_curve_cache: dict[str, pd.Series],
    ) -> pd.Series:
        cached = window_curve_cache.get(instrument.instrument_id)
        if cached is not None:
            return cached

        result = self._simulate_instrument(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            initial_capital=1000.0,
            monthly_contribution=0.0,
            force_download=force_download,
            series_cache=series_cache,
        )
        curve = (
            result.net_liquidation_curve
            if (
                fixed_income_tax_treatment in {"net", "both"}
                and result.net_liquidation_curve is not None
            )
            else result.equity_curve
        )
        normalized = curve.astype(float) / max(float(curve.iloc[0]), 1e-9)
        window_curve_cache[instrument.instrument_id] = normalized
        return normalized

    def _build_component_breakdown(
        self,
        result: _SimulationResult,
    ) -> list[dict[str, Any]]:
        if not result.instrument.components or not result.component_values:
            return []

        total_value = max(result.final_value, 1e-9)
        total_target = sum(weight for _, weight in result.instrument.components) or 1.0
        breakdown: list[dict[str, Any]] = []
        for component_id, weight in result.instrument.components:
            component_meta = self.instrument_map.get(component_id)
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

    def _build_category_breakdown(
        self,
        component_breakdown: list[dict[str, Any]],
        *,
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

    def _build_class_summary(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for result in results:
            grouped.setdefault(str(result["category_label"]), []).append(result)

        summary: list[dict[str, Any]] = []
        for category_label, items in grouped.items():
            summary.append(
                {
                    "category_label": category_label,
                    "asset_count": len(items),
                    "average_final_value": float(
                        np.mean([float(item["final_value"]) for item in items])
                    ),
                    "average_cagr": float(np.mean([float(item["cagr"]) for item in items])),
                    "average_real_cagr": float(
                        np.mean([float(item["real_cagr"]) for item in items])
                    ),
                    "average_max_drawdown": float(
                        np.mean([float(item["max_drawdown"]) for item in items])
                    ),
                    "leader_label": max(
                        items,
                        key=lambda item: float(item["final_value"]),
                    )["label"],
                }
            )
        return sorted(summary, key=lambda item: item["average_final_value"], reverse=True)

    def _build_highlights(
        self,
        results: list[dict[str, Any]],
        benchmarks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ordered = sorted(results, key=lambda item: float(item["final_value"]), reverse=True)
        best = ordered[0]
        best_real = max(results, key=lambda item: float(item["real_cagr"]))
        defensive = max(results, key=lambda item: float(item["max_drawdown"]))
        selic = next((item for item in benchmarks if item["benchmark_id"] == "selic_cash"), None)
        bova11 = next((item for item in benchmarks if item["benchmark_id"] == "bova11"), None)

        def _count_beating(benchmark: dict[str, Any] | None) -> int | None:
            if benchmark is None:
                return None
            return sum(
                1
                for item in results
                if float(item["final_value"]) > float(benchmark["final_value"])
            )

        beat_inflation_count = sum(
            1
            for item in results
            if float(item["final_value_real"]) > float(item["invested_total_real"])
        )
        insights = [
            f"{best['label']} foi o melhor comparativo em valor final nominal no periodo.",
            (
                f"{best_real['label']} entregou o melhor CAGR real, ou seja, "
                "o melhor ganho de poder de compra."
            ),
            (
                f"{defensive['label']} teve a queda maxima menos dolorosa "
                "entre os ativos escolhidos."
            ),
            (
                f"{beat_inflation_count} de {len(results)} comparativos preservaram "
                "ou ampliaram poder de compra acima da inflacao."
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
            "best_final_value": best,
            "best_real_cagr": best_real,
            "most_defensive": defensive,
            "beats_selic_count": _count_beating(selic),
            "beats_bova11_count": _count_beating(bova11),
            "beats_inflation_count": beat_inflation_count,
            "insights": insights,
        }

    def _build_inflation_summary(self, inflation_curve: pd.Series) -> dict[str, Any]:
        final_factor = float(inflation_curve.iloc[-1]) if not inflation_curve.empty else 1.0
        return {
            "label": "IPCA acumulado",
            "accumulated_rate": final_factor - 1.0,
            "purchasing_power_loss": 1.0 - (1.0 / final_factor if final_factor > 0 else 1.0),
            "availability_start": str(inflation_curve.index.min().date()),
            "availability_end": str(inflation_curve.index.max().date()),
            "source_label": "Banco Central do Brasil / SGS 433",
        }

    def _deflate_curve(self, curve: pd.Series, inflation_curve: pd.Series) -> pd.Series:
        aligned_inflation = inflation_curve.reindex(curve.index).ffill().bfill()
        aligned_inflation = aligned_inflation.where(aligned_inflation > 0, 1.0)
        real_curve = curve.divide(aligned_inflation)
        return real_curve.astype(float)

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

    def _intersection_index(self, series_list: list[pd.Series]) -> pd.DatetimeIndex:
        if not series_list:
            return pd.DatetimeIndex([])
        index = series_list[0].index
        for series in series_list[1:]:
            index = index.intersection(series.index)
        return index.sort_values()

    def _build_custom_portfolio_instruments(
        self,
        custom_portfolios: list[dict[str, Any]],
        *,
        warnings: list[str],
    ) -> list[InvestmentInstrument]:
        instruments: list[InvestmentInstrument] = []
        for position, payload in enumerate(custom_portfolios, start=1):
            label = str(payload.get("label") or f"Carteira personalizada {position}").strip()
            description = str(payload.get("description") or "").strip()
            normalized_components: list[tuple[str, float]] = []
            for component in payload.get("components") or []:
                component_id = str(component.get("component_id") or "").strip()
                if not component_id:
                    continue
                component_meta = self.instrument_map.get(component_id)
                if component_meta is None:
                    warnings.append(
                        "A carteira personalizada "
                        f"'{label}' ignorou o ativo desconhecido {component_id}."
                    )
                    continue
                weight = float(component.get("weight") or 0.0)
                if weight <= 0:
                    continue
                normalized_components.append((component_id, weight))

            if not normalized_components:
                warnings.append(
                    "A carteira personalizada "
                    f"'{label}' foi ignorada porque nao possui componentes validos."
                )
                continue

            instrument_id = str(payload.get("portfolio_id") or "").strip()
            if not instrument_id:
                slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
                instrument_id = f"CUSTOM_PORTFOLIO_{slug or position}"

            instruments.append(
                InvestmentInstrument(
                    instrument_id=instrument_id,
                    label=label,
                    ticker=None,
                    category_id="custom_portfolios",
                    category_label=CATEGORY_LABELS["custom_portfolios"],
                    description=(
                        description or "Carteira montada pelo usuario para comparar alocacoes."
                    ),
                    rationale=(
                        "Permite comparar uma alocacao personalizada contra ativos "
                        "isolados e carteiras guiadas."
                    ),
                    risk_label="Mista",
                    region_label="Brasil + exterior conforme os componentes",
                    source_kind="custom_portfolio",
                    listed_on_b3=False,
                    uses_adjusted_close=False,
                    rebalance_frequency=str(payload.get("rebalance_frequency") or "monthly"),
                    implementation_note=(
                        description
                        or "Rebalanceamento mensal com base nos pesos definidos pelo usuario."
                    ),
                    components=tuple(normalized_components),
                )
            )
        return instruments

    def _serialize_custom_portfolio_request(
        self,
        instrument: InvestmentInstrument,
    ) -> dict[str, Any]:
        return {
            "portfolio_id": instrument.instrument_id,
            "label": instrument.label,
            "description": instrument.description,
            "rebalance_frequency": instrument.rebalance_frequency,
            "components": [
                {"component_id": component_id, "weight": weight}
                for component_id, weight in instrument.components
            ],
        }

    def _series_color(self, series_id: str) -> str:
        palette = {
            "SELIC_PROXY": "#10b981",
            "CDI_PROXY": "#14b8a6",
            "CDI_INDEX": "#1d4ed8",
            "IPCA_PROXY": "#f97316",
            "IPCA_PLUS_6_PROXY": "#0f766e",
            "PREFIXADO_11_PROXY": "#f59e0b",
            "IDKA_PRE_1A": "#f59e0b",
            "IDKA_PRE_2A": "#fb923c",
            "IDKA_PRE_3A": "#ea580c",
            "IDKA_PRE_5A": "#9a3412",
            "IDKA_IPCA_2A": "#0f766e",
            "IDKA_IPCA_3A": "#14b8a6",
            "IDKA_IPCA_5A": "#0f766e",
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
            "IRFM11": "#7c3aed",
            "SMAL11": "#f43f5e",
            "DIVO11": "#eab308",
            "AAPL34": "#38bdf8",
            "MSFT34": "#0ea5e9",
            "GOGL34": "#60a5fa",
        }
        if series_id.startswith("CUSTOM_PORTFOLIO_"):
            return "#111827"
        return palette.get(series_id, "#94a3b8")
