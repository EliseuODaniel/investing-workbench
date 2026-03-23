"""Application service for walk-forward and out-of-sample validation."""

from __future__ import annotations

import io
import logging
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd

from src.bitcoin_martingale.domain.walkforward import (
    WalkForwardExecutionResult,
    WalkForwardRequest,
    WalkForwardWindowResult,
)
from src.bitcoin_martingale.infrastructure.persistence import LocalWalkForwardRepository
from src.config import AppConfig, StrategyConfig, load_strategy
from src.data import get_data
from src.engine import BacktestEngine
from src.metrics import calculate_metrics

logger = logging.getLogger(__name__)


class WalkForwardValidationService:
    """Execute persisted walk-forward validation over rolling train/test windows."""

    def __init__(self, repository: LocalWalkForwardRepository | None = None) -> None:
        self.repository = repository or LocalWalkForwardRepository()

    def execute(self, request: WalkForwardRequest) -> WalkForwardExecutionResult:
        """Run walk-forward validation and persist the results."""
        config = AppConfig.from_file(request.config_path)
        strategies = self._resolve_strategies(config, request.strategy_names)
        data = self._load_market_data(config)
        windows = self._build_windows(
            index=data.index,
            train_window_days=request.train_window_days,
            test_window_days=request.test_window_days,
            step_days=request.step_days,
        )
        if not windows:
            raise ValueError("Not enough data to build any train/test windows")

        results: list[WalkForwardWindowResult] = []

        for window_number, window in enumerate(windows, start=1):
            train_data = data.iloc[window["train_start"] : window["train_end"]].copy()
            test_data = data.iloc[window["test_start"] : window["test_end"]].copy()

            for strategy_config in strategies:
                train_metrics = self._evaluate_strategy(config, strategy_config, train_data)
                test_metrics = self._evaluate_strategy(config, strategy_config, test_data)
                results.append(
                    WalkForwardWindowResult(
                        window_id=f"window_{window_number:03d}",
                        strategy_name=strategy_config.name,
                        train_start=train_data.index[0].isoformat(),
                        train_end=train_data.index[-1].isoformat(),
                        test_start=test_data.index[0].isoformat(),
                        test_end=test_data.index[-1].isoformat(),
                        train_metrics=train_metrics,
                        test_metrics=test_metrics,
                    )
                )

        execution_result = WalkForwardExecutionResult(
            walkforward_id=self._build_walkforward_id(),
            created_at=datetime.now(UTC),
            config_path=request.config_path,
            strategy_names=[strategy.name for strategy in strategies],
            train_window_days=request.train_window_days,
            test_window_days=request.test_window_days,
            step_days=request.step_days,
            window_count=len(windows),
            results=results,
        )
        self.repository.persist_execution(execution_result)
        return execution_result

    def list_executions(self) -> list[dict[str, object]]:
        """List persisted walk-forward manifests."""
        return self.repository.list_executions()

    def get_manifest(self, walkforward_id: str) -> dict[str, object]:
        """Return a persisted walk-forward manifest."""
        return self.repository.get_manifest(walkforward_id)

    def get_results(self, walkforward_id: str) -> dict[str, object]:
        """Return persisted walk-forward results."""
        return self.repository.get_results(walkforward_id)

    def _resolve_strategies(
        self,
        config: AppConfig,
        requested_strategy_names: list[str] | None,
    ) -> list[StrategyConfig]:
        strategies = config.strategies
        if requested_strategy_names:
            strategies = [
                strategy
                for strategy in strategies
                if strategy.name in requested_strategy_names
            ]

        if not strategies:
            raise ValueError("No strategies available for walk-forward validation")

        return strategies

    def _load_market_data(self, config: AppConfig) -> pd.DataFrame:
        stdout_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer):
            data = get_data(
                start=config.backtest.start_date,
                end=config.backtest.end_date,
                cache_path=config.backtest.cache_path,
            )
        for line in stdout_buffer.getvalue().splitlines():
            logger.info("walkforward-market-data: %s", line)
        return data

    def _evaluate_strategy(
        self,
        config: AppConfig,
        strategy_config: StrategyConfig,
        data: pd.DataFrame,
    ) -> dict[str, float | int]:
        strategy = load_strategy(
            StrategyConfig(
                name=strategy_config.name,
                class_path=strategy_config.class_path,
                parameters=deepcopy(strategy_config.parameters),
            )
        )
        engine = BacktestEngine(
            initial_cash=config.backtest.initial_capital,
            apply_cash_yield=config.backtest.apply_cash_yield,
            selic_rate_annual=config.backtest.selic_rate_annual,
            yield_frequency=config.backtest.yield_frequency,
            use_real_selic=config.backtest.use_real_selic,
            selic_path=config.backtest.selic_path,
            selic_fallback_rate=config.backtest.selic_fallback_rate,
        )
        result = engine.run(data, strategy)
        metrics = calculate_metrics(
            result["equity"]["equity"],
            result["trades"],
            config.backtest.initial_capital,
            total_interest_earned=result.get("total_interest_earned", 0.0),
        )
        return {
            "total_return": float(metrics["total_return"]),
            "cagr": float(metrics["cagr"]),
            "sharpe_ratio": float(metrics["sharpe_ratio"]),
            "max_drawdown": float(metrics["max_drawdown"]),
            "volatility": float(metrics["volatility"]),
            "total_trades": int(metrics["total_trades"]),
        }

    def _build_windows(
        self,
        *,
        index: pd.Index,
        train_window_days: int,
        test_window_days: int,
        step_days: int,
    ) -> list[dict[str, int]]:
        total_rows = len(index)
        windows: list[dict[str, int]] = []
        cursor = train_window_days

        while cursor + test_window_days <= total_rows:
            windows.append(
                {
                    "train_start": cursor - train_window_days,
                    "train_end": cursor,
                    "test_start": cursor,
                    "test_end": cursor + test_window_days,
                }
            )
            cursor += step_days

        return windows

    def _build_walkforward_id(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        suffix = uuid4().hex[:8]
        return f"wf_{timestamp}_{suffix}"
