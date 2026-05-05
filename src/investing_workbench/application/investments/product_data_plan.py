"""Post-roadmap product-data planning for the investments catalog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import InvestmentInstrument
from .product_data_connectors import (
    PRODUCT_DATA_SOURCE_DEFINITIONS,
    build_market_filter_backlog,
    build_product_data_manifest,
    build_product_data_validation_plan,
    build_release_packages,
    load_cached_source_rows,
)

FII_CVM_CNPJ_CROSSWALK: tuple[dict[str, str], ...] = (
    {
        "ticker": "HGLG11",
        "cnpj_fundo": "11.728.688/0001-47",
        "source_note": "CNPJ divulgado em documentos e paginas publicas do fundo.",
    },
    {
        "ticker": "KNCR11",
        "cnpj_fundo": "16.706.958/0001-32",
        "source_note": "CNPJ divulgado em relatorio publico do fundo.",
    },
)


def build_product_data_plan(
    *,
    instruments: list[InvestmentInstrument],
    cache_root: Path | str = "data/product_sources",
) -> dict[str, Any]:
    """Build the next product-data expansion track from the current catalog."""

    visible_items = [item for item in instruments if item.visible_in_catalog]
    family_rows = _build_family_rows(visible_items)
    connected_count = sum(
        1
        for source in PRODUCT_DATA_SOURCE_DEFINITIONS
        if source["integration_status"] == "connected"
    )
    partial_count = sum(
        1
        for source in PRODUCT_DATA_SOURCE_DEFINITIONS
        if source["integration_status"] == "partial"
    )
    release_packages = build_release_packages()
    roadmap_steps = _build_roadmap_steps(release_packages)
    roadmap_completed_step_count = sum(
        1 for step in roadmap_steps if _roadmap_step_is_complete(str(step["status"]))
    )
    roadmap_step_count = len(roadmap_steps)
    return {
        "title": "Plano pos-roadmap de dados de produto",
        "plain_language_summary": (
            "O roadmap principal esta concluido. Esta trilha mostra como evoluir de catalogo "
            "didatico para dados externos vivos, com fonte, frescor, cache e caveat por produto."
        ),
        "status": "post_roadmap",
        "source_count": len(PRODUCT_DATA_SOURCE_DEFINITIONS),
        "connected_source_count": connected_count,
        "partial_source_count": partial_count,
        "roadmap_step_count": roadmap_step_count,
        "roadmap_completed_step_count": roadmap_completed_step_count,
        "roadmap_completion_pct": (
            roadmap_completed_step_count / roadmap_step_count if roadmap_step_count else 0.0
        ),
        "sources": [_source_payload(source) for source in PRODUCT_DATA_SOURCE_DEFINITIONS],
        "family_coverage": family_rows,
        "source_manifest": build_product_data_manifest(cache_root=cache_root),
        "catalog_enrichment": _build_catalog_enrichment(
            visible_items,
            cache_root=cache_root,
        ),
        "identity_map": build_fii_identity_map(cache_root=cache_root),
        "fii_cvm_bridge": build_fii_cvm_bridge(
            instruments=visible_items,
            cache_root=cache_root,
        ),
        "cvm_fund_profile": build_cvm_fund_profile(cache_root=cache_root),
        "cvm_fund_rankings": build_cvm_fund_rankings(cache_root=cache_root),
        "etf_bdr_profile": build_etf_bdr_profile(cache_root=cache_root),
        "etf_bdr_rankings": build_etf_bdr_rankings(cache_root=cache_root),
        "methodology_readiness_ranking": build_methodology_readiness_ranking(
            instruments=visible_items,
            cache_root=cache_root,
        ),
        "implementation_steps": [
            "Criar inventario versionado de fontes oficiais por familia de produto.",
            "Adicionar conectores leves com cache, timestamp, tamanho e ultima atualizacao.",
            "Ligar dados externos ao product_profile sem esconder lacunas metodologicas.",
            "Expandir catalogo apenas quando houver fonte, frescor e caveat claros.",
            "Promover novos dados para rankings/screeners somente depois de testes focados.",
            "Manter full backend/frontend validation antes de publicar cada pacote de dados.",
        ],
        "roadmap_steps": roadmap_steps,
        "next_release_candidates": release_packages,
        "market_filter_backlog": build_market_filter_backlog(),
        "validation_plan": build_product_data_validation_plan(),
        "quality_gate": [
            "Fonte primaria ou fonte explicitamente marcada como secundaria.",
            "Data de coleta e politica de refresh visiveis no payload.",
            "Teste backend de contrato e teste frontend quando aparecer na UI.",
            "Aviso claro quando o dado for proxy, indice teorico ou produto investivel.",
        ],
    }


def _build_family_rows(instruments: list[InvestmentInstrument]) -> list[dict[str, Any]]:
    families: dict[str, list[InvestmentInstrument]] = {}
    for instrument in instruments:
        families.setdefault(instrument.category_id, []).append(instrument)

    rows: list[dict[str, Any]] = []
    for family_id, items in sorted(families.items()):
        product_profile_count = sum(
            1 for item in items if item.to_payload().get("product_profile")
        )
        rows.append(
            {
                "family_id": family_id,
                "label": items[0].category_label,
                "instrument_count": len(items),
                "product_profile_count": product_profile_count,
                "coverage_score": product_profile_count / len(items) if items else 0.0,
                "external_data_status": _external_status_for_family(family_id),
            }
        )
    return rows


def _external_status_for_family(family_id: str) -> str:
    if family_id == "fixed_income_b3":
        return "connected"
    if family_id == "fiis":
        return "connected_seeded"
    if family_id in {"international_b3", "etfs_brazil", "stocks_brazil"}:
        return "partial"
    if family_id in {"guided_portfolios", "macro_proxies"}:
        return "modeled"
    return "planned"


def _build_roadmap_steps(release_packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "step_id": "fii_connector",
            "label": "Conector real de FIIs",
            "status": "available_seed",
            "release_ids": ["fii_income_data"],
        },
        {
            "step_id": "cvm_funds",
            "label": "CVM para fundos/FIIs",
            "status": "available",
            "release_ids": ["fii_income_data", "fund_cvm_profile"],
        },
        {
            "step_id": "treasury_depth",
            "label": "Tesouro Direto mais profundo",
            "status": "available",
            "release_ids": ["treasury_cashflow_data"],
        },
        {
            "step_id": "etf_bdr_tracking",
            "label": "Taxas e tracking de ETFs/BDRs",
            "status": "available_seed",
            "release_ids": ["etf_bdr_fee_tracking"],
        },
        {
            "step_id": "rankings_screeners",
            "label": "Rankings/screeners com dados novos",
            "status": "available",
            "release_ids": [item["release_id"] for item in release_packages],
        },
        {
            "step_id": "data_quality_panel",
            "label": "Painel de qualidade dos dados",
            "status": "available",
            "release_ids": [],
        },
        {
            "step_id": "dataset_versioning",
            "label": "Persistencia/versionamento dos datasets",
            "status": "manifest_available",
            "release_ids": [],
        },
        {
            "step_id": "market_explorer_filters",
            "label": "UX de exploracao de mercado",
            "status": "available",
            "release_ids": [],
        },
        {
            "step_id": "methodology_validation",
            "label": "Validacao metodologica",
            "status": "gated",
            "release_ids": [],
        },
    ]


def _roadmap_step_is_complete(status: str) -> bool:
    return status in {
        "available",
        "available_seed",
        "connected",
        "connected_seeded",
        "connected_next",
        "manifest_available",
        "gated",
        "enriched",
    }


def _source_payload(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "label": source["label"],
        "url": source["url"],
        "coverage": source["coverage"],
        "freshness_policy": source["freshness_policy"],
        "integration_status": source["integration_status"],
        "connector_status": source["connector_status"],
        "cache_key": source["cache_key"],
        "families": list(source["families"]),
        "expected_fields": list(source["expected_fields"]),
    }


def _build_catalog_enrichment(
    instruments: list[InvestmentInstrument],
    cache_root: Path | str,
) -> list[dict[str, Any]]:
    fii_rows = load_cached_source_rows(source_id="b3_fii_listed", cache_root=cache_root)
    fii_by_ticker = {row["ticker"].upper(): row for row in fii_rows if row.get("ticker")}
    fii_instruments = [
        item
        for item in instruments
        if item.category_id == "fiis" and item.ticker and item.ticker.upper() in fii_by_ticker
    ]
    sample = [
        {
            "instrument_id": item.instrument_id,
            "ticker": item.ticker,
            "segment": fii_by_ticker[str(item.ticker).upper()].get("segmento"),
            "listing_status": fii_by_ticker[str(item.ticker).upper()].get("status_listagem"),
        }
        for item in fii_instruments[:4]
    ]
    return [
        {
            "family_id": "fiis",
            "source_id": "b3_fii_listed",
            "matched_instrument_count": len(fii_instruments),
            "cached_row_count": len(fii_rows),
            "status": "enriched" if fii_instruments else "waiting_for_cache",
            "sample": sample,
            "next_action": (
                "Usar segmento/status como filtro real no Market Explorer."
                if fii_instruments
                else "Executar refresh de b3_fii_listed para ativar enriquecimento."
            ),
        }
    ]


def build_fii_identity_map(
    *,
    cache_root: Path | str = "data/product_sources",
) -> list[dict[str, Any]]:
    """Build the first ticker/name/source identity map for cached FIIs."""

    return [
        {
            "ticker": row.get("ticker"),
            "name": row.get("nome"),
            "segment": row.get("segmento"),
            "listing_status": row.get("status_listagem"),
            "source_id": "b3_fii_listed",
            "identity_status": "ticker_matched",
        }
        for row in load_cached_source_rows(source_id="b3_fii_listed", cache_root=cache_root)
        if row.get("ticker")
    ]


def build_fii_cvm_bridge(
    *,
    instruments: list[InvestmentInstrument],
    cache_root: Path | str = "data/product_sources",
) -> dict[str, Any]:
    """Bridge curated FII tickers to CVM CNPJs and cached daily-report rows."""

    fii_instruments = {
        str(item.ticker).upper(): item
        for item in instruments
        if item.category_id == "fiis" and item.ticker
    }
    cvm_rows = load_cached_source_rows(source_id="cvm_fund_daily_reports", cache_root=cache_root)
    latest_by_cnpj = _latest_cvm_rows_by_cnpj(cvm_rows)
    bridge_rows: list[dict[str, Any]] = []
    for item in FII_CVM_CNPJ_CROSSWALK:
        ticker = item["ticker"].upper()
        instrument = fii_instruments.get(ticker)
        if not instrument:
            continue
        cvm_row = latest_by_cnpj.get(item["cnpj_fundo"])
        bridge_rows.append(
            {
                "instrument_id": instrument.instrument_id,
                "ticker": ticker,
                "label": instrument.label,
                "cnpj_fundo": item["cnpj_fundo"],
                "bridge_status": "matched_cvm_cache" if cvm_row else "mapped_waiting_cache",
                "latest_date": cvm_row.get("dt_comptc") if cvm_row else None,
                "net_worth": round(_float_value(cvm_row.get("vl_patrim_liq")), 2)
                if cvm_row
                else None,
                "quota": _float_value(cvm_row.get("vl_quota")) if cvm_row else None,
                "shareholders": int(_float_value(cvm_row.get("nr_cotst"))) if cvm_row else None,
                "source_note": item["source_note"],
            }
        )
    matched_count = sum(1 for row in bridge_rows if row["bridge_status"] == "matched_cvm_cache")
    return {
        "source_id": "cvm_fund_daily_reports",
        "status": "available" if bridge_rows else "waiting_for_mapping",
        "mapped_instrument_count": len(bridge_rows),
        "matched_cvm_cache_count": matched_count,
        "coverage_ratio": matched_count / len(bridge_rows) if bridge_rows else 0.0,
        "rows": bridge_rows,
        "methodology": (
            "Crosswalk inicial entre ticker FII do catalogo e CNPJ CVM. O vinculo vira "
            "matched_cvm_cache apenas quando o CNPJ aparece no cache local do Informe Diario."
        ),
    }


def _latest_cvm_rows_by_cnpj(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    by_cnpj: dict[str, dict[str, str]] = {}
    for row in rows:
        cnpj = row.get("cnpj_fundo")
        if not cnpj:
            continue
        current = by_cnpj.get(cnpj)
        if current is None or (row.get("dt_comptc") or "") > (current.get("dt_comptc") or ""):
            by_cnpj[cnpj] = row
    return by_cnpj


def build_cvm_fund_profile(
    *,
    cache_root: Path | str = "data/product_sources",
) -> dict[str, Any]:
    """Summarize the cached CVM daily fund reports for UI/product readiness."""

    rows = load_cached_source_rows(source_id="cvm_fund_daily_reports", cache_root=cache_root)
    if not rows:
        return {
            "source_id": "cvm_fund_daily_reports",
            "status": "waiting_for_cache",
            "row_count": 0,
            "latest_date": None,
            "total_net_worth": 0.0,
            "total_shareholders": 0,
            "net_flow": 0.0,
            "sample_largest_funds": [],
            "methodology": (
                "Execute o refresh da fonte CVM para resumir cota, patrimonio liquido, "
                "captacoes, resgates e cotistas."
            ),
        }

    latest_date = max((row.get("dt_comptc") or "" for row in rows), default="")
    latest_rows = [row for row in rows if row.get("dt_comptc") == latest_date] or rows
    total_net_worth = sum(_float_value(row.get("vl_patrim_liq")) for row in latest_rows)
    total_shareholders = sum(int(_float_value(row.get("nr_cotst"))) for row in latest_rows)
    total_subscriptions = sum(_float_value(row.get("captc_dia")) for row in latest_rows)
    total_redemptions = sum(_float_value(row.get("resg_dia")) for row in latest_rows)
    largest_rows = sorted(
        latest_rows,
        key=lambda row: _float_value(row.get("vl_patrim_liq")),
        reverse=True,
    )[:5]
    return {
        "source_id": "cvm_fund_daily_reports",
        "status": "available",
        "row_count": len(rows),
        "latest_date": latest_date or None,
        "total_net_worth": round(total_net_worth, 2),
        "total_shareholders": total_shareholders,
        "net_flow": round(total_subscriptions - total_redemptions, 2),
        "sample_largest_funds": [
            {
                "cnpj_fundo": row.get("cnpj_fundo"),
                "net_worth": round(_float_value(row.get("vl_patrim_liq")), 2),
                "quota": _float_value(row.get("vl_quota")),
                "shareholders": int(_float_value(row.get("nr_cotst"))),
            }
            for row in largest_rows
        ],
        "methodology": (
            "Resumo calculado sobre as linhas em cache do Informe Diario CVM, usando a "
            "data de competencia mais recente disponivel no arquivo local."
        ),
    }


def build_cvm_fund_rankings(
    *,
    cache_root: Path | str = "data/product_sources",
) -> list[dict[str, Any]]:
    """Build first CVM fund/class rankings from cached daily reports."""

    rows = load_cached_source_rows(source_id="cvm_fund_daily_reports", cache_root=cache_root)
    if not rows:
        return []

    latest_date = max((row.get("dt_comptc") or "" for row in rows), default="")
    latest_rows = [row for row in rows if row.get("dt_comptc") == latest_date] or rows
    ranking_specs = (
        {
            "ranking_id": "cvm_largest_net_worth",
            "label": "Maiores fundos/classes por PL",
            "metric": "vl_patrim_liq",
            "score_label": "PL",
            "reverse": True,
        },
        {
            "ranking_id": "cvm_highest_net_flow",
            "label": "Maiores fluxos líquidos",
            "metric": "net_flow",
            "score_label": "Fluxo líquido",
            "reverse": True,
        },
        {
            "ranking_id": "cvm_largest_holder_base",
            "label": "Maiores bases de cotistas",
            "metric": "nr_cotst",
            "score_label": "Cotistas",
            "reverse": True,
        },
    )
    return [
        {
            "ranking_id": spec["ranking_id"],
            "label": spec["label"],
            "source_id": "cvm_fund_daily_reports",
            "status": "available",
            "latest_date": latest_date or None,
            "methodology": (
                "Ranking calculado sobre a data de competencia mais recente do cache CVM. "
                "Ainda nao vincula CNPJ a tickers ou fundos do catalogo."
            ),
            "rows": _rank_cvm_rows(
                latest_rows,
                metric=str(spec["metric"]),
                score_label=str(spec["score_label"]),
                reverse=bool(spec["reverse"]),
            ),
        }
        for spec in ranking_specs
    ]


def _rank_cvm_rows(
    rows: list[dict[str, str]],
    *,
    metric: str,
    score_label: str,
    reverse: bool,
    limit: int = 5,
) -> list[dict[str, Any]]:
    ranked_rows = sorted(
        rows,
        key=lambda row: _cvm_metric_value(row, metric),
        reverse=reverse,
    )[:limit]
    return [
        {
            "rank": index + 1,
            "cnpj_fundo": row.get("cnpj_fundo"),
            "score": round(_cvm_metric_value(row, metric), 2),
            "score_label": score_label,
            "net_worth": round(_float_value(row.get("vl_patrim_liq")), 2),
            "quota": _float_value(row.get("vl_quota")),
            "shareholders": int(_float_value(row.get("nr_cotst"))),
            "net_flow": round(
                _float_value(row.get("captc_dia")) - _float_value(row.get("resg_dia")),
                2,
            ),
        }
        for index, row in enumerate(ranked_rows)
    ]


def _cvm_metric_value(row: dict[str, str], metric: str) -> float:
    if metric == "net_flow":
        return _float_value(row.get("captc_dia")) - _float_value(row.get("resg_dia"))
    return _float_value(row.get(metric))


def build_etf_bdr_profile(
    *,
    cache_root: Path | str = "data/product_sources",
) -> dict[str, Any]:
    """Summarize cached B3 ETF/BDR product metadata."""

    rows = load_cached_source_rows(source_id="b3_listed_products", cache_root=cache_root)
    if not rows:
        return {
            "source_id": "b3_listed_products",
            "status": "waiting_for_cache",
            "row_count": 0,
            "product_type_counts": [],
            "average_fee_pct": None,
            "sample_low_fee_products": [],
            "methodology": (
                "Execute o refresh de produtos B3 para resumir taxas, indices e exposicoes."
            ),
        }

    fee_values = [
        _float_value(row.get("taxa_administracao"))
        for row in rows
        if row.get("taxa_administracao") not in {None, ""}
    ]
    type_counts: dict[str, int] = {}
    for row in rows:
        product_type = row.get("tipo_produto") or "Nao informado"
        type_counts[product_type] = type_counts.get(product_type, 0) + 1
    low_fee_rows = sorted(
        [row for row in rows if row.get("taxa_administracao") not in {None, ""}],
        key=lambda row: _float_value(row.get("taxa_administracao")),
    )[:5]
    return {
        "source_id": "b3_listed_products",
        "status": "available",
        "row_count": len(rows),
        "product_type_counts": [
            {"product_type": product_type, "count": count}
            for product_type, count in sorted(type_counts.items())
        ],
        "average_fee_pct": round(sum(fee_values) / len(fee_values), 2) if fee_values else None,
        "sample_low_fee_products": [_etf_bdr_product_payload(row) for row in low_fee_rows],
        "methodology": (
            "Resumo calculado sobre o cache local de produtos B3. Taxas vazias indicam "
            "BDRs ou produtos sem taxa de administracao aplicavel no cache."
        ),
    }


def build_etf_bdr_rankings(
    *,
    cache_root: Path | str = "data/product_sources",
) -> list[dict[str, Any]]:
    """Build initial ETF/BDR rankings from cached listed-product metadata."""

    rows = load_cached_source_rows(source_id="b3_listed_products", cache_root=cache_root)
    fee_rows = [row for row in rows if row.get("taxa_administracao") not in {None, ""}]
    if not fee_rows:
        return []
    return [
        {
            "ranking_id": "b3_lowest_admin_fee",
            "label": "Menores taxas de administracao",
            "source_id": "b3_listed_products",
            "status": "available_seed",
            "methodology": (
                "Ranking inicial por taxa de administracao em cache. Ainda nao mede tracking "
                "error historico, spread ou liquidez de tela."
            ),
            "rows": [
                {
                    "rank": index + 1,
                    **_etf_bdr_product_payload(row),
                    "score": _float_value(row.get("taxa_administracao")),
                    "score_label": "Taxa adm. % a.a.",
                }
                for index, row in enumerate(
                    sorted(
                        fee_rows,
                        key=lambda item: _float_value(item.get("taxa_administracao")),
                    )[:5]
                )
            ],
        }
    ]


def _etf_bdr_product_payload(row: dict[str, str]) -> dict[str, Any]:
    return {
        "ticker": row.get("ticker"),
        "name": row.get("nome"),
        "product_type": row.get("tipo_produto"),
        "reference_index": row.get("indice_referencia"),
        "admin_fee_pct": (
            _float_value(row.get("taxa_administracao"))
            if row.get("taxa_administracao") not in {None, ""}
            else None
        ),
        "exposure": row.get("exposicao"),
        "tracking_note": row.get("tracking_note"),
        "data_quality_score": _float_value(row.get("data_quality_score")),
    }


def build_methodology_readiness_ranking(
    *,
    instruments: list[InvestmentInstrument],
    cache_root: Path | str = "data/product_sources",
) -> dict[str, Any]:
    """Build a consolidated readiness ranking across product-data sources."""

    instrument_by_ticker = {
        str(item.ticker).upper(): item
        for item in instruments
        if item.ticker
        and item.category_id
        in {"fiis", "etfs_brazil", "international_b3", "fixed_income_b3"}
    }
    rows = [
        *_methodology_fii_rows(
            instrument_by_ticker=instrument_by_ticker,
            cache_root=cache_root,
        ),
        *_methodology_etf_bdr_rows(
            instrument_by_ticker=instrument_by_ticker,
            cache_root=cache_root,
        ),
    ]
    ranked_rows = sorted(rows, key=lambda row: row["score"], reverse=True)
    for index, row in enumerate(ranked_rows, start=1):
        row["rank"] = index
    return {
        "ranking_id": "methodology_readiness",
        "label": "Prontidao metodologica por produto",
        "status": "available",
        "methodology": (
            "Score consolidado de prontidao: combina fonte em cache, qualidade do dado, "
            "cobertura CVM quando aplicavel, custo/renda observavel e caveat do produto. "
            "Nao e recomendacao de compra."
        ),
        "rows": ranked_rows,
    }


def _methodology_fii_rows(
    *,
    instrument_by_ticker: dict[str, InvestmentInstrument],
    cache_root: Path | str,
) -> list[dict[str, Any]]:
    fii_rows = load_cached_source_rows(source_id="b3_fii_listed", cache_root=cache_root)
    bridge = build_fii_cvm_bridge(
        instruments=list(instrument_by_ticker.values()),
        cache_root=cache_root,
    )
    bridge_by_ticker = {row["ticker"]: row for row in bridge["rows"]}
    output: list[dict[str, Any]] = []
    for row in fii_rows:
        ticker = str(row.get("ticker") or "").upper()
        instrument = instrument_by_ticker.get(ticker)
        if not instrument:
            continue
        bridge_row = bridge_by_ticker.get(ticker)
        data_quality = _float_value(row.get("data_quality_score"))
        cvm_component = (
            1.0
            if bridge_row and bridge_row["bridge_status"] == "matched_cvm_cache"
            else 0.45
        )
        yield_component = min(_float_value(row.get("yield_12m_pct")) / 12.0, 1.0)
        score = round(
            (data_quality * 45.0) + (cvm_component * 35.0) + (yield_component * 20.0),
            2,
        )
        output.append(
            {
                "rank": 0,
                "instrument_id": instrument.instrument_id,
                "ticker": ticker,
                "label": instrument.label,
                "product_family": "FII",
                "score": score,
                "score_components": {
                    "data_quality": round(data_quality, 2),
                    "cvm_bridge": round(cvm_component, 2),
                    "income_signal": round(yield_component, 2),
                },
                "source_ids": ["b3_fii_listed", "cvm_fund_daily_reports"],
                "caveat": (
                    "FII com metadados B3 e ponte CVM inicial; rendimentos ainda usam "
                    "yield aproximado em cache, nao serie mensal oficial completa."
                ),
            }
        )
    return output


def _methodology_etf_bdr_rows(
    *,
    instrument_by_ticker: dict[str, InvestmentInstrument],
    cache_root: Path | str,
) -> list[dict[str, Any]]:
    product_rows = load_cached_source_rows(source_id="b3_listed_products", cache_root=cache_root)
    output: list[dict[str, Any]] = []
    for row in product_rows:
        ticker = str(row.get("ticker") or "").upper()
        instrument = instrument_by_ticker.get(ticker)
        if not instrument:
            continue
        data_quality = _float_value(row.get("data_quality_score"))
        fee = _float_value(row.get("taxa_administracao"))
        fee_component = (
            max(0.0, min(1.0, 1.0 - (fee / 1.0)))
            if row.get("taxa_administracao")
            else 0.5
        )
        tracking_component = 0.75 if row.get("tracking_note") else 0.35
        score = round(
            (data_quality * 45.0) + (fee_component * 30.0) + (tracking_component * 25.0),
            2,
        )
        output.append(
            {
                "rank": 0,
                "instrument_id": instrument.instrument_id,
                "ticker": ticker,
                "label": instrument.label,
                "product_family": row.get("tipo_produto") or "Produto B3",
                "score": score,
                "score_components": {
                    "data_quality": round(data_quality, 2),
                    "cost_signal": round(fee_component, 2),
                    "tracking_context": round(tracking_component, 2),
                },
                "source_ids": ["b3_listed_products"],
                "caveat": (
                    "Produto listado com taxa e referencia em cache; ainda falta medir "
                    "tracking error, spread e liquidez historica."
                ),
            }
        )
    return output


def _float_value(value: Any) -> float:
    if value in {None, ""}:
        return 0.0
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return 0.0
