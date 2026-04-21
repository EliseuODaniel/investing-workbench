"""SELIC data management for monthly and daily interest-rate series."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# SGS code for daily SELIC (% a.d.) from Banco Central do Brasil.
DAILY_SELIC_SGS_CODE = 11
# SGS code for annualized SELIC base 252, kept as a fallback for monthly derivation.
SELIC_SGS_CODE = 1178
_BCB_SERIES_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
_MONTHLY_CACHE: dict[tuple[str, bool, str | None, str | None], pd.DataFrame] = {}
_DAILY_CACHE: dict[tuple[str, bool, str | None, str | None], pd.DataFrame] = {}


def generate_fake_selic_data() -> pd.DataFrame:
    """Generate fake monthly SELIC data for tests and local fallbacks."""
    data = []

    for year in range(2020, 2025):
        for month in range(1, 13):
            if year < 2021:
                base_rate = 0.002
            elif year < 2023:
                base_rate = 0.008
            else:
                base_rate = 0.0108

            variation = 0.0002 * (month % 3 - 1)
            rate = max(0.0001, base_rate + variation)
            data.append({"year": year, "month": month, "rate": rate})

    return pd.DataFrame(data)


def _format_bcb_date(date_value: str | None, *, fallback: str) -> str:
    raw_value = date_value or fallback
    return pd.Timestamp(raw_value).strftime("%d/%m/%Y")


def _download_bcb_series(
    *,
    sgs_code: int,
    start_date: str | None,
    end_date: str | None,
) -> list[dict[str, str]]:
    import requests

    params = {
        "formato": "json",
        "dataInicial": _format_bcb_date(start_date, fallback="2020-01-01"),
        "dataFinal": _format_bcb_date(
            end_date,
            fallback=pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        ),
    }
    response = requests.get(
        _BCB_SERIES_URL.format(code=sgs_code),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected BCB response for SGS {sgs_code}: {payload!r}")
    return payload


def download_selic_data(
    start_date: str | None = None,
    end_date: str | None = None,
) -> Optional[pd.DataFrame]:
    """Download monthly effective SELIC rates from Banco Central do Brasil.

    The BCB `1178` series is published as a daily annualized rate (base 252),
    which should not be capitalized directly as a monthly return. To avoid
    overstating cash yield, the monthly dataset is derived by compounding the
    official daily SELIC series (`11`) inside each calendar month.
    """
    try:
        daily = download_daily_selic_data(start_date, end_date)
        if daily is None or daily.empty:
            return _download_monthly_from_annualized_series(
                start_date=start_date,
                end_date=end_date,
            )

        monthly = _aggregate_daily_rates_to_monthly(daily)
        logger.info(
            "Derived %s monthly effective SELIC rates from %s daily rows",
            len(monthly),
            len(daily),
        )
        return monthly
    except Exception as exc:
        logger.error("Failed to download monthly SELIC data: %s", exc)
        return None


def _download_monthly_from_annualized_series(
    *,
    start_date: str | None,
    end_date: str | None,
) -> Optional[pd.DataFrame]:
    """Fallback monthly derivation from the annualized base-252 BCB series."""
    raw_rows = _download_bcb_series(
        sgs_code=SELIC_SGS_CODE,
        start_date=start_date,
        end_date=end_date,
    )
    if not raw_rows:
        return None

    df = pd.DataFrame(raw_rows)
    df["date"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["annual_rate"] = pd.to_numeric(df["valor"], errors="coerce") / 100.0
    df = (
        df.dropna(subset=["date", "annual_rate"])
        .assign(
            year=lambda frame: frame["date"].dt.year, month=lambda frame: frame["date"].dt.month
        )
        .sort_values("date")
        .drop_duplicates(subset=["year", "month"], keep="last")
    )

    def _business_days_in_month(row: pd.Series) -> int:
        start = pd.Timestamp(year=int(row["year"]), month=int(row["month"]), day=1)
        end = start + pd.offsets.MonthEnd(0)
        return len(pd.date_range(start, end, freq="B"))

    df["business_days"] = df.apply(_business_days_in_month, axis=1)
    df["rate"] = (1.0 + df["annual_rate"]) ** (df["business_days"] / 252.0) - 1.0
    monthly = df[["year", "month", "rate"]].reset_index(drop=True)
    logger.warning(
        "Derived monthly SELIC from annualized SGS 1178 fallback for %s rows; "
        "daily series download was unavailable",
        len(monthly),
    )
    return monthly


def _aggregate_daily_rates_to_monthly(daily_rates: pd.DataFrame) -> pd.DataFrame:
    """Convert daily SELIC rates into monthly effective rates."""
    normalized = daily_rates.copy()
    normalized["date"] = pd.to_datetime(normalized["date"]).dt.normalize()
    normalized["rate"] = pd.to_numeric(normalized["rate"], errors="coerce")
    normalized = normalized.dropna(subset=["date", "rate"]).sort_values("date")

    monthly = (
        normalized.assign(
            year=normalized["date"].dt.year,
            month=normalized["date"].dt.month,
            gross_factor=1.0 + normalized["rate"],
        )
        .groupby(["year", "month"], as_index=False)["gross_factor"]
        .prod()
        .rename(columns={"gross_factor": "gross_month"})
    )
    monthly["rate"] = monthly["gross_month"] - 1.0
    return (
        monthly[["year", "month", "rate"]]
        .dropna()
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )


def download_daily_selic_data(
    start_date: str | None = None,
    end_date: str | None = None,
) -> Optional[pd.DataFrame]:
    """Download official daily SELIC (% a.d.) from Banco Central do Brasil."""
    try:
        raw_rows = _download_bcb_series(
            sgs_code=DAILY_SELIC_SGS_CODE,
            start_date=start_date,
            end_date=end_date,
        )
        if not raw_rows:
            return None

        df = pd.DataFrame(raw_rows)
        df["date"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df["rate"] = pd.to_numeric(df["valor"], errors="coerce") / 100.0
        daily = df[["date", "rate"]].dropna().sort_values("date").reset_index(drop=True)
        logger.info("Downloaded %s daily SELIC rates from BCB", len(daily))
        return daily
    except Exception as exc:
        logger.error("Failed to download daily SELIC data: %s", exc)
        return None


def save_selic_data(df: pd.DataFrame, path: str) -> None:
    """Save monthly SELIC data to CSV file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    df.to_csv(path, index=False)
    normalized_path = str(Path(path).resolve())
    for cache_key in list(_MONTHLY_CACHE):
        if cache_key[0] == normalized_path:
            _MONTHLY_CACHE[cache_key] = df.copy()
    logger.info("SELIC data saved to %s", path)


