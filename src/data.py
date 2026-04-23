"""Data management and Yahoo Finance helpers used by the backtest engine."""

from __future__ import annotations

import inspect
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

_DATA_SOURCE_ALIASES = {
    "BTC-BRL": [
        "BTC-BRL",
        "BTCBRL",
        "BTC=BRL",
        "BTC-BRL=X",
        "BTCBRL=X",
        "BTCBRL=BRL",
    ],
    "WEGE3": [
        "WEGE3.SA",
        "WEGE3",
    ],
    "WEGE3.SA": [
        "WEGE3.SA",
        "WEGE3",
    ],
}

_BTC_BRL_SYNTHETIC_SOURCES = {
    "crypto": ["BTC-USD"],
    "fx": ["USDBRL=X", "BRL=X"],
}


def _candidate_symbols(data_source: str) -> list[str]:
    """Return candidate symbols for Yahoo Finance."""
    base_source = str(data_source or "BTC-BRL").strip()
    if base_source in _DATA_SOURCE_ALIASES:
        return list(dict.fromkeys(_DATA_SOURCE_ALIASES[base_source]))

    normalized_source = base_source.upper()
    is_b3_cash_ticker = bool(re.fullmatch(r"[A-Z]{4,5}\d{1,2}", normalized_source))
    is_b3_embedded_digit_fund_ticker = bool(re.fullmatch(r"[A-Z0-9]{5,6}", normalized_source)) and (
        normalized_source.endswith("11")
        and any(char.isalpha() for char in normalized_source)
        and any(char.isdigit() for char in normalized_source[:-2])
    )
    if not base_source.endswith(".SA") and (
        base_source.isalpha() or is_b3_cash_ticker or is_b3_embedded_digit_fund_ticker
    ):
        return [f"{base_source}.SA", base_source]

    return [base_source]


def _is_btc_brl_source(data_source: str) -> bool:
    """Return whether one requested source should use the BTC/BRL fallback flow."""
    return str(data_source or "").strip().upper() in {"BTC-BRL", "BTC-BRL-SYNTH"}


