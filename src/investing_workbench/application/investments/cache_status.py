"""Cache observability helpers for the investments workspace."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_FRESH_DAYS = 7
_STALE_DAYS = 45


def build_investment_cache_status(
    *,
    data_dir: Path,
    fixed_income_dir: Path,
    tesouro_direto_dir: Path,
    fixed_income_backtest: dict[str, Any] | None,
) -> dict[str, Any]:
    """Describe local cache readiness for investment comparisons."""

    checked_at = datetime.now(UTC)
    caches = [
        _directory_cache(
            cache_id="listed_assets",
            label="Ativos listados e ETFs/FIIs/BDRs",
            path=data_dir,
            patterns=("*.parquet", "*.csv"),
            checked_at=checked_at,
            cold_start_note=(
                "Ativos listados podem baixar series historicas quando ainda nao ha arquivo local."
            ),
            refresh_hint=(
                "Atualize quando for comparar janelas muito recentes, ETFs/FIIs novos ou "
                "ativos que acabaram de entrar no catalogo."
            ),
        ),
        _directory_cache(
            cache_id="fixed_income_indexes",
            label="Indices de renda fixa",
            path=fixed_income_dir,
            patterns=("*.parquet", "*.csv"),
            checked_at=checked_at,
            cold_start_note=(
                "Estudos IDkA/CDI podem preparar cotacoes antes de calcular janelas moveis."
            ),
            refresh_hint=(
                "Atualize antes de estudos de renda fixa recentes ou quando janelas rolling "
                "ficarem divergentes de fontes oficiais."
            ),
        ),
        _directory_cache(
            cache_id="tesouro_direto",
            label="Tesouro Direto",
            path=tesouro_direto_dir,
            patterns=("*.parquet", "*.csv"),
            checked_at=checked_at,
            cold_start_note=(
                "Tesouro Direto pode carregar o historico oficial de precos e taxas "
                "no primeiro uso."
            ),
            refresh_hint=(
                "Atualize quando a comparacao depender de precos/taxas recentes do Tesouro "
                "ou quando houver vencimentos novos."
            ),
        ),
    ]
    used_cache_ids = _used_cache_ids(fixed_income_backtest)
    for item in caches:
        item["used_in_current_result"] = item["cache_id"] in used_cache_ids

    missing_current = [
        item["label"]
        for item in caches
        if item["used_in_current_result"] and item["file_count"] == 0
    ]
    status = "warm" if not missing_current else "cold_start_possible"

    return {
        "title": "Cache e preparacao dos dados",
        "plain_language_summary": (
            "Este bloco mostra se os dados historicos usados pela comparacao ja parecem "
            "preparados localmente ou se uma proxima rodada pode exigir download/processamento."
        ),
        "status": status,
        "status_label": "cache preparado" if status == "warm" else "cold start possivel",
        "checked_at": checked_at,
        "caches": caches,
        "takeaways": _cache_takeaways(caches, missing_current),
    }


def _directory_cache(
    *,
    cache_id: str,
    label: str,
    path: Path,
    patterns: tuple[str, ...],
    checked_at: datetime,
    cold_start_note: str,
    refresh_hint: str,
) -> dict[str, Any]:
    files = _matching_files(path, patterns)
    latest_file = max(files, key=lambda item: item.stat().st_mtime, default=None)
    latest_at_dt = (
        datetime.fromtimestamp(latest_file.stat().st_mtime, tz=UTC) if latest_file else None
    )
    latest_at = latest_at_dt.isoformat() if latest_at_dt else None
    age_days = (checked_at - latest_at_dt).days if latest_at_dt else None
    freshness_status, freshness_label = _freshness(age_days)
    total_bytes = sum(item.stat().st_size for item in files)
    return {
        "cache_id": cache_id,
        "label": label,
        "path": str(path),
        "patterns": list(patterns),
        "exists": path.exists(),
        "file_count": len(files),
        "total_size_bytes": total_bytes,
        "latest_file_name": latest_file.name if latest_file else None,
        "latest_file_at": latest_at,
        "age_days": age_days,
        "freshness_status": freshness_status,
        "freshness_label": freshness_label,
        "status": "warm" if files else "empty",
        "status_label": "com arquivos locais" if files else "sem arquivos locais",
        "cold_start_note": cold_start_note,
        "refresh_hint": refresh_hint,
    }


def _matching_files(path: Path, patterns: tuple[str, ...]) -> list[Path]:
    if not path.exists():
        return []
    files: list[Path] = []
    for pattern in patterns:
        files.extend(item for item in path.glob(pattern) if item.is_file())
    return sorted(set(files))


def _used_cache_ids(fixed_income_backtest: dict[str, Any] | None) -> set[str]:
    used = {"listed_assets"}
    if fixed_income_backtest is None:
        return used
    study_ids = {
        str(item.get("study_id"))
        for item in fixed_income_backtest.get("studies", [])
        if isinstance(item, dict)
    }
    if "index_duration" in study_ids:
        used.add("fixed_income_indexes")
    if "retail_treasury" in study_ids:
        used.update({"fixed_income_indexes", "tesouro_direto"})
    return used


def _freshness(age_days: int | None) -> tuple[str, str]:
    if age_days is None:
        return "empty", "sem historico local"
    if age_days <= _FRESH_DAYS:
        return "fresh", "atualizado recentemente"
    if age_days <= _STALE_DAYS:
        return "stale", "pode precisar atualizar"
    return "old", "provavelmente defasado"


def _cache_takeaways(
    caches: list[dict[str, Any]],
    missing_current: list[str],
) -> list[str]:
    if missing_current:
        return [
            (
                "A comparacao atual usa dados que podem exigir preparacao local: "
                + ", ".join(missing_current)
                + "."
            ),
            "Depois do primeiro preparo, as proximas rodadas tendem a ficar mais rapidas.",
        ]
    warm_count = sum(1 for item in caches if item["file_count"] > 0)
    stale_count = sum(1 for item in caches if item["freshness_status"] in {"stale", "old"})
    if stale_count:
        return [
            f"{warm_count} de {len(caches)} grupos de cache ja tem arquivos locais.",
            (
                f"{stale_count} grupo(s) tem arquivos que podem merecer atualizacao "
                "antes de estudos recentes."
            ),
        ]
    return [
        f"{warm_count} de {len(caches)} grupos de cache ja tem arquivos locais.",
        "Caches locais reduzem cold start, mas ainda podem precisar de atualizacao futura.",
    ]
