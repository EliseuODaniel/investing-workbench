"""Simulation engine used by the investment comparison service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.data import get_data
from src.selic import get_daily_rate, get_or_create_daily_selic_data

from .catalog import InvestmentInstrument
from .data_loading import InvestmentDataLoader
from .fixed_income import get_or_create_fixed_income_quotes
from .inflation import get_monthly_ipca_rate, get_or_create_ipca_data
from .market_proxy_simulation import build_market_proxy_price_series
from .market_simulation import (
    build_contribution_schedule,
    simulate_buy_and_hold_with_aportes,
    simulate_selic_proxy,
)
from .portfolio_simulation import simulate_model_portfolio
from .result_payloads import build_result_payload, summarize_curves
from .retail_fixed_income import fixed_income_exit_taxes
from .simulation_models import SimulationResult
from .tesouro_direto import get_or_create_tesouro_direto_history
from .tesouro_simulation import TesouroSimulationService


class InvestmentSimulationEngine:
    """Encapsulate simulation mechanics used by investment comparison."""

    def __init__(
        self,
        *,
        instrument_map: dict[str, InvestmentInstrument],
        data_dir: str | Path,
        fixed_income_dir: str | Path,
        tesouro_direto_dir: str | Path,
        selic_path: str,
        inflation_path: str,
        fallback_rate_annual: float,
        inflation_fallback_rate_annual: float,
        fixed_income_exit_taxes_func: Callable[..., float] = fixed_income_exit_taxes,
        get_daily_rate_func: Callable[..., float] = get_daily_rate,
        get_or_create_daily_selic_data_func: Any = get_or_create_daily_selic_data,
        get_data_func: Any = get_data,
        get_fixed_income_quotes_func: Any = get_or_create_fixed_income_quotes,
        get_monthly_ipca_rate_func: Any = get_monthly_ipca_rate,
        get_or_create_ipca_data_func: Any = get_or_create_ipca_data,
        get_tesouro_direto_history_func: Any = get_or_create_tesouro_direto_history,
    ) -> None:
        self.instrument_map = instrument_map
        self.selic_path = selic_path
        self.inflation_path = inflation_path
        self.fallback_rate_annual = fallback_rate_annual
        self.inflation_fallback_rate_annual = inflation_fallback_rate_annual
        self._fixed_income_exit_taxes = fixed_income_exit_taxes_func
        self._get_daily_rate = get_daily_rate_func
        self._get_or_create_daily_selic_data = get_or_create_daily_selic_data_func
        self._get_monthly_ipca_rate = get_monthly_ipca_rate_func
        self._get_or_create_ipca_data = get_or_create_ipca_data_func
        self._data_loader = InvestmentDataLoader(
            data_dir=data_dir,
            fixed_income_dir=fixed_income_dir,
            tesouro_direto_dir=tesouro_direto_dir,
            selic_path=selic_path,
            inflation_path=inflation_path,
            get_data_func=get_data_func,
            get_fixed_income_quotes_func=get_fixed_income_quotes_func,
            get_tesouro_direto_history_func=get_tesouro_direto_history_func,
        )
        self._tesouro_simulation = TesouroSimulationService(
            load_tesouro_family_history=self.prepare_tesouro_family_history,
            fixed_income_exit_taxes_func=self._fixed_income_exit_taxes,
        )

    def simulate_instrument(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> SimulationResult:
        if instrument.source_kind == "selic_proxy":
            equity_curve, flow_curve = simulate_selic_proxy(
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                monthly_contribution=monthly_contribution,
                selic_path=self.selic_path,
                fallback_rate_annual=self.fallback_rate_annual,
                get_or_create_daily_selic_data=self._get_or_create_daily_selic_data,
                get_daily_rate=self._get_daily_rate,
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
            price_series = self.load_fixed_income_index_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
            )
            equity_curve, flow_curve = simulate_buy_and_hold_with_aportes(
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
            price_series = self.build_proxy_price_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
            )
            equity_curve, flow_curve = simulate_buy_and_hold_with_aportes(
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

        price_series = self.load_adjusted_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
        )
        equity_curve, flow_curve = simulate_buy_and_hold_with_aportes(
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

    def load_adjusted_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
        strict_start: bool = True,
    ) -> pd.Series:
        return self._data_loader.load_adjusted_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
            strict_start=strict_start,
        )

    def load_fixed_income_index_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
        strict_start: bool = True,
    ) -> pd.Series:
        return self._data_loader.load_fixed_income_index_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            series_cache=series_cache,
            strict_start=strict_start,
        )

    def load_tesouro_direto_history(
        self,
        *,
        start_date: str,
        end_date: str,
        force_download: bool,
    ) -> pd.DataFrame:
        return self._data_loader.load_tesouro_direto_history(
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
        )

    def prepare_tesouro_family_history(
        self,
        *,
        start_date: str,
        end_date: str,
        title_type: str,
        force_download: bool,
    ) -> dict[str, Any]:
        return self._data_loader.prepare_tesouro_family_history(
            start_date=start_date,
            end_date=end_date,
            title_type=title_type,
            force_download=force_download,
        )

    def build_result_payload(
        self,
        result: SimulationResult,
        inflation_curve: pd.Series,
    ) -> dict[str, Any]:
        return build_result_payload(
            result=result,
            inflation_curve=inflation_curve,
            instrument_map=self.instrument_map,
        )

    def build_proxy_price_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
    ) -> pd.Series:
        return build_market_proxy_price_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            series_cache=series_cache,
            selic_path=self.selic_path,
            inflation_path=self.inflation_path,
            fallback_rate_annual=self.fallback_rate_annual,
            inflation_fallback_rate_annual=self.inflation_fallback_rate_annual,
            get_or_create_daily_selic_data=self._get_or_create_daily_selic_data,
            get_daily_rate=self._get_daily_rate,
            get_or_create_ipca_data=self._get_or_create_ipca_data,
            get_monthly_ipca_rate=self._get_monthly_ipca_rate,
        )

    def build_inflation_price_series(
        self,
        *,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
    ) -> pd.Series:
        inflation_instrument = self.instrument_map.get("IPCA_PROXY")
        if inflation_instrument is None:
            raise ValueError("O proxy de inflacao IPCA nao esta configurado no catalogo.")
        return self.build_proxy_price_series(
            instrument=inflation_instrument,
            start_date=start_date,
            end_date=end_date,
            series_cache=series_cache,
        )

    def series_color(self, series_id: str) -> str:
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
            "IMBB11": "#4f46e5",
            "B5P211": "#059669",
            "B5MB11": "#0f766e",
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

    def build_benchmark_entry(
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
            result = self.simulate_instrument(
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
            result = self.simulate_instrument(
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
        def _load_component_series_for_portfolio(
            component: InvestmentInstrument,
            start: str,
            end: str,
            force_dl: bool,
            cache: dict[str, pd.Series],
        ) -> pd.Series:
            return self._load_component_series(
                instrument=component,
                start_date=start,
                end_date=end,
                force_download=force_dl,
                series_cache=cache,
            )

        def _build_schedule(
            index: pd.DatetimeIndex,
            initial_cash: float,
            contribution: float,
        ) -> dict[pd.Timestamp, float]:
            return build_contribution_schedule(
                index=index,
                initial_capital=initial_cash,
                monthly_contribution=contribution,
            )

        return simulate_model_portfolio(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
            series_cache=series_cache,
            load_component_series=_load_component_series_for_portfolio,
            build_contribution_schedule=_build_schedule,
            pick_component_series=lambda component_id: self.instrument_map.get(component_id),
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
            return self.build_proxy_price_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
            )
        if instrument.source_kind == "fixed_income_index":
            return self.load_fixed_income_index_series(
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                series_cache=series_cache,
                strict_start=False,
            )
        return self.load_adjusted_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
            strict_start=False,
        )

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
        return self._tesouro_simulation.run_strategy(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
        )

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
    ) -> SimulationResult:
        metrics = summarize_curves(equity_curve, flow_curve)
        return SimulationResult(
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
