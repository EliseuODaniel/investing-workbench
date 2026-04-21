from types import SimpleNamespace
from unittest.mock import patch

from src.bitcoin_martingale.interfaces.cli.main import main

WORKSPACE_PAYLOAD = {
    "workspace_id": "research_ws_test",
    "created_at": "2026-03-24T19:00:00+00:00",
    "name": "CLI Workspace",
    "notes": "Ready for export.",
    "selected_experiment": {
        "experiment_type": "run",
        "experiment_id": "run_1",
    },
    "selection": {
        "optimization_id": None,
        "walkforward_id": None,
        "montecarlo_id": None,
        "anchor_run_id": "run_1",
    },
    "records": {
        "selected": {
            "experiment_id": "run_1",
            "experiment_type": "run",
            "created_at": "2026-03-24T18:55:00+00:00",
            "config_path": "configs/test.yaml",
            "strategy_names": ["Simple Martingale"],
            "artifact_dir": "runs/run_1",
            "status": "completed",
            "lineage": {},
            "summary": {
                "data_fingerprint": "abc123",
                "warnings": [],
            },
        },
        "optimization": None,
        "walkforward": None,
        "montecarlo": None,
        "anchor_run": {
            "experiment_id": "run_1",
            "experiment_type": "run",
            "created_at": "2026-03-24T18:55:00+00:00",
            "config_path": "configs/test.yaml",
            "strategy_names": ["Simple Martingale"],
            "artifact_dir": "runs/run_1",
            "status": "completed",
            "lineage": {},
            "summary": {
                "data_fingerprint": "abc123",
                "warnings": [],
            },
        },
    },
}


def _services():
    workspace_service = SimpleNamespace(
        list_workspaces=lambda: [WORKSPACE_PAYLOAD],
        get_workspace=lambda workspace_id: {
            **WORKSPACE_PAYLOAD,
            "workspace_id": workspace_id,
        },
    )
    return SimpleNamespace(research_workspace_service=workspace_service)


def test_research_workspaces_list_cli_prints_workspace_summary(capsys):
    with patch("src.bitcoin_martingale.interfaces.cli.main.build_services", return_value=_services()):
        main(["research-workspaces-list", "--limit", "5"])

    output = capsys.readouterr().out
    assert "research_ws_test" in output
    assert "CLI Workspace" in output
    assert "run/run_1" in output


def test_research_workspaces_export_cli_writes_markdown_and_html(tmp_path):
    markdown_path = tmp_path / "workspace.md"
    html_path = tmp_path / "workspace.html"

    with patch("src.bitcoin_martingale.interfaces.cli.main.build_services", return_value=_services()):
        main(
            [
                "research-workspaces-export",
                "--workspace-id",
                "research_ws_test",
                "--format",
                "markdown",
                "--output",
                str(markdown_path),
            ]
        )
        main(
            [
                "research-workspaces-export",
                "--workspace-id",
                "research_ws_test",
                "--format",
                "html",
                "--output",
                str(html_path),
            ]
        )

    assert markdown_path.exists()
    assert "# CLI Workspace" in markdown_path.read_text(encoding="utf-8")
    assert html_path.exists()
    assert "Research Workspace Report" in html_path.read_text(encoding="utf-8")
