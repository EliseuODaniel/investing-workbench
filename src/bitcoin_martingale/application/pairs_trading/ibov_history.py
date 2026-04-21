"""Official IBOV universe snapshots resolved from B3 BDI PDFs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pypdf import PdfReader

from src.bitcoin_martingale.infrastructure.persistence import LocalIndexUniverseRepository

INDEX_ID = "ibov"
DEFAULT_BDI_LOOKBACK_DAYS = 10
IBOV_REBALANCE_MONTHS = (1, 5, 9)
BDI_URL_TEMPLATE = "https://arquivos.b3.com.br/bdi/download/bdi/{date}/BDI_02_{compact_date}.pdf"
_DECIMAL_RE = re.compile(r"^[0-9][0-9.,]*$")
_DATE_LABEL_RE = re.compile(r"^Para .+ de \d{4}$")


@dataclass(frozen=True, slots=True)
class SnapshotResolution:
    """Resolved official IBOV snapshot plus user-facing resolution metadata."""

    snapshot: dict[str, Any]
    requested_as_of_date: str
    resolved_as_of_date: str
    cache_status: str


def build_bdi_pdf_url(as_of_date: str) -> str:
    """Build the official B3 BDI PDF URL for one date."""
    return BDI_URL_TEMPLATE.format(
        date=as_of_date,
        compact_date=as_of_date.replace("-", ""),
    )


def parse_ibov_snapshot_from_bdi_pdf(
    *,
    pdf_bytes: bytes,
    as_of_date: str,
    source_url: str,
) -> dict[str, Any]:
    """Parse one official IBOV snapshot from a B3 BDI PDF payload."""
    reader = PdfReader(BytesIO(pdf_bytes))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    return parse_ibov_snapshot_from_page_texts(
        page_texts=page_texts,
        as_of_date=as_of_date,
        source_url=source_url,
    )


def parse_ibov_snapshot_from_page_texts(
    *,
    page_texts: list[str],
    as_of_date: str,
    source_url: str,
) -> dict[str, Any]:
    """Parse one official IBOV snapshot from extracted BDI page text."""
    start_page = _find_ibov_section_start(page_texts)
    validity_label = _find_validity_label(page_texts=page_texts, start_page=start_page)

    constituents: list[dict[str, Any]] = []
    started = False
    for page_text in page_texts[start_page:]:
        page_rows = 0
        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue

            if not started:
                if line == "IBOVESPA":
                    started = True
                continue

            if line.startswith("Código"):
                continue

            if _is_constituent_line(line):
                row = _parse_constituent_line(line)
                if all(existing["ticker"] != row["ticker"] for existing in constituents):
                    constituents.append(row)
                page_rows += 1
                continue

            if page_rows > 0 and _looks_like_next_section(line):
                break

        if started and page_rows == 0 and constituents:
            break

    if not constituents:
        raise ValueError("Unable to parse official IBOV composition from the supplied BDI PDF.")

    return {
        "index_id": INDEX_ID,
        "snapshot_id": f"{INDEX_ID}_{as_of_date}",
        "as_of_date": as_of_date,
        "source_kind": "b3_bdi_pdf",
        "source_url": source_url,
        "validity_label": validity_label,
        "ticker_count": len(constituents),
        "tickers": [row["ticker"] for row in constituents],
        "constituents": constituents,
        "imported_at": datetime.now(UTC).isoformat(),
    }


class B3IbovUniverseHistoryService:
    """Resolve official IBOV universe snapshots and cache them locally."""

    def __init__(
        self,
        repository: LocalIndexUniverseRepository | None = None,
        download_pdf_bytes: Callable[[str], bytes] | None = None,
    ) -> None:
        self.repository = repository or LocalIndexUniverseRepository()
        self.download_pdf_bytes = download_pdf_bytes or _download_pdf_bytes

    def resolve_snapshot(
        self,
        *,
        as_of_date: str,
        force_refresh: bool = False,
        max_lookback_days: int = DEFAULT_BDI_LOOKBACK_DAYS,
        search_direction: str = "backward",
    ) -> SnapshotResolution:
        """Resolve one official IBOV snapshot, falling back to prior business dates when needed."""
        requested = date.fromisoformat(as_of_date)
        last_error: Exception | None = None

        for candidate in _candidate_dates(
            requested=requested,
            max_offset_days=max_lookback_days,
            search_direction=search_direction,
        ):
            candidate_iso = candidate.isoformat()

            if not force_refresh:
                cached = self.repository.find_snapshot(index_id=INDEX_ID, as_of_date=candidate_iso)
                if cached is not None:
                    return SnapshotResolution(
                        snapshot=cached,
                        requested_as_of_date=requested.isoformat(),
                        resolved_as_of_date=candidate_iso,
                        cache_status="cache_hit",
                    )

            try:
                source_url = build_bdi_pdf_url(candidate_iso)
                pdf_bytes = self.download_pdf_bytes(source_url)
                snapshot = parse_ibov_snapshot_from_bdi_pdf(
                    pdf_bytes=pdf_bytes,
                    as_of_date=candidate_iso,
                    source_url=source_url,
                )
                self.repository.persist_snapshot(
                    index_id=INDEX_ID,
                    as_of_date=candidate_iso,
                    snapshot=snapshot,
                )
                return SnapshotResolution(
                    snapshot=snapshot,
                    requested_as_of_date=requested.isoformat(),
                    resolved_as_of_date=candidate_iso,
                    cache_status="fetched",
                )
            except (FileNotFoundError, HTTPError, URLError, ValueError) as exc:
                last_error = exc
                continue

        message = (
            f"Unable to resolve an official B3 IBOV snapshot for {requested.isoformat()} "
            f"within {max_lookback_days} calendar days."
        )
        if last_error is not None:
            raise RuntimeError(message) from last_error
        raise RuntimeError(message)

    def list_cached_snapshots(self) -> list[dict[str, Any]]:
        """List cached official IBOV snapshots."""
        return self.repository.list_snapshots(index_id=INDEX_ID)

    def get_cached_snapshot(self, *, as_of_date: str) -> dict[str, Any]:
        """Load one cached official IBOV snapshot."""
        return self.repository.get_snapshot(index_id=INDEX_ID, as_of_date=as_of_date)

    def backfill_snapshots(
        self,
        *,
        start_date: str,
        end_date: str,
        force_refresh: bool = False,
    ) -> list[dict[str, Any]]:
        """Resolve and cache official IBOV snapshots around the rebalance cadence."""
        requested_start = date.fromisoformat(start_date)
        requested_end = date.fromisoformat(end_date)
        if requested_end < requested_start:
            raise ValueError("end_date must be greater than or equal to start_date")

        resolutions: list[dict[str, Any]] = []
        seen_resolved_dates: set[str] = set()
        for anchor in iter_rebalance_anchor_dates(start_date=start_date, end_date=end_date):
            resolution = self.resolve_snapshot(
                as_of_date=anchor,
                force_refresh=force_refresh,
                search_direction="forward",
            )
            if resolution.resolved_as_of_date in seen_resolved_dates:
                continue
            seen_resolved_dates.add(resolution.resolved_as_of_date)
            resolutions.append(
                {
                    "requested_as_of_date": resolution.requested_as_of_date,
                    "resolved_as_of_date": resolution.resolved_as_of_date,
                    "cache_status": resolution.cache_status,
                    "ticker_count": int(resolution.snapshot.get("ticker_count", 0)),
                    "validity_label": resolution.snapshot.get("validity_label"),
                    "source_url": resolution.snapshot.get("source_url"),
                }
            )
        return resolutions


def _download_pdf_bytes(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        return response.read()


def iter_rebalance_anchor_dates(*, start_date: str, end_date: str) -> list[str]:
    """Return monthly anchor dates for IBOV rebalancing windows between two dates."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be greater than or equal to start_date")

    anchors: list[str] = []
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        if cursor.month in IBOV_REBALANCE_MONTHS and cursor >= start:
            anchors.append(cursor.isoformat())
        month = cursor.month + 1
        year = cursor.year
        if month == 13:
            month = 1
            year += 1
        cursor = date(year, month, 1)

    if start.isoformat() not in anchors:
        anchors.insert(0, start.isoformat())
    return sorted(dict.fromkeys(anchors))


