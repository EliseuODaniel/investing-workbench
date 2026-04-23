from __future__ import annotations

from src.investing_workbench.application.pairs_trading.ibov_history import (
    B3IbovUniverseHistoryService,
    parse_ibov_snapshot_from_page_texts,
)
from src.investing_workbench.infrastructure.persistence import LocalIndexUniverseRepository


def test_parse_ibov_snapshot_from_page_texts_extracts_constituents() -> None:
    payload = parse_ibov_snapshot_from_page_texts(
        page_texts=[
            "\n".join(
                [
                    "Composição das Carteiras de Índices",
                    "Para Janeiro a Abril de 2025",
                    "IBOVESPA",
                    "Código Ação Tipo Quantidade teórica Participação (%)",
                    "ABEV3 AMBEV S/A ON EDJ 4,394,835,131 2.5803",
                    "B3SA3 B3 ON NM 5,392,540,963 2.8224",
                    "ITUB4 ITAUUNIBANCO PN N1 4,792,902,422 7.4065",
                ]
            ),
            "\n".join(
                [
                    "WEGE3 WEG ON NM 1,485,954,732 2.7645",
                    "YDUQ3 YDUQS PART ON NM 261,365,845 0.1461",
                    "IGCX",
                ]
            ),
        ],
        as_of_date="2025-01-20",
        source_url="https://arquivos.b3.com.br/example.pdf",
    )

    assert payload["as_of_date"] == "2025-01-20"
    assert payload["validity_label"] == "Para Janeiro a Abril de 2025"
    assert payload["ticker_count"] == 5
    assert payload["tickers"][:3] == ["ABEV3", "B3SA3", "ITUB4"]
    assert payload["constituents"][0]["weight_pct"] == 2.5803
    assert payload["constituents"][-1]["ticker"] == "YDUQ3"


def test_ibov_history_service_falls_back_to_prior_cached_business_date(
    monkeypatch,
    tmp_path,
) -> None:
    repository = LocalIndexUniverseRepository(base_dir=tmp_path / "index_universes")

    def fake_download(url: str) -> bytes:
        if "2025-01-21" in url:
            raise FileNotFoundError(url)
        return b"pdf"

    def fake_parse(*, pdf_bytes: bytes, as_of_date: str, source_url: str):
        assert pdf_bytes == b"pdf"
        return {
            "index_id": "ibov",
            "snapshot_id": f"ibov_{as_of_date}",
            "as_of_date": as_of_date,
            "source_kind": "b3_bdi_pdf",
            "source_url": source_url,
            "validity_label": "Para Janeiro a Abril de 2025",
            "ticker_count": 2,
            "tickers": ["AAA1", "BBB1"],
            "constituents": [
                {
                    "ticker": "AAA1",
                    "descriptor": "AAA ON",
                    "theoretical_quantity": 1,
                    "weight_pct": 1.0,
                },
                {
                    "ticker": "BBB1",
                    "descriptor": "BBB ON",
                    "theoretical_quantity": 1,
                    "weight_pct": 1.0,
                },
            ],
            "imported_at": "2025-01-20T00:00:00+00:00",
        }

    monkeypatch.setattr(
        "src.investing_workbench.application.pairs_trading.ibov_history.parse_ibov_snapshot_from_bdi_pdf",
        fake_parse,
    )

    service = B3IbovUniverseHistoryService(
        repository=repository,
        download_pdf_bytes=fake_download,
    )
    resolution = service.resolve_snapshot(as_of_date="2025-01-21")

    assert resolution.requested_as_of_date == "2025-01-21"
    assert resolution.resolved_as_of_date == "2025-01-20"
    assert resolution.cache_status == "fetched"

    cached = service.resolve_snapshot(as_of_date="2025-01-20")
    assert cached.cache_status == "cache_hit"
    assert cached.snapshot["tickers"] == ["AAA1", "BBB1"]
