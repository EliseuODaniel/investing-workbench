"""Domain models for cointegration-based pairs trading."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class BorrowOverride:
    ticker: str
    borrow_rate_annual: float | None = None
    short_eligible: bool | None = None
    margin_haircut: float | None = None
    source: str = "snapshot"


@dataclass(slots=True)
class UniverseAsset:
    ticker: str
    sector_group: str
    rows: int
    start: str
    end: str
    median_notional_brl: float
    min_close: float
    max_close: float
    short_eligible: bool
    borrow_proxy_rate_annual: float = 0.0
    short_score: float = 0.0
    realized_vol_annual: float = 0.0
    margin_haircut: float = 0.50
    borrow_source: str = "proxy"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PairSelection:
    y_ticker: str
    x_ticker: str
    sector_group: str
    formation_start: str
    formation_end: str
    trade_start: str
    trade_end: str
    return_corr: float
    level_corr: float
    coint_t_stat: float
    coint_pvalue: float
    adf_stat: float
    adf_pvalue: float
    beta: float
    intercept: float
    half_life: float
    same_group: bool
    y_borrow_rate_annual: float = 0.0
    x_borrow_rate_annual: float = 0.0
    y_short_score: float = 0.0
    x_short_score: float = 0.0
    y_margin_haircut: float = 0.50
    x_margin_haircut: float = 0.50
    y_borrow_source: str = "proxy"
    x_borrow_source: str = "proxy"
    stability_score: float = 0.0
    structural_break_risk: float = 1.0
    ranking_score: float = 0.0
    spread_history_seed: list[float] = field(default_factory=list, repr=False)

    @property
    def pair_label(self) -> str:
        return f"{self.y_ticker}~{self.x_ticker}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("spread_history_seed", None)
        payload["pair_label"] = self.pair_label
        return payload


@dataclass(slots=True)
class PendingOrder:
    pair_label: str
    action: str
    signal_date: str
    execute_date: str
    reason: str
    direction: str | None = None
    zscore: float | None = None
    beta_override: float | None = None


@dataclass(slots=True)
class OpenPairPosition:
    position_id: str
    window_id: str
    pair_label: str
    y_ticker: str
    x_ticker: str
    sector_group: str
    long_ticker: str
    short_ticker: str
    direction: str
    beta: float
    z_entry: float
    entry_signal_date: str
    entry_date: str
    entry_long_price: float
    entry_short_price: float
    long_shares: float
    short_shares: float
    long_notional: float
    short_notional: float
    gross_exposure_entry: float
    allocation_pct: float
    entry_fees: float
    entry_slippage_cost: float
    margin_posted: float = 0.0
    margin_haircut: float = 0.50
    short_borrow_rate_annual: float = 0.0
    short_borrow_source: str = "proxy"
    holding_days: int = 0
    dividend_pnl: float = 0.0
    short_borrow_cost: float = 0.0


@dataclass(slots=True)
class ClosedPairTrade:
    position_id: str
    window_id: str
    pair_label: str
    y_ticker: str
    x_ticker: str
    sector_group: str
    long_ticker: str
    short_ticker: str
    direction: str
    entry_signal_date: str
    entry_date: str
    exit_date: str
    exit_reason: str
    beta: float
    z_entry: float
    z_exit: float
    entry_long_price: float
    entry_short_price: float
    exit_long_price: float
    exit_short_price: float
    long_shares: float
    short_shares: float
    long_notional: float
    short_notional: float
    gross_exposure_entry: float
    gross_exposure_exit: float
    allocation_pct: float
    gross_pnl: float
    net_pnl: float
    entry_fees: float
    exit_fees: float
    fees_paid: float
    slippage_cost: float
    short_borrow_cost: float
    short_borrow_rate_annual: float
    short_borrow_source: str
    dividend_pnl: float
    margin_posted: float
    margin_haircut: float
    cash_release: float
    holding_days: int

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["duration_days"] = self.holding_days
        return payload
