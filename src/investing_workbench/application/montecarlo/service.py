"""Application service for Monte Carlo robustness analysis."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import numpy as np

from src.api.models import BacktestRequest
from src.investing_workbench.application.runs import RunBacktestService
from src.investing_workbench.domain.montecarlo import (
    MonteCarloExecutionResult,
    MonteCarloMethod,
    MonteCarloRequest,
    MonteCarloSimulationSummary,
    MonteCarloStrategyResult,
)
from src.investing_workbench.infrastructure.persistence import (
    LocalMonteCarloRepository,
    LocalRunsRepository,
)


class MonteCarloSimulationService:
    """Execute Monte Carlo robustness analysis and persist its artifacts."""

    def __init__(
        self,
        run_service: RunBacktestService | None = None,
        repository: LocalMonteCarloRepository | None = None,
        runs_repository: LocalRunsRepository | None = None,
    ) -> None:
        self.run_service = run_service or RunBacktestService()
        self.repository = repository or LocalMonteCarloRepository()
        self.runs_repository = runs_repository or self.run_service.runs_repository

    def execute(self, request: MonteCarloRequest) -> MonteCarloExecutionResult:
        """Execute a Monte Carlo analysis and persist the result set."""
        config_path, source_run_id, response_payload = self._resolve_response_payload(request)
        strategy_names = request.strategy_names or list(response_payload["results"].keys())
        if not strategy_names:
            raise ValueError("No strategies available for Monte Carlo analysis")

        strategy_results: list[MonteCarloStrategyResult] = []
        warnings: list[str] = []

        for strategy_index, strategy_name in enumerate(strategy_names):
            strategy_payload = response_payload["results"].get(strategy_name)
            if strategy_payload is None:
                raise ValueError(f"Strategy '{strategy_name}' not found in source run")

            trade_pnls = self._extract_trade_pnls(strategy_payload)
            if not trade_pnls:
                warning = (
                    f"Strategy '{strategy_name}' has no closed SELL trades; Monte Carlo skipped"
                )
                warnings.append(warning)
                continue

            strategy_results.append(
                self._simulate_strategy(
                    strategy_name=strategy_name,
                    trade_pnls=trade_pnls,
                    initial_capital=self._resolve_initial_capital(
                        response_payload,
                        strategy_payload,
                    ),
                    request=request,
                    seed_offset=strategy_index,
                )
            )

        if not strategy_results:
            raise ValueError(
                "Monte Carlo analysis requires at least one strategy with closed trades"
            )

        execution_result = MonteCarloExecutionResult(
            montecarlo_id=self._build_montecarlo_id(),
            created_at=datetime.now(UTC),
            config_path=config_path,
            source_run_id=source_run_id,
            strategy_names=[result.strategy_name for result in strategy_results],
            simulation_count=request.simulation_count,
            random_seed=request.random_seed,
            method=request.method,
            ruin_threshold_pct=request.ruin_threshold_pct,
            results=strategy_results,
            warnings=warnings,
        )
        self.repository.persist_execution(execution_result)
        return execution_result

    def list_executions(self) -> list[dict[str, object]]:
        """List persisted Monte Carlo manifests."""
        return self.repository.list_executions()

    def get_manifest(self, montecarlo_id: str) -> dict[str, object]:
        """Return a persisted Monte Carlo manifest."""
        return self.repository.get_manifest(montecarlo_id)

    def get_results(self, montecarlo_id: str) -> dict[str, object]:
        """Return persisted Monte Carlo results."""
        return self.repository.get_results(montecarlo_id)

    def _resolve_response_payload(
        self,
        request: MonteCarloRequest,
    ) -> tuple[str | None, str, dict[str, Any]]:
        if request.run_id:
            manifest = self.runs_repository.get_manifest(request.run_id)
            response_payload = self.runs_repository.get_response_payload(request.run_id)
            return str(manifest.get("config_path")), request.run_id, response_payload

        response = self.run_service.run(
            BacktestRequest(
                config_path=request.config_path,
                strategies=request.strategy_names,
            )
        )
        run_info = response.run_info or {}
        source_run_id = str(run_info.get("run_id", ""))
        if not source_run_id:
            raise ValueError("Backtest execution did not return a persisted run id")
        return request.config_path, source_run_id, response.model_dump(mode="json")

    def _extract_trade_pnls(self, strategy_payload: dict[str, Any]) -> list[float]:
        trade_pnls: list[float] = []
        for trade in strategy_payload.get("trades", []):
            if trade.get("action") != "SELL":
                continue
            pnl_value = trade.get("pnl")
            if pnl_value is None:
                continue
            trade_pnls.append(float(pnl_value))
        return trade_pnls

    def _resolve_initial_capital(
        self,
        response_payload: dict[str, Any],
        strategy_payload: dict[str, Any],
    ) -> float:
        buy_hold_equity = response_payload.get("buy_hold_equity", [])
        if buy_hold_equity:
            return float(buy_hold_equity[0]["cash"])

        equity_points = strategy_payload.get("equity", [])
        if equity_points:
            return float(equity_points[0]["equity"])

        raise ValueError("Unable to infer initial capital for Monte Carlo analysis")

    def _simulate_strategy(
        self,
        *,
        strategy_name: str,
        trade_pnls: list[float],
        initial_capital: float,
        request: MonteCarloRequest,
        seed_offset: int,
    ) -> MonteCarloStrategyResult:
        rng = random.Random(request.random_seed + seed_offset)
        actual_stats = self._compute_path_stats(initial_capital, trade_pnls)
        simulations: list[MonteCarloSimulationSummary] = []

        for simulation_number in range(1, request.simulation_count + 1):
            sampled_trade_pnls = self._sample_trade_pnls(
                trade_pnls=trade_pnls,
                rng=rng,
                method=request.method,
            )
            stats = self._compute_path_stats(initial_capital, sampled_trade_pnls)
            simulations.append(
                MonteCarloSimulationSummary(
                    simulation_number=simulation_number,
                    final_equity=stats["final_equity"],
                    total_return=stats["total_return"],
                    max_drawdown=stats["max_drawdown"],
                    min_equity=stats["min_equity"],
                )
            )

        final_equities = np.array(
            [simulation.final_equity for simulation in simulations],
            dtype=float,
        )
        total_returns = np.array(
            [simulation.total_return for simulation in simulations],
            dtype=float,
        )
        max_drawdowns = np.array(
            [simulation.max_drawdown for simulation in simulations],
            dtype=float,
        )
        min_equities = np.array(
            [simulation.min_equity for simulation in simulations],
            dtype=float,
        )
        ruin_floor = initial_capital * (1 - request.ruin_threshold_pct)

        warnings = self._build_warnings(
            loss_probability=float(np.mean(final_equities < initial_capital)),
            ruin_probability=float(np.mean(min_equities <= ruin_floor)),
            worst_drawdown=float(np.min(max_drawdowns)),
        )

        return MonteCarloStrategyResult(
            strategy_name=strategy_name,
            trade_count=len(trade_pnls),
            simulation_count=request.simulation_count,
            method=request.method,
            actual_final_equity=actual_stats["final_equity"],
            actual_total_return=actual_stats["total_return"],
            actual_max_drawdown=actual_stats["max_drawdown"],
            loss_probability=float(np.mean(final_equities < initial_capital)),
            ruin_probability=float(np.mean(min_equities <= ruin_floor)),
            percentile_05_final_equity=float(np.percentile(final_equities, 5)),
            median_final_equity=float(np.percentile(final_equities, 50)),
            percentile_95_final_equity=float(np.percentile(final_equities, 95)),
            percentile_05_total_return=float(np.percentile(total_returns, 5)),
            median_total_return=float(np.percentile(total_returns, 50)),
            percentile_95_total_return=float(np.percentile(total_returns, 95)),
            percentile_05_max_drawdown=float(np.percentile(max_drawdowns, 5)),
            median_max_drawdown=float(np.percentile(max_drawdowns, 50)),
            percentile_95_max_drawdown=float(np.percentile(max_drawdowns, 95)),
            worst_final_equity=float(np.min(final_equities)),
            best_final_equity=float(np.max(final_equities)),
            warnings=warnings,
            simulations=simulations,
        )

    def _sample_trade_pnls(
        self,
        *,
        trade_pnls: list[float],
        rng: random.Random,
        method: MonteCarloMethod,
    ) -> list[float]:
        if method == MonteCarloMethod.SHUFFLE:
            sampled = trade_pnls.copy()
            rng.shuffle(sampled)
            return sampled

        return [trade_pnls[rng.randrange(len(trade_pnls))] for _ in trade_pnls]

    def _compute_path_stats(
        self,
        initial_capital: float,
        trade_pnls: list[float],
    ) -> dict[str, float]:
        equity = initial_capital
        peak = initial_capital
        min_equity = initial_capital
        max_drawdown = 0.0

        for pnl in trade_pnls:
            equity += pnl
            peak = max(peak, equity)
            min_equity = min(min_equity, equity)
            drawdown = (equity - peak) / peak if peak else 0.0
            max_drawdown = min(max_drawdown, drawdown)

        return {
            "final_equity": float(equity),
            "total_return": float((equity - initial_capital) / initial_capital),
            "max_drawdown": float(max_drawdown),
            "min_equity": float(min_equity),
        }

    def _build_warnings(
        self,
        *,
        loss_probability: float,
        ruin_probability: float,
        worst_drawdown: float,
    ) -> list[str]:
        warnings: list[str] = []
        if loss_probability >= 0.5:
            warnings.append("Loss probability is at or above 50% across simulations")
        if ruin_probability > 0:
            warnings.append("At least one simulation breached the configured ruin threshold")
        if worst_drawdown <= -0.4:
            warnings.append("Tail drawdowns reached 40% or worse in simulations")
        return warnings

    def _build_montecarlo_id(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        suffix = uuid4().hex[:8]
        return f"mc_{timestamp}_{suffix}"
