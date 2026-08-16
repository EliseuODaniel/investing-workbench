"""Unit tests for detailed Brazilian multi-asset liquidation tax simulation."""

from __future__ import annotations

from src.investing_workbench.application.investments.tax_simulation import (
    AssetTaxHolding,
    simulate_portfolio_liquidation_tax,
)


def test_stock_sales_under_20k_are_exempt() -> None:
    holdings: list[AssetTaxHolding] = [
        {
            "instrument_id": "petr4",
            "label": "PETR4",
            "asset_class": "stocks",
            "cost_basis": 10000.0,
            "current_value": 15000.0,  # 5k profit, total sales 15k <= 20k
            "holding_days": 100,
        }
    ]

    report = simulate_portfolio_liquidation_tax(holdings)
    assert report["stock_exemption_applied"] is True
    assert report["total_tax_due"] == 0.0
    assert report["assets"][0]["is_exempt"] is True
    assert report["effective_tax_rate_pct"] == 0.0


def test_stock_sales_over_20k_are_taxed_at_15_pct() -> None:
    holdings: list[AssetTaxHolding] = [
        {
            "instrument_id": "vale3",
            "label": "VALE3",
            "asset_class": "stocks",
            "cost_basis": 15000.0,
            "current_value": 25000.0,  # 10k profit, total sales 25k > 20k
            "holding_days": 100,
        }
    ]

    report = simulate_portfolio_liquidation_tax(holdings)
    assert report["stock_exemption_applied"] is False
    assert report["total_tax_due"] == 1500.0  # 15% of 10k profit
    assert report["assets"][0]["tax_rate_pct"] == 15.0


def test_fii_capital_gains_are_taxed_at_20_pct_without_20k_exemption() -> None:
    holdings: list[AssetTaxHolding] = [
        {
            "instrument_id": "knri11",
            "label": "KNRI11",
            "asset_class": "fiis",
            "cost_basis": 4000.0,
            "current_value": 5000.0,  # 1k profit, sale is only 5k but FII has no 20k exemption
            "holding_days": 200,
        }
    ]

    report = simulate_portfolio_liquidation_tax(holdings)
    assert report["total_tax_due"] == 200.0  # 20% of 1k profit
    assert report["assets"][0]["tax_rate_pct"] == 20.0


def test_exempt_fixed_income_has_zero_tax() -> None:
    holdings: list[AssetTaxHolding] = [
        {
            "instrument_id": "lci_inter",
            "label": "LCI Banco Inter",
            "asset_class": "fixed_income_exempt",
            "cost_basis": 10000.0,
            "current_value": 12000.0,
            "holding_days": 400,
        }
    ]

    report = simulate_portfolio_liquidation_tax(holdings)
    assert report["total_tax_due"] == 0.0
    assert report["assets"][0]["is_exempt"] is True


def test_taxable_fixed_income_regressive_rates_and_iof() -> None:
    # 15 days holding (subject to IOF + 22.5% IR)
    holdings_short: list[AssetTaxHolding] = [
        {
            "instrument_id": "cdb_short",
            "label": "CDB 15 dias",
            "asset_class": "fixed_income_taxable",
            "cost_basis": 10000.0,
            "current_value": 10100.0,  # 100 profit
            "holding_days": 15,  # 50% IOF
        }
    ]
    report_short = simulate_portfolio_liquidation_tax(holdings_short)
    assert report_short["total_iof_due"] == 50.0  # 50% of 100 profit
    # Taxable gain is 50. IR is 22.5% of 50 = 11.25
    assert report_short["total_tax_due"] == 11.25

    # 800 days holding (> 720 days = 15% IR, 0% IOF)
    holdings_long: list[AssetTaxHolding] = [
        {
            "instrument_id": "cdb_long",
            "label": "CDB 800 dias",
            "asset_class": "fixed_income_taxable",
            "cost_basis": 10000.0,
            "current_value": 13000.0,  # 3000 profit
            "holding_days": 800,
        }
    ]
    report_long = simulate_portfolio_liquidation_tax(holdings_long)
    assert report_long["total_iof_due"] == 0.0
    assert report_long["total_tax_due"] == 450.0  # 15% of 3000
