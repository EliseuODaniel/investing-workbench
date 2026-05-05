"""Retail fixed-income helpers for didactic comparisons."""

from __future__ import annotations

from typing import Any, TypedDict

FIXED_INCOME_IOF_TABLE: dict[int, float] = {
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

_REFERENCE_CDI_ANNUAL_RATE = 0.105
_TAX_EXEMPT_CDI_RATES = (0.80, 0.85, 0.90, 0.95, 1.00)
_TAX_EXEMPT_PRODUCTS = ("LCI/LCA", "Debenture incentivada")


class _TaxableProductExample(TypedDict):
    product_id: str
    label: str
    gross_pct_cdi: float
    annual_fee_rate: float
    liquidity: str
    credit_note: str


_TAXABLE_PRODUCT_EXAMPLES: tuple[_TaxableProductExample, ...] = (
    {
        "product_id": "cdb_liquidez_diaria_100_cdi",
        "label": "CDB liquidez diaria 100% CDI",
        "gross_pct_cdi": 1.00,
        "annual_fee_rate": 0.0,
        "liquidity": "D+0/D+1, conforme emissor",
        "credit_note": "Risco de credito do emissor, normalmente com FGC ate limites aplicaveis.",
    },
    {
        "product_id": "tesouro_selic_proxy",
        "label": "Tesouro Selic como referencia de varejo",
        "gross_pct_cdi": 0.98,
        "annual_fee_rate": 0.0,
        "liquidity": "Liquidez diaria via Tesouro Direto, sujeita a calendario e spread/preco.",
        "credit_note": "Risco soberano e marcacao a mercado geralmente baixa, mas nao nula.",
    },
    {
        "product_id": "fundo_di_025_fee",
        "label": "Fundo DI 100% CDI com taxa 0,25% a.a.",
        "gross_pct_cdi": 1.00,
        "annual_fee_rate": 0.0025,
        "liquidity": "Liquidez depende do fundo; pode haver D+0, D+1 ou mais.",
        "credit_note": (
            "Risco de carteira, taxa de administracao e possivel come-cotas nao modelado."
        ),
    },
    {
        "product_id": "fundo_di_100_fee",
        "label": "Fundo DI 100% CDI com taxa 1,00% a.a.",
        "gross_pct_cdi": 1.00,
        "annual_fee_rate": 0.01,
        "liquidity": "Liquidez depende do fundo; taxa alta pode consumir parte relevante do CDI.",
        "credit_note": (
            "Risco de carteira, taxa de administracao e possivel come-cotas nao modelado."
        ),
    },
)


def fixed_income_ir_rate(holding_days: int) -> float:
    """Return the Brazilian regressive fixed-income IR rate for a holding period."""

    if holding_days <= 180:
        return 0.225
    if holding_days <= 360:
        return 0.20
    if holding_days <= 720:
        return 0.175
    return 0.15


def fixed_income_iof_rate(holding_days: int) -> float:
    """Return IOF rate for gains on redemptions below 30 calendar days."""

    return FIXED_INCOME_IOF_TABLE.get(holding_days, 0.0) if holding_days < 30 else 0.0


def fixed_income_exit_taxes(
    *,
    cost_basis: float,
    sale_value: float,
    holding_days: int,
) -> float:
    """Estimate IR + IOF on fixed-income gains for one liquidation event."""

    gross_gain = max(0.0, float(sale_value - cost_basis))
    if gross_gain <= 0:
        return 0.0
    iof_tax = gross_gain * fixed_income_iof_rate(holding_days)
    ir_tax = max(0.0, gross_gain - iof_tax) * fixed_income_ir_rate(holding_days)
    return float(iof_tax + ir_tax)


def build_retail_fixed_income_equivalence(
    *,
    decision_profile: dict[str, Any],
    fixed_income_backtest: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a first retail CDB versus LCI/LCA after-tax equivalence table."""

    profile_horizon_years = int(decision_profile.get("horizon_years") or 5)
    profile_holding_days = max(30, int(round(profile_horizon_years * 365.25)))
    horizons = sorted({180, 360, 720, profile_holding_days})
    rows: list[dict[str, Any]] = []
    for holding_days in horizons:
        for tax_exempt_product in _TAX_EXEMPT_PRODUCTS:
            for tax_exempt_pct_cdi in _TAX_EXEMPT_CDI_RATES:
                rows.append(
                    _build_equivalence_row(
                        holding_days=holding_days,
                        tax_exempt_product=tax_exempt_product,
                        tax_exempt_pct_cdi=tax_exempt_pct_cdi,
                        reference_cdi_annual_rate=_REFERENCE_CDI_ANNUAL_RATE,
                    )
                )

    return {
        "title": "Equivalencia liquida em renda fixa de varejo",
        "plain_language_summary": (
            "Esta tabela responde uma pergunta pratica: quanto um CDB tributado precisaria "
            "pagar em % do CDI para empatar, depois de IR e IOF, com uma LCI/LCA isenta."
        ),
        "reference_cdi_annual_rate": _REFERENCE_CDI_ANNUAL_RATE,
        "profile_horizon_days": profile_holding_days,
        "profile_horizon_label": (f"{profile_horizon_years} ano(s), conforme o perfil de decisao"),
        "uses_fixed_income_backtest": fixed_income_backtest is not None,
        "rows": rows,
        "taxable_product_examples": [
            _build_taxable_product_example(
                holding_days=profile_holding_days,
                reference_cdi_annual_rate=_REFERENCE_CDI_ANNUAL_RATE,
                **example,
            )
            for example in _TAXABLE_PRODUCT_EXAMPLES
        ],
        "assumptions": [
            "LCI/LCA e debenture incentivada sao tratadas como isentas de IR para pessoa fisica.",
            (
                "CDB e Tesouro seguem IR regressivo sobre o ganho e IOF para resgates "
                "antes de 30 dias."
            ),
            (
                "Exemplos de Tesouro Selic e fundos DI usam percentuais aproximados do CDI "
                "e taxas informadas como premissas didaticas, nao como oferta real."
            ),
            "A conta usa uma taxa CDI anual de referencia e nao busca ofertas reais de mercado.",
            (
                "Nao inclui FGC, risco de credito, carencia, liquidez secundaria, spread "
                "ou aporte minimo."
            ),
        ],
        "next_steps": [
            "Permitir editar CDI esperado, prazo e percentual do CDI.",
            (
                "Adicionar CDB com liquidez diaria, CDB no vencimento, LCI/LCA com "
                "carencia e debentures incentivadas."
            ),
            (
                "Comparar equivalencia liquida contra Tesouro Selic e fundos DI com "
                "taxa de administracao."
            ),
        ],
    }


def _build_taxable_product_example(
    *,
    holding_days: int,
    reference_cdi_annual_rate: float,
    product_id: str,
    label: str,
    gross_pct_cdi: float,
    annual_fee_rate: float,
    liquidity: str,
    credit_note: str,
) -> dict[str, Any]:
    years = max(float(holding_days) / 365.25, 1.0 / 365.25)
    ir_rate = fixed_income_ir_rate(holding_days)
    iof_rate = fixed_income_iof_rate(holding_days)
    gross_annual_rate = max(0.0, reference_cdi_annual_rate * gross_pct_cdi - annual_fee_rate)
    gross_final_factor = (1.0 + gross_annual_rate) ** years
    gross_gain = max(0.0, gross_final_factor - 1.0)
    iof_tax = gross_gain * iof_rate
    ir_tax = max(0.0, gross_gain - iof_tax) * ir_rate
    net_gain = max(0.0, gross_gain - iof_tax - ir_tax)
    net_final_factor = 1.0 + net_gain
    net_annual_rate = net_final_factor ** (1.0 / years) - 1.0
    net_pct_cdi = net_annual_rate / reference_cdi_annual_rate

    return {
        "product_id": product_id,
        "label": label,
        "holding_days": holding_days,
        "gross_pct_cdi": gross_pct_cdi,
        "annual_fee_rate": annual_fee_rate,
        "gross_annual_rate": gross_annual_rate,
        "ir_rate": ir_rate,
        "iof_rate": iof_rate,
        "net_annual_rate": net_annual_rate,
        "net_pct_cdi": net_pct_cdi,
        "liquidity": liquidity,
        "credit_note": credit_note,
        "interpretation": (
            f"{label} entrega aproximadamente {net_pct_cdi:.0%} do CDI liquido "
            f"em {holding_days} dias, antes de spreads, come-cotas ou detalhes da oferta."
        ),
    }


def _build_equivalence_row(
    *,
    holding_days: int,
    tax_exempt_product: str,
    tax_exempt_pct_cdi: float,
    reference_cdi_annual_rate: float,
) -> dict[str, Any]:
    years = max(float(holding_days) / 365.25, 1.0 / 365.25)
    ir_rate = fixed_income_ir_rate(holding_days)
    iof_rate = fixed_income_iof_rate(holding_days)
    net_gain_retention = (1.0 - iof_rate) * (1.0 - ir_rate)
    tax_exempt_annual_rate = reference_cdi_annual_rate * tax_exempt_pct_cdi
    tax_exempt_final_factor = (1.0 + tax_exempt_annual_rate) ** years
    taxable_gross_final_factor = 1.0 + (
        (tax_exempt_final_factor - 1.0) / max(net_gain_retention, 1e-9)
    )
    equivalent_cdb_annual_rate = taxable_gross_final_factor ** (1.0 / years) - 1.0
    equivalent_cdb_pct_cdi = equivalent_cdb_annual_rate / reference_cdi_annual_rate

    return {
        "holding_days": holding_days,
        "holding_years": years,
        "tax_exempt_product": tax_exempt_product,
        "tax_exempt_pct_cdi": tax_exempt_pct_cdi,
        "tax_exempt_annual_rate": tax_exempt_annual_rate,
        "ir_rate": ir_rate,
        "iof_rate": iof_rate,
        "net_gain_retention": net_gain_retention,
        "equivalent_cdb_pct_cdi": equivalent_cdb_pct_cdi,
        "equivalent_cdb_annual_rate": equivalent_cdb_annual_rate,
        "interpretation": (
            f"Uma {tax_exempt_product} a {tax_exempt_pct_cdi:.0%} do CDI por {holding_days} dias "
            f"equivale aproximadamente a um CDB a {equivalent_cdb_pct_cdi:.0%} do CDI."
        ),
    }
