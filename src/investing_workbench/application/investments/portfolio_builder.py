"""Helpers to normalize and serialize custom portfolio payloads."""

from __future__ import annotations

import re
from typing import Any

from .catalog import CATEGORY_LABELS, InvestmentInstrument


def build_custom_portfolio_instruments(
    custom_portfolios: list[dict[str, Any]],
    *,
    warnings: list[str],
    instrument_map: dict[str, InvestmentInstrument],
) -> list[InvestmentInstrument]:
    """Build portfolio instruments from user supplied component payloads."""
    instruments: list[InvestmentInstrument] = []
    for position, payload in enumerate(custom_portfolios, start=1):
        label = str(payload.get("label") or f"Carteira personalizada {position}").strip()
        description = str(payload.get("description") or "").strip()
        normalized_components: list[tuple[str, float]] = []
        for component in payload.get("components") or []:
            component_id = str(component.get("component_id") or "").strip()
            if not component_id:
                continue
            component_meta = instrument_map.get(component_id)
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


def serialize_custom_portfolio_request(instrument: InvestmentInstrument) -> dict[str, Any]:
    """Serialize a normalized custom portfolio for request echo payloads."""
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
