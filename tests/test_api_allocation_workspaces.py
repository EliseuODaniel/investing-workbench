"""Tests for allocation workspace API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.investing_workbench.application.allocation_workspaces import AllocationWorkspaceService
from src.investing_workbench.infrastructure.persistence import LocalAllocationWorkspacesRepository
from tests.support import override_api_services

client = TestClient(app)

REQUEST_PAYLOAD = {
    "cash": 2000.0,
    "holdings": [
        {"asset": "BTC-BRL", "quantity": 0.05},
        {"asset": "ETH-USD", "quantity": 2.0},
    ],
    "prices": {
        "BTC-BRL": 60000.0,
        "ETH-USD": 2000.0,
        "SPY": 900.0,
    },
    "targets": [
        {"asset": "BTC-BRL", "target_weight": 0.5},
        {"asset": "ETH-USD", "target_weight": 0.2},
        {"asset": "SPY", "target_weight": 0.1},
    ],
    "reserve_cash": 500.0,
    "weight_tolerance": 0.02,
    "min_trade_notional": 250.0,
}


def test_save_and_list_allocation_workspaces(tmp_path):
    repository = LocalAllocationWorkspacesRepository(base_dir=tmp_path / "allocation_workspaces")
    service = AllocationWorkspaceService(repository=repository)

    with override_api_services(allocation_workspace_service=service):
        save_response = client.post(
            "/allocations/workspaces",
            json={
                "name": "Balanced portfolio",
                "notes": "Monthly rebalance draft",
                "request": REQUEST_PAYLOAD,
            },
        )
        workspace_id = save_response.json()["workspace_id"]
        list_response = client.get("/allocations/workspaces")
        detail_response = client.get(f"/allocations/workspaces/{workspace_id}")

    assert save_response.status_code == 200
    assert save_response.json()["name"] == "Balanced portfolio"
    assert save_response.json()["summary"]["asset_count"] == 3
    assert list_response.status_code == 200
    assert list_response.json()[0]["workspace_id"] == workspace_id
    assert detail_response.status_code == 200
    assert detail_response.json()["plan"]["needs_rebalance"] is True


def test_update_and_import_allocation_workspaces(tmp_path):
    repository = LocalAllocationWorkspacesRepository(base_dir=tmp_path / "allocation_workspaces")
    service = AllocationWorkspaceService(repository=repository)

    with override_api_services(allocation_workspace_service=service):
        save_response = client.post(
            "/allocations/workspaces",
            json={
                "name": "Editable portfolio",
                "request": REQUEST_PAYLOAD,
            },
        )
        workspace = save_response.json()
        workspace_id = workspace["workspace_id"]
        update_response = client.patch(
            f"/allocations/workspaces/{workspace_id}",
            json={"name": "Updated portfolio", "notes": "Raise SPY weight next month"},
        )
        import_response = client.post(
            "/allocations/workspaces/import",
            json={"payload": update_response.json()},
        )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated portfolio"
    assert update_response.json()["notes"] == "Raise SPY weight next month"
    assert import_response.status_code == 200
    assert import_response.json()["workspace_id"] != workspace_id
    assert import_response.json()["request"]["prices"]["SPY"] == 900.0


def test_delete_allocation_workspace(tmp_path):
    repository = LocalAllocationWorkspacesRepository(base_dir=tmp_path / "allocation_workspaces")
    service = AllocationWorkspaceService(repository=repository)

    with override_api_services(allocation_workspace_service=service):
        created = client.post(
            "/allocations/workspaces",
            json={
                "name": "To delete",
                "request": REQUEST_PAYLOAD,
            },
        ).json()
        workspace_id = created["workspace_id"]

        delete_response = client.delete(f"/allocations/workspaces/{workspace_id}")
        list_response = client.get("/allocations/workspaces")
        detail_response = client.get(f"/allocations/workspaces/{workspace_id}")

    assert delete_response.status_code == 204
    assert list_response.json() == []
    assert detail_response.status_code == 404
