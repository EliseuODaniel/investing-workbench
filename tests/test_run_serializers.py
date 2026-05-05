from pathlib import Path

from src.investing_workbench.application.runs.serializers import build_config_info


def test_build_config_info_accepts_list_strategy_configs() -> None:
    config = build_config_info(
        Path("configs/sample.yaml"),
        {"name": "Sample", "strategies": [{"name": "Buy & Hold"}, {"name": "Momentum"}]},
    )

    assert config.name == "sample"
    assert config.display_name == "Sample"
    assert config.strategies == ["Buy & Hold", "Momentum"]


def test_build_config_info_accepts_optimization_strategy_maps() -> None:
    config = build_config_info(
        Path("configs/optimization_simple_martingale.yaml"),
        {
            "strategies": {
                "Simple Martingale": {"base_bet": {"values": [250.0, 500.0]}},
                "Risk-Cap Martingale": {"max_layers": {"start": 2, "stop": 4}},
            }
        },
    )

    assert config.name == "optimization_simple_martingale"
    assert config.display_name == "optimization_simple_martingale"
    assert config.strategies == ["Simple Martingale", "Risk-Cap Martingale"]
