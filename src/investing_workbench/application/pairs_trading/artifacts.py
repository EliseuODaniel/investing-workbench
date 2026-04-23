"""Persistence helpers for B3 pairs-trading artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.investing_workbench.infrastructure.persistence.pairs_repo import (
    LocalPairsBacktestsRepository,
)

from .contracts import PairsContext
from .dto import PairsBacktestManifest, PairsBacktestResults


class PairsArtifactsService:
    """Persist and reload normalized pairs-trading manifests and results."""

    def __init__(self, repository: LocalPairsBacktestsRepository) -> None:
        self.repository = repository

    def list_backtests(self) -> list[dict[str, Any]]:
        """List persisted pairs-trading manifests."""
        return [
            PairsBacktestManifest.from_payload(manifest).to_dict()
            for manifest in self.repository.list_backtests()
        ]

    def get_manifest(self, backtest_id: str) -> dict[str, Any]:
        """Load one persisted pairs-trading manifest."""
        return PairsBacktestManifest.from_payload(
            self.repository.get_manifest(backtest_id)
        ).to_dict()

    def get_results(self, backtest_id: str) -> dict[str, Any]:
        """Load one persisted pairs-trading result set."""
        return PairsBacktestResults.from_payload(self.repository.get_results(backtest_id)).to_dict()

    def persist_backtest(
        self,
        *,
        backtest_id: str,
        context: PairsContext,
        start_date: str,
        end_date: str,
        batch_mode: bool,
        benchmark_ids: list[str],
        benchmark_series: list[dict[str, Any]],
        scenario_results: list[dict[str, Any]],
        candidate_pairs: list[dict[str, Any]],
        robustness_report: dict[str, Any],
        warnings: list[str],
        reconstitution_plan: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Persist one normalized pairs manifest plus results payload."""
        created_at = datetime.now(UTC).isoformat()
        manifest = PairsBacktestManifest(
            pairs_backtest_id=backtest_id,
            created_at=created_at,
            preset_id=(
                str(context.preset_metadata.get("preset_id"))
                if context.preset_metadata
                else "custom"
            ),
            preset_label=(
                str(context.preset_metadata.get("label")) if context.preset_metadata else "Custom"
            ),
            universe_as_of_date=context.resolved_as_of_date,
            start_date=start_date,
            end_date=end_date,
            requested_tickers=context.requested_tickers,
            available_tickers=sorted(context.data_by_ticker),
            eligible_tickers=[row["ticker"] for row in context.eligible_records],
            scenario_count=len(scenario_results),
            batch_mode=batch_mode,
            benchmark_ids=benchmark_ids,
            candidate_pair_count=len(candidate_pairs),
            reconstitution_segment_count=len(reconstitution_plan),
            warnings=warnings,
        ).to_dict()
        results = PairsBacktestResults(
            pairs_backtest_id=backtest_id,
            created_at=created_at,
            manifest=manifest,
            preset=context.preset_metadata,
            universe={
                "requested_tickers": context.requested_tickers,
                "resolved_as_of_date": context.resolved_as_of_date,
                "reconstitution_plan": reconstitution_plan,
                "quality_report": context.quality_report,
                "assets": context.universe_records,
                "eligible_assets": context.eligible_records,
                "unavailable_tickers": context.unavailable_tickers,
            },
            candidate_pairs=candidate_pairs,
            benchmarks=benchmark_series,
            scenarios=scenario_results,
            robustness_report=robustness_report,
            warnings=warnings,
        ).to_dict()
        self.repository.persist_execution(
            backtest_id=backtest_id,
            manifest=manifest,
            results=results,
        )
        return results
