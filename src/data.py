"""Data management for BTC-BRL backtesting."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf


def get_data(
    start: str = "2020-01-01",
    end: Optional[str] = None,
    cache_path: Optional[str] = "data/btc_brl.parquet",
    force_download: bool = False,
) -> pd.DataFrame:
    """Get BTC-BRL daily data with caching.

    Args:
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format (default: today)
        cache_path: Path to cache file
        force_download: Force redownload even if cache exists

    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume
    """
    if end is None:
        end = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Check cache
    if cache_path is not None and not force_download:
        cache_file = Path(cache_path)
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        if cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                # Check if cache covers requested range
                df_start = df.index.min().strftime("%Y-%m-%d")
                df_end = (df.index.max() + timedelta(days=1)).strftime("%Y-%m-%d")

                if df_start <= start and df_end >= end:
                    print(f"Using cached data from {cache_path}")
                    return df.loc[start:end].copy()
            except Exception as e:
                print(f"Error reading cache: {e}")

    # Download data
    print(f"Downloading BTC-BRL data from {start} to {end}")

    # Try multiple symbols for BTC-BRL
    symbols_to_try = ["BTC-BRL", "BTCBRL", "BTC=BRL"]
    df = None

    for symbol in symbols_to_try:
        try:
            data = yf.download(symbol, start=start, end=end, progress=False)
            if len(data) > 0:
                print(f"Successfully downloaded {symbol} data")
                df = data
                break
        except Exception as e:
            print(f"Failed to download {symbol}: {e}")
            continue

    if df is None:
        # Fallback to BTC-USD if BTC-BRL not available
        print("BTC-BRL not available, falling back to BTC-USD")
        df = yf.download("BTC-USD", start=start, end=end, progress=False)
        if len(df) == 0:
            raise ValueError("No data available for any Bitcoin symbol")

    # Clean data
    df = df.dropna()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Handle MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten MultiIndex columns to simple names
        df.columns = [col[0] for col in df.columns]

    # Convert any remaining objects to numeric values
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop any rows that became NaN after conversion
    df = df.dropna()

    # Save to cache if path is provided
    if cache_path is not None:
        cache_file = Path(cache_path)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_file)
        print(f"Data cached to {cache_path}")

    return df


def validate_data(df: pd.DataFrame) -> bool:
    """Validate DataFrame has required columns and no obvious issues."""
    required_cols = ["Open", "High", "Low", "Close", "Volume"]

    if not all(col in df.columns for col in required_cols):
        return False

    # Check for price anomalies
    if (df["High"] < df["Low"]).any():
        return False

    if (df["Close"] > df["High"]).any() or (df["Close"] < df["Low"]).any():
        return False

    return True