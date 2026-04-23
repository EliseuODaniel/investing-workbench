"""Application services for reproducible one-off scenarios."""

from __future__ import annotations

from argparse import Namespace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .wege3_regra_a import run_scenario


class Wege3RegraAScenarioService:
    """Run the dedicated WEGE3 Regra A scenario through the existing backtest app."""

    def __init__(
        self,
        *,
        reports_dir: str | Path = "reports",
        cache_path: str = "data/wege3_sa.parquet",
        selic_path: str = "data/selic_daily.csv",
    ) -> None:
        self.reports_dir = Path(reports_dir)
        self.cache_path = cache_path
        self.selic_path = selic_path

    def run(
        self,
        *,
        start_date: str = "2021-01-01",
        end_date: str | None = None,
        force_download: bool = False,
    ) -> dict[str, Any]:
        """Execute the WEGE3 Regra A scenario and return a UI-friendly payload."""
        generated_at = datetime.now(UTC)
        run_stamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
        summary_output = self.reports_dir / f"wege3_regra_a_{run_stamp}_summary.json"
        trades_output = self.reports_dir / f"wege3_regra_a_{run_stamp}_trades.csv"

        args = Namespace(
            start_date=start_date,
            end_date=end_date,
            cache_path=self.cache_path,
            selic_path=self.selic_path,
            force_download=force_download,
            summary_output=str(summary_output),
            trades_output=str(trades_output),
        )
        summary = run_scenario(args)
        trades = pd.read_csv(trades_output)

        resolved_end_date = summary["dataset"]["end_session"]
        reproduction_command = (
            "./.venv/bin/python -m src.investing_workbench.application.scenarios.wege3_regra_a "
            f"--start-date {start_date} "
            f"--end-date {resolved_end_date} "
            f"{'--force-download ' if force_download else ''}"
            f"--summary-output {summary_output} "
            f"--trades-output {trades_output}"
        ).strip()

        return {
            "scenario_id": "wege3_regra_a",
            "scenario_label": "WEGE3 Regra A",
            "generated_at": generated_at,
            "request": {
                "start_date": start_date,
                "end_date": end_date,
                "force_download": force_download,
            },
            "assumptions": summary["assumptions"],
            "dataset": summary["dataset"],
            "result": summary["result"],
            "statistics": summary["statistics"],
            "benchmarks": summary["benchmarks"],
            "audit": summary["audit"],
            "comparison_variants": summary.get("comparison_variants", []),
            "best_strategy": summary.get("best_strategy", {}),
            "parameter_search": summary.get("parameter_search", {}),
            "strategy_context": summary.get("strategy_context", {}),
            "comparison_chart": summary.get("comparison_chart", {}),
            "trades": trades.to_dict(orient="records"),
            "artifacts": {
                "summary_output_path": str(summary_output),
                "trades_output_path": str(trades_output),
                "comparison_output_path": summary.get("audit", {}).get("comparison_csv_path"),
                "comparison_trades_output_path": summary.get("audit", {}).get(
                    "comparison_trades_csv_path"
                ),
                "search_output_path": summary.get("audit", {}).get("search_csv_path"),
            },
            "reproduction_command": reproduction_command,
        }
