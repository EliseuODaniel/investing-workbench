from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from src.bitcoin_martingale.interfaces.cli.main import main


class _StubPairsService:
    def __init__(self) -> None:
        self.last_backtest_kwargs: dict[str, object] | None = None

    def list_universe_presets(self):
        return [{"preset_id": "ibov_proxy", "label": "IBOV Proxy", "ticker_count": 20}]

    def list_ibov_snapshots(self):
        return [
            {
                "as_of_date": "2025-01-20",
                "ticker_count": 2,
                "validity_label": "Para Janeiro a Abril de 2025",
            }
        ]

    def get_ibov_snapshot(self, *, as_of_date: str):
        return {"as_of_date": as_of_date, "tickers": ["PETR4", "VALE3"]}

    def backfill_ibov_snapshots(self, **_: object):
        return {"snapshot_count": 1, "snapshots": [{"resolved_as_of_date": "2025-01-20"}]}

    def screen_pairs(self, **_: object):
        return {
            "summary": {"candidate_pair_count": 1},
            "candidate_pairs": [{"pair_label": "PETR4~PETR3"}],
        }

    def run_backtest(self, **kwargs: object):
        self.last_backtest_kwargs = kwargs
        return {
            "pairs_backtest_id": "pairs_1",
            "created_at": "2026-04-20T15:00:00Z",
            "manifest": {"pairs_backtest_id": "pairs_1"},
            "preset": {"preset_id": "ibov_proxy"},
            "universe": {},
            "candidate_pairs": [],
            "benchmarks": [],
            "scenarios": [{"scenario_id": "realistic_cointegration"}],
            "robustness_report": {"rankings": []},
            "warnings": [],
        }


class _StubPairsJobService:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, object] | None = None
        self.last_batch_mode = False

    def create_job(self, payload: dict[str, object], batch_mode: bool = False):
        self.last_kwargs = payload
        self.last_batch_mode = batch_mode
        return {"job_id": "pairs_job_1", "status": "queued", "batch_mode": batch_mode}

    def list_jobs(self, **_: object):
        return [{"job_id": "pairs_job_1", "status": "queued"}]

    def get_job(self, job_id: str):
        return {"job_id": job_id, "status": "queued"}

    def run_worker_loop(self, **_: object):
        return {"processed_jobs": 1}


def _services() -> SimpleNamespace:
    return SimpleNamespace(
        pairs_trading_service=_StubPairsService(),
        pairs_backtest_job_service=_StubPairsJobService(),
    )


def test_pairs_universes_cli_prints_text_summary(capsys) -> None:
    with patch(
        "src.bitcoin_martingale.interfaces.cli.main.build_services",
        return_value=_services(),
    ):
        main(["pairs-universes"])

    output = capsys.readouterr().out
    assert "ibov_proxy" in output
    assert "tickers=20" in output


def test_pairs_screen_cli_prints_json(capsys) -> None:
    with patch(
        "src.bitcoin_martingale.interfaces.cli.main.build_services",
        return_value=_services(),
    ):
        main(["pairs-screen", "--tickers", "PETR4", "PETR3"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["candidate_pair_count"] == 1
    assert payload["candidate_pairs"][0]["pair_label"] == "PETR4~PETR3"


def test_pairs_ibov_snapshots_cli_prints_summary(capsys) -> None:
    with patch(
        "src.bitcoin_martingale.interfaces.cli.main.build_services",
        return_value=_services(),
    ):
        main(["pairs-ibov-snapshots"])

    output = capsys.readouterr().out
    assert "2025-01-20" in output
    assert "tickers=2" in output


def test_pairs_backtest_cli_forwards_portfolio_controls(capsys) -> None:
    stub_service = _StubPairsService()
    with patch(
        "src.bitcoin_martingale.interfaces.cli.main.build_services",
        return_value=SimpleNamespace(
            pairs_trading_service=stub_service,
            pairs_backtest_job_service=_StubPairsJobService(),
        ),
    ):
        main(
            [
                "pairs-backtest",
                "--tickers",
                "PETR4",
                "PETR3",
                "--portfolio-construction",
                "risk_parity",
                "--target-pair-volatility-annual",
                "0.10",
                "--max-gross-exposure-pct",
                "0.80",
                "--max-net-exposure-pct",
                "0.05",
                "--max-sector-pairs",
                "1",
                "--borrow-snapshot-path",
                "data/borrow/b3_snapshot.csv",
            ]
        )

    assert "pairs_1" in capsys.readouterr().out
    assert stub_service.last_backtest_kwargs is not None
    assert stub_service.last_backtest_kwargs["portfolio_construction"] == "risk_parity"
    assert stub_service.last_backtest_kwargs["target_pair_volatility_annual"] == 0.10
    assert stub_service.last_backtest_kwargs["max_gross_exposure_pct"] == 0.80
    assert stub_service.last_backtest_kwargs["max_net_exposure_pct"] == 0.05
    assert stub_service.last_backtest_kwargs["max_sector_pairs"] == 1
    assert (
        stub_service.last_backtest_kwargs["borrow_snapshot_path"] == "data/borrow/b3_snapshot.csv"
    )


def test_pairs_backtest_job_cli_forwards_payload(capsys) -> None:
    stub_service = _StubPairsService()
    stub_job_service = _StubPairsJobService()
    with patch(
        "src.bitcoin_martingale.interfaces.cli.main.build_services",
        return_value=SimpleNamespace(
            pairs_trading_service=stub_service,
            pairs_backtest_job_service=stub_job_service,
        ),
    ):
        main(
            [
                "pairs-backtest-job",
                "--tickers",
                "PETR4",
                "PETR3",
                "--portfolio-construction",
                "risk_parity",
            ]
        )

    assert "pairs_job_1" in capsys.readouterr().out
    assert stub_job_service.last_kwargs is not None
    assert stub_job_service.last_kwargs["portfolio_construction"] == "risk_parity"
    assert stub_job_service.last_batch_mode is False
