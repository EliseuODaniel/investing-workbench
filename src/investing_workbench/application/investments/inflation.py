"""IPCA inflation helpers used by the didactic investments workspace."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

IPCA_SGS_CODE = 433
_BCB_SERIES_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
_MONTHLY_CACHE: dict[tuple[str, bool, str | None, str | None], pd.DataFrame] = {}


def generate_fake_ipca_data() -> pd.DataFrame:
    """Generate a lightweight monthly inflation fallback for offline usage."""
    rows: list[dict[str, float | int]] = []
    for year in range(2020, 2028):
        for month in range(1, 13):
            if year <= 2020:
                base_rate = 0.0022
            elif year <= 2022:
                base_rate = 0.0058
            elif year <= 2024:
                base_rate = 0.0037
            else:
                base_rate = 0.0034
            variation = 0.0005 * ((month % 4) - 1.5)
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "rate": max(0.0001, base_rate + variation),
                }
            )
    return pd.DataFrame(rows)


def _format_bcb_date(date_value: str | None, *, fallback: str) -> str:
    raw_value = date_value or fallback
    return pd.Timestamp(raw_value).strftime("%d/%m/%Y")


def download_ipca_data(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame | None:
    """Download official monthly IPCA variation from Banco Central do Brasil."""
    import requests

    params = {
        "formato": "json",
        "dataInicial": _format_bcb_date(start_date, fallback="2020-01-01"),
        "dataFinal": _format_bcb_date(
            end_date,
            fallback=pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        ),
    }
    try:
        response = requests.get(
            _BCB_SERIES_URL.format(code=IPCA_SGS_CODE),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"Unexpected BCB response for SGS {IPCA_SGS_CODE}: {payload!r}")
        if not payload:
            return None

        frame = pd.DataFrame(payload)
        frame["date"] = pd.to_datetime(frame["data"], format="%d/%m/%Y")
        frame["rate"] = pd.to_numeric(frame["valor"], errors="coerce") / 100.0
        monthly = (
            frame.dropna(subset=["date", "rate"])
            .assign(
                year=lambda item: item["date"].dt.year,
                month=lambda item: item["date"].dt.month,
            )[["year", "month", "rate"]]
            .sort_values(["year", "month"])
            .reset_index(drop=True)
        )
        logger.info("Downloaded %s monthly IPCA rates from BCB", len(monthly))
        return monthly
    except Exception as exc:
        logger.error("Failed to download IPCA data: %s", exc)
        return None


def save_ipca_data(df: pd.DataFrame, path: str) -> None:
    """Persist monthly IPCA data to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    normalized = df.sort_values(["year", "month"]).reset_index(drop=True)
    normalized.to_csv(path, index=False)
    normalized_path = str(Path(path).resolve())
    for cache_key in list(_MONTHLY_CACHE):
        if cache_key[0] == normalized_path:
            _MONTHLY_CACHE[cache_key] = normalized.copy()


def load_ipca_data(path: str) -> pd.DataFrame | None:
    """Load cached monthly IPCA data from CSV."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return None

        frame = pd.read_csv(file_path)
        required_columns = ["year", "month", "rate"]
        if not all(column in frame.columns for column in required_columns):
            return None

        frame["year"] = frame["year"].astype(int)
        frame["month"] = frame["month"].astype(int)
        frame["rate"] = pd.to_numeric(frame["rate"], errors="coerce")
        return frame.dropna(subset=["rate"]).reset_index(drop=True)
    except Exception as exc:
        logger.error("Failed to load cached IPCA data from %s: %s", path, exc)
        return None


def get_monthly_ipca_rate(
    ipca_data: pd.DataFrame,
    year: int,
    month: int,
    *,
    fallback_rate_annual: float = 0.045,
) -> float:
    """Resolve one monthly IPCA rate using the latest available row as fallback."""
    if ipca_data is None or ipca_data.empty:
        return float((1.0 + fallback_rate_annual) ** (1.0 / 12.0) - 1.0)

    matching = ipca_data[(ipca_data["year"] == year) & (ipca_data["month"] == month)]
    if not matching.empty:
        return float(matching.iloc[-1]["rate"])

    last_rate = float(ipca_data.iloc[-1]["rate"])
    if pd.notna(last_rate):
        return last_rate
    return float((1.0 + fallback_rate_annual) ** (1.0 / 12.0) - 1.0)


def get_or_create_ipca_data(
    path: str = "data/ipca_monthly.csv",
    *,
    use_download: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Load, refresh, or synthesize the monthly IPCA series."""
    normalized_path = str(Path(path).resolve())
    cache_key = (normalized_path, use_download, start_date, end_date)
    cached = _MONTHLY_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    ipca_data = load_ipca_data(path)
    if ipca_data is not None and not ipca_data.empty:
        if start_date is None and end_date is None:
            _MONTHLY_CACHE[cache_key] = ipca_data.copy()
            return ipca_data

        start = pd.Timestamp(start_date or "2020-01-01").replace(day=1)
        end = pd.Timestamp(end_date or pd.Timestamp.utcnow()).replace(day=1)
        available = pd.to_datetime(dict(year=ipca_data["year"], month=ipca_data["month"], day=1))
        if available.min() <= start and available.max() >= end:
            _MONTHLY_CACHE[cache_key] = ipca_data.copy()
            return ipca_data

    if use_download:
        downloaded = download_ipca_data(start_date, end_date)
        if downloaded is not None and not downloaded.empty:
            save_ipca_data(downloaded, path)
            _MONTHLY_CACHE[cache_key] = downloaded.copy()
            return downloaded

    fallback = generate_fake_ipca_data()
    save_ipca_data(fallback, path)
    _MONTHLY_CACHE[cache_key] = fallback.copy()
    return fallback
