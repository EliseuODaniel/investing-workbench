from __future__ import annotations

from src.api.models import BacktestRequest
from src.bitcoin_martingale.application.runs.dto import BacktestRunInput
from src.bitcoin_martingale.application.runs.request_adapter import to_backtest_run_input


def test_request_adapter_normalizes_api_model_payload() -> None:
    payload = BacktestRequest(
        config_path="configs/test.yaml",
        strategies=["Simple Martingale"],
        initial_capital=25000,
        force_download=True,
        fee_rate=0.0003,
        buy_slippage=0.0005,
        max_volume_participation=0.1,
        benchmarks=["SPY"],
        include_selic_benchmark=True,
    )

    request = to_backtest_run_input(payload)

    assert request == BacktestRunInput(
        config_path="configs/test.yaml",
        strategies=["Simple Martingale"],
        initial_capital=25000.0,
        force_download=True,
        fee_rate=0.0003,
        buy_slippage=0.0005,
        max_volume_participation=0.1,
        benchmarks=["SPY"],
        include_selic_benchmark=True,
        include_buy_hold_benchmark=True,
    )


def test_request_adapter_normalizes_mapping_payload() -> None:
    request = to_backtest_run_input(
        {
            "config_path": "configs/alt.yaml",
            "max_layers": 6,
            "apply_cash_yield": True,
            "allow_partial_fills": False,
            "include_buy_hold_benchmark": False,
        }
    )

    assert request.config_path == "configs/alt.yaml"
    assert request.max_layers == 6
    assert request.apply_cash_yield is True
    assert request.allow_partial_fills is False
    assert request.include_buy_hold_benchmark is False
