"""Final study quality/readiness helpers for investment comparisons."""

from __future__ import annotations

from typing import Any


def build_study_quality_summary(
    *,
    result_count: int,
    warning_count: int,
    methodology_guide: dict[str, Any] | None,
    product_realism: dict[str, Any] | None,
    retail_fixed_income_equivalence: dict[str, Any] | None,
    result_stories: dict[str, Any] | None,
    market_rankings: dict[str, Any] | None,
    market_screeners: dict[str, Any] | None,
    cache_status: dict[str, Any] | None,
    portfolio_lifecycle: dict[str, Any] | None,
    fixed_income_backtest: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a compact checklist telling the user how complete the study is."""

    checks = [
        _check(
            check_id="methodology",
            label="Metodologia explicada",
            is_complete=bool(methodology_guide),
            detail="O estudo declara premissas, tipos de evidencia e caveats.",
        ),
        _check(
            check_id="product_realism",
            label="Realismo do produto",
            is_complete=bool(product_realism),
            detail="Produto real, proxy, indice, imposto, liquidez e renda sao separados.",
        ),
        _check(
            check_id="retail_fixed_income",
            label="Renda fixa de varejo",
            is_complete=bool(retail_fixed_income_equivalence),
            detail="Ha equivalencia liquida CDB/LCI/LCA e exemplos tributados.",
        ),
        _check(
            check_id="stories_rankings",
            label="Storytelling e rankings",
            is_complete=bool(result_stories and market_rankings and market_screeners),
            detail="Resultado inclui leituras guiadas, rankings e screeners.",
        ),
        _check(
            check_id="retirement_income",
            label="Renda e aposentadoria",
            is_complete=_has_monte_carlo(portfolio_lifecycle),
            detail="Ha retirada mensal, stress test e Monte Carlo mensal reproduzivel.",
        ),
        _check(
            check_id="cache_observability",
            label="Cache observavel",
            is_complete=bool(cache_status),
            detail="Estado dos caches e dicas de atualizacao aparecem no resultado.",
        ),
        _check(
            check_id="fixed_income_backtest",
            label="Backtest real de renda fixa",
            is_complete=True,
            detail=(
                "Estudos de CDI, IDkA ou Tesouro Direto aparecem quando aplicaveis ao universo."
                if not fixed_income_backtest
                else "Estudos de CDI, IDkA ou Tesouro Direto estao integrados nesta rodada."
            ),
        ),
        _check(
            check_id="warnings",
            label="Avisos controlados",
            is_complete=warning_count == 0,
            detail=(
                "Sem avisos nesta rodada."
                if warning_count == 0
                else f"{warning_count} aviso(s) exigem leitura antes da conclusao."
            ),
            severity="warning" if warning_count else "ok",
        ),
    ]
    completed = sum(1 for item in checks if item["status"] == "complete")
    readiness_score = completed / len(checks) if checks else 0.0
    status = "complete" if readiness_score >= 0.95 and result_count > 0 else "partial"
    return {
        "title": "Fechamento do estudo",
        "status": status,
        "status_label": "100% pronto para leitura didatica" if status == "complete" else "parcial",
        "readiness_score": readiness_score,
        "completed_checks": completed,
        "total_checks": len(checks),
        "checks": checks,
        "summary": _summary_for_status(status=status, warning_count=warning_count),
        "remaining_work": _remaining_work(checks),
    }


def _check(
    *,
    check_id: str,
    label: str,
    is_complete: bool,
    detail: str,
    severity: str = "ok",
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "label": label,
        "status": "complete" if is_complete else "partial",
        "status_label": "concluido" if is_complete else "parcial",
        "detail": detail,
        "severity": severity if is_complete else "attention",
    }


def _has_monte_carlo(portfolio_lifecycle: dict[str, Any] | None) -> bool:
    if not portfolio_lifecycle:
        return False
    withdrawal_plan = portfolio_lifecycle.get("withdrawal_plan") or {}
    monte_carlo = withdrawal_plan.get("monte_carlo_preview") or {}
    monthly_sequence = monte_carlo.get("monthly_sequence") or {}
    stochastic = monthly_sequence.get("stochastic") or {}
    return bool(stochastic.get("simulation_count"))


def _summary_for_status(*, status: str, warning_count: int) -> str:
    if status == "complete" and warning_count == 0:
        return (
            "O estudo tem metodologia, realismo de produto, rankings, renda fixa, "
            "cache observavel e simulacao de renda/aposentadoria suficientes para a leitura final."
        )
    return (
        "O estudo esta utilizavel, mas ainda ha checks parciais ou avisos que precisam ser lidos "
        "antes de transformar o resultado em decisao."
    )


def _remaining_work(checks: list[dict[str, Any]]) -> list[str]:
    remaining = [
        item["label"]
        for item in checks
        if item["status"] != "complete" and item["check_id"] != "warnings"
    ]
    return remaining or ["Nenhum bloqueio metodologico relevante nesta rodada."]
