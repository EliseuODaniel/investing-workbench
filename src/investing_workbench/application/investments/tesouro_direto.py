"""Official Tesouro Direto history helpers for retail fixed-income studies."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

TESOURO_DIRETO_CSV_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
)

_TESOURO_DIRETO_CACHE: dict[str, pd.DataFrame] = {}


@dataclass(frozen=True)
class TesouroDiretoStrategyDefinition:
    """One retail fixed-income strategy backed by official Tesouro Direto quotes."""

    instrument_id: str
    title_type: str
    family_id: str
    family_label: str
    target_duration_years: float | None = None
    min_years_to_maturity: float | None = None
    max_years_to_maturity: float | None = None
    selection_rule: str = "closest_duration"


TESOURO_DIRETO_STRATEGIES: dict[str, TesouroDiretoStrategyDefinition] = {
    "TD_SELIC": TesouroDiretoStrategyDefinition(
        instrument_id="TD_SELIC",
        title_type="Tesouro Selic",
        family_id="post_fixed",
        family_label="Tesouro Selic / pos-fixado",
        selection_rule="shortest_maturity",
    ),
    "TD_PREFIXADO_2A": TesouroDiretoStrategyDefinition(
        instrument_id="TD_PREFIXADO_2A",
        title_type="Tesouro Prefixado",
        family_id="prefixado",
        family_label="Tesouro Prefixado",
        target_duration_years=2.0,
        min_years_to_maturity=1.5,
        max_years_to_maturity=2.5,
    ),
    "TD_PREFIXADO_3A": TesouroDiretoStrategyDefinition(
        instrument_id="TD_PREFIXADO_3A",
        title_type="Tesouro Prefixado",
        family_id="prefixado",
        family_label="Tesouro Prefixado",
        target_duration_years=3.0,
        min_years_to_maturity=2.5,
        max_years_to_maturity=3.5,
    ),
    "TD_PREFIXADO_5A": TesouroDiretoStrategyDefinition(
        instrument_id="TD_PREFIXADO_5A",
        title_type="Tesouro Prefixado",
        family_id="prefixado",
        family_label="Tesouro Prefixado",
        target_duration_years=5.0,
        min_years_to_maturity=4.0,
        max_years_to_maturity=6.0,
    ),
    "TD_IPCA_2A": TesouroDiretoStrategyDefinition(
        instrument_id="TD_IPCA_2A",
        title_type="Tesouro IPCA+",
        family_id="ipca_plus",
        family_label="Tesouro IPCA+ / juros reais",
        target_duration_years=2.0,
        min_years_to_maturity=1.5,
        max_years_to_maturity=2.5,
    ),
    "TD_IPCA_3A": TesouroDiretoStrategyDefinition(
        instrument_id="TD_IPCA_3A",
        title_type="Tesouro IPCA+",
        family_id="ipca_plus",
        family_label="Tesouro IPCA+ / juros reais",
        target_duration_years=3.0,
        min_years_to_maturity=2.5,
        max_years_to_maturity=3.5,
    ),
    "TD_IPCA_5A": TesouroDiretoStrategyDefinition(
        instrument_id="TD_IPCA_5A",
        title_type="Tesouro IPCA+",
        family_id="ipca_plus",
        family_label="Tesouro IPCA+ / juros reais",
        target_duration_years=5.0,
        min_years_to_maturity=4.0,
        max_years_to_maturity=6.0,
    ),
}


def get_tesouro_direto_strategy_definition(
    instrument_id: str,
) -> TesouroDiretoStrategyDefinition | None:
    """Resolve one official Tesouro Direto strategy definition."""
    return TESOURO_DIRETO_STRATEGIES.get(instrument_id)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_tesouro_direto_frame(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = frame.rename(
        columns={
            "Tipo Titulo": "title_type",
            "Data Vencimento": "maturity_date",
            "Data Base": "date",
            "Taxa Compra Manha": "investor_sell_rate",
            "Taxa Venda Manha": "investor_buy_rate",
            "PU Compra Manha": "investor_sell_price",
            "PU Venda Manha": "investor_buy_price",
            "PU Base Manha": "base_price",
        }
    )
    for column in ("date", "maturity_date"):
        renamed[column] = pd.to_datetime(
            renamed[column],
            dayfirst=True,
            errors="coerce",
        ).dt.normalize()
    for column in (
        "investor_sell_rate",
        "investor_buy_rate",
        "investor_sell_price",
        "investor_buy_price",
        "base_price",
    ):
        renamed[column] = renamed[column].map(_to_float)
    normalized = (
        renamed[
            [
                "title_type",
                "maturity_date",
                "date",
                "investor_sell_rate",
                "investor_buy_rate",
                "investor_sell_price",
                "investor_buy_price",
                "base_price",
            ]
        ]
        .dropna(subset=["title_type", "maturity_date", "date", "investor_buy_price"])
        .drop_duplicates(subset=["title_type", "maturity_date", "date"], keep="last")
        .sort_values(["date", "title_type", "maturity_date"])
        .reset_index(drop=True)
    )
    normalized["years_to_maturity"] = (
        (normalized["maturity_date"] - normalized["date"]).dt.days.astype(float) / 365.25
    )
    normalized["title_key"] = (
        normalized["title_type"]
        + "::"
        + normalized["maturity_date"].dt.strftime("%Y-%m-%d")
    )
    return normalized[
        normalized["years_to_maturity"] > 0
    ].reset_index(drop=True)


def download_tesouro_direto_history() -> pd.DataFrame | None:
    """Download the official Tesouro Direto historical CSV."""
    import requests

    try:
        response = requests.get(
            TESOURO_DIRETO_CSV_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=60,
        )
        response.raise_for_status()
        raw = pd.read_csv(
            BytesIO(response.content),
            sep=";",
            encoding="latin1",
            dtype=str,
        )
        normalized = _normalize_tesouro_direto_frame(raw)
        logger.info("Downloaded %s Tesouro Direto rows", len(normalized))
        return normalized
    except Exception as exc:
        logger.error("Failed to download Tesouro Direto history: %s", exc)
        return None


def load_tesouro_direto_history(path: str | Path) -> pd.DataFrame | None:
    """Load normalized official Tesouro Direto history from CSV."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return None
        frame = pd.read_csv(file_path, parse_dates=["date", "maturity_date"])
        if not {
            "title_type",
            "maturity_date",
            "date",
            "investor_sell_price",
            "investor_buy_price",
            "base_price",
        }.issubset(frame.columns):
            return None
        frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
        frame["maturity_date"] = pd.to_datetime(frame["maturity_date"]).dt.normalize()
        for column in (
            "investor_sell_rate",
            "investor_buy_rate",
            "investor_sell_price",
            "investor_buy_price",
            "base_price",
            "years_to_maturity",
        ):
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
        normalized = (
            frame.dropna(subset=["title_type", "maturity_date", "date", "investor_buy_price"])
            .drop_duplicates(subset=["title_type", "maturity_date", "date"], keep="last")
            .sort_values(["date", "title_type", "maturity_date"])
            .reset_index(drop=True)
        )
        if "title_key" not in normalized.columns:
            normalized["title_key"] = (
                normalized["title_type"]
                + "::"
                + normalized["maturity_date"].dt.strftime("%Y-%m-%d")
            )
        return normalized
    except Exception as exc:
        logger.error("Failed to load Tesouro Direto cache from %s: %s", path, exc)
        return None


