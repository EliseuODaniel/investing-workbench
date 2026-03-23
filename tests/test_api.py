"""Tests for FastAPI backend."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models import BacktestRequest
from src.bitcoin_martingale.application.runs import RunBacktestService
from src.bitcoin_martingale.infrastructure.persistence import LocalRunsRepository

client = TestClient(app)


class TestConfigsEndpoint:
    """Test /configs endpoint."""

    def test_get_configs_success(self):
        """Test successful config listing."""
        response = client.get("/configs")
        assert response.status_code == 200

        configs = response.json()
        assert isinstance(configs, list)

        if configs:  # If configs exist
            config = configs[0]
            assert "name" in config
            assert "path" in config
            assert "display_name" in config

    def test_get_configs_no_configs_dir(self):
        """Test when configs directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            response = client.get("/configs")
            assert response.status_code == 404
            assert "Configs directory not found" in response.json()["detail"]


class TestBacktestEndpoint:
    """Test /backtest endpoint."""

    def test_backtest_invalid_config(self):
        """Test backtest with invalid config file."""
        request_data = {"config_path": "nonexistent.yaml"}

        response = client.post("/backtest", json=request_data)
        assert response.status_code == 404
        assert "Config file not found" in response.json()["detail"]

    def test_backtest_endpoint_exists(self):
        """Test that backtest endpoint exists and accepts POST."""
        # Just test that the endpoint exists and returns expected error format
        request_data = {"strategies": ["Nonexistent Strategy"]}

        response = client.post("/backtest", json=request_data)
        # Should return 404 for config not found, or 400 for no strategies, etc.
        # We just test it doesn't return a routing error
        assert response.status_code in [400, 404, 500]
        assert "detail" in response.json()


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns basic info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "Bitcoin Martingale Backtest API" in data["message"]
        assert data["version"] == "1.0.0"


class TestCSVDowloadEndpoint:
    """Test CSV download endpoint."""

    def test_csv_download_endpoint_exists(self):
        """Test that CSV download endpoint exists."""
        response = client.get("/reports/test_strategy/download")
        assert response.status_code == 501
        assert "detail" in response.json()


class TestPersistedRunsEndpoint:
    """Test persisted run artifact endpoints."""

    def test_list_runs_endpoint(self):
        """The runs listing endpoint should respond successfully."""
        response = client.get("/runs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_run_manifest_not_found(self):
        """Unknown run ids should return 404."""
        response = client.get("/runs/does-not-exist")
        assert response.status_code == 404
        assert "Run manifest not found" in response.json()["detail"]

    def test_run_response_not_found(self):
        """Unknown persisted responses should return 404."""
        response = client.get("/runs/does-not-exist/response")
        assert response.status_code == 404
        assert "Run response not found" in response.json()["detail"]

    def test_run_config_not_found(self):
        """Unknown config snapshots should return 404."""
        response = client.get("/runs/does-not-exist/config")
        assert response.status_code == 404
        assert "Run config snapshot not found" in response.json()["detail"]

    def test_run_data_profile_not_found(self):
        """Unknown data profiles should return 404."""
        response = client.get("/runs/does-not-exist/data-profile")
        assert response.status_code == 404
        assert "Run data profile not found" in response.json()["detail"]

    def test_run_strategy_csv_not_found(self):
        """Unknown strategy exports should return 404."""
        response = client.get("/runs/does-not-exist/strategies/foo/trades.csv")
        assert response.status_code == 404
        assert "Run response not found" in response.json()["detail"]

    def test_run_config_and_data_profile_success(self, tmp_path):
        """Persisted config snapshots and data profiles should be exposed by the API."""
        repository = LocalRunsRepository(base_dir=tmp_path)
        patched_service = RunBacktestService(runs_repository=repository)
        response_model = patched_service.run(BacktestRequest(config_path="configs/test.yaml"))
        run_id = response_model.run_info["run_id"]

        with patch("src.api.main.service", patched_service):
            config_response = client.get(f"/runs/{run_id}/config")
            data_profile_response = client.get(f"/runs/{run_id}/data-profile")

        assert config_response.status_code == 200
        assert config_response.json()["backtest"]["cache_path"] == "data/btc_brl.parquet"
        assert data_profile_response.status_code == 200
        assert data_profile_response.json()["data_fingerprint"]
