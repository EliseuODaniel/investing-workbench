"""Fixed-income index helpers used by the didactic investments workspace."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_PUBLIC_QUOTES_URL = "https://api.maisretorno.com/v3/indexes/quotes/{identifier}"
_QUOTE_CACHE: dict[tuple[str, str | None, str | None], pd.DataFrame] = {}


@dataclass(frozen=True)
class FixedIncomeIndexDefinition:
    """One public fixed-income index used by the backtest workspace."""

    instrument_id: str
    public_quote_id: str
    family_id: str
    family_label: str
    duration_years: int | None = None


FIXED_INCOME_INDEX_DEFINITIONS: dict[str, FixedIncomeIndexDefinition] = {
    "CDI_INDEX": FixedIncomeIndexDefinition(
        instrument_id="CDI_INDEX",
        public_quote_id="cdi",
        family_id="post_fixed",
        family_label="Pos-fixado / CDI",
    ),
    "IDKA_PRE_1A": FixedIncomeIndexDefinition(
        instrument_id="IDKA_PRE_1A",
        public_quote_id="idka-pre-1a",
        family_id="prefixado",
        family_label="Prefixado",
        duration_years=1,
    ),
    "IDKA_PRE_2A": FixedIncomeIndexDefinition(
        instrument_id="IDKA_PRE_2A",
        public_quote_id="idka-pre-2a",
        family_id="prefixado",
        family_label="Prefixado",
        duration_years=2,
    ),
    "IDKA_PRE_3A": FixedIncomeIndexDefinition(
        instrument_id="IDKA_PRE_3A",
        public_quote_id="idka-pre-3a",
        family_id="prefixado",
        family_label="Prefixado",
        duration_years=3,
    ),
    "IDKA_PRE_5A": FixedIncomeIndexDefinition(
        instrument_id="IDKA_PRE_5A",
        public_quote_id="idka-pre-5a",
        family_id="prefixado",
        family_label="Prefixado",
        duration_years=5,
    ),
    "IDKA_IPCA_2A": FixedIncomeIndexDefinition(
        instrument_id="IDKA_IPCA_2A",
        public_quote_id="idka-ipca-2a",
        family_id="ipca_plus",
        family_label="IPCA+ / juros reais",
        duration_years=2,
    ),
    "IDKA_IPCA_3A": FixedIncomeIndexDefinition(
        instrument_id="IDKA_IPCA_3A",
        public_quote_id="idka-ipca-3a",
        family_id="ipca_plus",
        family_label="IPCA+ / juros reais",
        duration_years=3,
    ),
    "IDKA_IPCA_5A": FixedIncomeIndexDefinition(
        instrument_id="IDKA_IPCA_5A",
        public_quote_id="idka-ipca-5a",
        family_id="ipca_plus",
        family_label="IPCA+ / juros reais",
        duration_years=5,
    ),
}


def get_fixed_income_definition(instrument_id: str) -> FixedIncomeIndexDefinition | None:
    """Resolve the fixed-income metadata used by one public index."""
    return FIXED_INCOME_INDEX_DEFINITIONS.get(instrument_id)


def download_fixed_income_quotes(
    instrument_id: str,
) -> pd.DataFrame | None:
    """Download public daily quotes for one fixed-income index."""
    import requests

    definition = get_fixed_income_definition(instrument_id)
    if definition is None:
        raise ValueError(f"Indice de renda fixa desconhecido: {instrument_id}")

    try:
        response = requests.get(
            _PUBLIC_QUOTES_URL.format(identifier=definition.public_quote_id),
            headers={
                "Referer": "https://maisretorno.com/",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("quotes") or []
        if not rows:
            return None

        frame = pd.DataFrame(rows)
        frame["date"] = (
            pd.to_datetime(frame["d"], unit="ms", utc=True).dt.tz_convert(None).dt.normalize()
        )
        frame["close"] = pd.to_numeric(frame["c"], errors="coerce")
        quotes = (
            frame[["date", "close"]]
            .dropna()
            .drop_duplicates(subset=["date"], keep="last")
            .sort_values("date")
            .reset_index(drop=True)
        )
        logger.info(
            "Downloaded %s daily quotes for %s",
            len(quotes),
            definition.public_quote_id,
        )
        return quotes
    except Exception as exc:
        logger.error("Failed to download fixed-income quotes for %s: %s", instrument_id, exc)
        return None


def load_fixed_income_quotes(path: str | Path) -> pd.DataFrame | None:
    """Load cached fixed-income quotes from CSV."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return None
        frame = pd.read_csv(file_path)
        if not {"date", "close"}.issubset(frame.columns):
            return None
        frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        return (
            frame[["date", "close"]]
            .dropna()
            .drop_duplicates(subset=["date"], keep="last")
            .sort_values("date")
            .reset_index(drop=True)
        )
    except Exception as exc:
        logger.error("Failed to load cached fixed-income quotes from %s: %s", path, exc)
        return None


