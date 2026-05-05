"""Internal simulation value objects for investment comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .catalog import InvestmentInstrument


@dataclass(frozen=True)
class SimulationResult:
    instrument: InvestmentInstrument
    equity_curve: pd.Series
    flow_curve: pd.Series
    invested_total: float
    final_value: float
    net_profit: float
    twr_total: float
    cagr: float
    annual_volatility: float
    max_drawdown: float
    availability_start: str
    availability_end: str
    component_values: dict[str, float] | None = None
    net_liquidation_curve: pd.Series | None = None
    taxes_paid_total: float = 0.0
    realized_taxes_paid: float = 0.0
    estimated_exit_taxes: float = 0.0
    strategy_metadata: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument.instrument_id,
            "label": self.instrument.label,
            "ticker": self.instrument.ticker,
            "category_id": self.instrument.category_id,
            "category_label": self.instrument.category_label,
            "description": self.instrument.description,
            "rationale": self.instrument.rationale,
            "risk_label": self.instrument.risk_label,
            "region_label": self.instrument.region_label,
            "source_kind": self.instrument.source_kind,
            "invested_total": float(self.invested_total),
            "final_value": float(self.final_value),
            "net_profit": float(self.net_profit),
            "total_return_on_invested": (
                float(self.final_value / self.invested_total - 1.0)
                if self.invested_total > 0
                else 0.0
            ),
            "time_weighted_return": float(self.twr_total),
            "cagr": float(self.cagr),
            "annual_volatility": float(self.annual_volatility),
            "max_drawdown": float(self.max_drawdown),
            "availability_start": self.availability_start,
            "availability_end": self.availability_end,
            "taxes_paid_total": float(self.taxes_paid_total),
            "realized_taxes_paid": float(self.realized_taxes_paid),
            "estimated_exit_taxes": float(self.estimated_exit_taxes),
            "strategy_metadata": self.strategy_metadata or {},
        }
