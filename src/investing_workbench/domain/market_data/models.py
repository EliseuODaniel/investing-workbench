"""Market data domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

import pandas as pd


@dataclass(slots=True)
class MarketBar:
    """Normalized representation of a single OHLCV bar."""

    asset: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_series(
        cls,
        row: pd.Series,
        *,
        asset: str = "BTC-BRL",
        timeframe: str = "1d",
    ) -> "MarketBar":
        """Create a market bar from a pandas row."""
        return cls(
            asset=asset,
            timeframe=timeframe,
            timestamp=row.name.to_pydatetime(),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=float(row["Volume"]),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the bar as a JSON-friendly dictionary."""
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload
