"""Tests for local product-data source refreshes."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from zipfile import ZipFile

import pytest

from src.investing_workbench.application.investments import catalog as investment_catalog
from src.investing_workbench.application.investments.catalog import INSTRUMENTS
from src.investing_workbench.application.investments.product_data_connectors import (
    ProductDataSourceService,
    load_cached_source_rows,
    parse_b3_fii_rows_from_text,
    parse_cvm_daily_report_zip_bytes,
)
from src.investing_workbench.application.investments.product_data_plan import (
    build_product_data_plan,
)


def _seed_collector(source: dict[str, object]) -> tuple[list[dict[str, str]], str, str, str | None]:
    del source
    return (
        [
            {
                "ticker": "HGLG11",
                "nome": "CSHG Logistica",
                "segmento": "Logistica",
                "gestor": "Credit Suisse Hedging-Griffo",
                "administrador": "Credit Suisse Hedging-Griffo",
                "status_listagem": "Listado",
                "yield_12m_pct": "8.4",
                "liquidity_label": "Alta",
                "income_focus": "Renda e tijolo",
                "data_quality_score": "0.82",
            },
            {
                "ticker": "VISC11",
                "nome": "Vinci Shopping Centers",
                "segmento": "Shopping centers",
                "gestor": "Vinci Real Estate",
                "administrador": "BRL Trust",
                "status_listagem": "Listado",
                "yield_12m_pct": "9.1",
                "liquidity_label": "Media",
                "income_focus": "Renda e shopping",
                "data_quality_score": "0.78",
            },
            {
                "ticker": "KNCR11",
                "nome": "Kinea Rendimentos Imobiliarios",
                "segmento": "Recebiveis imobiliarios",
                "gestor": "Kinea Investimentos",
                "administrador": "Intrag DTVM",
                "status_listagem": "Listado",
                "yield_12m_pct": "10.6",
                "liquidity_label": "Alta",
                "income_focus": "Renda recorrente",
                "data_quality_score": "0.84",
            },
            {
                "ticker": "MXRF11",
                "nome": "Maxi Renda",
                "segmento": "Recebiveis imobiliarios",
                "gestor": "XP Vista Asset",
                "administrador": "BTG Pactual",
                "status_listagem": "Listado",
                "yield_12m_pct": "11.2",
                "liquidity_label": "Alta",
                "income_focus": "Renda recorrente",
                "data_quality_score": "0.74",
            },
            {
                "ticker": "XPML11",
                "nome": "XP Malls",
                "segmento": "Shopping centers",
                "gestor": "XP Vista Asset",
                "administrador": "BTG Pactual",
                "status_listagem": "Listado",
                "yield_12m_pct": "8.9",
                "liquidity_label": "Media",
                "income_focus": "Renda e shopping",
                "data_quality_score": "0.72",
            },
        ],
        "official_html",
        "Teste com coleta controlada.",
        None,
    )


def _cvm_seed_collector(
    source: dict[str, object],
) -> tuple[list[dict[str, str]], str, str, str | None]:
    del source
    return (
        [
            {
                "cnpj_fundo": "11.728.688/0001-47",
                "dt_comptc": "2026-05-04",
                "vl_total": "100000000.00",
                "vl_quota": "100.000000",
                "vl_patrim_liq": "99000000.00",
                "captc_dia": "0.00",
                "resg_dia": "0.00",
                "nr_cotst": "1000",
            },
            {
                "cnpj_fundo": "16.706.958/0001-32",
                "dt_comptc": "2026-05-04",
                "vl_total": "250000000.00",
                "vl_quota": "125.000000",
                "vl_patrim_liq": "248500000.00",
                "captc_dia": "150000.00",
                "resg_dia": "25000.00",
                "nr_cotst": "2500",
            },
        ],
        "official_zip",
        "Teste com coleta CVM controlada.",
        None,
    )


def test_product_data_refresh_persists_fii_manifest(tmp_path: Path) -> None:
    service = ProductDataSourceService(
        cache_root=tmp_path / "product_sources",
        collect_b3_fii_rows_func=_seed_collector,
    )

    response = service.refresh_source(source_id="b3_fii_listed", force=True)
    manifest = service.list_manifest()
    rows = load_cached_source_rows(
        source_id="b3_fii_listed",
        cache_root=tmp_path / "product_sources",
    )

    assert response["status"] == "refreshed"
    assert response["manifest"]["row_count"] == 5
    assert response["manifest"]["schema_version"] == "b3_fii_listed.v2"
    assert response["manifest"]["collection_mode"] == "official_html"
    assert response["manifest"]["checksum_sha256"]
    assert response["history"][0]["status"] == "refreshed"
    assert response["history"][0]["duration_ms"] >= 0
    assert response["history"][0]["source_attempted_url"]
    source_manifest = next(
        item for item in manifest["sources"] if item["source_id"] == "b3_fii_listed"
    )
    assert source_manifest["row_count"] == 5
    assert source_manifest["schema_version"] == "b3_fii_listed.v2"
    assert rows[0]["ticker"] == "HGLG11"


def test_parse_b3_fii_rows_from_fixture() -> None:
    fixture = Path("tests/fixtures/product_data/b3_fii_listed_sample.html").read_text(
        encoding="utf-8"
    )

    rows = parse_b3_fii_rows_from_text(fixture)

    assert {row["ticker"] for row in rows} == {"HGLG11", "KNCR11", "VISC11"}


def test_product_data_plan_reports_catalog_enrichment_after_refresh(tmp_path: Path) -> None:
    service = ProductDataSourceService(
        cache_root=tmp_path / "product_sources",
        collect_b3_fii_rows_func=_seed_collector,
    )
    service.refresh_source(source_id="b3_fii_listed", force=True)

    payload = build_product_data_plan(
        instruments=list(INSTRUMENTS),
        cache_root=tmp_path / "product_sources",
    )

    enrichment = payload["catalog_enrichment"][0]
    assert enrichment["family_id"] == "fiis"
    assert enrichment["cached_row_count"] == 5
    assert enrichment["matched_instrument_count"] >= 3
    assert enrichment["status"] == "enriched"
    assert payload["identity_map"]


def test_product_data_plan_reports_cvm_fund_profile(tmp_path: Path) -> None:
    service = ProductDataSourceService(
        cache_root=tmp_path / "product_sources",
        collect_cvm_fund_rows_func=_cvm_seed_collector,
    )
    service.refresh_source(source_id="cvm_fund_daily_reports", force=True)

    payload = build_product_data_plan(
        instruments=list(INSTRUMENTS),
        cache_root=tmp_path / "product_sources",
    )

    profile = payload["cvm_fund_profile"]
    assert profile["status"] == "available"
    assert profile["row_count"] == 2
    assert profile["latest_date"] == "2026-05-04"
    assert profile["total_net_worth"] == 347500000.0
    assert profile["net_flow"] == 125000.0
    assert profile["sample_largest_funds"][0]["cnpj_fundo"] == "16.706.958/0001-32"
    bridge = payload["fii_cvm_bridge"]
    assert bridge["mapped_instrument_count"] == 2
    assert bridge["matched_cvm_cache_count"] == 2
    assert bridge["coverage_ratio"] == 1.0
    assert {row["ticker"] for row in bridge["rows"]} == {"HGLG11", "KNCR11"}
    rankings = payload["cvm_fund_rankings"]
    assert {item["ranking_id"] for item in rankings} == {
        "cvm_largest_net_worth",
        "cvm_highest_net_flow",
        "cvm_largest_holder_base",
    }
    largest = next(item for item in rankings if item["ranking_id"] == "cvm_largest_net_worth")
    assert largest["rows"][0]["cnpj_fundo"] == "16.706.958/0001-32"
    flow = next(item for item in rankings if item["ranking_id"] == "cvm_highest_net_flow")
    assert flow["rows"][0]["score"] == 125000.0


def test_cvm_refresh_writes_initial_manifest(tmp_path: Path) -> None:
    service = ProductDataSourceService(
        cache_root=tmp_path / "product_sources",
        collect_cvm_fund_rows_func=_cvm_seed_collector,
    )

    response = service.refresh_source(source_id="cvm_fund_daily_reports", force=True)

    assert response["status"] == "refreshed"
    assert response["manifest"]["schema_version"] == "cvm_fund_daily_reports.v1"
    assert response["manifest"]["row_count"] == 2
    assert response["history"][0]["collection_mode"] == "official_zip"
    rows = load_cached_source_rows(
        source_id="cvm_fund_daily_reports",
        cache_root=tmp_path / "product_sources",
    )
    assert rows[0]["vl_patrim_liq"] == "99000000.00"
    assert rows[0]["nr_cotst"] == "1000"


def test_b3_listed_products_refresh_and_profile(tmp_path: Path) -> None:
    service = ProductDataSourceService(cache_root=tmp_path / "product_sources")

    response = service.refresh_source(source_id="b3_listed_products", force=True)
    payload = build_product_data_plan(
        instruments=list(INSTRUMENTS),
        cache_root=tmp_path / "product_sources",
    )

    assert response["status"] == "refreshed"
    assert response["manifest"]["schema_version"] == "b3_listed_products.v1"
    assert response["manifest"]["row_count"] >= 6
    assert response["history"][0]["collection_mode"] == "curated_seed"
    profile = payload["etf_bdr_profile"]
    assert profile["status"] == "available"
    assert profile["row_count"] == response["manifest"]["row_count"]
    assert profile["average_fee_pct"] is not None
    rankings = payload["etf_bdr_rankings"]
    assert rankings[0]["ranking_id"] == "b3_lowest_admin_fee"
    assert rankings[0]["rows"][0]["score"] <= rankings[0]["rows"][-1]["score"]


def test_product_data_plan_builds_methodology_readiness_ranking(tmp_path: Path) -> None:
    service = ProductDataSourceService(
        cache_root=tmp_path / "product_sources",
        collect_b3_fii_rows_func=_seed_collector,
        collect_cvm_fund_rows_func=_cvm_seed_collector,
    )
    service.refresh_source(source_id="b3_fii_listed", force=True)
    service.refresh_source(source_id="cvm_fund_daily_reports", force=True)
    service.refresh_source(source_id="b3_listed_products", force=True)

    payload = build_product_data_plan(
        instruments=list(INSTRUMENTS),
        cache_root=tmp_path / "product_sources",
    )

    ranking = payload["methodology_readiness_ranking"]
    tickers = {row["ticker"] for row in ranking["rows"]}
    assert ranking["status"] == "available"
    assert {"HGLG11", "KNCR11", "BOVA11", "IVVB11"} <= tickers
    assert ranking["rows"][0]["rank"] == 1
    assert ranking["rows"][0]["score"] >= ranking["rows"][-1]["score"]
    assert all(row["caveat"] for row in ranking["rows"])


def test_product_data_plan_marks_roadmap_complete(tmp_path: Path) -> None:
    service = ProductDataSourceService(
        cache_root=tmp_path / "product_sources",
        collect_b3_fii_rows_func=_seed_collector,
        collect_cvm_fund_rows_func=_cvm_seed_collector,
    )
    service.refresh_source(source_id="b3_fii_listed", force=True)
    service.refresh_source(source_id="cvm_fund_daily_reports", force=True)
    service.refresh_source(source_id="b3_listed_products", force=True)

    payload = build_product_data_plan(
        instruments=list(INSTRUMENTS),
        cache_root=tmp_path / "product_sources",
    )

    planned_statuses = {"specified", "mapped", "backlog_mapped", "planned"}
    roadmap_statuses = {step["status"] for step in payload["roadmap_steps"]}
    release_statuses = {release["status"] for release in payload["next_release_candidates"]}
    assert payload["roadmap_step_count"] == 9
    assert payload["roadmap_completed_step_count"] == 9
    assert payload["roadmap_completion_pct"] == 1.0
    assert roadmap_statuses.isdisjoint(planned_statuses)
    assert release_statuses.isdisjoint(planned_statuses)


def test_parse_cvm_daily_report_zip_bytes() -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        delimiter=";",
        fieldnames=[
            "CNPJ_FUNDO_CLASSE",
            "DT_COMPTC",
            "VL_TOTAL",
            "VL_QUOTA",
            "VL_PATRIM_LIQ",
            "CAPTC_DIA",
            "RESG_DIA",
            "NR_COTST",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "CNPJ_FUNDO_CLASSE": "00.000.000/0001-91",
            "DT_COMPTC": "2026-04-30",
            "VL_TOTAL": "100000000.00",
            "VL_QUOTA": "100.000000",
            "VL_PATRIM_LIQ": "99000000.00",
            "CAPTC_DIA": "10.00",
            "RESG_DIA": "5.00",
            "NR_COTST": "1000",
        }
    )
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, mode="w") as archive:
        archive.writestr("inf_diario_fi_202604.csv", buffer.getvalue().encode("latin1"))

    rows = parse_cvm_daily_report_zip_bytes(zip_buffer.getvalue())

    assert rows == [
        {
            "cnpj_fundo": "00.000.000/0001-91",
            "dt_comptc": "2026-04-30",
            "vl_total": "100000000.00",
            "vl_quota": "100.000000",
            "vl_patrim_liq": "99000000.00",
            "captc_dia": "10.00",
            "resg_dia": "5.00",
            "nr_cotst": "1000",
        }
    ]


def test_catalog_builds_fii_income_ranking_from_cached_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_rows(*, source_id: str, cache_root: str = "data/product_sources") -> list[dict[str, str]]:
        del cache_root
        assert source_id == "b3_fii_listed"
        return [
            {
                "ticker": "KNCR11",
                "segmento": "Recebiveis imobiliarios",
                "status_listagem": "Listado",
                "yield_12m_pct": "10.6",
                "liquidity_label": "Alta",
                "income_focus": "Renda recorrente",
                "data_quality_score": "0.84",
            },
            {
                "ticker": "VISC11",
                "segmento": "Shopping centers",
                "status_listagem": "Listado",
                "yield_12m_pct": "9.1",
                "liquidity_label": "Media",
                "income_focus": "Renda e shopping",
                "data_quality_score": "0.78",
            },
        ]

    monkeypatch.setattr(
        "src.investing_workbench.application.investments.product_data_connectors."
        "load_cached_source_rows",
        fake_rows,
    )

    visible_items = [item for item in INSTRUMENTS if item.visible_in_catalog]
    filters = investment_catalog._build_product_data_filters(visible_items)
    screeners = investment_catalog._build_product_data_screeners(visible_items)
    rankings = investment_catalog._build_product_data_rankings(visible_items)

    assert {item["filter_id"] for item in filters} >= {
        "fii_liquidity",
        "fii_income_focus",
    }
    screener_rows = {row["instrument_id"]: row for row in screeners[0]["rows"]}
    assert screener_rows["KNCR11"]["yield_12m_pct"] == 10.6
    income_ranking = next(item for item in rankings if item["ranking_id"] == "fii_income_quality")
    assert income_ranking["rows"][0]["instrument_id"] == "KNCR11"
    assert income_ranking["rows"][0]["score"] > income_ranking["rows"][1]["score"]