def save_fixed_income_quotes(df: pd.DataFrame, path: str | Path) -> None:
    """Persist fixed-income quotes to CSV."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = (
        df.assign(date=pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d"))
        .sort_values("date")
        .reset_index(drop=True)
    )
    normalized.to_csv(file_path, index=False)
    normalized_path = str(file_path.resolve())
    for cache_key in list(_QUOTE_CACHE):
        if cache_key[0] == normalized_path:
            _QUOTE_CACHE.pop(cache_key, None)


def get_or_create_fixed_income_quotes(
    instrument_id: str,
    *,
    cache_dir: str | Path = "data/fixed_income_indexes",
    use_download: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Load, refresh, or download the public quote history for one index."""
    definition = get_fixed_income_definition(instrument_id)
    if definition is None:
        raise ValueError(f"Indice de renda fixa desconhecido: {instrument_id}")

    file_path = Path(cache_dir) / f"{definition.public_quote_id}.csv"
    normalized_path = str(file_path.resolve())
    cache_key = (normalized_path, start_date, end_date)
    cached = _QUOTE_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    quotes = load_fixed_income_quotes(file_path)
    resolved_start = pd.Timestamp(start_date) if start_date else None
    resolved_end = pd.Timestamp(end_date) if end_date else None
    needs_refresh = quotes is None or quotes.empty
    if quotes is not None and not quotes.empty:
        quote_start = pd.Timestamp(quotes["date"].min())
        quote_end = pd.Timestamp(quotes["date"].max())
        if resolved_start is not None and quote_start > resolved_start:
            needs_refresh = True
        if resolved_end is not None and quote_end < resolved_end:
            needs_refresh = True

    if needs_refresh and use_download:
        downloaded = download_fixed_income_quotes(instrument_id)
        if downloaded is not None and not downloaded.empty:
            save_fixed_income_quotes(downloaded, file_path)
            quotes = downloaded

    if quotes is None or quotes.empty:
        raise ValueError(f"Nao foi possivel obter cotacoes para {definition.public_quote_id}.")

    filtered = quotes.copy()
    if resolved_start is not None:
        filtered = filtered[filtered["date"] >= resolved_start]
    if resolved_end is not None:
        filtered = filtered[filtered["date"] <= resolved_end]
    filtered = filtered.reset_index(drop=True)
    if filtered.empty:
        raise ValueError(
            f"{definition.public_quote_id} nao possui cotacoes para o periodo solicitado."
        )
    _QUOTE_CACHE[cache_key] = filtered.copy()
    return filtered


def build_fixed_income_cache_metadata(cache_dir: str | Path) -> dict[str, Any]:
    """Summarize the local fixed-income quote cache state for API responses."""
    cache_path = Path(cache_dir)
    items: list[dict[str, Any]] = []
    available_count = 0

    for definition in FIXED_INCOME_INDEX_DEFINITIONS.values():
        file_path = cache_path / f"{definition.public_quote_id}.csv"
        if not file_path.exists():
            items.append(
                {
                    "instrument_id": definition.instrument_id,
                    "label": definition.public_quote_id,
                    "family_id": definition.family_id,
                    "family_label": definition.family_label,
                    "cache_path": str(file_path),
                    "available": False,
                }
            )
            continue

        stat = file_path.stat()
        available_count += 1
        items.append(
            {
                "instrument_id": definition.instrument_id,
                "label": definition.public_quote_id,
                "family_id": definition.family_id,
                "family_label": definition.family_label,
                "cache_path": str(file_path),
                "available": True,
                "cached_at": pd.Timestamp(stat.st_mtime, unit="s", tz="UTC").isoformat(),
                "size_bytes": stat.st_size,
            }
        )

    return {
        "label": "Mais Retorno API publica / indices de renda fixa",
        "url": "https://api.maisretorno.com/v3/",
        "cache_dir": str(cache_path),
        "available_count": available_count,
        "total_count": len(items),
        "items": items,
    }
