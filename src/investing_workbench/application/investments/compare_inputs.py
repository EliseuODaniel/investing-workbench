"""Input validation and normalization for investment comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from .catalog import BENCHMARK_OPTIONS, InvestmentInstrument
from .decision_profile import normalize_decision_profile


@dataclass(frozen=True)
class PreparedComparisonInputs:
    """Validated comparison inputs ready for orchestration."""

    generated_at: datetime
    end_date_resolved: str
    normalized_decision_profile: dict[str, Any]
    benchmark_keys: list[str]
    warnings: list[str]
    selected_assets: list[InvestmentInstrument]
    custom_instruments: list[InvestmentInstrument]
    comparison_instruments: list[InvestmentInstrument]


CustomPortfolioBuilder = Callable[[list[dict[str, Any]], list[str]], list[InvestmentInstrument]]


def prepare_comparison_inputs(
    *,
    asset_ids: list[str],
    instrument_map: dict[str, InvestmentInstrument],
    custom_portfolios: list[dict[str, Any]] | None,
    custom_portfolio_builder: CustomPortfolioBuilder,
    end_date: str | None,
    initial_capital: float,
    monthly_contribution: float,
    benchmark_ids: list[str] | None,
    fixed_income_study_mode: str,
    fixed_income_tax_treatment: str,
    fixed_income_window_frequency: str,
    decision_profile: dict[str, Any] | None,
) -> PreparedComparisonInputs:
    """Validate request-level fields and resolve selected instruments."""
    _validate_comparison_parameters(
        asset_ids=asset_ids,
        custom_portfolios=custom_portfolios,
        initial_capital=initial_capital,
        monthly_contribution=monthly_contribution,
        fixed_income_study_mode=fixed_income_study_mode,
        fixed_income_tax_treatment=fixed_income_tax_treatment,
        fixed_income_window_frequency=fixed_income_window_frequency,
    )

    generated_at = datetime.now(UTC)
    warnings: list[str] = []
    selected_assets = _resolve_selected_assets(
        asset_ids=asset_ids,
        instrument_map=instrument_map,
        warnings=warnings,
    )
    custom_instruments = custom_portfolio_builder(custom_portfolios or [], warnings)
    comparison_instruments = [*selected_assets, *custom_instruments]
    if not comparison_instruments:
        raise ValueError("Nenhum investimento valido foi reconhecido pelo comparador.")

    return PreparedComparisonInputs(
        generated_at=generated_at,
        end_date_resolved=end_date or generated_at.strftime("%Y-%m-%d"),
        normalized_decision_profile=normalize_decision_profile(decision_profile),
        benchmark_keys=(
            benchmark_ids
            if benchmark_ids is not None
            else [item["benchmark_id"] for item in BENCHMARK_OPTIONS]
        ),
        warnings=warnings,
        selected_assets=selected_assets,
        custom_instruments=custom_instruments,
        comparison_instruments=comparison_instruments,
    )


def _validate_comparison_parameters(
    *,
    asset_ids: list[str],
    custom_portfolios: list[dict[str, Any]] | None,
    initial_capital: float,
    monthly_contribution: float,
    fixed_income_study_mode: str,
    fixed_income_tax_treatment: str,
    fixed_income_window_frequency: str,
) -> None:
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


def _resolve_selected_assets(
    *,
    asset_ids: list[str],
    instrument_map: dict[str, InvestmentInstrument],
    warnings: list[str],
) -> list[InvestmentInstrument]:
    selected_assets: list[InvestmentInstrument] = []
    for asset_id in asset_ids:
        instrument = instrument_map.get(asset_id)
        if instrument is None:
            warnings.append(f"Ativo desconhecido ignorado: {asset_id}")
            continue
        selected_assets.append(instrument)
    return selected_assets
