"""Investor decision profile helpers for didactic investment comparisons."""

from __future__ import annotations

from typing import Any

_OBJECTIVES = {
    "balanced": "Equilibrar retorno e risco",
    "reserve": "Reserva e liquidez",
    "real_return": "Ganhar acima da inflacao",
    "income": "Gerar renda",
    "growth": "Crescer patrimonio",
    "retirement": "Aposentadoria",
}

_LIQUIDITY_NEEDS = {
    "daily": "Posso precisar a qualquer momento",
    "monthly": "Posso esperar algumas semanas",
    "long_term": "Nao preciso de liquidez no curto prazo",
}

_MARK_TO_MARKET_TOLERANCE = {
    "low": "Baixa",
    "medium": "Media",
    "high": "Alta",
}

_TAX_VIEWS = {
    "gross": "Bruta",
    "net": "Liquida estimada",
    "both": "Bruta e liquida",
}

DEFAULT_DECISION_PROFILE: dict[str, Any] = {
    "objective": "balanced",
    "horizon_years": 5,
    "liquidity_need": "monthly",
    "mark_to_market_tolerance": "medium",
    "tax_view": "gross",
    "monthly_income_target": 0.0,
}


def normalize_decision_profile(raw_profile: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize optional user preferences into a stable response payload."""

    raw = {**DEFAULT_DECISION_PROFILE, **(raw_profile or {})}
    objective = _normalize_choice(
        raw.get("objective"),
        choices=_OBJECTIVES,
        field_name="objective",
    )
    liquidity_need = _normalize_choice(
        raw.get("liquidity_need"),
        choices=_LIQUIDITY_NEEDS,
        field_name="liquidity_need",
    )
    mark_to_market_tolerance = _normalize_choice(
        raw.get("mark_to_market_tolerance"),
        choices=_MARK_TO_MARKET_TOLERANCE,
        field_name="mark_to_market_tolerance",
    )
    tax_view = _normalize_choice(
        raw.get("tax_view"),
        choices=_TAX_VIEWS,
        field_name="tax_view",
    )
    horizon_years = _bounded_int(raw.get("horizon_years"), minimum=1, maximum=40)
    monthly_income_target = max(0.0, _safe_float(raw.get("monthly_income_target")))

    return {
        "objective": objective,
        "objective_label": _OBJECTIVES[objective],
        "horizon_years": horizon_years,
        "liquidity_need": liquidity_need,
        "liquidity_need_label": _LIQUIDITY_NEEDS[liquidity_need],
        "mark_to_market_tolerance": mark_to_market_tolerance,
        "mark_to_market_tolerance_label": _MARK_TO_MARKET_TOLERANCE[mark_to_market_tolerance],
        "tax_view": tax_view,
        "tax_view_label": _TAX_VIEWS[tax_view],
        "monthly_income_target": monthly_income_target,
    }


def build_decision_profile_notes(profile: dict[str, Any]) -> list[str]:
    """Plain-language notes that explain how the profile affects interpretation."""

    notes = [
        (
            f"Objetivo informado: {profile['objective_label']} em um horizonte de "
            f"{profile['horizon_years']} ano(s)."
        ),
        f"Liquidez: {profile['liquidity_need_label']}.",
        (
            "Tolerancia a marcacao a mercado: "
            f"{profile['mark_to_market_tolerance_label'].lower()}."
        ),
        f"Leitura tributaria preferida: {profile['tax_view_label'].lower()}.",
    ]
    if profile["monthly_income_target"] > 0:
        notes.append(
            "Meta de renda mensal informada: "
            f"R$ {profile['monthly_income_target']:,.2f} antes de ajustes finos."
        )
    return notes


def decision_profile_options() -> dict[str, Any]:
    """Expose available profile choices to tests or future catalog responses."""

    return {
        "objectives": _OBJECTIVES,
        "liquidity_needs": _LIQUIDITY_NEEDS,
        "mark_to_market_tolerances": _MARK_TO_MARKET_TOLERANCE,
        "tax_views": _TAX_VIEWS,
        "defaults": DEFAULT_DECISION_PROFILE,
    }


def _normalize_choice(
    value: Any,
    *,
    choices: dict[str, str],
    field_name: str,
) -> str:
    normalized = str(value or "").strip()
    if normalized not in choices:
        valid = ", ".join(sorted(choices))
        raise ValueError(f"Perfil de decisao invalido para {field_name}: use {valid}.")
    return normalized


def _bounded_int(value: Any, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = int(DEFAULT_DECISION_PROFILE["horizon_years"])
    return min(max(parsed, minimum), maximum)


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
