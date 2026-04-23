from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from src.investing_workbench.application.allocations import AllocationPlanningService
from src.investing_workbench.interfaces.cli.main import main


def test_allocations_plan_cli_prints_plan(capsys, tmp_path):
    input_path = tmp_path / "allocation.json"
    input_path.write_text(
        json.dumps(
            {
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
            }
        ),
        encoding="utf-8",
    )

    services = SimpleNamespace(allocation_service=AllocationPlanningService())
    with patch(
        "src.investing_workbench.interfaces.cli.main.build_services",
        return_value=services,
    ):
        main(["allocations-plan", "--input", str(input_path)])

    output = capsys.readouterr().out
    assert '"asset": "SPY"' in output
    assert '"action": "sell"' in output
    assert '"action": "buy"' in output


def test_allocations_plan_cli_writes_output_file(tmp_path):
    input_path = tmp_path / "allocation.json"
    output_path = tmp_path / "plan.json"
    input_path.write_text(
        json.dumps(
            {
                "cash": 1000.0,
                "holdings": [{"asset": "SPY", "quantity": 5.0}],
                "prices": {"SPY": 100.0},
                "targets": [{"asset": "SPY", "target_weight": 0.2}],
            }
        ),
        encoding="utf-8",
    )

    services = SimpleNamespace(allocation_service=AllocationPlanningService())
    with patch(
        "src.investing_workbench.interfaces.cli.main.build_services",
        return_value=services,
    ):
        main(
            [
                "allocations-plan",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
            ]
        )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["needs_rebalance"] is True
    assert payload["actions"][0]["asset"] == "SPY"