def save_tesouro_direto_history(df: pd.DataFrame, path: str | Path) -> None:
    """Persist normalized Tesouro Direto history to CSV."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = df.copy()
    normalized["date"] = pd.to_datetime(normalized["date"]).dt.strftime("%Y-%m-%d")
    normalized["maturity_date"] = (
        pd.to_datetime(normalized["maturity_date"]).dt.strftime("%Y-%m-%d")
    )
    normalized.to_csv(file_path, index=False)
    _TESOURO_DIRETO_CACHE.pop(str(file_path.resolve()), None)


def get_or_create_tesouro_direto_history(
    *,
    cache_dir: str | Path = "data/tesouro_direto",
    use_download: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Load, refresh, or download the official Tesouro Direto history."""
    file_path = Path(cache_dir) / "tesouro_direto_precos_taxas.csv"
    normalized_path = str(file_path.resolve())
    cached = _TESOURO_DIRETO_CACHE.get(normalized_path)
    if cached is not None:
        frame = cached.copy()
    else:
        frame = load_tesouro_direto_history(file_path)
        needs_refresh = frame is None or frame.empty
        if needs_refresh and use_download:
            downloaded = download_tesouro_direto_history()
            if downloaded is not None and not downloaded.empty:
                save_tesouro_direto_history(downloaded, file_path)
                frame = downloaded
        if frame is None or frame.empty:
            raise ValueError("Nao foi possivel obter o historico oficial do Tesouro Direto.")
        _TESOURO_DIRETO_CACHE[normalized_path] = frame.copy()

    filtered = frame.copy()
    if start_date is not None:
        filtered = filtered[filtered["date"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered[filtered["date"] <= pd.Timestamp(end_date)]
    filtered = filtered.reset_index(drop=True)
    if filtered.empty:
        raise ValueError("O Tesouro Direto nao possui historico para o periodo solicitado.")
    return filtered


def build_tesouro_cache_metadata(cache_dir: str | Path) -> dict[str, Any]:
    """Summarize the local Tesouro Direto cache state for API responses."""
    file_path = Path(cache_dir) / "tesouro_direto_precos_taxas.csv"
    if not file_path.exists():
        return {
            "label": "Tesouro Transparente / Tesouro Direto",
            "url": TESOURO_DIRETO_CSV_URL,
            "cache_path": str(file_path),
            "available": False,
        }
    stat = file_path.stat()
    return {
        "label": "Tesouro Transparente / Tesouro Direto",
        "url": TESOURO_DIRETO_CSV_URL,
        "cache_path": str(file_path),
        "available": True,
        "cached_at": pd.Timestamp(stat.st_mtime, unit="s", tz="UTC").isoformat(),
        "size_bytes": stat.st_size,
    }
