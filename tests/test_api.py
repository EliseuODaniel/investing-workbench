"""Tests for FastAPI backend."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models import BacktestRequest
from src.bitcoin_martingale.application.datasets import DatasetCatalogService
from src.bitcoin_martingale.application.montecarlo import MonteCarloSimulationService
from src.bitcoin_martingale.application.optimizations import (
    OptimizationExecutionService,
    OptimizationPlanningService,
)
from src.bitcoin_martingale.application.runs import RunBacktestService
from src.bitcoin_martingale.application.walkforward import WalkForwardValidationService
from src.bitcoin_martingale.infrastructure.persistence import (
    LocalMonteCarloRepository,
    LocalOptimizationsRepository,
    LocalRunsRepository,
    LocalWalkForwardRepository,
)

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


class TestDatasetsEndpoint:
    """Test dataset catalog endpoints."""

    def test_list_datasets(self):
        response = client.get("/datasets")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert any(item["path"] == "data/btc_brl.parquet" for item in response.json())

    def test_get_dataset_detail(self):
        list_response = client.get("/datasets")
        dataset_id = list_response.json()[0]["dataset_id"]

        response = client.get(f"/datasets/{dataset_id}")
        assert response.status_code == 200
        assert response.json()["dataset_id"] == dataset_id
        assert "preview_rows" in response.json()
        assert "provenance" in response.json()

    def test_import_dataset(self, tmp_path):
        source_path = tmp_path / "import.csv"
        source_path.write_text("Date,Open,High,Low,Close\n2024-01-01,1,2,0.5,1.5\n", encoding="utf-8")

        with patch(
            "src.api.main.dataset_service",
            DatasetCatalogService(data_dir=tmp_path / "data"),
        ):
            response = client.post(
                "/datasets/import",
                json={"source_path": str(source_path)},
            )

        assert response.status_code == 200
        assert response.json()["name"] == "import"
        assert response.json()["provenance"]["source_kind"] == "imported"


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
        assert response.status_code == 404
        assert "No persisted run found" in response.json()["detail"]


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

    def test_run_html_report_not_found(self):
        """Unknown HTML reports should return 404."""
        response = client.get("/runs/does-not-exist/report.html")
        assert response.status_code == 404
        assert "Run HTML report not found" in response.json()["detail"]

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

    def test_run_html_report_and_legacy_csv_success(self, tmp_path):
        """Persisted HTML reports and legacy latest-strategy CSV should be downloadable."""
        repository = LocalRunsRepository(base_dir=tmp_path)
        patched_service = RunBacktestService(runs_repository=repository)
        response_model = patched_service.run(BacktestRequest(config_path="configs/test.yaml"))
        run_id = response_model.run_info["run_id"]
        strategy_name = next(iter(response_model.results.keys()))

        with patch("src.api.main.service", patched_service):
            html_response = client.get(f"/runs/{run_id}/report.html")
            csv_response = client.get(f"/reports/{strategy_name}/download")

        assert html_response.status_code == 200
        assert "text/html" in html_response.headers["content-type"]
        assert run_id in html_response.text
        assert csv_response.status_code == 200
        assert "timestamp,action,price,quantity,layer,pnl" in csv_response.text


class TestOptimizationsEndpoint:
    """Test optimization planning and execution endpoints."""

    def test_plan_optimization_endpoint(self):
        request_data = {
            "config_path": "configs/test.yaml",
            "strategies": ["Simple Martingale"],
            "parameter_space": {
                "base_bet": {"values": [250.0, 500.0]},
            },
        }

        response = client.post("/optimizations/plan", json=request_data)

        assert response.status_code == 200
        assert response.json()["trial_count"] == 2

    def test_execute_optimization_and_fetch_results(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        optimizations_repository = LocalOptimizationsRepository(base_dir=tmp_path / "optimizations")
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_planner = OptimizationPlanningService()
        patched_optimization_service = OptimizationExecutionService(
            run_service=patched_run_service,
            repository=optimizations_repository,
        )
        request_data = {
            "config_path": "configs/test.yaml",
            "strategies": ["Simple Martingale"],
            "parameter_space": {
                "base_bet": {"values": [250.0, 500.0]},
            },
            "objective": "total_return",
        }

        with (
            patch("src.api.main.service", patched_run_service),
            patch("src.api.main.optimization_planner", patched_planner),
            patch("src.api.main.optimization_service", patched_optimization_service),
        ):
            execute_response = client.post("/optimizations", json=request_data)

            optimization_id = execute_response.json()["optimization_id"]
            list_response = client.get("/optimizations")
            manifest_response = client.get(f"/optimizations/{optimization_id}")
            results_response = client.get(f"/optimizations/{optimization_id}/results")

        assert execute_response.status_code == 200
        assert execute_response.json()["completed_trial_count"] == 2
        assert list_response.status_code == 200
        assert list_response.json()[0]["optimization_id"] == optimization_id
        assert manifest_response.status_code == 200
        assert manifest_response.json()["optimization_id"] == optimization_id
        assert results_response.status_code == 200
        assert len(results_response.json()["ranked_results"]) == 2


class TestWalkForwardEndpoint:
    """Test walk-forward validation endpoints."""

    def test_execute_walkforward_and_fetch_results(self, tmp_path):
        repository = LocalWalkForwardRepository(base_dir=tmp_path / "walkforward")
        patched_service = WalkForwardValidationService(repository=repository)
        request_data = {
            "config_path": "configs/test.yaml",
            "strategies": ["Simple Martingale"],
            "train_window_days": 45,
            "test_window_days": 20,
            "step_days": 20,
        }

        with patch("src.api.main.walkforward_service", patched_service):
            execute_response = client.post("/walkforward", json=request_data)
            walkforward_id = execute_response.json()["walkforward_id"]
            list_response = client.get("/walkforward")
            manifest_response = client.get(f"/walkforward/{walkforward_id}")
            results_response = client.get(f"/walkforward/{walkforward_id}/results")

        assert execute_response.status_code == 200
        assert execute_response.json()["window_count"] > 0
        assert list_response.status_code == 200
        assert list_response.json()[0]["walkforward_id"] == walkforward_id
        assert manifest_response.status_code == 200
        assert manifest_response.json()["walkforward_id"] == walkforward_id
        assert results_response.status_code == 200
        assert len(results_response.json()["results"]) > 0


class TestMonteCarloEndpoint:
    """Test Monte Carlo robustness endpoints."""

    def test_execute_montecarlo_and_fetch_results(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        montecarlo_repository = LocalMonteCarloRepository(base_dir=tmp_path / "montecarlo")
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_service = MonteCarloSimulationService(
            run_service=patched_run_service,
            repository=montecarlo_repository,
            runs_repository=runs_repository,
        )
        request_data = {
            "config_path": "configs/test.yaml",
            "strategies": ["Simple Martingale"],
            "simulation_count": 20,
            "random_seed": 7,
        }

        with (
            patch("src.api.main.service", patched_run_service),
            patch("src.api.main.montecarlo_service", patched_service),
        ):
            execute_response = client.post("/montecarlo", json=request_data)
            montecarlo_id = execute_response.json()["montecarlo_id"]
            list_response = client.get("/montecarlo")
            manifest_response = client.get(f"/montecarlo/{montecarlo_id}")
            results_response = client.get(f"/montecarlo/{montecarlo_id}/results")

        assert execute_response.status_code == 200
        assert execute_response.json()["simulation_count"] == 20
        assert execute_response.json()["source_run_id"].startswith("run_")
        assert list_response.status_code == 200
        assert list_response.json()[0]["montecarlo_id"] == montecarlo_id
        assert manifest_response.status_code == 200
        assert manifest_response.json()["montecarlo_id"] == montecarlo_id
        assert results_response.status_code == 200
        assert len(results_response.json()["results"][0]["simulations"]) == 20
