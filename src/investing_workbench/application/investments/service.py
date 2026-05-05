"""Didactic cross-asset comparison service for B3-listed investments."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.data import get_data
from src.selic import get_daily_rate, get_or_create_daily_selic_data

from .cache_status import build_investment_cache_status
from .catalog import (
    INSTRUMENTS,
    PRESETS,
    InvestmentInstrument,
    build_catalog_payload,
)
from .compare_inputs import prepare_comparison_inputs
from .final_quality import build_study_quality_summary
from .fixed_income import get_or_create_fixed_income_quotes
from .fixed_income_studies import FixedIncomeStudyService
from .inflation import get_monthly_ipca_rate, get_or_create_ipca_data
from .market_rankings import build_market_rankings
from .market_screeners import build_market_screeners
from .narratives import (
    build_fixed_income_decision_guide,
    build_methodology_guide,
    build_portfolio_objective_summary,
)
from .portfolio_builder import (
    build_custom_portfolio_instruments,
    serialize_custom_portfolio_request,
)
from .portfolio_lifecycle import build_portfolio_lifecycle_scenarios
from .product_realism import build_product_realism_metadata
from .result_payloads import (
    build_benchmark_payload,
    build_chart_points,
    build_inflation_summary,
    deflate_curve,
    union_index,
)
from .retail_fixed_income import (
    build_retail_fixed_income_equivalence,
    fixed_income_exit_taxes,
)
from .simulation_engine import InvestmentSimulationEngine
from .simulation_models import SimulationResult
from .summaries import build_class_summary, build_highlights, build_result_stories
from .tesouro_direto import (
    TESOURO_DIRETO_CSV_URL,
    get_or_create_tesouro_direto_history,
)


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
        self._simulation_engine = InvestmentSimulationEngine(
            instrument_map=self.instrument_map,
            data_dir=self.data_dir,
            fixed_income_dir=self.fixed_income_dir,
            tesouro_direto_dir=self.tesouro_direto_dir,
            selic_path=self.selic_path,
            inflation_path=self.inflation_path,
            fallback_rate_annual=self.fallback_rate_annual,
            inflation_fallback_rate_annual=self.inflation_fallback_rate_annual,
            fixed_income_exit_taxes_func=fixed_income_exit_taxes,
            get_daily_rate_func=get_daily_rate,
            get_or_create_daily_selic_data_func=get_or_create_daily_selic_data,
            get_data_func=get_data,
            get_fixed_income_quotes_func=get_or_create_fixed_income_quotes,
            get_monthly_ipca_rate_func=get_monthly_ipca_rate,
            get_or_create_ipca_data_func=get_or_create_ipca_data,
            get_tesouro_direto_history_func=get_or_create_tesouro_direto_history,
        )
        self._fixed_income_studies = FixedIncomeStudyService(self)

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

    def build_market_rankings_snapshot(
        self,
        *,
        preset_id: str = "first_steps",
        asset_ids: list[str] | None = None,
        start_date: str = "2021-01-01",
        end_date: str | None = None,
        initial_capital: float = 10000.0,
        monthly_contribution: float = 0.0,
        benchmark_ids: list[str] | None = None,
        decision_profile: dict[str, Any] | None = None,
        force_download: bool = False,
    ) -> dict[str, Any]:
        """Build a compact rankings/screeners snapshot for market exploration."""
        selected_asset_ids = asset_ids or self._preset_asset_ids(preset_id)
        resolved_benchmarks = benchmark_ids or ["selic_cash"]
        comparison = self.compare(
            asset_ids=selected_asset_ids,
            custom_portfolios=[],
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            benchmark_ids=resolved_benchmarks,
            fixed_income_study_mode="auto",
            fixed_income_tax_treatment="gross",
            fixed_income_window_frequency="monthly",
            decision_profile=decision_profile,
            force_download=force_download,
        )
        return {
            "generated_at": comparison["generated_at"],
            "request": {
                "preset_id": preset_id,
                "asset_ids": selected_asset_ids,
                "start_date": start_date,
                "end_date": comparison["request"].get("end_date"),
                "benchmark_ids": resolved_benchmarks,
                "decision_profile": comparison["request"].get("decision_profile", {}),
                "force_download": force_download,
            },
            "market_rankings": comparison["market_rankings"],
            "market_screeners": comparison["market_screeners"],
            "cache_status": comparison["cache_status"],
            "warnings": comparison["warnings"],
        }

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
        decision_profile: dict[str, Any] | None = None,
        force_download: bool = False,
    ) -> dict[str, Any]:
        prepared_inputs = prepare_comparison_inputs(
            asset_ids=asset_ids,
            instrument_map=self.instrument_map,
            custom_portfolios=custom_portfolios,
            custom_portfolio_builder=lambda portfolios, warnings: (
                build_custom_portfolio_instruments(
                    portfolios,
                    warnings=warnings,
                    instrument_map=self.instrument_map,
                )
            ),
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            benchmark_ids=benchmark_ids,
            fixed_income_study_mode=fixed_income_study_mode,
            fixed_income_tax_treatment=fixed_income_tax_treatment,
            fixed_income_window_frequency=fixed_income_window_frequency,
            decision_profile=decision_profile,
        )
        generated_at = prepared_inputs.generated_at
        end_date_resolved = prepared_inputs.end_date_resolved
        normalized_decision_profile = prepared_inputs.normalized_decision_profile
        benchmark_keys = prepared_inputs.benchmark_keys
        warnings = prepared_inputs.warnings
        series_cache: dict[str, pd.Series] = {}
        selected_assets = prepared_inputs.selected_assets
        custom_instruments = prepared_inputs.custom_instruments
        comparison_instruments = prepared_inputs.comparison_instruments

        results: list[SimulationResult] = []
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
            self._build_result_payload(
                result=result,
                inflation_curve=inflation_curve,
            )
            for result in ordered_results
        ]
        benchmark_payloads = [
            build_benchmark_payload(
                benchmark_entry=entry,
                inflation_curve=inflation_curve,
                instrument_map=self.instrument_map,
            )
            for entry in benchmark_entries
        ]

        union_index_ = union_index(
            [item.equity_curve for item in results]
            + [item["result"].equity_curve for item in benchmark_entries]
        )
        chart_points = build_chart_points(union_index_, chart_curves)
        real_chart_curves = {
            series_id: deflate_curve(curve, inflation_curve)
            for series_id, curve in chart_curves.items()
        }
        real_chart_points = build_chart_points(union_index_, real_chart_curves)
        class_summary = build_class_summary(result_payloads)
        highlight_summary = build_highlights(result_payloads, benchmark_payloads)
        fixed_income_backtest = self._fixed_income_studies.build_backtest(
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
        assumptions = [
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
        ]
        methodology_guide = build_methodology_guide(
            results=result_payloads,
            benchmarks=benchmark_payloads,
            fixed_income_backtest=fixed_income_backtest,
            assumptions=assumptions,
            decision_profile=normalized_decision_profile,
        )
        fixed_income_decision_guide = build_fixed_income_decision_guide(
            fixed_income_backtest=fixed_income_backtest,
            decision_profile=normalized_decision_profile,
        )
        portfolio_objective_summary = build_portfolio_objective_summary(
            results=result_payloads,
            fixed_income_backtest=fixed_income_backtest,
            decision_profile=normalized_decision_profile,
        )
        portfolio_lifecycle = build_portfolio_lifecycle_scenarios(
            results=result_payloads,
            decision_profile=normalized_decision_profile,
        )
        product_realism = build_product_realism_metadata(
            results=result_payloads,
            benchmarks=benchmark_payloads,
            fixed_income_backtest=fixed_income_backtest,
            decision_profile=normalized_decision_profile,
        )
        retail_fixed_income_equivalence = build_retail_fixed_income_equivalence(
            decision_profile=normalized_decision_profile,
            fixed_income_backtest=fixed_income_backtest,
        )
        result_stories = build_result_stories(
            result_payloads,
            benchmark_payloads,
            decision_profile=normalized_decision_profile,
        )
        market_rankings = build_market_rankings(
            results=result_payloads,
            benchmarks=benchmark_payloads,
            decision_profile=normalized_decision_profile,
            simulation_results=ordered_results,
            benchmark_results={
                str(entry["benchmark_id"]): entry["result"] for entry in benchmark_entries
            },
            beta_reference_id=benchmark_reference_id,
        )
        market_screeners = build_market_screeners(results=result_payloads)
        cache_status = build_investment_cache_status(
            data_dir=self.data_dir,
            fixed_income_dir=self.fixed_income_dir,
            tesouro_direto_dir=self.tesouro_direto_dir,
            fixed_income_backtest=fixed_income_backtest,
        )
        study_quality = build_study_quality_summary(
            result_count=len(result_payloads),
            warning_count=len(warnings),
            methodology_guide=methodology_guide,
            product_realism=product_realism,
            retail_fixed_income_equivalence=retail_fixed_income_equivalence,
            result_stories=result_stories,
            market_rankings=market_rankings,
            market_screeners=market_screeners,
            cache_status=cache_status,
            portfolio_lifecycle=portfolio_lifecycle,
            fixed_income_backtest=fixed_income_backtest,
        )

        return {
            "generated_at": generated_at,
            "request": {
                "asset_ids": [item.instrument_id for item in selected_assets],
                "custom_portfolios": [
                    serialize_custom_portfolio_request(item) for item in custom_instruments
                ],
                "start_date": start_date,
                "end_date": end_date_resolved,
                "initial_capital": initial_capital,
                "monthly_contribution": monthly_contribution,
                "benchmark_ids": benchmark_keys,
                "fixed_income_study_mode": fixed_income_study_mode,
                "fixed_income_tax_treatment": fixed_income_tax_treatment,
                "fixed_income_window_frequency": fixed_income_window_frequency,
                "decision_profile": normalized_decision_profile,
                "force_download": force_download,
            },
            "catalog_snapshot": {
                "categories": build_catalog_payload()["categories"],
                "selected_assets": [item.to_payload() for item in comparison_instruments],
                "presets": [item.to_payload() for item in PRESETS],
            },
            "assumptions": assumptions,
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
            "inflation": build_inflation_summary(inflation_curve),
            "class_summary": class_summary,
            "highlights": highlight_summary,
            "fixed_income_backtest": fixed_income_backtest,
            "methodology_guide": methodology_guide,
            "product_realism": product_realism,
            "retail_fixed_income_equivalence": retail_fixed_income_equivalence,
            "result_stories": result_stories,
            "market_rankings": market_rankings,
            "market_screeners": market_screeners,
            "cache_status": cache_status,
            "fixed_income_decision_guide": fixed_income_decision_guide,
            "portfolio_objective_summary": portfolio_objective_summary,
            "portfolio_lifecycle": portfolio_lifecycle,
            "study_quality": study_quality,
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
    ) -> SimulationResult:
        return self._simulation_engine.simulate_instrument(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
            series_cache=series_cache,
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
        return self._simulation_engine.load_adjusted_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            series_cache=series_cache,
            strict_start=strict_start,
        )

    def _load_fixed_income_index_series(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
        strict_start: bool = True,
    ) -> pd.Series:
        return self._simulation_engine.load_fixed_income_index_series(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            series_cache=series_cache,
            strict_start=strict_start,
        )

    def _prepare_tesouro_family_history(
        self,
        *,
        start_date: str,
        end_date: str,
        title_type: str,
        force_download: bool,
    ) -> dict[str, Any]:
        return self._simulation_engine.prepare_tesouro_family_history(
            start_date=start_date,
            end_date=end_date,
            title_type=title_type,
            force_download=force_download,
        )

    def _build_result_payload(
        self,
        result: SimulationResult,
        inflation_curve: pd.Series,
    ) -> dict[str, Any]:
        return self._simulation_engine.build_result_payload(
            result=result,
            inflation_curve=inflation_curve,
        )

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
        return self._simulation_engine.build_benchmark_entry(
            benchmark_id=benchmark_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
            series_cache=series_cache,
        )

    def _build_inflation_price_series(
        self,
        *,
        start_date: str,
        end_date: str,
        series_cache: dict[str, pd.Series],
    ) -> pd.Series:
        return self._simulation_engine.build_inflation_price_series(
            start_date=start_date,
            end_date=end_date,
            series_cache=series_cache,
        )

    def _series_color(self, series_id: str) -> str:
        return self._simulation_engine.series_color(series_id)

    def _preset_asset_ids(self, preset_id: str) -> list[str]:
        preset = next((item for item in PRESETS if item.preset_id == preset_id), None)
        if preset is None:
            raise ValueError(f"Preset de ranking de mercado invalido: {preset_id}")
        return list(preset.asset_ids)
