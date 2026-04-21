from src.bitcoin_martingale.application.research_workspaces import build_workspace_report


def test_build_workspace_report_includes_key_sections():
    report = build_workspace_report(
        {
            "workspace_id": "research_ws_1",
            "created_at": "2026-03-24T18:00:00+00:00",
            "name": "Martingale Review",
            "notes": "Cross-check before sharing.",
            "selected_experiment": {
                "experiment_type": "optimization",
                "experiment_id": "opt_1",
            },
            "selection": {
                "optimization_id": "opt_1",
                "walkforward_id": "wf_1",
                "montecarlo_id": None,
                "anchor_run_id": "run_1",
            },
            "records": {
                "selected": {
                    "experiment_id": "opt_1",
                    "experiment_type": "optimization",
                    "created_at": "2026-03-24T18:00:00+00:00",
                    "config_path": "configs/test.yaml",
                    "strategy_names": ["Simple Martingale"],
                    "artifact_dir": "optimizations/opt_1",
                    "status": "completed",
                    "lineage": {"best_run_id": "run_1"},
                    "summary": {
                        "objective": "sharpe_ratio",
                        "warnings": ["Trial plan was truncated"],
                    },
                },
                "optimization": {
                    "experiment_id": "opt_1",
                    "experiment_type": "optimization",
                    "created_at": "2026-03-24T18:00:00+00:00",
                    "config_path": "configs/test.yaml",
                    "strategy_names": ["Simple Martingale"],
                    "artifact_dir": "optimizations/opt_1",
                    "status": "completed",
                    "lineage": {"best_run_id": "run_1"},
                    "summary": {
                        "objective": "sharpe_ratio",
                        "completed_trial_count": 16,
                        "trial_count": 32,
                        "warnings": ["Trial plan was truncated"],
                    },
                },
                "walkforward": {
                    "experiment_id": "wf_1",
                    "experiment_type": "walkforward",
                    "created_at": "2026-03-24T18:10:00+00:00",
                    "config_path": "configs/test.yaml",
                    "strategy_names": ["Simple Martingale"],
                    "artifact_dir": "walkforward/wf_1",
                    "status": "completed",
                    "lineage": {},
                    "summary": {
                        "window_count": 4,
                        "train_window_days": 120,
                        "test_window_days": 30,
                        "step_days": 30,
                        "warnings": [],
                    },
                },
                "montecarlo": None,
                "anchor_run": {
                    "experiment_id": "run_1",
                    "experiment_type": "run",
                    "created_at": "2026-03-24T17:50:00+00:00",
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
    )

    assert report["executive_summary"].startswith('Workspace "Martingale Review"')
    assert any(metric["label"] == "Optimization Objective" for metric in report["key_metrics"])
    assert "## Key Metrics" in report["markdown"]
    assert "Research Workspace Report" in report["html"]