def _find_ibov_section_start(page_texts: list[str]) -> int:
    for page_index, text in enumerate(page_texts):
        if "IBOVESPA" in text and "Quantidade teórica" in text:
            return page_index
        if "IBOVESPA" in text and "Participação (%)" in text:
            return page_index
    raise ValueError("Unable to find an IBOVESPA section in the supplied BDI content.")


def _candidate_dates(
    *,
    requested: date,
    max_offset_days: int,
    search_direction: str,
) -> list[date]:
    if search_direction not in {"backward", "forward"}:
        raise ValueError("search_direction must be 'backward' or 'forward'")
    if search_direction == "backward":
        return [requested - timedelta(days=offset) for offset in range(max_offset_days + 1)]
    return [requested + timedelta(days=offset) for offset in range(max_offset_days + 1)]


def _find_validity_label(*, page_texts: list[str], start_page: int) -> str | None:
    for page_index in range(max(0, start_page - 1), min(len(page_texts), start_page + 2)):
        for raw_line in page_texts[page_index].splitlines():
            line = " ".join(raw_line.split())
            if _DATE_LABEL_RE.match(line):
                return line
    return None


def _is_constituent_line(line: str) -> bool:
    tokens = line.split()
    if len(tokens) < 4:
        return False
    if not _looks_like_ticker(tokens[0]):
        return False
    return _DECIMAL_RE.match(tokens[-2]) is not None and _DECIMAL_RE.match(tokens[-1]) is not None


def _parse_constituent_line(line: str) -> dict[str, Any]:
    tokens = line.split()
    ticker = tokens[0].upper()
    descriptor = " ".join(tokens[1:-2]).strip()
    quantity_token = tokens[-2]
    weight_token = tokens[-1]
    return {
        "ticker": ticker,
        "descriptor": descriptor,
        "theoretical_quantity": _parse_quantity(quantity_token),
        "weight_pct": _parse_decimal(weight_token),
    }


def _parse_quantity(value: str) -> int:
    digits = value.replace(".", "").replace(",", "")
    return int(digits)


def _parse_decimal(value: str) -> float:
    normalized = (
        value.replace(".", "").replace(",", ".")
        if value.count(",") == 1 and value.count(".") > 1
        else value.replace(",", ".")
    )
    return float(normalized)


def _looks_like_ticker(token: str) -> bool:
    if not (4 <= len(token) <= 7):
        return False
    if not any(char.isdigit() for char in token):
        return False
    return token.isalnum() and token.upper() == token


def _looks_like_next_section(line: str) -> bool:
    if _is_constituent_line(line):
        return False
    if line in {"BDI", "Indicadores e Informativos", "Boletim Diário do Mercado"}:
        return False
    if line.startswith("REFERENTE A "):
        return False
    if line.startswith("Código "):
        return False
    compact = line.replace(" ", "")
    if compact.isupper() and len(compact) <= 12 and not any(char.isdigit() for char in compact):
        return True
    return False
