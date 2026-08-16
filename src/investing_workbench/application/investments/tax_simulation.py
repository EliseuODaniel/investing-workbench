"""Detailed Brazilian multi-asset tax simulation on liquidation and income."""

from __future__ import annotations

from typing import TypedDict


class AssetTaxHolding(TypedDict):
    instrument_id: str
    label: str
    asset_class: str  # "stocks", "fiis", "fixed_income_taxable", "fixed_income_exempt", etc.
    cost_basis: float
    current_value: float
    holding_days: int


class AssetLiquidationTaxResult(TypedDict):
    instrument_id: str
    label: str
    asset_class: str
    cost_basis: float
    sale_value: float
    capital_gain: float
    taxable_gain: float
    tax_rate_pct: float
    iof_rate_pct: float
    iof_amount: float
    tax_due: float
    net_proceeds: float
    is_exempt: bool
    exemption_rule: str | None


class PortfolioLiquidationTaxReport(TypedDict):
    total_cost_basis: float
    total_sale_value: float
    total_gross_profit: float
    total_taxable_gain: float
    total_tax_due: float
    total_iof_due: float
    total_net_proceeds: float
    effective_tax_rate_pct: float
    stock_monthly_sales_total: float
    stock_exemption_applied: bool
    assets: list[AssetLiquidationTaxResult]
    methodology: str


# Regressive IOF table for the first 29 days
IOF_REGRESSIVE_RATES: dict[int, float] = {
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


def simulate_portfolio_liquidation_tax(
    holdings: list[AssetTaxHolding],
    other_monthly_stock_sales: float = 0.0,
) -> PortfolioLiquidationTaxReport:
    """Calculate exact Brazilian income tax on liquidation of a multi-asset portfolio."""

    total_stock_sales = (
        sum(h["current_value"] for h in holdings if h["asset_class"] == "stocks")
        + other_monthly_stock_sales
    )
    stock_exemption_applies = total_stock_sales <= 20000.0

    asset_results: list[AssetLiquidationTaxResult] = []
    total_cost = 0.0
    total_sale = 0.0
    total_profit = 0.0
    total_taxable = 0.0
    total_tax = 0.0
    total_iof = 0.0
    total_net = 0.0

    for h in holdings:
        cost = max(0.0, float(h["cost_basis"]))
        sale = max(0.0, float(h["current_value"]))
        days = max(1, int(h["holding_days"]))
        gain = max(0.0, sale - cost)
        asset_class = h["asset_class"]

        tax_rate = 0.0
        iof_rate = 0.0
        is_exempt = False
        exemption_rule = None

        if asset_class == "stocks":
            if stock_exemption_applies:
                is_exempt = True
                exemption_rule = (
                    "Isencao de IR para vendas mensais de acoes <= R$ 20.000 (Lei 9.250/95)"
                )
                tax_rate = 0.0
            else:
                tax_rate = 0.15
        elif asset_class == "fiis":
            tax_rate = 0.20  # 20% on capital gain for FIIs
        elif asset_class == "fixed_income_exempt":
            is_exempt = True
            exemption_rule = (
                "Isencao de IR para LCI/LCA/CRI/CRA/Debentures (Lei 11.033/04 e 12.431/11)"
            )
            tax_rate = 0.0
        elif asset_class in ("fixed_income_taxable", "fund_multimarket"):
            if days <= 180:
                tax_rate = 0.225
            elif days <= 360:
                tax_rate = 0.20
            elif days <= 720:
                tax_rate = 0.175
            else:
                tax_rate = 0.15

            if days < 30:
                iof_rate = IOF_REGRESSIVE_RATES.get(days, 0.0)
        elif asset_class == "fund_equity":
            tax_rate = 0.15
        else:
            tax_rate = 0.15

        iof_amount = gain * iof_rate
        taxable_gain = max(0.0, gain - iof_amount) if not is_exempt else 0.0
        tax_due = taxable_gain * tax_rate
        net_proceeds = sale - iof_amount - tax_due

        total_cost += cost
        total_sale += sale
        total_profit += gain
        total_taxable += taxable_gain
        total_tax += tax_due
        total_iof += iof_amount
        total_net += net_proceeds

        asset_results.append(
            {
                "instrument_id": h["instrument_id"],
                "label": h["label"],
                "asset_class": asset_class,
                "cost_basis": round(cost, 2),
                "sale_value": round(sale, 2),
                "capital_gain": round(gain, 2),
                "taxable_gain": round(taxable_gain, 2),
                "tax_rate_pct": round(tax_rate * 100, 1),
                "iof_rate_pct": round(iof_rate * 100, 1),
                "iof_amount": round(iof_amount, 2),
                "tax_due": round(tax_due, 2),
                "net_proceeds": round(net_proceeds, 2),
                "is_exempt": is_exempt,
                "exemption_rule": exemption_rule,
            }
        )

    effective_rate = (total_tax / total_profit * 100.0) if total_profit > 0 else 0.0

    return {
        "total_cost_basis": round(total_cost, 2),
        "total_sale_value": round(total_sale, 2),
        "total_gross_profit": round(total_profit, 2),
        "total_taxable_gain": round(total_taxable, 2),
        "total_tax_due": round(total_tax, 2),
        "total_iof_due": round(total_iof, 2),
        "total_net_proceeds": round(total_net, 2),
        "effective_tax_rate_pct": round(effective_rate, 2),
        "stock_monthly_sales_total": round(total_stock_sales, 2),
        "stock_exemption_applied": stock_exemption_applies,
        "assets": asset_results,
        "methodology": (
            "Simula tributacao brasileira por classe de ativo: tabela regressiva (22.5% a 15%) "
            "e IOF para renda fixa comum; isencao para LCI/LCA; isencao de R$ 20k/mes para acoes; "
            "e 20% sobre ganho de capital em FIIs."
        ),
    }
