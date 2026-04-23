"""Portfolio allocation API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models import (
    AllocationPlanRequestModel,
    AllocationPlanResponseModel,
    AllocationWorkspaceCreateRequestModel,
    AllocationWorkspaceImportRequestModel,
    AllocationWorkspaceModel,
    AllocationWorkspaceUpdateRequestModel,
)
from src.investing_workbench.domain.allocations import RebalancePlanRequest
from src.investing_workbench.interfaces.api.deps import get_service
from src.investing_workbench.interfaces.api.errors import to_http_exception

router = APIRouter(prefix="/allocations", tags=["allocations"])


@router.post("/rebalance-plan", response_model=AllocationPlanResponseModel)
async def build_rebalance_plan(
    payload: AllocationPlanRequestModel,
    request: Request,
) -> AllocationPlanResponseModel:
    """Build a rebalance plan from current holdings and target weights."""
    try:
        plan = get_service(request, "allocation_service").build_plan(
            RebalancePlanRequest.from_dict(payload.model_dump())
        )
        return AllocationPlanResponseModel.model_validate(plan.to_dict())
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/workspaces", response_model=list[AllocationWorkspaceModel])
async def list_allocation_workspaces(request: Request) -> list[AllocationWorkspaceModel]:
    """List saved allocation workspaces."""
    try:
        return [
            AllocationWorkspaceModel.model_validate(workspace)
            for workspace in get_service(request, "allocation_workspace_service").list_workspaces()
        ]
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/workspaces", response_model=AllocationWorkspaceModel)
async def save_allocation_workspace(
    payload: AllocationWorkspaceCreateRequestModel,
    request: Request,
) -> AllocationWorkspaceModel:
    """Persist a rebalance planning request together with its computed plan."""
    try:
        workspace = get_service(request, "allocation_workspace_service").save_workspace(
            request_payload=payload.request.model_dump(),
            name=payload.name,
            notes=payload.notes,
        )
        return AllocationWorkspaceModel.model_validate(workspace)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/workspaces/import", response_model=AllocationWorkspaceModel)
async def import_allocation_workspace(
    payload: AllocationWorkspaceImportRequestModel,
    request: Request,
) -> AllocationWorkspaceModel:
    """Import a previously exported allocation workspace."""
    try:
        workspace = get_service(request, "allocation_workspace_service").import_workspace(
            payload.payload
        )
        return AllocationWorkspaceModel.model_validate(workspace)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/workspaces/{workspace_id}", response_model=AllocationWorkspaceModel)
async def get_allocation_workspace(workspace_id: str, request: Request) -> AllocationWorkspaceModel:
    """Return one saved allocation workspace."""
    try:
        workspace = get_service(request, "allocation_workspace_service").get_workspace(workspace_id)
        return AllocationWorkspaceModel.model_validate(workspace)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.patch("/workspaces/{workspace_id}", response_model=AllocationWorkspaceModel)
async def update_allocation_workspace(
    workspace_id: str,
    payload: AllocationWorkspaceUpdateRequestModel,
    request: Request,
) -> AllocationWorkspaceModel:
    """Update editable metadata for one saved allocation workspace."""
    try:
        workspace = get_service(request, "allocation_workspace_service").update_workspace(
            workspace_id,
            name=payload.name,
            notes=payload.notes,
        )
        return AllocationWorkspaceModel.model_validate(workspace)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_allocation_workspace(workspace_id: str, request: Request) -> None:
    """Delete one saved allocation workspace."""
    try:
        get_service(request, "allocation_workspace_service").delete_workspace(workspace_id)
        return None
    except Exception as exc:
        raise to_http_exception(exc) from exc
