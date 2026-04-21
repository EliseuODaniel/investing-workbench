"""Focused API tests for B3 pairs-trading routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from tests.support import override_api_services

client = TestClient(app)


class _StubPairsTradingService:
    def list_universe_presets(self) -> list[dict[str, object]]:
        return [{"preset_id": "ibov_proxy", "label": "IBOV Proxy", "ticker_count": 20}]

    def list_ibov_snapshots(self) -> list[dict[str, object]]:
        return [
            {
                "index_id": "ibov",
                "snapshot_id": "ibov_2025-01-20",
                "as_of_date": "2025-01-20",
                "source_kind": "b3_bdi_pdf",
                "source_url": "https://arquivos.b3.com.br/example.pdf",
                "validity_label": "Para Janeiro a Abril de 2025",
                "ticker_count": 2,
                "tickers": ["PETR4", "VALE3"],
                "constituents": [],
                "imported_at": "2026-04-20T15:00:00+00:00",
            }
        ]

    def get_ibov_snapshot(self, *, as_of_date: str) -> dict[str, object]:
        return self.list_ibov_snapshots()[0] | {"as_of_date": as_of_date}

    def backfill_ibov_snapshots(self, **_: object) -> dict[str, object]:
        return {
            "index_id": "ibov",
            "start_date": "2025-01-01",
            "end_date": "2025-09-01",
            "snapshot_count": 1,
            "snapshots": [
                {
                    "requested_as_of_date": "2025-01-01",
                    "resolved_as_of_date": "2025-01-20",
                    "cache_status": "cache_hit",
                    "ticker_count": 2,
                }
            ],
        }

    def resolve_universe(self, **_: object) -> dict[str, object]:
        return {
            "preset": {"preset_id": "ibov_proxy"},
            "requested_tickers": ["PETR4", "VALE3"],
            "as_of_date": None,
            "resolved_as_of_date": None,
            "start_date": "2021-01-01",
            "end_date": None,
            "common_index_start": "2021-01-01",
            "common_index_end": "2022-01-01",
            "common_index_days": 250,
            "quality_report": {"eligible_ticker_count": 2},
            "assets": [],
            "eligible_assets": [],
            "unavailable_tickers": {},
            "warnings": [],
        }

    def screen_pairs(self, **_: object) -> dict[str, object]:
        return {
            "preset": {"preset_id": "ibov_proxy"},
            "requested_tickers": ["PETR4", "VALE3"],
            "screening_window": {"formation_days": 252, "test_days": 21},
            "criteria": {"require_cointegration": True},
            "summary": {"candidate_pair_count": 1, "selected_pair_count": 1},
            "quality_report": {},
            "selected_pairs": [{"pair_label": "PETR4~VALE3"}],
            "candidate_pairs": [{"pair_label": "PETR4~VALE3"}],
            "warnings": [],
        }

    def run_backtest(self, **_: object) -> dict[str, object]:
        return {
            "pairs_backtest_id": "pairs_1",
            "created_at": "2026-04-20T15:00:00+00:00",
            "manifest": {"pairs_backtest_id": "pairs_1"},
            "preset": {"preset_id": "ibov_proxy"},
            "universe": {},
            "candidate_pairs": [],
            "benchmarks": [],
            "scenarios": [{"scenario_id": "realistic_cointegration"}],
            "robustness_report": {"rankings": []},
            "warnings": [],
        }

    def run_batch(self, **_: object) -> dict[str, object]:
        payload = self.run_backtest()
        payload["scenarios"] = [
            {"scenario_id": "realistic_cointegration"},
            {"scenario_id": "low_friction_cointegration"},
        ]
        return payload

    def list_backtests(self) -> list[dict[str, object]]:
        return [
            {
                "pairs_backtest_id": "pairs_1",
                "created_at": "2026-04-20T15:00:00+00:00",
                "preset_id": "ibov_proxy",
                "preset_label": "IBOV Proxy",
                "start_date": "2021-01-01",
                "end_date": None,
                "requested_tickers": ["PETR4", "VALE3"],
                "available_tickers": ["PETR4", "VALE3"],
                "eligible_tickers": ["PETR4", "VALE3"],
                "scenario_count": 2,
                "batch_mode": True,
                "benchmark_ids": ["equal_weight"],
                "candidate_pair_count": 1,
                "reconstitution_segment_count": 0,
                "warnings": [],
            }
        ]

    def get_manifest(self, backtest_id: str) -> dict[str, object]:
        return self.list_backtests()[0] | {"pairs_backtest_id": backtest_id}

    def get_results(self, backtest_id: str) -> dict[str, object]:
        return self.run_backtest() | {"pairs_backtest_id": backtest_id}


class _StubPairsJobService:
    def create_job(self, _payload: object, batch_mode: bool = False) -> dict[str, object]:
        return {
            "job_id": "pairs_job_1",
            "job_type": "pairs_backtest",
            "status": "queued",
            "created_at": "2026-04-20T15:00:00+00:00",
            "updated_at": "2026-04-20T15:00:00+00:00",
            "started_at": None,
            "finished_at": None,
            "attempt_count": 1,
            "cancel_requested": False,
            "request_payload": {"preset_id": "ibov_proxy"},
            "batch_mode": batch_mode,
            "preset_id": "ibov_proxy",
            "requested_tickers": ["PETR4", "VALE3"],
            "progress": {
                "phase": "queued",
                "message": "queued",
                "percent": 0.0,
                "updated_at": "2026-04-20T15:00:00+00:00",
            },
            "worker_id": None,
            "pairs_backtest_id": None,
            "result_available": False,
            "error": None,
            "events": [],
        }

    def list_jobs(self, **_: object) -> list[dict[str, object]]:
        return [self.create_job(None)]

    def get_job(self, _job_id: str) -> dict[str, object]:
        return self.create_job(None) | {"job_id": "pairs_job_9"}

    def cancel_job(self, _job_id: str) -> dict[str, object]:
        return self.get_job("pairs_job_9") | {"status": "cancelled", "cancel_requested": True}

    def resume_job(self, _job_id: str) -> dict[str, object]:
        return self.get_job("pairs_job_9") | {"status": "queued", "attempt_count": 2}

    def get_job_response(self, _job_id: str) -> dict[str, object]:
        return _StubPairsTradingService().run_backtest()


class _ErrorPairsTradingService(_StubPairsTradingService):
    def get_ibov_snapshot(self, *, as_of_date: str) -> dict[str, object]:
        raise FileNotFoundError(f"Snapshot not found: {as_of_date}")

    def resolve_universe(self, **_: object) -> dict[str, object]:
        raise ValueError("Invalid universe payload")


class _ErrorPairsJobService(_StubPairsJobService):
    def get_job_response(self, _job_id: str) -> dict[str, object]:
        raise ValueError("Pairs job 'pairs_job_9' does not have a completed result yet")


def test_pairs_routes_use_current_service_container() -> None:
    with override_api_services(
        pairs_trading_service=_StubPairsTradingService(),
        pairs_backtest_job_service=_StubPairsJobService(),
    ):
        universes = client.get("/pairs/universes")
        snapshots = client.get("/pairs/ibov-snapshots")
        snapshot = client.get("/pairs/ibov-snapshots/2025-01-20")
        backfill = client.post(
            "/pairs/ibov-snapshots/backfill",
            json={"start_date": "2025-01-01", "end_date": "2025-09-01"},
        )
        resolve = client.post("/pairs/universe/resolve", json={})
        screener = client.post("/pairs/screener", json={})
        backtest = client.post("/pairs/backtests", json={})
        backtest_job = client.post("/pairs/backtests/jobs", json={})
        batch_job = client.post("/pairs/backtests/jobs/batch", json={})
        jobs = client.get("/pairs/backtests/jobs")
        job = client.get("/pairs/backtests/jobs/pairs_job_9")
        cancel_job = client.post("/pairs/backtests/jobs/pairs_job_9/cancel")
        resume_job = client.post("/pairs/backtests/jobs/pairs_job_9/resume")
        job_response = client.get("/pairs/backtests/jobs/pairs_job_9/response")
        batch = client.post("/pairs/backtests/batch", json={})
        manifests = client.get("/pairs/backtests")
        manifest = client.get("/pairs/backtests/pairs_9")
        results = client.get("/pairs/backtests/pairs_9/results")

    assert universes.status_code == 200
    assert snapshots.status_code == 200
    assert snapshot.status_code == 200
    assert backfill.status_code == 200
    assert resolve.status_code == 200
    assert screener.status_code == 200
    assert backtest.status_code == 200
    assert backtest_job.status_code == 200
    assert batch_job.status_code == 200
    assert jobs.status_code == 200
    assert job.status_code == 200
    assert cancel_job.status_code == 200
    assert resume_job.status_code == 200
    assert job_response.status_code == 200
    assert batch.status_code == 200
    assert manifests.status_code == 200
    assert manifest.status_code == 200
    assert results.status_code == 200
    assert universes.json()[0]["preset_id"] == "ibov_proxy"
    assert snapshots.json()[0]["snapshot_id"] == "ibov_2025-01-20"
    assert snapshot.json()["as_of_date"] == "2025-01-20"
    assert backfill.json()["snapshot_count"] == 1
    assert resolve.json()["quality_report"]["eligible_ticker_count"] == 2
    assert screener.json()["summary"]["candidate_pair_count"] == 1
    assert backtest.json()["pairs_backtest_id"] == "pairs_1"
    assert backtest_job.json()["job_id"] == "pairs_job_1"
    assert batch_job.json()["batch_mode"] is True
    assert jobs.json()[0]["job_id"] == "pairs_job_1"
    assert job.json()["job_id"] == "pairs_job_9"
    assert cancel_job.json()["status"] == "cancelled"
    assert resume_job.json()["attempt_count"] == 2
    assert job_response.json()["pairs_backtest_id"] == "pairs_1"
    assert len(batch.json()["scenarios"]) == 2
    assert manifests.json()[0]["pairs_backtest_id"] == "pairs_1"
    assert manifest.json()["pairs_backtest_id"] == "pairs_9"
    assert results.json()["pairs_backtest_id"] == "pairs_9"


def test_pairs_routes_translate_file_not_found_and_value_errors() -> None:
    with override_api_services(
        pairs_trading_service=_ErrorPairsTradingService(),
        pairs_backtest_job_service=_ErrorPairsJobService(),
    ):
        snapshot = client.get("/pairs/ibov-snapshots/2025-01-20")
        resolve = client.post("/pairs/universe/resolve", json={})
        job_response = client.get("/pairs/backtests/jobs/pairs_job_9/response")

    assert snapshot.status_code == 404
    assert "Snapshot not found" in snapshot.json()["detail"]
    assert resolve.status_code == 400
    assert resolve.json()["detail"] == "Invalid universe payload"
    assert job_response.status_code == 400
    assert "does not have a completed result yet" in job_response.json()["detail"]
