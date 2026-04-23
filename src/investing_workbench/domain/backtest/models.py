"""Core backtest state models with compatibility for legacy strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd


@dataclass
class Trade:
    """Record of a single executed trade."""

    timestamp: pd.Timestamp
    action: str
    price: float
    quantity: float
    cost: float
    pnl: Optional[float] = None
    layer: Optional[int] = None
    notional: Optional[float] = None
    cash_after: Optional[float] = None
    position_after: Optional[float] = None
    reference_after: Optional[float] = None
    requested_quantity: Optional[float] = None
    fill_ratio: Optional[float] = None
    event_notes: Optional[dict[str, Any]] = None


@dataclass
class Layer:
    """Open position layer tracked by the engine."""

    entry_price: float
    quantity: float
    cost: float
    timestamp: pd.Timestamp
    layer_id: int


@dataclass
class State:
    """Current backtest state exposed to strategies."""

    cash: float
    layers: list[Layer] = field(default_factory=list)
    equity_history: list[float] = field(default_factory=list)
    cash_history: list[float] = field(default_factory=list)
    timestamp_history: list[pd.Timestamp] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    max_equity: float = field(default_factory=lambda: 0.0)
    total_interest_earned: float = field(default_factory=lambda: 0.0)
    selic_rates_used: dict[str, float] = field(default_factory=dict)
    total_dividends_received: float = field(default_factory=lambda: 0.0)
    total_fees_paid: float = field(default_factory=lambda: 0.0)
    corporate_actions_log: list[dict[str, Any]] = field(default_factory=list)
    execution_log: list[dict[str, Any]] = field(default_factory=list)
