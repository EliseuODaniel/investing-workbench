"""DTOs for application-layer run orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class RunRequestSummary:
    """Minimal summary of a resolved run request."""

    config_path: str
    strategy_count: int
    benchmark_count: int


@dataclass(slots=True)
class BacktestRunInput:
    """Transport-agnostic application input for running a backtest."""

    config_path: str = "configs/martingale.yaml"
    strategies: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None
    initial_capital: float | None = None
    base_bet: float | None = None
    multiplier: float | None = None
    drop_step: float | None = None
    take_profit: float | None = None
    max_layers: int | None = None
    data_source: str | None = None
    cache_path: str | None = None
    force_download: bool = False
    apply_cash_yield: bool | None = None
    selic_rate_annual: float | None = None
    use_real_selic: bool | None = None
    selic_path: str | None = None
    selic_fallback_rate: float | None = None
    fee_rate: float | None = None
    fixed_fee: float | None = None
    buy_slippage: float | None = None
    sell_slippage: float | None = None
    max_volume_participation: float | None = None
    allow_partial_fills: bool | None = None
    min_fill_quantity: float | None = None
    benchmarks: list[str] | None = None
    include_selic_benchmark: bool | None = None
    include_buy_hold_benchmark: bool | None = None

    def to_request_payload(self) -> dict[str, Any]:
        """Serialize the input into a compact, persistence-friendly payload."""
        return {
            key: value for key, value in asdict(self).items() if value is not None and value != []
        }
