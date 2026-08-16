"""Unit tests for FII dividends and Tesouro Direto coupon cash flows."""

from __future__ import annotations

from src.investing_workbench.application.investments.fii_dividends import (
    calculate_fii_dividend_cash_flows,
)
from src.investing_workbench.application.investments.tesouro_simulation import (
    calculate_coupon_bond_cash_flows,
)


def test_fii_dividend_cash_flows_exemption_and_reinvestment() -> None:
    # 24 months, 0.8% a.m. yield, R$ 10.000 initial, R$ 100 share price (100 shares)
    stream = calculate_fii_dividend_cash_flows(
        ticker="HGLG11",
        label="CSHG Logística",
        initial_capital=10000.0,
        share_price=100.0,
        months=24,
        monthly_dividend_yield=0.008,
        reinvest=True,
    )

    assert stream["ticker"] == "HGLG11"
    assert stream["initial_shares"] == 100.0
    assert stream["final_shares"] > 100.0  # shares increased via reinvestment
    assert stream["total_net_dividends"] > 1920.0
    assert stream["total_tax_saved"] > 0.0
    assert len(stream["monthly_schedule"]) == 24
    for month in stream["monthly_schedule"]:
        assert month["income_tax"] == 0.0  # exempt
        assert month["net_dividend"] == month["gross_dividend"]


def test_tesouro_coupon_bond_cash_flows_regressive_tax() -> None:
    # 5 years (10 semesters) NTN-B 6% a.a. + 4.5% IPCA
    coupons = calculate_coupon_bond_cash_flows(
        bond_type="NTN-B_JUROS",
        principal_amount=10000.0,
        annual_coupon_rate=0.06,
        years=5,
        annual_inflation_rate=0.045,
        reinvest=False,
    )

    assert coupons["total_semesters"] == 10
    assert len(coupons["schedule"]) == 10
    # First coupon rate is 22.5% (<= 180 days)
    assert coupons["schedule"][0]["tax_rate_pct"] == 22.5
    # Second coupon rate is 20.0% (<= 360 days)
    assert coupons["schedule"][1]["tax_rate_pct"] == 20.0
    # Third & Fourth are 17.5% (<= 720 days)
    assert coupons["schedule"][2]["tax_rate_pct"] == 17.5
    assert coupons["schedule"][3]["tax_rate_pct"] == 17.5
    # Fifth onwards are 15.0% (> 720 days)
    assert coupons["schedule"][4]["tax_rate_pct"] == 15.0
    assert coupons["schedule"][9]["tax_rate_pct"] == 15.0

    assert coupons["total_gross_coupons"] > coupons["total_net_coupons"]
    assert coupons["total_tax_withheld"] > 0
    assert coupons["effective_tax_rate_pct"] < 22.5