def _normalize_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe columns from yfinance output."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [col[0] for col in df.columns]

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    df = df.sort_index()

    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    for column in required_columns + ["Adj Close", "Dividends", "Stock Splits"]:
        if column not in df.columns:
            df[column] = 0.0

    for column in required_columns + ["Adj Close", "Dividends", "Stock Splits", "Volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df[required_columns + ["Adj Close", "Dividends", "Stock Splits"]]


def _resolve_end_date(end: Optional[str]) -> str:
    """Resolve a safe end date string for yfinance."""
    if end is None:
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return end


def _load_cached_data(path: Path, start: str, end: str) -> Optional[pd.DataFrame]:
    """Load cached data if it fully covers the requested period."""
    if not path.exists():
        return None

    try:
        cached = pd.read_parquet(path)
        cached = _normalize_required_columns(cached)
    except Exception:
        return None

    start_dt = pd.Timestamp(start).tz_localize(None)
    end_dt = pd.to_datetime(end).tz_localize(None)
    df_start = cached.index.min().tz_localize(None)
    df_end = cached.index.max().tz_localize(None)

    if df_start <= start_dt and df_end >= end_dt - pd.Timedelta(days=1):
        return cached.loc[start_dt:end_dt]
    return None


def _load_cached_data_any(path: Path) -> Optional[pd.DataFrame]:
    """Load one cache file without enforcing full date coverage."""
    if not path.exists():
        return None
    try:
        cached = pd.read_parquet(path)
        return _normalize_required_columns(cached)
    except Exception:
        return None


def _download_data(
    symbol: str,
    start: str,
    end: str,
    *,
    interval: str = "1d",
    include_actions: bool = True,
) -> pd.DataFrame:
    """Download data from Yahoo Finance with a deterministic fallback chain."""
    history_kwargs = {
        "start": start,
        "end": end,
        "interval": interval,
        "auto_adjust": False,
        "actions": include_actions,
    }

    # yfinance changed kwargs across versions; keep deterministic behavior with
    # graceful fallback when arguments are unsupported.
    history_signature = inspect.signature(yf.Ticker.history)
    available_kwargs = set(history_signature.parameters)
    if "repair" in available_kwargs:
        history_kwargs["repair"] = True
    if "progress" in available_kwargs:
        history_kwargs["progress"] = False

    data = yf.Ticker(symbol).history(**history_kwargs)

    if data is None or data.empty:
        return pd.DataFrame()

    return _normalize_required_columns(data)


def _merge_market_data_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge multiple normalized market-data frames, preferring later sources."""
    usable = [frame for frame in frames if frame is not None and not frame.empty]
    if not usable:
        return pd.DataFrame()
    merged = pd.concat(usable).sort_index()
    merged = merged[~merged.index.duplicated(keep="last")]
    return _normalize_required_columns(merged)


def _invert_fx_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Invert an FX frame so it represents USD/BRL instead of BRL/USD."""
    inverted = frame.copy()
    inverted["Open"] = 1.0 / frame["Open"]
    inverted["High"] = 1.0 / frame["Low"]
    inverted["Low"] = 1.0 / frame["High"]
    inverted["Close"] = 1.0 / frame["Close"]
    inverted["Adj Close"] = inverted["Close"]
    return inverted


def _download_first_available(
    symbols: list[str],
    *,
    start: str,
    end: str,
    interval: str,
) -> tuple[pd.DataFrame, list[str], Exception | None]:
    """Download the first non-empty symbol from one fallback chain."""
    attempted: list[str] = []
    last_error: Exception | None = None
    for symbol in symbols:
        attempted.append(symbol)
        try:
            downloaded = _download_data(
                symbol=symbol,
                start=start,
                end=end,
                interval=interval,
                include_actions=False,
            )
            if not downloaded.empty:
                if symbol == "BRL=X":
                    return _invert_fx_frame(downloaded), attempted, last_error
                return downloaded, attempted, last_error
        except Exception as error:
            last_error = error
            print(f"Failed to download {symbol}: {error}")
    return pd.DataFrame(), attempted, last_error


def _synthetic_cache_path(source: str, cache_path: Optional[str]) -> Path:
    """Return the synthetic BTC/BRL cache path associated with one request."""
    if cache_path:
        cache_file = Path(cache_path)
        if cache_file.name == "btc_brl.parquet":
            return cache_file.with_name("btc_brl_synth.parquet")
        if cache_file.suffix:
            return cache_file.with_name(f"{cache_file.stem}_synth{cache_file.suffix}")
        return cache_file.with_name(f"{cache_file.name}_synth.parquet")
    normalized = str(source or "BTC-BRL").strip().lower().replace("-", "_")
    return Path(f"data/{normalized}_synth.parquet")


def _build_btc_brl_synthetic(
    *,
    start: str,
    end: str,
    interval: str,
    cache_path: Optional[str],
    force_download: bool,
) -> tuple[pd.DataFrame, list[str], Exception | None]:
    """Build a BTC/BRL series from BTC/USD and USD/BRL when direct BRL quotes fail."""
    requested_end = _resolve_end_date(end)
    start_dt = pd.Timestamp(start).tz_localize(None)
    end_dt = pd.Timestamp(requested_end).tz_localize(None)
    synthetic_cache = _synthetic_cache_path("BTC-BRL", cache_path)
    synthetic_cache.parent.mkdir(parents=True, exist_ok=True)

    if not force_download:
        cached = _load_cached_data(synthetic_cache, start, requested_end)
        if cached is not None and not cached.empty:
            print(f"Using cached synthetic BTC-BRL data from {synthetic_cache}")
            return cached, ["cached synthetic BTC-BRL"], None

    btc_usd, attempted_crypto, crypto_error = _download_first_available(
        _BTC_BRL_SYNTHETIC_SOURCES["crypto"],
        start=start,
        end=requested_end,
        interval=interval,
    )
    usd_brl, attempted_fx, fx_error = _download_first_available(
        _BTC_BRL_SYNTHETIC_SOURCES["fx"],
        start=start,
        end=requested_end,
        interval=interval,
    )
    attempted = attempted_crypto + attempted_fx
    if btc_usd.empty or usd_brl.empty:
        return pd.DataFrame(), attempted, crypto_error or fx_error

    aligned_fx = usd_brl.reindex(btc_usd.index).ffill().dropna(subset=["Close"])
    merged = btc_usd.join(aligned_fx, lsuffix="_btc", rsuffix="_fx", how="left").dropna()
    if merged.empty:
        return pd.DataFrame(), attempted, None

    synthetic = pd.DataFrame(index=merged.index)
    for column in ["Open", "High", "Low", "Close"]:
        synthetic[column] = merged[f"{column}_btc"] * merged[f"{column}_fx"]
    synthetic["Volume"] = merged["Volume_btc"]
    synthetic["Adj Close"] = synthetic["Close"]
    synthetic["Dividends"] = 0.0
    synthetic["Stock Splits"] = 0.0
    synthetic = _normalize_required_columns(synthetic)
    synthetic.to_parquet(synthetic_cache)
    print(
        "Built synthetic BTC-BRL data from BTC-USD and FX fallback "
        f"and cached it to {synthetic_cache}"
    )
    return synthetic.loc[start_dt:end_dt], attempted, None


def get_data(
    start: str = "2020-01-01",
    end: Optional[str] = None,
    cache_path: Optional[str] = "data/btc_brl.parquet",
    force_download: bool = False,
    data_source: Optional[str] = None,
    interval: str = "1d",
    include_actions: bool = True,
) -> pd.DataFrame:
    """Download and cache market data.

    Args:
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format (exclusive)
        cache_path: Destination cache file path
        force_download: Force redownload even if cache exists
        data_source: Source asset symbol (e.g., BTC-BRL, WEGE3)
        interval: Yahoo Finance interval (default: 1d)
        include_actions: Include Dividends and Stock Splits columns
    """
    requested_end = _resolve_end_date(end)
    start_dt = pd.Timestamp(start).tz_localize(None)
    end_dt = pd.Timestamp(requested_end).tz_localize(None)
    source = data_source or "BTC-BRL"

    if cache_path is not None:
        cache_file = Path(cache_path)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        partial_cached = _load_cached_data_any(cache_file)
        if not force_download:
            cached = _load_cached_data(cache_file, start, requested_end)
            if cached is not None and not cached.empty:
                print(f"Using cached data from {cache_path}")
                return cached
    else:
        cache_file = None
        partial_cached = None

    print(f"Downloading {source} data from {start} to {requested_end} (interval={interval})")

    attempted_symbols = _candidate_symbols(source)
    downloaded = pd.DataFrame()
    last_error = None

    for symbol in attempted_symbols:
        try:
            downloaded = _download_data(
                symbol=symbol,
                start=start,
                end=requested_end,
                interval=interval,
                include_actions=include_actions,
            )
            if not downloaded.empty:
                print(f"Successfully downloaded {symbol}")
                break
        except Exception as error:
            last_error = error
            print(f"Failed to download {symbol}: {error}")

    synthetic_attempts: list[str] = []
    if downloaded.empty and _is_btc_brl_source(source):
        synthetic, synthetic_attempts, synthetic_error = _build_btc_brl_synthetic(
            start=start,
            end=requested_end,
            interval=interval,
            cache_path=cache_path,
            force_download=force_download,
        )
        if not synthetic.empty:
            merge_candidates: list[pd.DataFrame] = []
            if partial_cached is not None and not partial_cached.empty:
                merge_candidates.append(partial_cached)
            merge_candidates.append(synthetic)
            downloaded = _merge_market_data_frames(merge_candidates).loc[start_dt:end_dt]
            freshness_cutoff = pd.Timestamp(requested_end).tz_localize(None) - pd.Timedelta(days=7)
            if downloaded.empty or downloaded.index.max().tz_localize(None) < freshness_cutoff:
                downloaded = pd.DataFrame()
            else:
                print(
                    "Using BTC-BRL synthetic fallback through " f"{downloaded.index.max().date()}"
                )
        if downloaded.empty and synthetic_error is not None:
            last_error = synthetic_error

    if downloaded.empty:
        attempted_description = attempted_symbols + synthetic_attempts
        message = (
            f"Unable to download data for '{source}' (tested: {', '.join(attempted_description)})"
        )
        if last_error is not None:
            message = f"{message}: {last_error}"
        raise ValueError(message)

    downloaded = downloaded.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    downloaded = downloaded.loc[~downloaded.index.duplicated(keep="first")]
    downloaded = downloaded.sort_index()

    if cache_path is not None:
        cache_file = Path(cache_path)
        downloaded.to_parquet(cache_file)
        print(f"Data cached to {cache_path}")

    return downloaded.loc[start_dt:end_dt]


def validate_data(df: pd.DataFrame) -> bool:
    """Validate dataframe has required columns and simple consistency checks."""
    required_cols = ["Open", "High", "Low", "Close", "Volume"]

    if not all(col in df.columns for col in required_cols):
        return False
    if df.empty:
        return False
    if (df["High"] < df["Low"]).any():
        return False
    if (df["Close"] > df["High"]).any() or (df["Close"] < df["Low"]).any():
        return False
    return True
