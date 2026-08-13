"""Tests for FastAPI backend."""

import json
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models import BacktestRequest
from src.investing_workbench.application.backtest_jobs import BacktestJobService
from src.investing_workbench.application.datasets import DatasetCatalogService
from src.investing_workbench.application.experiments import ExperimentRegistryService
from src.investing_workbench.application.montecarlo import MonteCarloSimulationService
from src.investing_workbench.application.optimizations import (
    OptimizationExecutionService,
    OptimizationPlanningService,
)
from src.investing_workbench.application.research_workspaces import ResearchWorkspaceService
from src.investing_workbench.application.runs import RunBacktestService
from src.investing_workbench.application.walkforward import WalkForwardValidationService
from src.investing_workbench.infrastructure.persistence import (
    LocalBacktestJobsRepository,
    LocalMonteCarloRepository,
    LocalOptimizationsRepository,
    LocalPairsBacktestsRepository,
    LocalResearchWorkspacesRepository,
    LocalRunsRepository,
    LocalWalkForwardRepository,
)
from tests.support import override_api_services

client = TestClient(app)


def _wait_for_job_status(
    job_id: str, expected_status: str, timeout_seconds: float = 5.0
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = client.get(f"/backtest/jobs/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == expected_status:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for {job_id} to reach status {expected_status}")


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


class TestBacktestStrategyCatalogEndpoint:
    def test_get_strategy_catalog(self):
        response = client.get("/backtests/strategy-catalog")

        assert response.status_code == 200
        payload = response.json()
        assert payload["title"] == "Catalogo de estrategias"
        assert any(item["strategy_id"] == "martingale_v1" for item in payload["strategies"])
        assert any(
            item["parameter_defaults"]
            for item in payload["strategies"]
            if item["strategy_id"] == "pairs_cointegration"
        )
        assert any(item["dimension_id"] == "robustness" for item in payload["score_dimensions"])

    def test_create_strategy_setup_plan(self):
        response = client.post(
            "/backtests/strategy-setup-plan",
            json={
                "strategy_id": "pairs_cointegration",
                "label": "Pairs por cointegracao",
                "family": "market_neutral",
                "direction": "long_short",
                "parameter_values": {"formation_window": 252, "entry_zscore": 2.0},
                "universe": ["PETR4", "VALE3"],
                "timeframe": "daily",
                "setup_notes": ["Revalidar janela."],
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["route_hint"] == "/pairs/backtests"
        assert payload["readiness"] == "ready_to_review"
        assert payload["run_request"]["formation_window"] == 252

    def test_create_strategy_setup_plan_for_core_backtest(self):
        response = client.post(
            "/backtests/strategy-setup-plan",
            json={
                "strategy_id": "buy_and_hold",
                "label": "Buy and hold",
                "family": "benchmark",
                "direction": "long",
                "parameter_values": {"initial_capital": 10000},
                "universe": ["BOVA11"],
                "timeframe": "daily",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["route_hint"] == "/backtest"
        assert payload["run_request"]["config_path"] == "configs/test.yaml"
        assert payload["run_request"]["strategies"] == ["Buy & Hold"]


class TestDatasetsEndpoint:
    """Test dataset catalog endpoints."""

    def test_list_datasets(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "sample.csv").write_text(
            "Date,Open,High,Low,Close\n2024-01-01,1,2,0.5,1.5\n",
            encoding="utf-8",
        )

        with override_api_services(dataset_service=DatasetCatalogService(data_dir=data_dir)):
            response = client.get("/datasets")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["name"] == "sample"

    def test_get_dataset_detail(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "sample.csv").write_text(
            "Date,Open,High,Low,Close\n2024-01-01,1,2,0.5,1.5\n",
            encoding="utf-8",
        )
        dataset_service = DatasetCatalogService(data_dir=data_dir)
        dataset_id = dataset_service.list_datasets()[0]["dataset_id"]

        with override_api_services(dataset_service=dataset_service):
            response = client.get(f"/datasets/{dataset_id}")

        assert response.status_code == 200
        assert response.json()["dataset_id"] == dataset_id
        assert "preview_rows" in response.json()
        assert "provenance" in response.json()

    def test_import_dataset(self, tmp_path):
        source_path = tmp_path / "import.csv"
        source_path.write_text(
            "Date,Open,High,Low,Close\n2024-01-01,1,2,0.5,1.5\n", encoding="utf-8"
        )

        with override_api_services(
            dataset_service=DatasetCatalogService(data_dir=tmp_path / "data")
        ):
            response = client.post(
                "/datasets/import",
                json={"source_path": str(source_path)},
            )

        assert response.status_code == 200
        assert response.json()["name"] == "import"
        assert response.json()["provenance"]["source_kind"] == "imported"

    def test_refresh_policy_and_due_endpoints(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        source_path = data_dir / "btc_brl.parquet"
        import pandas as pd

        pd.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-02"],
                "Open": [1.0, 2.0],
                "High": [2.0, 3.0],
                "Low": [0.5, 1.5],
                "Close": [1.5, 2.5],
            }
        ).to_parquet(source_path, index=False)

        patched_dataset_service = DatasetCatalogService(data_dir=data_dir)
        dataset_id = patched_dataset_service.list_datasets()[0]["dataset_id"]

        with override_api_services(dataset_service=patched_dataset_service):
            policy_response = client.post(
                f"/datasets/{dataset_id}/refresh-policy",
                json={
                    "enabled": True,
                    "interval_days": 1,
                    "start_date": "2020-01-01",
                },
            )

        metadata_path = data_dir / ".catalog" / f"{dataset_id}.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["last_refreshed_at"] = (datetime.now(UTC) - timedelta(days=5)).isoformat()
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        with (
            override_api_services(dataset_service=patched_dataset_service),
            patch(
                "src.investing_workbench.application.datasets.service.get_data",
                return_value=pd.DataFrame({"Close": [1.0]}),
            ),
        ):
            due_response = client.get("/datasets/refresh-due")
            execute_due_response = client.post("/datasets/refresh-due", json={"limit": 1})

        assert policy_response.status_code == 200
        assert policy_response.json()["provenance"]["refresh_policy"]["enabled"] is True
        assert due_response.status_code == 200
        assert due_response.json()[0]["dataset_id"] == dataset_id
        assert execute_due_response.status_code == 200
        assert execute_due_response.json()[0]["dataset_id"] == dataset_id


class TestAllocationsEndpoint:
    """Test portfolio allocation endpoints."""

    def test_rebalance_plan_success(self):
        response = client.post(
            "/allocations/rebalance-plan",
            json={
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
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["needs_rebalance"] is True
        assert payload["target_cash"] == pytest.approx(1800.0)
        assert any(
            action["asset"] == "ETH-USD" and action["action"] == "sell"
            for action in payload["actions"]
        )

    def test_rebalance_plan_rejects_missing_prices(self):
        response = client.post(
            "/allocations/rebalance-plan",
            json={
                "cash": 1000.0,
                "holdings": [{"asset": "BTC-BRL", "quantity": 0.1}],
                "prices": {},
                "targets": [{"asset": "BTC-BRL", "target_weight": 0.5}],
            },
        )

        assert response.status_code == 400
        assert "Missing prices" in response.json()["detail"]


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

    def test_backtest_response_exposes_execution_contract(self, tmp_path):
        repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        patched_service = RunBacktestService(runs_repository=repository)

        with override_api_services(run_service=patched_service):
            response = client.post("/backtest", json={"config_path": "configs/test.yaml"})

        assert response.status_code == 200
        payload = response.json()
        assert "warnings" in payload
        first_result = next(iter(payload["results"].values()))
        assert "execution_summary" in first_result
        assert "warnings" in first_result
        assert "execution_log" in first_result


class TestBacktestJobsEndpoint:
    """Test async backtest job endpoints."""

    def test_async_backtest_job_lifecycle(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        run_service = RunBacktestService(runs_repository=runs_repository)
        job_service = BacktestJobService(
            run_service=run_service,
            jobs_repository=LocalBacktestJobsRepository(base_dir=tmp_path / "jobs"),
            max_workers=1,
        )

        with override_api_services(
            run_service=run_service,
            backtest_job_service=job_service,
        ):
            create_response = client.post(
                "/backtest/jobs", json={"config_path": "configs/test.yaml"}
            )

            assert create_response.status_code == 200
            job_payload = create_response.json()
            assert job_payload["status"] in {"queued", "running"}

            completed_payload = _wait_for_job_status(job_payload["job_id"], "completed")
            assert completed_payload["result_available"] is True
            assert completed_payload["run_id"]

            list_response = client.get("/backtest/jobs")
            assert list_response.status_code == 200
            assert any(item["job_id"] == job_payload["job_id"] for item in list_response.json())

            response_payload = client.get(f"/backtest/jobs/{job_payload['job_id']}/response")
            assert response_payload.status_code == 200
            assert "results" in response_payload.json()


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns basic info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "Investing Workbench API" in data["message"]
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

        with override_api_services(run_service=patched_service):
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

        with override_api_services(run_service=patched_service):
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

        with override_api_services(
            run_service=patched_run_service,
            optimization_planner=patched_planner,
            optimization_service=patched_optimization_service,
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

    def test_list_experiments_endpoint(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        optimizations_repository = LocalOptimizationsRepository(base_dir=tmp_path / "optimizations")
        walkforward_repository = LocalWalkForwardRepository(base_dir=tmp_path / "walkforward")
        montecarlo_repository = LocalMonteCarloRepository(base_dir=tmp_path / "montecarlo")

        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_optimization_service = OptimizationExecutionService(
            run_service=patched_run_service,
            repository=optimizations_repository,
        )
        patched_walkforward_service = WalkForwardValidationService(
            repository=walkforward_repository
        )
        patched_montecarlo_service = MonteCarloSimulationService(
            run_service=patched_run_service,
            repository=montecarlo_repository,
            runs_repository=runs_repository,
        )
        patched_registry = ExperimentRegistryService(
            runs_repository=runs_repository,
            optimizations_repository=optimizations_repository,
            walkforward_repository=walkforward_repository,
            montecarlo_repository=montecarlo_repository,
        )

        optimization_request = {
            "config_path": "configs/test.yaml",
            "strategies": ["Simple Martingale"],
            "parameter_space": {"base_bet": {"values": [250.0]}},
        }
        walkforward_request = {
            "config_path": "configs/test.yaml",
            "strategies": ["Simple Martingale"],
            "train_window_days": 45,
            "test_window_days": 20,
            "step_days": 20,
        }
        montecarlo_request = {
            "config_path": "configs/test.yaml",
            "strategies": ["Simple Martingale"],
            "simulation_count": 10,
            "random_seed": 7,
        }

        with override_api_services(
            run_service=patched_run_service,
            optimization_service=patched_optimization_service,
            walkforward_service=patched_walkforward_service,
            montecarlo_service=patched_montecarlo_service,
            experiment_registry_service=patched_registry,
        ):
            client.post("/backtest", json={"config_path": "configs/test.yaml"})
            client.post("/optimizations", json=optimization_request)
            client.post("/walkforward", json=walkforward_request)
            client.post("/montecarlo", json=montecarlo_request)
            experiments_response = client.get("/experiments")

        assert experiments_response.status_code == 200
        payload = experiments_response.json()
        experiment_types = {item["experiment_type"] for item in payload}
        assert {"run", "optimization", "walkforward", "montecarlo"}.issubset(experiment_types)
        assert all("artifact_dir" in item for item in payload)

    def test_list_experiments_endpoint_supports_filters(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        optimizations_repository = LocalOptimizationsRepository(base_dir=tmp_path / "optimizations")
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_optimization_service = OptimizationExecutionService(
            run_service=patched_run_service,
            repository=optimizations_repository,
        )
        patched_registry = ExperimentRegistryService(
            runs_repository=runs_repository,
            optimizations_repository=optimizations_repository,
        )

        with override_api_services(
            run_service=patched_run_service,
            optimization_service=patched_optimization_service,
            experiment_registry_service=patched_registry,
        ):
            client.post("/backtest", json={"config_path": "configs/test.yaml"})
            client.post(
                "/optimizations",
                json={
                    "config_path": "configs/test.yaml",
                    "strategies": ["Simple Martingale"],
                    "parameter_space": {"base_bet": {"values": [250.0]}},
                },
            )
            filtered_response = client.get(
                "/experiments",
                params={"experiment_type": "optimization", "strategy_name": "Simple Martingale"},
            )

        assert filtered_response.status_code == 200
        payload = filtered_response.json()
        assert len(payload) == 1
        assert payload[0]["experiment_type"] == "optimization"

    def test_experiment_registry_includes_pairs_backtests(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        pairs_repository = LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
        patched_registry = ExperimentRegistryService(
            runs_repository=runs_repository,
            pairs_repository=pairs_repository,
        )
        pairs_repository.persist_execution(
            backtest_id="pairs_1",
            manifest={
                "pairs_backtest_id": "pairs_1",
                "created_at": "2026-04-20T15:00:00+00:00",
                "preset_id": "ibov_proxy",
                "preset_label": "IBOV Proxy",
                "universe_as_of_date": None,
                "start_date": "2021-01-01",
                "end_date": None,
                "requested_tickers": ["PETR4", "PETR3"],
                "available_tickers": ["PETR4", "PETR3"],
                "eligible_tickers": ["PETR4", "PETR3"],
                "scenario_count": 1,
                "batch_mode": False,
                "benchmark_ids": ["equal_weight"],
                "candidate_pair_count": 1,
                "reconstitution_segment_count": 0,
                "warnings": [],
            },
            results={
                "pairs_backtest_id": "pairs_1",
                "created_at": "2026-04-20T15:00:00+00:00",
                "manifest": {"pairs_backtest_id": "pairs_1"},
                "preset": {"preset_id": "ibov_proxy"},
                "universe": {},
                "candidate_pairs": [],
                "benchmarks": [],
                "scenarios": [],
                "robustness_report": {"rankings": []},
                "warnings": [],
            },
        )

        with override_api_services(
            experiment_registry_service=patched_registry,
        ):
            experiments_response = client.get(
                "/experiments",
                params={"experiment_type": "pairs_backtest"},
            )
            detail_response = client.get("/experiments/pairs_backtest/pairs_1")

        assert experiments_response.status_code == 200
        payload = experiments_response.json()
        assert len(payload) == 1
        assert payload[0]["experiment_type"] == "pairs_backtest"
        assert payload[0]["experiment_id"] == "pairs_1"
        assert detail_response.status_code == 200
        assert detail_response.json()["record"]["experiment_type"] == "pairs_backtest"
        assert detail_response.json()["manifest"]["pairs_backtest_id"] == "pairs_1"

    def test_get_experiment_endpoint_returns_detail_payload(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_registry = ExperimentRegistryService(runs_repository=runs_repository)

        with override_api_services(
            run_service=patched_run_service,
            experiment_registry_service=patched_registry,
        ):
            run_response = client.post("/backtest", json={"config_path": "configs/test.yaml"})
            run_id = run_response.json()["run_info"]["run_id"]
            detail_response = client.get(f"/experiments/run/{run_id}")

        assert detail_response.status_code == 200
        payload = detail_response.json()
        assert payload["record"]["experiment_id"] == run_id
        assert payload["record"]["experiment_type"] == "run"
        assert payload["manifest"]["run_id"] == run_id

    def test_get_experiment_endpoint_includes_related_experiments(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        montecarlo_repository = LocalMonteCarloRepository(base_dir=tmp_path / "montecarlo")
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_montecarlo_service = MonteCarloSimulationService(
            run_service=patched_run_service,
            repository=montecarlo_repository,
            runs_repository=runs_repository,
        )
        patched_registry = ExperimentRegistryService(
            runs_repository=runs_repository,
            montecarlo_repository=montecarlo_repository,
        )

        with override_api_services(
            run_service=patched_run_service,
            montecarlo_service=patched_montecarlo_service,
            experiment_registry_service=patched_registry,
        ):
            run_response = client.post("/backtest", json={"config_path": "configs/test.yaml"})
            run_id = run_response.json()["run_info"]["run_id"]
            montecarlo_response = client.post(
                "/montecarlo",
                json={
                    "run_id": run_id,
                    "strategies": ["Simple Martingale"],
                    "simulation_count": 10,
                    "random_seed": 7,
                },
            )
            detail_response = client.get(f"/experiments/run/{run_id}")

        assert montecarlo_response.status_code == 200
        assert detail_response.status_code == 200
        payload = detail_response.json()
        assert len(payload["related_experiments"]) == 1
        assert payload["related_experiments"][0]["relationship"] == "source_run_for_montecarlo"
        assert payload["related_experiments"][0]["record"]["experiment_type"] == "montecarlo"

    def test_save_and_list_research_workspaces(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        workspaces_repository = LocalResearchWorkspacesRepository(
            base_dir=tmp_path / "research_workspaces"
        )
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_registry = ExperimentRegistryService(runs_repository=runs_repository)
        patched_workspace_service = ResearchWorkspaceService(
            repository=workspaces_repository,
            experiment_registry_service=patched_registry,
        )

        with override_api_services(
            run_service=patched_run_service,
            experiment_registry_service=patched_registry,
            research_workspace_service=patched_workspace_service,
        ):
            run_response = client.post("/backtest", json={"config_path": "configs/test.yaml"})
            run_id = run_response.json()["run_info"]["run_id"]
            save_response = client.post(
                "/research-workspaces",
                json={
                    "name": "Simple run workspace",
                    "selected_experiment_type": "run",
                    "selected_experiment_id": run_id,
                    "anchor_run_id": run_id,
                },
            )
            workspace_id = save_response.json()["workspace_id"]
            list_response = client.get("/research-workspaces")
            detail_response = client.get(f"/research-workspaces/{workspace_id}")

        assert save_response.status_code == 200
        assert save_response.json()["name"] == "Simple run workspace"
        assert save_response.json()["records"]["selected"]["experiment_id"] == run_id
        assert list_response.status_code == 200
        assert list_response.json()[0]["workspace_id"] == workspace_id
        assert detail_response.status_code == 200
        assert detail_response.json()["selection"]["anchor_run_id"] == run_id

    def test_update_and_import_research_workspaces(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        workspaces_repository = LocalResearchWorkspacesRepository(
            base_dir=tmp_path / "research_workspaces"
        )
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_registry = ExperimentRegistryService(runs_repository=runs_repository)
        patched_workspace_service = ResearchWorkspaceService(
            repository=workspaces_repository,
            experiment_registry_service=patched_registry,
        )

        with override_api_services(
            run_service=patched_run_service,
            experiment_registry_service=patched_registry,
            research_workspace_service=patched_workspace_service,
        ):
            run_response = client.post("/backtest", json={"config_path": "configs/test.yaml"})
            run_id = run_response.json()["run_info"]["run_id"]
            save_response = client.post(
                "/research-workspaces",
                json={
                    "name": "Editable workspace",
                    "selected_experiment_type": "run",
                    "selected_experiment_id": run_id,
                    "anchor_run_id": run_id,
                },
            )
            workspace = save_response.json()
            workspace_id = workspace["workspace_id"]
            update_response = client.patch(
                f"/research-workspaces/{workspace_id}",
                json={"name": "Updated workspace", "notes": "Saved notes"},
            )
            import_response = client.post(
                "/research-workspaces/import",
                json={"payload": update_response.json()},
            )

        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated workspace"
        assert update_response.json()["notes"] == "Saved notes"
        assert import_response.status_code == 200
        assert import_response.json()["workspace_id"] != workspace_id
        assert import_response.json()["name"] == "Updated workspace"

    def test_export_research_workspace_report_formats(self, tmp_path):
        runs_repository = LocalRunsRepository(base_dir=tmp_path / "runs")
        workspaces_repository = LocalResearchWorkspacesRepository(
            base_dir=tmp_path / "research_workspaces"
        )
        patched_run_service = RunBacktestService(runs_repository=runs_repository)
        patched_registry = ExperimentRegistryService(runs_repository=runs_repository)
        patched_workspace_service = ResearchWorkspaceService(
            repository=workspaces_repository,
            experiment_registry_service=patched_registry,
        )

        with override_api_services(
            run_service=patched_run_service,
            experiment_registry_service=patched_registry,
            research_workspace_service=patched_workspace_service,
        ):
            run_response = client.post("/backtest", json={"config_path": "configs/test.yaml"})
            run_id = run_response.json()["run_info"]["run_id"]
            save_response = client.post(
                "/research-workspaces",
                json={
                    "name": "Report workspace",
                    "selected_experiment_type": "run",
                    "selected_experiment_id": run_id,
                    "anchor_run_id": run_id,
                },
            )
            workspace_id = save_response.json()["workspace_id"]
            json_response = client.get(f"/research-workspaces/{workspace_id}/report")
            markdown_response = client.get(
                f"/research-workspaces/{workspace_id}/report?format=markdown"
            )
            html_response = client.get(f"/research-workspaces/{workspace_id}/report?format=html")

        assert json_response.status_code == 200
        assert json_response.json()["workspace"]["workspace_id"] == workspace_id
        assert json_response.json()["report"]["title"] == "Report workspace"

        assert markdown_response.status_code == 200
        assert markdown_response.headers["content-type"].startswith("text/markdown")
        assert "# Report workspace" in markdown_response.text

        assert html_response.status_code == 200
        assert html_response.headers["content-type"].startswith("text/html")
        assert "Research Workspace Report" in html_response.text


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

        with override_api_services(walkforward_service=patched_service):
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

        with override_api_services(
            run_service=patched_run_service,
            montecarlo_service=patched_service,
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
