"""Fixed-income studies extracted from the investments service."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .fixed_income import build_fixed_income_cache_metadata, get_fixed_income_definition
from .simulation_models import SimulationResult
from .tesouro_direto import (
    TESOURO_DIRETO_CSV_URL,
    build_tesouro_cache_metadata,
    get_tesouro_direto_strategy_definition,
)


class FixedIncomeStudyService:
    """Build didactic fixed-income studies from simulated results."""

    def __init__(self, service: Any) -> None:
        self._service = service

    def build_backtest(
        self,
        *,
        results: list[SimulationResult],
        comparison_instruments: list[Any],
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
        results: list[SimulationResult],
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> SimulationResult | None:
        benchmark_result = next(
            (item for item in results if item.instrument.instrument_id == "CDI_INDEX"),
            None,
        )
        if benchmark_result is not None:
            return benchmark_result

        benchmark_instrument = self._service.instrument_map.get("CDI_INDEX")
        if benchmark_instrument is None:
            return None
        return self._service._simulate_instrument(
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
        results: list[SimulationResult],
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
        results: list[SimulationResult],
        comparison_instruments: list[Any],
        benchmark_result: SimulationResult,
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

        benchmark_curve = self._service._load_fixed_income_index_series(
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
            quote_curve = self._service._load_fixed_income_index_series(
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
            "cache": build_fixed_income_cache_metadata(self._service.fixed_income_dir),
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
        results: list[SimulationResult],
        comparison_instruments: list[Any],
        benchmark_result: SimulationResult,
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
            "cache": build_tesouro_cache_metadata(self._service.tesouro_direto_dir),
            "benchmark_cache": build_fixed_income_cache_metadata(self._service.fixed_income_dir),
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
        result: SimulationResult,
        inflation_curve: pd.Series,
        benchmark_result: SimulationResult,
        fixed_income_tax_treatment: str,
    ) -> dict[str, Any]:
        payload = self._service._build_result_payload(result, inflation_curve)
        benchmark_payload = (
            payload
            if result.instrument.instrument_id == benchmark_result.instrument.instrument_id
            else self._service._build_result_payload(benchmark_result, inflation_curve)
        )
        metric_fields = self._fixed_income_metric_fields(fixed_income_tax_treatment)
        definition_metadata = self._fixed_income_definition_metadata(result.instrument)
        benchmark_value = float(benchmark_payload[metric_fields["final_value"]])
        benchmark_real_value = float(benchmark_payload[metric_fields["final_value_real"]])
        display_value = float(payload[metric_fields["final_value"]])
        display_real_value = float(payload[metric_fields["final_value_real"]])
        return {
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

    def _fixed_income_definition_metadata(self, instrument: Any) -> dict[str, Any]:
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
                    "Nos IPCA+, alongar do curto para o longo mudou "
                    f"{ipca_gap:.2%} no acumulado, reforcando a tese de premio relativamente "
                    "pequeno para mais duration."
                )

            short_pre = self._pick_duration_row(rows, family_id="prefixado", side="min")
            long_pre = self._pick_duration_row(rows, family_id="prefixado", side="max")
            if short_pre is not None and long_pre is not None and short_pre != long_pre:
                pre_gap = float(long_pre["display_value"] / short_pre["display_value"] - 1.0)
                takeaways.append(
                    "Nos prefixados, alongar do curto para o longo mudou "
                    f"{pre_gap:.2%}, um salto bem mais visivel do que no bloco de IPCA+."
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
        instrument: Any,
        benchmark_instrument: Any,
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
        instrument: Any,
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
        result = self._service._simulate_instrument(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            force_download=force_download,
            series_cache=series_cache,
        )
        payload = self._service._build_result_payload(result, inflation_curve)
        simulation_cache[cache_key] = payload
        return payload

    def _fixed_income_observation_index(
        self,
        *,
        instrument: Any,
        start_date: str,
        end_date: str,
        force_download: bool,
        series_cache: dict[str, pd.Series],
    ) -> pd.DatetimeIndex:
        if instrument.source_kind == "fixed_income_index":
            curve = self._service._load_fixed_income_index_series(
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
            prepared = self._service._prepare_tesouro_family_history(
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
        instrument: Any,
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

        result = self._service._simulate_instrument(
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
