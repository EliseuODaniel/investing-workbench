"""Historical and projected dividend cash flow modeling for Real Estate Investment Funds (FIIs)."""

from __future__ import annotations

from typing import TypedDict


class FiiDividendMonth(TypedDict):
    month_index: int
    shares_held: float
    dividend_per_share: float
    gross_dividend: float
    net_dividend: float
    income_tax: float
    reinvested_shares: float
    closing_shares: float


class FiiDividendStream(TypedDict):
    ticker: str
    label: str
    reinvest_dividends: bool
    initial_shares: float
    final_shares: float
    total_net_dividends: float
    total_tax_saved: float
    current_yield_on_cost_pct: float
    average_monthly_dividend: float
    monthly_schedule: list[FiiDividendMonth]
    tax_note: str


def calculate_fii_dividend_cash_flows(
    *,
    ticker: str,
    label: str = "FII",
    initial_capital: float = 10000.0,
    share_price: float = 100.0,
    months: int = 24,
    monthly_dividend_yield: float = 0.008,  # ~0.8% a.m. (9.6% a.a.)
    reinvest: bool = True,
) -> FiiDividendStream:
    """Calculate month-by-month dividend cash flow and reinvestment compounding for a FII."""

    clean_ticker = ticker.strip().upper()
    initial_shares = max(1.0, initial_capital / max(1.0, share_price))
    current_shares = initial_shares
    total_net = 0.0
    total_tax_saved = 0.0
    schedule: list[FiiDividendMonth] = []

    price = max(1.0, share_price)
    dpa = price * monthly_dividend_yield

    for m in range(1, max(1, months) + 1):
        gross_div = current_shares * dpa
        # FII dividends are 100% exempt from income tax for individual investors (Lei 11.033/2004)
        net_div = gross_div
        tax_saved = gross_div * 0.15  # 15% standard equity tax that is saved
        total_tax_saved += tax_saved
        total_net += net_div

        if reinvest:
            new_shares = net_div / price
            closing_shares = current_shares + new_shares
        else:
            new_shares = 0.0
            closing_shares = current_shares

        schedule.append(
            {
                "month_index": m,
                "shares_held": round(current_shares, 4),
                "dividend_per_share": round(dpa, 4),
                "gross_dividend": round(gross_div, 2),
                "net_dividend": round(net_div, 2),
                "income_tax": 0.0,
                "reinvested_shares": round(new_shares, 4),
                "closing_shares": round(closing_shares, 4),
            }
        )
        current_shares = closing_shares

    final_monthly_div = current_shares * dpa
    yield_on_cost = (
        (final_monthly_div * 12.0 / initial_capital) * 100.0 if initial_capital > 0 else 0.0
    )

    return {
        "ticker": clean_ticker,
        "label": label,
        "reinvest_dividends": reinvest,
        "initial_shares": round(initial_shares, 4),
        "final_shares": round(current_shares, 4),
        "total_net_dividends": round(total_net, 2),
        "total_tax_saved": round(total_tax_saved, 2),
        "current_yield_on_cost_pct": round(yield_on_cost, 2),
        "average_monthly_dividend": round(total_net / months, 2) if months > 0 else 0.0,
        "monthly_schedule": schedule,
        "tax_note": (
            "Rendimentos mensais de FIIs sao isentos de Imposto de Renda para pessoa fisica "
            "conforme Lei 11.033/2004, desde que negociados em bolsa e com >= 100 cotistas."
        ),
    }
