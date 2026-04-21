import json
from pathlib import Path

from src.bitcoin_martingale.application.runs.service import RunBacktestService
from src.bitcoin_martingale.infrastructure.persistence import LocalRunsRepository


def _write_run(
    base_dir: Path,
    *,
    run_id: str,
    monthly_rates: list[float],
    apply_cash_yield: bool = True,
    use_real_selic: bool = True,
) -> None:
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "created_at": "2026-04-21T16:00:00Z",
                "config_path": "configs/martingale.yaml",
                "artifact_dir": str(run_dir),
                "strategy_names": ["Fixed Martingale"],
                "benchmark_names": ["Buy & Hold"],
                "request_payload": {},
                "data_info": {},
                "config_snapshot_path": str(run_dir / "config_resolved.json"),
                "data_profile_path": str(run_dir / "data_profile.json"),
                "data_fingerprint": "abc123",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "config_resolved.json").write_text(
        json.dumps(
            {
                "backtest": {
                    "apply_cash_yield": apply_cash_yield,
                    "use_real_selic": use_real_selic,
                    "initial_capital": 10000,
                }
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "data_profile.json").write_text("{}", encoding="utf-8")
    (run_dir / "response.json").write_text(
        json.dumps(
            {
                "results": {
                    "Fixed Martingale": {
                        "strategy_name": "Fixed Martingale",
                        "equity": [],
                        "trades": [],
                        "metrics": {
                            "total_return": 10.0,
                            "cagr": 2.0,
                            "sharpe_ratio": 1.0,
                            "sortino_ratio": 1.0,
                            "max_drawdown": -0.1,
                            "hit_rate": 0.5,
                            "profit_factor": 1.1,
                            "total_trades": 1,
                            "avg_trade_pnl": 100,
                            "volatility": 0.2,
                            "total_interest_earned": 1000,
                            "total_fees_paid": 0,
                            "total_dividends_received": 0,
                            "selic_rates_used": [
                                {"date": f"2020-{index + 1:02d}", "rate": rate}
                                for index, rate in enumerate(monthly_rates)
                            ],
                        },
                        "start_price": 1,
                        "end_price": 2,
                        "execution_log": [],
                        "execution_summary": {},
                        "warnings": [],
                    }
                },
                "buy_hold_equity": [],
                "benchmarks": {},
                "run_info": {"run_id": run_id},
                "data_info": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )


def test_list_runs_marks_legacy_invalid_selic_runs(tmp_path: Path) -> None:
    _write_run(tmp_path, run_id="run_legacy", monthly_rates=[0.044, 0.0415, 0.0365])
    service = RunBacktestService(runs_repository=LocalRunsRepository(base_dir=tmp_path))

    runs = service.list_runs()

    assert runs[0]["run_quality"]["status"] == "legacy_invalid"
    assert runs[0]["run_quality"]["code"] == "selic_monthly_cache_bug"


def test_get_run_response_injects_quality_warning_for_legacy_run(tmp_path: Path) -> None:
    _write_run(tmp_path, run_id="run_legacy", monthly_rates=[0.044, 0.0415, 0.0365])
    service = RunBacktestService(runs_repository=LocalRunsRepository(base_dir=tmp_path))

    payload = service.get_run_response("run_legacy")

    assert payload["run_quality"]["status"] == "legacy_invalid"
    assert "SELIC mensal real" in payload["warnings"][0]


def test_valid_runs_remain_unflagged(tmp_path: Path) -> None:
    _write_run(tmp_path, run_id="run_valid", monthly_rates=[0.0037, 0.0029, 0.0034])
    service = RunBacktestService(runs_repository=LocalRunsRepository(base_dir=tmp_path))

    runs = service.list_runs()
    payload = service.get_run_response("run_valid")

    assert "run_quality" not in runs[0]
    assert "run_quality" not in payload