def save_daily_selic_data(df: pd.DataFrame, path: str) -> None:
    """Save daily SELIC data to CSV file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    serializable = df.copy()
    serializable["date"] = pd.to_datetime(serializable["date"]).dt.strftime("%Y-%m-%d")
    serializable = serializable.sort_values("date").reset_index(drop=True)
    serializable.to_csv(path, index=False)
    normalized_path = str(Path(path).resolve())
    parsed = df.copy()
    parsed["date"] = pd.to_datetime(parsed["date"])
    parsed = parsed.sort_values("date").reset_index(drop=True)
    for cache_key in list(_DAILY_CACHE):
        if cache_key[0] == normalized_path:
            _DAILY_CACHE[cache_key] = parsed.copy()
    logger.info("Daily SELIC data saved to %s", path)


def load_selic_data(path: str) -> Optional[pd.DataFrame]:
    """Load monthly SELIC data from CSV file."""
    try:
        if not Path(path).exists():
            logger.warning("SELIC file not found: %s", path)
            return None

        df = pd.read_csv(path)
        required_columns = ["year", "month", "rate"]
        if not all(col in df.columns for col in required_columns):
            logger.error("SELIC file missing required columns: %s", required_columns)
            return None

        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
        df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
        df = df.dropna(subset=["rate"]).reset_index(drop=True)
        logger.info("Loaded %s monthly SELIC rates from %s", len(df), path)
        return df
    except Exception as exc:
        logger.error("Error loading SELIC data from %s: %s", path, exc)
        return None


def load_daily_selic_data(path: str) -> Optional[pd.DataFrame]:
    """Load daily SELIC data from CSV file."""
    try:
        if not Path(path).exists():
            logger.warning("Daily SELIC file not found: %s", path)
            return None

        df = pd.read_csv(path)
        required_columns = ["date", "rate"]
        if not all(col in df.columns for col in required_columns):
            logger.error("Daily SELIC file missing required columns: %s", required_columns)
            return None

        df["date"] = pd.to_datetime(df["date"])
        df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
        df = df.dropna(subset=["date", "rate"]).sort_values("date").reset_index(drop=True)
        logger.info("Loaded %s daily SELIC rates from %s", len(df), path)
        return df
    except Exception as exc:
        logger.error("Error loading daily SELIC data from %s: %s", path, exc)
        return None


def get_monthly_rate(
    selic_data: pd.DataFrame,
    year: int,
    month: int,
    fallback_rate_annual: float = 0.13,
) -> float:
    """Get monthly SELIC rate for a specific month/year with fallback."""
    if selic_data is None or selic_data.empty:
        monthly_fallback = (1 + fallback_rate_annual) ** (1 / 12) - 1
        logger.warning(
            "No SELIC data available, using fallback monthly rate: %.6f",
            monthly_fallback,
        )
        return monthly_fallback

    mask = (selic_data["year"] == year) & (selic_data["month"] == month)
    matching_rows = selic_data[mask]

    if not matching_rows.empty:
        rate = float(matching_rows.iloc[0]["rate"])
        logger.debug("Found SELIC rate for %s-%02d: %.6f", year, month, rate)
        return rate

    last_rate = float(selic_data.iloc[-1]["rate"])
    logger.warning(
        "SELIC rate not found for %s-%02d, using last available: %.6f",
        year,
        month,
        last_rate,
    )
    return last_rate


def get_daily_rate(
    selic_data: pd.DataFrame,
    date: pd.Timestamp | datetime | str,
    fallback_rate_annual: float = 0.13,
) -> float:
    """Get the official daily SELIC rate for one date, with deterministic fallback."""
    if selic_data is None or selic_data.empty:
        daily_fallback = (1 + fallback_rate_annual) ** (1 / 252) - 1
        logger.warning(
            "No daily SELIC data available, using fallback daily rate: %.6f",
            daily_fallback,
        )
        return daily_fallback

    target_date = pd.Timestamp(date)
    if target_date.tzinfo is not None:
        target_date = target_date.tz_localize(None)
    target_date = target_date.normalize()
    normalized = selic_data.copy()
    normalized["date"] = pd.to_datetime(normalized["date"]).dt.normalize()

    exact = normalized[normalized["date"] == target_date]
    if not exact.empty:
        return float(exact.iloc[0]["rate"])

    previous = normalized[normalized["date"] <= target_date]
    if not previous.empty:
        rate = float(previous.iloc[-1]["rate"])
        logger.debug(
            "Daily SELIC rate not found for %s, using previous business-day value %.6f",
            target_date.date(),
            rate,
        )
        return rate

    daily_fallback = (1 + fallback_rate_annual) ** (1 / 252) - 1
    logger.warning(
        "Daily SELIC rate not found for %s, using fallback daily rate %.6f",
        target_date.date(),
        daily_fallback,
    )
    return daily_fallback


def get_or_create_selic_data(
    path: str = "data/selic.csv",
    use_download: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
    fallback_rate_annual: float = 0.13,
) -> pd.DataFrame:
    """Get monthly SELIC data, creating it if necessary."""
    normalized_path = str(Path(path).resolve())
    cache_key = (normalized_path, use_download, start_date, end_date)
    cached = _MONTHLY_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    selic_data = load_selic_data(path)
    if selic_data is not None and validate_selic_data(selic_data):
        if start_date is None and end_date is None:
            _MONTHLY_CACHE[cache_key] = selic_data.copy()
            return selic_data

        start_ts = pd.Timestamp(start_date).normalize() if start_date else None
        end_ts = pd.Timestamp(end_date).normalize() if end_date else None
        available = selic_data.assign(
            period_start=pd.to_datetime(
                dict(year=selic_data["year"], month=selic_data["month"], day=1)
            ).dt.normalize()
        )
        min_date = available["period_start"].min()
        max_date = available["period_start"].max()
        has_start = start_ts is None or min_date <= start_ts.replace(day=1)
        has_end = end_ts is None or max_date >= end_ts.replace(day=1)
        if has_start and has_end:
            _MONTHLY_CACHE[cache_key] = selic_data.copy()
            return selic_data
    elif selic_data is not None:
        logger.warning(
            "Existing monthly SELIC cache at %s is outside the expected monthly range; "
            "refreshing it from BCB.",
            path,
        )

    if use_download:
        logger.info("Attempting to download real monthly SELIC data...")
        selic_data = download_selic_data(start_date, end_date)
        if selic_data is not None:
            save_selic_data(selic_data, path)
            _MONTHLY_CACHE[cache_key] = selic_data.copy()
            return selic_data

    logger.info("Generating fake SELIC data for testing...")
    selic_data = generate_fake_selic_data()
    save_selic_data(selic_data, path)
    _MONTHLY_CACHE[cache_key] = selic_data.copy()
    return selic_data


def get_or_create_daily_selic_data(
    path: str = "data/selic_daily.csv",
    use_download: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Optional[pd.DataFrame]:
    """Get official daily SELIC data, downloading it when needed."""
    normalized_path = str(Path(path).resolve())
    cache_key = (normalized_path, use_download, start_date, end_date)
    cached = _DAILY_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    selic_data = load_daily_selic_data(path)
    if selic_data is not None and not selic_data.empty:
        if start_date is None and end_date is None:
            _DAILY_CACHE[cache_key] = selic_data.copy()
            return selic_data

        start_ts = pd.Timestamp(start_date).normalize() if start_date else None
        end_ts = pd.Timestamp(end_date).normalize() if end_date else None
        min_date = selic_data["date"].min().normalize()
        max_date = selic_data["date"].max().normalize()
        has_start = start_ts is None or min_date <= start_ts
        has_end = end_ts is None or max_date >= end_ts
        if has_start and has_end:
            _DAILY_CACHE[cache_key] = selic_data.copy()
            return selic_data

    if use_download:
        logger.info("Attempting to download official daily SELIC data...")
        selic_data = download_daily_selic_data(start_date, end_date)
        if selic_data is not None and not selic_data.empty:
            save_daily_selic_data(selic_data, path)
            _DAILY_CACHE[cache_key] = selic_data.copy()
            return selic_data

    if selic_data is not None and not selic_data.empty:
        _DAILY_CACHE[cache_key] = selic_data.copy()
    return selic_data


def validate_selic_data(df: pd.DataFrame) -> bool:
    """Validate monthly SELIC data format and content."""
    if df is None or df.empty:
        logger.error("SELIC data is empty")
        return False

    required_columns = ["year", "month", "rate"]
    if not all(col in df.columns for col in required_columns):
        logger.error("Missing required columns: %s", required_columns)
        return False

    if df["year"].min() < 2000 or df["year"].max() > 2100:
        logger.error("Invalid year range: %s - %s", df["year"].min(), df["year"].max())
        return False

    if df["month"].min() < 1 or df["month"].max() > 12:
        logger.error("Invalid month range: %s - %s", df["month"].min(), df["month"].max())
        return False

    if df["rate"].min() < 0 or df["rate"].max() > 0.05:
        logger.error("Invalid rate range: %.6f - %.6f", df["rate"].min(), df["rate"].max())
        return False

    logger.info("SELIC data validation passed")
    return True
