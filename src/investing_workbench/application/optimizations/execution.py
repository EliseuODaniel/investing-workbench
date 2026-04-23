"""Application service for executing persisted optimization runs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.investing_workbench.application.optimizations.service import OptimizationPlanningService
from src.investing_workbench.application.runs import RunBacktestService
from src.investing_workbench.domain.optimizations import (
    OptimizationExecutionResult,
    OptimizationRequest,
    OptimizationTrialResult,
)
from src.investing_workbench.infrastructure.persistence import LocalOptimizationsRepository


class OptimizationExecutionService:
    """Execute planned trials and persist ranked optimization results."""

    def __init__(
        self,
        planner: OptimizationPlanningService | None = None,
        run_service: RunBacktestService | None = None,
        repository: LocalOptimizationsRepository | None = None,
    ) -> None:
        self.planner = planner or OptimizationPlanningService()
        self.run_service = run_service or RunBacktestService()
        self.repository = repository or LocalOptimizationsRepository()

    def execute(self, request: OptimizationRequest) -> OptimizationExecutionResult:
        """Execute a planned optimization and persist its manifest and results."""
        plan = self.planner.build_plan(request)
        optimization_id = self._build_optimization_id()
        trial_results: list[OptimizationTrialResult] = []

        for trial in plan.trials:
            request_payload = {
                "optimization_id": optimization_id,
                "trial_id": trial.trial_id,
                "objective": request.objective,
                "direction": request.direction.value,
            }
            try:
                response = self.run_service.run_trial(
                    config_path=request.config_path,
                    strategy_name=trial.strategy_name,
                    parameter_overrides=trial.parameters,
                    request_payload=request_payload,
                )
                strategy_result = response.results[trial.strategy_name]
                metrics_payload = strategy_result.metrics.model_dump()
                objective_value = self._extract_objective(metrics_payload, request.objective)
                run_info = response.run_info or {}
                trial_results.append(
                    OptimizationTrialResult(
                        trial_id=trial.trial_id,
                        strategy_name=trial.strategy_name,
                        parameters=trial.parameters,
                        run_id=str(run_info.get("run_id")) if run_info.get("run_id") else None,
                        objective=request.objective,
                        objective_value=objective_value,
                        metrics=metrics_payload,
                    )
                )
            except Exception as exc:
                trial_results.append(
                    OptimizationTrialResult(
                        trial_id=trial.trial_id,
                        strategy_name=trial.strategy_name,
                        parameters=trial.parameters,
                        run_id=None,
                        objective=request.objective,
                        objective_value=None,
                        status="failed",
                        error=str(exc),
                    )
                )

        execution_result = OptimizationExecutionResult(
            optimization_id=optimization_id,
            created_at=datetime.now(UTC),
            config_path=request.config_path,
            objective=request.objective,
            direction=request.direction,
            mode=request.mode,
            random_seed=request.random_seed,
            strategy_names=plan.strategy_names,
            trial_count=plan.trial_count,
            truncated=plan.truncated,
            warnings=plan.warnings,
            results=trial_results,
        )
        self.repository.persist_execution(execution_result)
        return execution_result

    def list_optimizations(self) -> list[dict[str, object]]:
        """List persisted optimization manifests."""
        return self.repository.list_optimizations()

    def get_manifest(self, optimization_id: str) -> dict[str, object]:
        """Return a persisted optimization manifest."""
        return self.repository.get_manifest(optimization_id)

    def get_results(self, optimization_id: str) -> dict[str, object]:
        """Return persisted optimization results."""
        return self.repository.get_results(optimization_id)

    def _build_optimization_id(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        suffix = uuid4().hex[:8]
        return f"opt_{timestamp}_{suffix}"

    def _extract_objective(self, metrics_payload: dict[str, float], objective: str) -> float:
        if objective not in metrics_payload:
            raise ValueError(f"Objective '{objective}' not found in strategy metrics")
        return float(metrics_payload[objective])
