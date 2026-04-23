"""Optimization, walk-forward, and Monte Carlo API routes."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Query, Request, Response

from src.api.models import (
    MonteCarloRequestModel,
    OptimizationPlanRequest,
    ResearchWorkspaceCreateRequestModel,
    ResearchWorkspaceImportRequestModel,
    ResearchWorkspaceUpdateRequestModel,
    WalkForwardRequestModel,
)
from src.investing_workbench.interfaces.api.deps import get_service
from src.investing_workbench.interfaces.api.errors import to_http_exception
from src.investing_workbench.interfaces.api.services import (
    to_montecarlo_request,
    to_optimization_request,
    to_walkforward_request,
)

router = APIRouter(tags=["research"])


@router.post("/optimizations/plan")
async def plan_optimization(payload: OptimizationPlanRequest, request: Request) -> dict[str, Any]:
    """Preview a reproducible optimization trial plan."""
    try:
        optimization_request = to_optimization_request(payload)
        planner = get_service(request, "optimization_planner")
        return planner.build_plan(optimization_request).to_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/optimizations")
async def execute_optimization(
    payload: OptimizationPlanRequest, request: Request
) -> dict[str, Any]:
    """Execute and persist an optimization job."""
    try:
        optimization_request = to_optimization_request(payload)
        optimization_service = get_service(request, "optimization_service")
        return optimization_service.execute(optimization_request).results_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/experiments")
async def list_experiments(
    request: Request,
    experiment_type: str | None = Query(default=None),
    strategy_name: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1),
) -> list[dict[str, Any]]:
    """List normalized experiment records across persisted workflow types."""
    try:
        return get_service(request, "experiment_registry_service").list_experiments(
            experiment_type=experiment_type,
            strategy_name=strategy_name,
            limit=limit,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/experiments/{experiment_type}/{experiment_id}")
async def get_experiment(
    experiment_type: str, experiment_id: str, request: Request
) -> dict[str, Any]:
    """Return one normalized experiment record together with its persisted manifest."""
    try:
        return get_service(request, "experiment_registry_service").get_experiment(
            experiment_type=experiment_type,
            experiment_id=experiment_id,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/research-workspaces")
async def list_research_workspaces(request: Request) -> list[dict[str, Any]]:
    """List saved research workspaces."""
    try:
        return get_service(request, "research_workspace_service").list_workspaces()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/research-workspaces")
async def save_research_workspace(
    payload: ResearchWorkspaceCreateRequestModel,
    request: Request,
) -> dict[str, Any]:
    """Persist a curated research workspace selection."""
    try:
        return get_service(request, "research_workspace_service").save_workspace(
            name=payload.name,
            notes=payload.notes,
            selected_experiment_type=payload.selected_experiment_type,
            selected_experiment_id=payload.selected_experiment_id,
            optimization_id=payload.optimization_id,
            walkforward_id=payload.walkforward_id,
            montecarlo_id=payload.montecarlo_id,
            anchor_run_id=payload.anchor_run_id,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/research-workspaces/import")
async def import_research_workspace(
    payload: ResearchWorkspaceImportRequestModel,
    request: Request,
) -> dict[str, Any]:
    """Import a previously exported research workspace."""
    try:
        return get_service(request, "research_workspace_service").import_workspace(payload.payload)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/research-workspaces/{workspace_id}")
async def get_research_workspace(workspace_id: str, request: Request) -> dict[str, Any]:
    """Return one saved research workspace."""
    try:
        return get_service(request, "research_workspace_service").get_workspace(workspace_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.patch("/research-workspaces/{workspace_id}")
async def update_research_workspace(
    workspace_id: str,
    payload: ResearchWorkspaceUpdateRequestModel,
    request: Request,
) -> dict[str, Any]:
    """Update editable metadata for one saved research workspace."""
    try:
        return get_service(request, "research_workspace_service").update_workspace(
            workspace_id,
            name=payload.name,
            notes=payload.notes,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/research-workspaces/{workspace_id}/report", response_model=None)
async def export_research_workspace_report(
    workspace_id: str,
    request: Request,
    format: Literal["json", "markdown", "html"] = Query(default="json"),
) -> dict[str, Any] | Response:
    """Export one saved research workspace report in machine or document form."""
    try:
        workspace_service = get_service(request, "research_workspace_service")
        workspace = workspace_service.get_workspace(workspace_id)
        report = workspace_service.build_report(workspace_id)

        if format == "markdown":
            return Response(content=report["markdown"], media_type="text/markdown")
        if format == "html":
            return Response(content=report["html"], media_type="text/html")
        return {
            "workspace": workspace,
            "report": report,
        }
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/optimizations")
async def list_optimizations(request: Request) -> list[dict[str, Any]]:
    """List persisted optimization jobs."""
    try:
        return get_service(request, "optimization_service").list_optimizations()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/optimizations/{optimization_id}")
async def get_optimization_manifest(optimization_id: str, request: Request) -> dict[str, Any]:
    """Return the persisted manifest for an optimization job."""
    try:
        return get_service(request, "optimization_service").get_manifest(optimization_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/optimizations/{optimization_id}/results")
async def get_optimization_results(optimization_id: str, request: Request) -> dict[str, Any]:
    """Return the persisted ranked results for an optimization job."""
    try:
        return get_service(request, "optimization_service").get_results(optimization_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/walkforward")
async def execute_walkforward(payload: WalkForwardRequestModel, request: Request) -> dict[str, Any]:
    """Execute and persist walk-forward validation."""
    try:
        walkforward_request = to_walkforward_request(payload)
        walkforward_service = get_service(request, "walkforward_service")
        return walkforward_service.execute(walkforward_request).results_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/walkforward")
async def list_walkforward_executions(request: Request) -> list[dict[str, Any]]:
    """List persisted walk-forward validations."""
    try:
        return get_service(request, "walkforward_service").list_executions()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/walkforward/{walkforward_id}")
async def get_walkforward_manifest(walkforward_id: str, request: Request) -> dict[str, Any]:
    """Return the persisted manifest for a walk-forward validation."""
    try:
        return get_service(request, "walkforward_service").get_manifest(walkforward_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/walkforward/{walkforward_id}/results")
async def get_walkforward_results(walkforward_id: str, request: Request) -> dict[str, Any]:
    """Return the persisted results for a walk-forward validation."""
    try:
        return get_service(request, "walkforward_service").get_results(walkforward_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/montecarlo")
async def execute_montecarlo(payload: MonteCarloRequestModel, request: Request) -> dict[str, Any]:
    """Execute and persist Monte Carlo robustness analysis."""
    try:
        montecarlo_request = to_montecarlo_request(payload)
        return get_service(request, "montecarlo_service").execute(montecarlo_request).results_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/montecarlo")
async def list_montecarlo_executions(request: Request) -> list[dict[str, Any]]:
    """List persisted Monte Carlo analyses."""
    try:
        return get_service(request, "montecarlo_service").list_executions()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/montecarlo/{montecarlo_id}")
async def get_montecarlo_manifest(montecarlo_id: str, request: Request) -> dict[str, Any]:
    """Return the persisted manifest for a Monte Carlo analysis."""
    try:
        return get_service(request, "montecarlo_service").get_manifest(montecarlo_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/montecarlo/{montecarlo_id}/results")
async def get_montecarlo_results(montecarlo_id: str, request: Request) -> dict[str, Any]:
    """Return the persisted results for a Monte Carlo analysis."""
    try:
        return get_service(request, "montecarlo_service").get_results(montecarlo_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc
