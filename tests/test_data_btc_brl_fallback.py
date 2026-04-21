from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data import get_data


def _frame(
    start: str,
    closes: list[float],
    *,
    volume: float = 1000.0,
) -> pd.DataFrame:
    index = pd.date_range(start, periods=len(closes), freq="D")
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [value * 1.01 for value in closes],
            "Low": [value * 0.99 for value in closes],
            "Close": closes,
            "Adj Close": closes,
            "Volume": [volume] * len(closes),
            "Dividends": [0.0] * len(closes),
            "Stock Splits": [0.0] * len(closes),
        },
        index=index,
    )


def test_get_data_falls_back_to_synthetic_btc_brl_and_merges_partial_cache(
    monkeypatch,
    tmp_path: Path,
) -> None:
    direct_cache_path = tmp_path / "btc_brl.parquet"
    _frame("2020-01-01", [100.0, 110.0, 120.0]).to_parquet(direct_cache_path)

    btc_usd = _frame("2021-01-01", [20000.0, 21000.0, 22000.0, 23000.0, 24000.0])
    usd_brl = _frame("2021-01-01", [5.0, 5.0, 5.0, 5.0, 5.0], volume=0.0)

    def fake_download_data(
        symbol: str,
        start: str,
        end: str,
        *,
        interval: str = "1d",
        include_actions: bool = True,
    ) -> pd.DataFrame:
        if symbol in {"BTC-USD"}:
            return btc_usd
        if symbol in {"USDBRL=X"}:
            return usd_brl
        return pd.DataFrame()

    monkeypatch.setattr("src.data._download_data", fake_download_data)

    resolved = get_data(
        start="2020-01-01",
        end="2021-01-05",
        cache_path=str(direct_cache_path),
        force_download=False,
        data_source="BTC-BRL",
        include_actions=True,
    )

    assert resolved.index.min() == pd.Timestamp("2020-01-01")
    assert resolved.index.max() == pd.Timestamp("2021-01-05")
    assert resolved.loc[pd.Timestamp("2020-01-03"), "Close"] == 120.0
    assert resolved.loc[pd.Timestamp("2021-01-01"), "Close"] == 100000.0
    assert resolved.loc[pd.Timestamp("2021-01-05"), "Close"] == 120000.0
    assert (tmp_path / "btc_brl_synth.parquet").exists()
