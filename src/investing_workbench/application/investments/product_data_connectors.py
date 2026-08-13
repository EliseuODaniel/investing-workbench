"""Source readiness helpers for post-roadmap product data."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from zipfile import ZipFile

PRODUCT_DATA_SOURCE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "source_id": "b3_fii_listed",
        "label": "B3 - FIIs listados",
        "url": (
            "https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/"
            "renda-variavel/fundos-de-investimentos/fii/fiis-listados/"
        ),
        "coverage": "Lista e metadados de fundos imobiliarios listados na B3.",
        "freshness_policy": "refresh semanal ou manual quando o catalogo mudar",
        "integration_status": "connected",
        "connector_status": "connected_seeded",
        "cache_key": "b3_fii_listed",
        "families": ["fiis"],
        "expected_fields": [
            "ticker",
            "nome",
            "segmento",
            "gestor",
            "administrador",
            "status_listagem",
            "yield_12m_pct",
            "liquidity_label",
            "income_focus",
            "data_quality_score",
        ],
    },
    {
        "source_id": "cvm_fund_daily_reports",
        "label": "CVM - Informe diario de fundos",
        "url": "https://dados.cvm.gov.br/dataset/fi-doc-inf_diario",
        "coverage": "PL, cota, captacoes e resgates de fundos informados a CVM.",
        "freshness_policy": "refresh diario com tolerancia a atraso de publicacao",
        "integration_status": "connected",
        "connector_status": "connected_seeded",
        "cache_key": "cvm_fund_daily_reports",
        "families": ["funds", "fiis"],
        "expected_fields": [
            "cnpj_fundo",
            "dt_comptc",
            "vl_total",
            "vl_quota",
            "vl_patrim_liq",
            "captc_dia",
            "resg_dia",
            "nr_cotst",
        ],
    },
    {
        "source_id": "tesouro_transparente",
        "label": "Tesouro Transparente - Tesouro Direto",
        "url": (
            "https://www.tesourotransparente.gov.br/temas/divida-publica-federal/" "tesouro-direto"
        ),
        "coverage": "Precos, taxas, vendas, resgates e cupons do Tesouro Direto.",
        "freshness_policy": "refresh diario quando estudos de Tesouro forem usados",
        "integration_status": "connected",
        "connector_status": "connected",
        "cache_key": "tesouro_direto",
        "families": ["tesouro_direct_strategy", "fixed_income_b3"],
        "expected_fields": [
            "data_base",
            "titulo",
            "vencimento",
            "taxa_compra",
            "pu_compra",
            "pu_venda",
        ],
    },
    {
        "source_id": "b3_listed_products",
        "label": "B3 - Produtos listados e dados publicos",
        "url": "https://www.b3.com.br/",
        "coverage": "Negociacao, listagem, indices, ETFs, BDRs e dados publicos de mercado.",
        "freshness_policy": "refresh sob demanda com cache observavel",
        "integration_status": "partial",
        "connector_status": "partial",
        "cache_key": "b3_listed_products",
        "families": ["stocks_brazil", "etfs_brazil", "international_b3", "fiis"],
        "expected_fields": [
            "ticker",
            "nome",
            "tipo_produto",
            "indice_referencia",
            "taxa_administracao",
            "exposicao",
            "tracking_note",
            "data_quality_score",
        ],
    },
)


def build_product_data_manifest(
    *,
    cache_root: Path | str = "data/product_sources",
) -> dict[str, Any]:
    """Describe local source-cache readiness without forcing a network refresh."""

    root = Path(cache_root)
    checked_at = datetime.now(UTC)
    sources = [
        _source_manifest(source=source, root=root, checked_at=checked_at)
        for source in PRODUCT_DATA_SOURCE_DEFINITIONS
    ]
    warm_count = sum(1 for source in sources if source["file_count"] > 0)
    stale_count = sum(1 for source in sources if source["freshness_status"] in {"stale", "old"})
    return {
        "title": "Manifesto local de dados externos",
        "plain_language_summary": (
            "Mostra quais fontes de produto ja tem cache local e quais ainda sao apenas "
            "conectores especificados para o proximo refresh."
        ),
        "cache_root": str(root),
        "checked_at": checked_at.isoformat(),
        "source_count": len(sources),
        "warm_source_count": warm_count,
        "stale_source_count": stale_count,
        "sources": sources,
        "takeaways": _manifest_takeaways(sources=sources, warm_count=warm_count),
    }


class ProductDataSourceService:
    """Refresh and inspect local product-data source caches."""

    def __init__(
        self,
        *,
        cache_root: Path | str = "data/product_sources",
        collect_b3_fii_rows_func: Any = None,
        collect_cvm_fund_rows_func: Any = None,
    ) -> None:
        self.cache_root = Path(cache_root)
        self._collect_b3_fii_rows = collect_b3_fii_rows_func or _collect_b3_fii_rows
        self._collect_cvm_fund_rows = collect_cvm_fund_rows_func or _collect_cvm_fund_rows

    def list_manifest(self) -> dict[str, Any]:
        """Return the current product-source manifest."""

        return build_product_data_manifest(cache_root=self.cache_root)

    def list_refresh_history(
        self,
        *,
        source_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return the latest refresh attempts for one product-data source."""

        source = source_definition(source_id)
        return _read_refresh_history(
            self.cache_root / str(source["cache_key"]),
            limit=limit,
        )

    def refresh_source(
        self,
        *,
        source_id: str,
        force: bool = False,
    ) -> dict[str, Any]:
        """Refresh one supported source into the local product-source cache."""

        source = source_definition(source_id)
        started_at = datetime.now(UTC)
        started_perf = perf_counter()
        attempted_url = str(source["url"])
        if source["source_id"] not in {
            "b3_fii_listed",
            "cvm_fund_daily_reports",
            "b3_listed_products",
        }:
            response: dict[str, Any] = {
                "source_id": source_id,
                "status": "refresh_not_required",
                "status_label": "refresh nao requerido",
                "message": "Esta fonte e resolvida por outro conector operacional do workbench.",
                "manifest": self._existing_manifest(source),
            }
            self._append_history(
                source=source,
                response=response,
                started_at=started_at,
                duration_ms=_duration_ms(started_perf),
                attempted_url=attempted_url,
            )
            response["history"] = self.list_refresh_history(source_id=source_id)
            return response

        cache_dir = self.cache_root / str(source["cache_key"])
        manifest_path = cache_dir / "manifest.json"
        if manifest_path.exists() and not force:
            response = {
                "source_id": source_id,
                "status": "cache_hit",
                "status_label": "cache reaproveitado",
                "message": "Use force=true para recriar o cache local desta fonte.",
                "manifest": self._existing_manifest(source),
            }
            self._append_history(
                source=source,
                response=response,
                started_at=started_at,
                duration_ms=_duration_ms(started_perf),
                attempted_url=attempted_url,
            )
            response["history"] = self.list_refresh_history(source_id=source_id)
            return response

        cache_dir.mkdir(parents=True, exist_ok=True)
        if source["source_id"] == "b3_fii_listed":
            rows, collection_mode, caveat, fetch_error = self._collect_b3_fii_rows(source)
            manifest = _write_source_cache(
                cache_dir=cache_dir,
                source=source,
                rows=rows,
                file_name="fiis_listados.csv",
                schema_version="b3_fii_listed.v2",
                collection_mode=collection_mode,
                fetch_error=fetch_error,
                caveat=caveat,
            )
        elif source["source_id"] == "cvm_fund_daily_reports":
            rows, collection_mode, caveat, fetch_error = self._collect_cvm_fund_rows(source)
            manifest = _write_source_cache(
                cache_dir=cache_dir,
                source=source,
                rows=rows,
                file_name="informe_diario_seed.csv",
                schema_version="cvm_fund_daily_reports.v1",
                collection_mode=collection_mode,
                fetch_error=fetch_error,
                caveat=caveat,
            )
        else:
            rows, collection_mode, caveat, fetch_error = _collect_b3_listed_product_rows(source)
            manifest = _write_source_cache(
                cache_dir=cache_dir,
                source=source,
                rows=rows,
                file_name="produtos_listados.csv",
                schema_version="b3_listed_products.v1",
                collection_mode=collection_mode,
                fetch_error=fetch_error,
                caveat=caveat,
            )
        response = {
            "source_id": source_id,
            "status": "refreshed",
            "status_label": "cache atualizado",
            "message": "Cache local de dados de produto criado com manifesto persistido.",
            "manifest": manifest,
        }
        self._append_history(
            source=source,
            response=response,
            started_at=started_at,
            duration_ms=_duration_ms(started_perf),
            attempted_url=attempted_url,
        )
        response["history"] = self.list_refresh_history(source_id=source_id)
        return response

    def _existing_manifest(self, source: dict[str, Any]) -> dict[str, Any] | None:
        manifest_path = self.cache_root / str(source["cache_key"]) / "manifest.json"
        if not manifest_path.exists():
            return None
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def _append_history(
        self,
        *,
        source: dict[str, Any],
        response: dict[str, Any],
        started_at: datetime,
        duration_ms: int,
        attempted_url: str,
    ) -> None:
        cache_dir = self.cache_root / str(source["cache_key"])
        cache_dir.mkdir(parents=True, exist_ok=True)
        finished_at = datetime.now(UTC)
        manifest_value = response.get("manifest")
        manifest: dict[str, Any] = manifest_value if isinstance(manifest_value, dict) else {}
        history_row = {
            "ran_at": finished_at.isoformat(),
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_ms": duration_ms,
            "source_attempted_url": attempted_url,
            "source_id": response["source_id"],
            "status": response["status"],
            "status_label": response["status_label"],
            "message": response["message"],
            "row_count": manifest.get("row_count"),
            "schema_version": manifest.get("schema_version"),
            "checksum_sha256": manifest.get("checksum_sha256"),
            "collection_mode": manifest.get("collection_mode"),
            "fetch_error": manifest.get("fetch_error"),
        }
        with (cache_dir / "refresh_history.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(history_row, ensure_ascii=True) + "\n")


def source_definition(source_id: str) -> dict[str, Any]:
    """Return the source definition for a source id."""

    for source in PRODUCT_DATA_SOURCE_DEFINITIONS:
        if source["source_id"] == source_id:
            return source
    raise ValueError(f"Fonte de dados de produto desconhecida: {source_id}")


def load_cached_source_rows(
    *,
    source_id: str,
    cache_root: Path | str = "data/product_sources",
) -> list[dict[str, str]]:
    """Load cached CSV rows for a supported product-data source."""

    source = source_definition(source_id)
    manifest_path = Path(cache_root) / str(source["cache_key"]) / "manifest.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    file_name = str(manifest.get("file_name") or "")
    if not file_name:
        return []
    data_path = manifest_path.parent / file_name
    if not data_path.exists():
        return []
    with data_path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_release_packages() -> list[dict[str, Any]]:
    """Return the product-data release packages that implement the next plan."""

    return [
        {
            "release_id": "fii_income_data",
            "label": "FIIs: segmentos, rendimentos e liquidez",
            "source_ids": ["b3_fii_listed", "cvm_fund_daily_reports"],
            "user_value": "Separar renda mensal, segmento, liquidez e qualidade do dado por FII.",
            "screeners_enabled": ["renda_recorrente_fii", "liquidez_fii"],
            "ranking_candidates": ["yield_12m", "vacancia_proxy", "liquidez_media"],
            "status": "available_seed",
        },
        {
            "release_id": "fund_cvm_profile",
            "label": "Fundos/CVM: cota, PL e fluxo",
            "source_ids": ["cvm_fund_daily_reports"],
            "user_value": "Comparar fundos por serie de cota, tamanho, captacao e resgate.",
            "screeners_enabled": ["pl_minimo", "fluxo_liquido"],
            "ranking_candidates": ["retorno_cota", "crescimento_pl", "resgate_relativo"],
            "status": "available",
        },
        {
            "release_id": "treasury_cashflow_data",
            "label": "Tesouro: cupons, vendas, resgates e liquidez",
            "source_ids": ["tesouro_transparente"],
            "user_value": "Aprofundar renda fixa real com fluxo de caixa e marcação a mercado.",
            "screeners_enabled": ["duration_tesouro", "cupom_semestral"],
            "ranking_candidates": ["taxa_real", "stress_duration", "liquidez_tesouro"],
            "status": "available",
        },
        {
            "release_id": "etf_bdr_fee_tracking",
            "label": "ETFs/BDRs: custo, tracking e exposicao",
            "source_ids": ["b3_listed_products"],
            "user_value": "Mostrar diferenca entre indice teorico, produto investivel e custo.",
            "screeners_enabled": ["custo_etf", "exposicao_exterior_b3"],
            "ranking_candidates": ["taxa_administracao", "tracking_gap", "volume_medio"],
            "status": "available_seed",
        },
    ]


def build_market_filter_backlog() -> list[dict[str, Any]]:
    """Describe the filters that should become active as source fields arrive."""

    return [
        {
            "filter_id": "income_policy",
            "label": "Renda distribuida",
            "families": ["fiis", "stocks_brazil", "etfs_brazil"],
            "status": "partially_modeled",
        },
        {
            "filter_id": "liquidity",
            "label": "Liquidez negociada",
            "families": ["fiis", "etfs_brazil", "stocks_brazil", "international_b3"],
            "status": "needs_external_data",
        },
        {
            "filter_id": "fee_model",
            "label": "Taxa/custo do produto",
            "families": ["etfs_brazil", "funds"],
            "status": "needs_external_data",
        },
        {
            "filter_id": "tax_treatment",
            "label": "Tratamento tributario",
            "families": ["fixed_income_b3", "fiis", "stocks_brazil", "etfs_brazil"],
            "status": "modeled",
        },
        {
            "filter_id": "investability",
            "label": "Indice, proxy ou produto investivel",
            "families": ["fixed_income_b3", "macro_proxies", "etfs_brazil"],
            "status": "available",
        },
    ]


def build_product_data_validation_plan() -> list[dict[str, Any]]:
    """Return validation gates for each post-roadmap data stage."""

    return [
        {
            "gate_id": "source_contract",
            "label": "Contrato da fonte",
            "checks": [
                "URL oficial registrada",
                "campos esperados versionados",
                "familias de produto declaradas",
            ],
        },
        {
            "gate_id": "cache_manifest",
            "label": "Cache e manifesto",
            "checks": [
                "timestamp de coleta",
                "quantidade de arquivos/linhas",
                "idade do cache",
                "fallback quando fonte externa falha",
            ],
        },
        {
            "gate_id": "methodology_caveat",
            "label": "Caveat metodologico",
            "checks": [
                "produto investivel versus indice/proxy",
                "IR/IOF/taxas quando aplicavel",
                "liquidez e prazo visiveis",
            ],
        },
        {
            "gate_id": "ux_contract",
            "label": "Contrato de UI",
            "checks": [
                "tipo TypeScript atualizado",
                "painel didatico renderizado",
                "teste frontend focado",
            ],
        },
    ]


def _source_manifest(
    *,
    source: dict[str, Any],
    root: Path,
    checked_at: datetime,
) -> dict[str, Any]:
    cache_dir = root / str(source["cache_key"])
    files = _source_files(cache_dir)
    persisted_manifest = _read_persisted_manifest(cache_dir)
    latest_file = max(files, key=lambda item: item.stat().st_mtime, default=None)
    latest_at_dt = (
        datetime.fromtimestamp(latest_file.stat().st_mtime, tz=UTC) if latest_file else None
    )
    age_days = (checked_at - latest_at_dt).days if latest_at_dt else None
    freshness_status, freshness_label = _freshness(age_days)
    return {
        "source_id": source["source_id"],
        "cache_key": source["cache_key"],
        "cache_dir": str(cache_dir),
        "exists": cache_dir.exists(),
        "file_count": len(files),
        "total_size_bytes": sum(item.stat().st_size for item in files),
        "latest_file_name": latest_file.name if latest_file else None,
        "latest_file_at": latest_at_dt.isoformat() if latest_at_dt else None,
        "age_days": age_days,
        "freshness_status": freshness_status,
        "freshness_label": freshness_label,
        "connector_status": source["connector_status"],
        "expected_fields": list(source["expected_fields"]),
        "row_count": persisted_manifest.get("row_count") if persisted_manifest else None,
        "schema_version": persisted_manifest.get("schema_version") if persisted_manifest else None,
        "source_url": persisted_manifest.get("source_url") if persisted_manifest else source["url"],
        "checksum_sha256": (
            persisted_manifest.get("checksum_sha256") if persisted_manifest else None
        ),
        "collection_mode": (
            persisted_manifest.get("collection_mode") if persisted_manifest else None
        ),
        "refresh_history": _read_refresh_history(cache_dir),
    }


def _source_files(cache_dir: Path) -> list[Path]:
    if not cache_dir.exists():
        return []
    patterns = ("*.csv", "*.parquet", "*.json", "*.jsonl", "*.zip")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(item for item in cache_dir.glob(pattern) if item.is_file())
    return sorted(set(files))


def _read_persisted_manifest(cache_dir: Path) -> dict[str, Any] | None:
    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _read_refresh_history(cache_dir: Path, *, limit: int = 5) -> list[dict[str, Any]]:
    history_path = cache_dir / "refresh_history.jsonl"
    if not history_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return list(reversed(rows[-limit:]))


def _freshness(age_days: int | None) -> tuple[str, str]:
    if age_days is None:
        return "empty", "sem cache local"
    if age_days <= 7:
        return "fresh", "atualizado recentemente"
    if age_days <= 45:
        return "stale", "pode precisar atualizar"
    return "old", "provavelmente defasado"


def _manifest_takeaways(
    *,
    sources: list[dict[str, Any]],
    warm_count: int,
) -> list[str]:
    if warm_count == 0:
        return [
            "Nenhuma fonte nova de produto tem cache local dedicado ainda.",
            "A tela ja mostra os conectores especificados para guiar a proxima coleta.",
        ]
    stale_count = sum(1 for source in sources if source["freshness_status"] in {"stale", "old"})
    if stale_count:
        return [
            f"{warm_count} fonte(s) ja tem cache local dedicado.",
            f"{stale_count} fonte(s) podem precisar de refresh antes de rankings vivos.",
        ]
    return [
        f"{warm_count} fonte(s) ja tem cache local dedicado.",
        "Fontes com cache fresco podem ser promovidas para filtros e rankings depois dos testes.",
    ]


def _rows_to_csv_bytes(*, rows: list[dict[str, str]], fieldnames: list[str]) -> bytes:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _duration_ms(started_perf: float) -> int:
    return max(0, int((perf_counter() - started_perf) * 1000))


def _write_source_cache(
    *,
    cache_dir: Path,
    source: dict[str, Any],
    rows: list[dict[str, str]],
    file_name: str,
    schema_version: str,
    collection_mode: str,
    fetch_error: str | None,
    caveat: str,
) -> dict[str, Any]:
    data_path = cache_dir / file_name
    csv_bytes = _rows_to_csv_bytes(rows=rows, fieldnames=list(source["expected_fields"]))
    data_path.write_bytes(csv_bytes)
    checksum = hashlib.sha256(csv_bytes).hexdigest()
    manifest = {
        "source_id": source["source_id"],
        "source_url": source["url"],
        "schema_version": schema_version,
        "collected_at": datetime.now(UTC).isoformat(),
        "row_count": len(rows),
        "file_name": data_path.name,
        "checksum_sha256": checksum,
        "fields": list(source["expected_fields"]),
        "collection_mode": collection_mode,
        "fetch_error": fetch_error,
        "caveat": caveat,
    }
    (cache_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return manifest


def _collect_b3_fii_rows(
    source: dict[str, Any],
) -> tuple[list[dict[str, str]], str, str, str | None]:
    fetch_error: str | None
    try:
        rows = _fetch_b3_fii_rows(source)
    except Exception as exc:  # pragma: no cover - network shape changes often
        rows = []
        fetch_error = str(exc)
    else:
        fetch_error = None

    if rows:
        return (
            rows,
            "official_html",
            (
                "Coleta automatica extraida da pagina oficial B3. Campos nao publicados "
                "na pagina sao mantidos como nao informado."
            ),
            fetch_error,
        )

    return (
        _b3_fii_seed_rows(),
        "curated_seed_fallback",
        (
            "Fallback local curado usado porque a coleta automatica da pagina oficial "
            "nao retornou tabela confiavel nesta execucao."
        ),
        fetch_error or "pagina oficial sem tabela estruturada detectavel",
    )


def _fetch_b3_fii_rows(source: dict[str, Any]) -> list[dict[str, str]]:
    import requests

    response = requests.get(
        str(source["url"]),
        timeout=20,
        headers={"User-Agent": "InvestingWorkbench/1.0"},
    )
    response.raise_for_status()
    html = response.text
    return parse_b3_fii_rows_from_text(html)


def parse_b3_fii_rows_from_text(text: str) -> list[dict[str, str]]:
    """Extract FII rows from B3 HTML/JSON-like content."""

    tickers = sorted(set(re.findall(r"\b[A-Z]{4}11\b", text)))
    return [
        {
            "ticker": ticker,
            "nome": ticker,
            "segmento": "Nao informado",
            "gestor": "Nao informado",
            "administrador": "Nao informado",
            "status_listagem": "Listado",
            "yield_12m_pct": "",
            "liquidity_label": "Nao informado",
            "income_focus": "Nao informado",
            "data_quality_score": "0.45",
        }
        for ticker in tickers
    ]


def _collect_cvm_fund_rows(
    source: dict[str, Any],
) -> tuple[list[dict[str, str]], str, str, str | None]:
    fetch_error: str | None
    try:
        rows = _fetch_cvm_fund_rows()
    except Exception as exc:  # pragma: no cover - external dataset can move or lag
        rows = []
        fetch_error = str(exc)
    else:
        fetch_error = None

    if rows:
        return (
            rows,
            "official_zip",
            (
                "Coleta automatica do ZIP mensal de Informe Diario da CVM. "
                "O cache local guarda uma amostra recente para validar contrato, PL, cota e fluxos."
            ),
            fetch_error,
        )

    del source
    return (
        _cvm_fund_seed_rows(),
        "curated_seed_fallback",
        (
            "Semente local para validar manifesto e contrato do Informe Diario quando "
            "o ZIP oficial ainda nao esta disponivel ou falha nesta execucao."
        ),
        fetch_error or "nenhum arquivo CVM estruturado retornou linhas",
    )


def _fetch_cvm_fund_rows() -> list[dict[str, str]]:
    import requests

    errors: list[str] = []
    for url in _cvm_monthly_zip_candidates():
        try:
            response = requests.get(
                url,
                timeout=25,
                headers={"User-Agent": "InvestingWorkbench/1.0"},
            )
            response.raise_for_status()
            rows = parse_cvm_daily_report_zip_bytes(response.content)
        except Exception as exc:  # pragma: no cover - exercised through parser tests
            errors.append(f"{url}: {exc}")
            continue
        if rows:
            return rows
    raise RuntimeError("; ".join(errors) or "nenhum candidato de ZIP CVM tentou download")


def _cvm_monthly_zip_candidates(reference: datetime | None = None) -> list[str]:
    now = reference or datetime.now(UTC)
    year = now.year
    month = now.month
    previous_year = year if month > 1 else year - 1
    previous_month = month - 1 if month > 1 else 12
    periods = [(year, month), (previous_year, previous_month)]
    return [
        (
            "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/"
            f"inf_diario_fi_{period_year}{period_month:02d}.zip"
        )
        for period_year, period_month in periods
    ]


def parse_cvm_daily_report_zip_bytes(
    content: bytes,
    *,
    row_limit: int = 500,
) -> list[dict[str, str]]:
    """Parse a CVM monthly Informe Diario ZIP into normalized rows."""

    with ZipFile(io.BytesIO(content)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            return []
        raw = archive.read(csv_names[0])
    text = raw.decode("latin1")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    rows: list[dict[str, str]] = []
    for raw_row in reader:
        normalized = _normalize_cvm_daily_report_row(raw_row)
        if normalized:
            rows.append(normalized)
        if len(rows) >= row_limit:
            break
    return rows


def _normalize_cvm_daily_report_row(row: dict[str, str]) -> dict[str, str]:
    normalized = {
        "cnpj_fundo": (
            row.get("CNPJ_FUNDO") or row.get("CNPJ_FUNDO_CLASSE") or row.get("cnpj_fundo") or ""
        ),
        "dt_comptc": row.get("DT_COMPTC") or row.get("dt_comptc") or "",
        "vl_total": row.get("VL_TOTAL") or row.get("vl_total") or "",
        "vl_quota": row.get("VL_QUOTA") or row.get("vl_quota") or "",
        "vl_patrim_liq": row.get("VL_PATRIM_LIQ") or row.get("vl_patrim_liq") or "",
        "captc_dia": row.get("CAPTC_DIA") or row.get("captc_dia") or "",
        "resg_dia": row.get("RESG_DIA") or row.get("resg_dia") or "",
        "nr_cotst": row.get("NR_COTST") or row.get("nr_cotst") or "",
    }
    if not normalized["cnpj_fundo"] or not normalized["dt_comptc"]:
        return {}
    return normalized


def _cvm_fund_seed_rows() -> list[dict[str, str]]:
    return [
        {
            "cnpj_fundo": "00.000.000/0001-91",
            "dt_comptc": "2026-05-04",
            "vl_total": "100000000.00",
            "vl_quota": "100.000000",
            "vl_patrim_liq": "99000000.00",
            "captc_dia": "0.00",
            "resg_dia": "0.00",
            "nr_cotst": "1000",
        },
        {
            "cnpj_fundo": "00.000.000/0002-72",
            "dt_comptc": "2026-05-04",
            "vl_total": "250000000.00",
            "vl_quota": "125.000000",
            "vl_patrim_liq": "248500000.00",
            "captc_dia": "150000.00",
            "resg_dia": "25000.00",
            "nr_cotst": "2500",
        },
    ]


def _collect_b3_listed_product_rows(
    source: dict[str, Any],
) -> tuple[list[dict[str, str]], str, str, str | None]:
    del source
    return (
        _b3_listed_product_seed_rows(),
        "curated_seed",
        (
            "Semente local curada para operacionalizar taxa, indice de referencia e "
            "exposicao de ETFs/BDRs enquanto a coleta estruturada B3 e preparada."
        ),
        None,
    )


def _b3_listed_product_seed_rows() -> list[dict[str, str]]:
    return [
        {
            "ticker": "BOVA11",
            "nome": "iShares Ibovespa Fundo de Indice",
            "tipo_produto": "ETF Brasil",
            "indice_referencia": "Ibovespa",
            "taxa_administracao": "0.30",
            "exposicao": "Bolsa Brasil",
            "tracking_note": "Produto investivel que busca replicar indice amplo local.",
            "data_quality_score": "0.78",
        },
        {
            "ticker": "IVVB11",
            "nome": "iShares S&P 500 Fundo de Investimento em Cotas",
            "tipo_produto": "ETF internacional",
            "indice_referencia": "S&P 500",
            "taxa_administracao": "0.23",
            "exposicao": "Exterior em reais",
            "tracking_note": "Exposicao global em reais, sujeita a cambio e tracking do veiculo.",
            "data_quality_score": "0.80",
        },
        {
            "ticker": "IMAB11",
            "nome": "It Now IMA-B Fundo de Indice",
            "tipo_produto": "ETF renda fixa",
            "indice_referencia": "IMA-B",
            "taxa_administracao": "0.25",
            "exposicao": "NTN-B ampla",
            "tracking_note": "Produto investivel que aproxima indice de titulos IPCA+.",
            "data_quality_score": "0.76",
        },
        {
            "ticker": "IMBB11",
            "nome": "Bradesco IMA-B Fundo de Indice",
            "tipo_produto": "ETF renda fixa",
            "indice_referencia": "IMA-B",
            "taxa_administracao": "0.20",
            "exposicao": "NTN-B ampla",
            "tracking_note": "Produto investivel de renda fixa com taxa e tracking proprios.",
            "data_quality_score": "0.74",
        },
        {
            "ticker": "B5P211",
            "nome": "It Now B5P2 Fundo de Indice",
            "tipo_produto": "ETF renda fixa",
            "indice_referencia": "IMA-B 5 P2",
            "taxa_administracao": "0.20",
            "exposicao": "NTN-B curta",
            "tracking_note": "ETF de duration mais curta que o IMA-B amplo.",
            "data_quality_score": "0.74",
        },
        {
            "ticker": "B5MB11",
            "nome": "Bradesco IMA-B 5+ Fundo de Indice",
            "tipo_produto": "ETF renda fixa",
            "indice_referencia": "IMA-B 5+",
            "taxa_administracao": "0.20",
            "exposicao": "NTN-B longa",
            "tracking_note": "ETF de duration mais longa, mais sensivel a juros reais.",
            "data_quality_score": "0.72",
        },
        {
            "ticker": "AAPL34",
            "nome": "BDR Apple",
            "tipo_produto": "BDR",
            "indice_referencia": "Apple Inc.",
            "taxa_administracao": "",
            "exposicao": "Acao global via B3",
            "tracking_note": "BDR representa ativo externo; nao e indice nem fundo.",
            "data_quality_score": "0.66",
        },
        {
            "ticker": "TSLA34",
            "nome": "BDR Tesla",
            "tipo_produto": "BDR",
            "indice_referencia": "Tesla Inc.",
            "taxa_administracao": "",
            "exposicao": "Acao global via B3",
            "tracking_note": "BDR representa ativo externo; volatilidade e cambio importam.",
            "data_quality_score": "0.64",
        },
    ]


def _b3_fii_seed_rows() -> list[dict[str, str]]:
    return [
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
            "ticker": "KNRI11",
            "nome": "Kinea Renda Imobiliaria",
            "segmento": "Hibrido",
            "gestor": "Kinea Investimentos",
            "administrador": "Intrag DTVM",
            "status_listagem": "Listado",
            "yield_12m_pct": "8.0",
            "liquidity_label": "Alta",
            "income_focus": "Renda diversificada",
            "data_quality_score": "0.80",
        },
        {
            "ticker": "XPLG11",
            "nome": "XP Log",
            "segmento": "Logistica",
            "gestor": "XP Vista Asset",
            "administrador": "BTG Pactual",
            "status_listagem": "Listado",
            "yield_12m_pct": "8.7",
            "liquidity_label": "Media",
            "income_focus": "Renda e tijolo",
            "data_quality_score": "0.76",
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
    ]
