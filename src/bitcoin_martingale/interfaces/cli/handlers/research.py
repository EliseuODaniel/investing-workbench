"""Optimization, walk-forward, and Monte Carlo CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from src.bitcoin_martingale.application.research_workspaces import build_workspace_report
from src.bitcoin_martingale.domain.montecarlo import MonteCarloMethod, MonteCarloRequest
from src.bitcoin_martingale.domain.walkforward import WalkForwardRequest
from src.bitcoin_martingale.interfaces.cli.core_runtime import build_optimization_request
from src.bitcoin_martingale.interfaces.cli.services import CliServices

COMMANDS = {
    "experiments-list",
    "experiments-show",
    "research-workspaces-list",
    "research-workspaces-show",
    "research-workspaces-export",
    "optimize-plan",
    "optimize-run",
    "optimizations-list",
    "optimizations-show",
    "optimizations-results",
    "walkforward-run",
    "walkforward-list",
    "walkforward-show",
    "walkforward-results",
    "montecarlo-run",
    "montecarlo-list",
    "montecarlo-show",
    "montecarlo-results",
}


def handle(args: argparse.Namespace, services: CliServices) -> None:
    """Dispatch research commands."""
    try:
        if args.command == "experiments-list":
            records = services.experiment_registry_service.list_experiments(
                experiment_type=args.experiment_type,
                strategy_name=args.strategy_name,
                limit=args.limit,
            )
            for record in records:
                strategy_count = len(cast(list[object], record.get("strategy_names", [])))
                print(
                    f"{record['experiment_id']} | {record['experiment_type']} | "
                    f"{record['created_at']} | strategies={strategy_count}"
                )
        elif args.command == "experiments-show":
            experiment_payload = services.experiment_registry_service.get_experiment(
                experiment_type=args.experiment_type,
                experiment_id=args.experiment_id,
            )
            print(json.dumps(experiment_payload, indent=2, sort_keys=True))
        elif args.command == "research-workspaces-list":
            workspaces = services.research_workspace_service.list_workspaces()[: args.limit]
            for workspace in workspaces:
                print(
                    f"{workspace['workspace_id']} | {workspace['created_at']} | "
                    f"{workspace['name']} | "
                    f"{workspace['selected_experiment']['experiment_type']}/"
                    f"{workspace['selected_experiment']['experiment_id']}"
                )
        elif args.command == "research-workspaces-show":
            workspace = services.research_workspace_service.get_workspace(args.workspace_id)
            print(json.dumps(workspace, indent=2, sort_keys=True))
        elif args.command == "research-workspaces-export":
            workspace = services.research_workspace_service.get_workspace(args.workspace_id)
            report = build_workspace_report(workspace)
            export_payload: str
            if args.format == "json":
                export_payload = json.dumps(
                    {"workspace": workspace, "report": report},
                    indent=2,
                    sort_keys=True,
                )
            elif args.format == "html":
                export_payload = cast(str, report["html"])
            else:
                export_payload = cast(str, report["markdown"])

            if args.output:
                Path(args.output).write_text(export_payload, encoding="utf-8")
            else:
                print(export_payload)
        elif args.command == "optimize-plan":
            request = build_optimization_request(args)
            plan = services.optimization_planner.build_plan(request)
            print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        elif args.command == "optimize-run":
            request = build_optimization_request(args)
            result = services.optimization_service.execute(request)
            print(json.dumps(result.results_dict(), indent=2, sort_keys=True))
        elif args.command == "optimizations-list":
            optimizations = services.optimization_service.list_optimizations()[: args.limit]
            for optimization in optimizations:
                strategy_names = cast(list[object], optimization.get("strategy_names", []))
                print(
                    f"{optimization['optimization_id']} | {optimization['created_at']} | "
                    f"objective={optimization['objective']} | "
                    "completed="
                    f"{optimization['completed_trial_count']}/{optimization['trial_count']} | "
                    f"strategies={len(strategy_names)}"
                )
        elif args.command == "optimizations-show":
            manifest = services.optimization_service.get_manifest(args.optimization_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        elif args.command == "optimizations-results":
            results = services.optimization_service.get_results(args.optimization_id)
            print(json.dumps(results, indent=2, sort_keys=True))
        elif args.command == "walkforward-run":
            walkforward_request = WalkForwardRequest(
                config_path=args.config,
                strategy_names=args.strategies,
                train_window_days=args.train_days,
                test_window_days=args.test_days,
                step_days=args.step_days,
            )
            walkforward_results = services.walkforward_service.execute(walkforward_request)
            print(json.dumps(walkforward_results.results_dict(), indent=2, sort_keys=True))
        elif args.command == "walkforward-list":
            executions = services.walkforward_service.list_executions()[: args.limit]
            for execution in executions:
                strategy_names = cast(list[object], execution.get("strategy_names", []))
                print(
                    f"{execution['walkforward_id']} | {execution['created_at']} | "
                    f"windows={execution['window_count']} | "
                    f"strategies={len(strategy_names)}"
                )
        elif args.command == "walkforward-show":
            manifest = services.walkforward_service.get_manifest(args.walkforward_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        elif args.command == "walkforward-results":
            results = services.walkforward_service.get_results(args.walkforward_id)
            print(json.dumps(results, indent=2, sort_keys=True))
        elif args.command == "montecarlo-run":
            montecarlo_request = MonteCarloRequest(
                config_path=args.config,
                run_id=args.run_id,
                strategy_names=args.strategies,
                simulation_count=args.simulations,
                random_seed=args.seed,
                method=MonteCarloMethod(args.method),
                ruin_threshold_pct=args.ruin_threshold_pct,
            )
            montecarlo_results = services.montecarlo_service.execute(montecarlo_request)
            print(json.dumps(montecarlo_results.results_dict(), indent=2, sort_keys=True))
        elif args.command == "montecarlo-list":
            executions = services.montecarlo_service.list_executions()[: args.limit]
            for execution in executions:
                strategy_names = cast(list[object], execution.get("strategy_names", []))
                print(
                    f"{execution['montecarlo_id']} | {execution['created_at']} | "
                    f"simulations={execution['simulation_count']} | "
                    f"strategies={len(strategy_names)}"
                )
        elif args.command == "montecarlo-show":
            manifest = services.montecarlo_service.get_manifest(args.montecarlo_id)
            print(json.dumps(manifest, indent=2, sort_keys=True))
        elif args.command == "montecarlo-results":
            results = services.montecarlo_service.get_results(args.montecarlo_id)
            print(json.dumps(results, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"Failed to process research command: {exc}")
        sys.exit(1)
