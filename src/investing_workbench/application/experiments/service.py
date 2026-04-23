"""Unified experiment registry across persisted research workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from src.investing_workbench.application.experiments.dto import (
    ExperimentDetail,
    ExperimentLineage,
    ExperimentRecord,
    ExperimentRelation,
)
from src.investing_workbench.infrastructure.persistence import (
    LocalMonteCarloRepository,
    LocalOptimizationsRepository,
    LocalPairsBacktestsRepository,
    LocalRunsRepository,
    LocalWalkForwardRepository,
)


class ExperimentRegistryService:
    """Aggregate persisted workflows into a shared experiment registry view."""

    def __init__(
        self,
        runs_repository: LocalRunsRepository | None = None,
        optimizations_repository: LocalOptimizationsRepository | None = None,
        walkforward_repository: LocalWalkForwardRepository | None = None,
        montecarlo_repository: LocalMonteCarloRepository | None = None,
        pairs_repository: LocalPairsBacktestsRepository | None = None,
    ) -> None:
        self.runs_repository = runs_repository or LocalRunsRepository()
        self.optimizations_repository = optimizations_repository or LocalOptimizationsRepository()
        self.walkforward_repository = walkforward_repository or LocalWalkForwardRepository()
        self.montecarlo_repository = montecarlo_repository or LocalMonteCarloRepository()
        self.pairs_repository = pairs_repository or LocalPairsBacktestsRepository()

    def list_experiments(
        self,
        *,
        experiment_type: str | None = None,
        strategy_name: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, object]]:
        """Return normalized registry records ordered from newest to oldest."""
        records = [
            *self._collect_runs(),
            *self._collect_optimizations(),
            *self._collect_walkforward(),
            *self._collect_montecarlo(),
            *self._collect_pairs_backtests(),
        ]
        if experiment_type:
            records = [record for record in records if record.experiment_type == experiment_type]
        if strategy_name:
            records = [record for record in records if strategy_name in record.strategy_names]
        records.sort(key=lambda record: record.created_at, reverse=True)
        if limit is not None:
            records = records[:limit]
        return [record.to_dict() for record in records]

    def get_experiment(
        self,
        *,
        experiment_type: str,
        experiment_id: str,
    ) -> dict[str, object]:
        """Return a normalized registry record together with its persisted manifest."""
        all_records = self._all_records()
        record = self._get_record(
            experiment_type=experiment_type,
            experiment_id=experiment_id,
            records=all_records,
        )
        manifest = self._load_manifest(experiment_type=experiment_type, experiment_id=experiment_id)
        related_experiments = self._build_related_experiments(
            target_record=record,
            records=all_records,
        )
        return ExperimentDetail(
            record=record,
            manifest=manifest,
            related_experiments=related_experiments,
        ).to_dict()

    def _all_records(self) -> list[ExperimentRecord]:
        return [
            *self._collect_runs(),
            *self._collect_optimizations(),
            *self._collect_walkforward(),
            *self._collect_montecarlo(),
            *self._collect_pairs_backtests(),
        ]

    def _collect_runs(self) -> list[ExperimentRecord]:
        return [
            ExperimentRecord(
                experiment_id=cast(str, manifest["run_id"]),
                experiment_type="run",
                created_at=str(manifest.get("created_at", "")),
                config_path=self._optional_str(manifest.get("config_path")),
                strategy_names=self._strategy_names(manifest),
                artifact_dir=self._artifact_dir(self.runs_repository.base_dir, manifest, "run_id"),
                summary={
                    "benchmark_names": cast(list[str], manifest.get("benchmark_names", [])),
                    "data_fingerprint": self._optional_str(manifest.get("data_fingerprint")),
                    "warnings": [],
                },
            )
            for manifest in self.runs_repository.list_runs()
        ]

    def _get_record(
        self,
        *,
        experiment_type: str,
        experiment_id: str,
        records: list[ExperimentRecord] | None = None,
    ) -> ExperimentRecord:
        for record in records or self._records_for_type(experiment_type):
            if record.experiment_id == experiment_id:
                return record
        raise FileNotFoundError(
            f"Experiment not found for type '{experiment_type}': {experiment_id}"
        )

    def _build_related_experiments(
        self,
        *,
        target_record: ExperimentRecord,
        records: list[ExperimentRecord],
    ) -> list[ExperimentRelation]:
        relations: list[ExperimentRelation] = []
        for candidate in records:
            if (
                candidate.experiment_id == target_record.experiment_id
                and candidate.experiment_type == target_record.experiment_type
            ):
                continue

            relationship = self._resolve_relationship(
                target_record=target_record,
                candidate=candidate,
            )
            if relationship:
                relations.append(
                    ExperimentRelation(
                        relationship=relationship,
                        record=candidate,
                    )
                )

        relations.sort(key=lambda relation: relation.record.created_at, reverse=True)
        return relations

    def _resolve_relationship(
        self,
        *,
        target_record: ExperimentRecord,
        candidate: ExperimentRecord,
    ) -> str | None:
        target_lineage = target_record.lineage
        candidate_lineage = candidate.lineage

        if (
            target_lineage.best_run_id == candidate.experiment_id
            and candidate.experiment_type == "run"
        ):
            return "best_run"
        if (
            target_lineage.source_run_id == candidate.experiment_id
            and candidate.experiment_type == "run"
        ):
            return "source_run"
        if (
            target_lineage.parent_optimization_id == candidate.experiment_id
            and candidate.experiment_type == "optimization"
        ):
            return "parent_optimization"
        if (
            candidate_lineage.best_run_id == target_record.experiment_id
            and target_record.experiment_type == "run"
        ):
            return "best_run_for_optimization"
        if (
            candidate_lineage.source_run_id == target_record.experiment_id
            and target_record.experiment_type == "run"
        ):
            return "source_run_for_montecarlo"
        if (
            candidate_lineage.parent_optimization_id == target_record.experiment_id
            and target_record.experiment_type == "optimization"
        ):
            return "child_of_optimization"
        return None

    def _load_manifest(self, *, experiment_type: str, experiment_id: str) -> dict[str, object]:
        if experiment_type == "run":
            return self.runs_repository.get_manifest(experiment_id)
        if experiment_type == "optimization":
            return self.optimizations_repository.get_manifest(experiment_id)
        if experiment_type == "walkforward":
            return self.walkforward_repository.get_manifest(experiment_id)
        if experiment_type == "montecarlo":
            return self.montecarlo_repository.get_manifest(experiment_id)
        if experiment_type == "pairs_backtest":
            return self.pairs_repository.get_manifest(experiment_id)
        raise ValueError(f"Unsupported experiment type: {experiment_type}")

    def _records_for_type(self, experiment_type: str) -> list[ExperimentRecord]:
        if experiment_type == "run":
            return self._collect_runs()
        if experiment_type == "optimization":
            return self._collect_optimizations()
        if experiment_type == "walkforward":
            return self._collect_walkforward()
        if experiment_type == "montecarlo":
            return self._collect_montecarlo()
        if experiment_type == "pairs_backtest":
            return self._collect_pairs_backtests()
        raise ValueError(f"Unsupported experiment type: {experiment_type}")

    def _collect_optimizations(self) -> list[ExperimentRecord]:
        return [
            ExperimentRecord(
                experiment_id=cast(str, manifest["optimization_id"]),
                experiment_type="optimization",
                created_at=str(manifest.get("created_at", "")),
                config_path=self._optional_str(manifest.get("config_path")),
                strategy_names=self._strategy_names(manifest),
                artifact_dir=self._artifact_dir(
                    self.optimizations_repository.base_dir,
                    manifest,
                    "optimization_id",
                ),
                lineage=ExperimentLineage(
                    best_run_id=self._optional_str(manifest.get("best_run_id")),
                ),
                summary={
                    "objective": self._optional_str(manifest.get("objective")),
                    "direction": self._optional_str(manifest.get("direction")),
                    "trial_count": manifest.get("trial_count"),
                    "completed_trial_count": manifest.get("completed_trial_count"),
                    "warnings": cast(list[str], manifest.get("warnings", [])),
                },
            )
            for manifest in self.optimizations_repository.list_optimizations()
        ]

    def _collect_walkforward(self) -> list[ExperimentRecord]:
        return [
            ExperimentRecord(
                experiment_id=cast(str, manifest["walkforward_id"]),
                experiment_type="walkforward",
                created_at=str(manifest.get("created_at", "")),
                config_path=self._optional_str(manifest.get("config_path")),
                strategy_names=self._strategy_names(manifest),
                artifact_dir=self._artifact_dir(
                    self.walkforward_repository.base_dir,
                    manifest,
                    "walkforward_id",
                ),
                summary={
                    "train_window_days": manifest.get("train_window_days"),
                    "test_window_days": manifest.get("test_window_days"),
                    "step_days": manifest.get("step_days"),
                    "window_count": manifest.get("window_count"),
                    "warnings": [],
                },
            )
            for manifest in self.walkforward_repository.list_executions()
        ]

    def _collect_montecarlo(self) -> list[ExperimentRecord]:
        return [
            ExperimentRecord(
                experiment_id=cast(str, manifest["montecarlo_id"]),
                experiment_type="montecarlo",
                created_at=str(manifest.get("created_at", "")),
                config_path=self._optional_str(manifest.get("config_path")),
                strategy_names=self._strategy_names(manifest),
                artifact_dir=self._artifact_dir(
                    self.montecarlo_repository.base_dir,
                    manifest,
                    "montecarlo_id",
                ),
                lineage=ExperimentLineage(
                    source_run_id=self._optional_str(manifest.get("source_run_id")),
                ),
                summary={
                    "simulation_count": manifest.get("simulation_count"),
                    "method": self._optional_str(manifest.get("method")),
                    "ruin_threshold_pct": manifest.get("ruin_threshold_pct"),
                    "warnings": cast(list[str], manifest.get("warnings", [])),
                },
            )
            for manifest in self.montecarlo_repository.list_executions()
        ]

    def _collect_pairs_backtests(self) -> list[ExperimentRecord]:
        return [
            ExperimentRecord(
                experiment_id=cast(str, manifest["pairs_backtest_id"]),
                experiment_type="pairs_backtest",
                created_at=str(manifest.get("created_at", "")),
                config_path=None,
                strategy_names=["pairs_trading"],
                artifact_dir=self._artifact_dir(
                    self.pairs_repository.base_dir,
                    manifest,
                    "pairs_backtest_id",
                ),
                summary={
                    "preset_id": self._optional_str(manifest.get("preset_id")),
                    "preset_label": self._optional_str(manifest.get("preset_label")),
                    "scenario_count": manifest.get("scenario_count"),
                    "candidate_pair_count": manifest.get("candidate_pair_count"),
                    "reconstitution_segment_count": manifest.get("reconstitution_segment_count"),
                    "benchmark_ids": cast(list[str], manifest.get("benchmark_ids", [])),
                    "warnings": cast(list[str], manifest.get("warnings", [])),
                },
            )
            for manifest in self.pairs_repository.list_backtests()
        ]

    def _artifact_dir(
        self,
        base_dir: Path,
        manifest: dict[str, Any],
        id_key: str,
    ) -> str:
        return str(base_dir / str(manifest[id_key]))

    def _strategy_names(self, manifest: dict[str, Any]) -> list[str]:
        return cast(list[str], manifest.get("strategy_names", []))

    def _optional_str(self, value: object) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
