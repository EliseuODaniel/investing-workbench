"""Application service for run orchestration."""

from __future__ import annotations

import hashlib
import io
import logging
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import yaml

from src.api.models import (
    BacktestRequest,
    BacktestResponse,
    BenchmarkResult,
    ConfigInfo,
    EquityPoint,
    StrategyMetrics,
    StrategyResult,
    Trade,
)
from src.benchmarks import get_benchmark_data, get_selic_benchmark
from src.bitcoin_martingale.domain.runs import RunManifest
from src.bitcoin_martingale.infrastructure.persistence import LocalRunsRepository
from src.bitcoin_martingale.infrastructure.reporting import PersistedRunHTMLReportBuilder
from src.config import AppConfig, BenchmarkConfig, load_strategy
from src.data import get_data
from src.engine import BacktestEngine
from src.metrics import calculate_metrics

logger = logging.getLogger(__name__)


class RunBacktestService:
    """Service layer for API and CLI orchestration."""

    def __init__(self, runs_repository: LocalRunsRepository | None = None) -> None:
        self.runs_repository = runs_repository or LocalRunsRepository()
        self.report_builder = PersistedRunHTMLReportBuilder()

    def list_configs(self) -> list[ConfigInfo]:
        """List available YAML configs for the application."""
        configs_dir = Path("configs")
        if not configs_dir.exists():
            raise FileNotFoundError("Configs directory not found")

        configs: list[ConfigInfo] = []
        for config_file in configs_dir.glob("*.yaml"):
            try:
                with config_file.open("r", encoding="utf-8") as handle:
                    config_data = yaml.safe_load(handle)

                display_name = config_data.get("name", config_file.stem)
                strategy_names = [
                    strategy.get("name", "") for strategy in config_data.get("strategies", [])
                ]

                configs.append(
                    ConfigInfo(
                        name=config_file.stem,
                        path=str(config_file),
                        display_name=display_name,
                        strategies=strategy_names,
                    )
                )
            except Exception:
                logger.exception("Skipping invalid config file: %s", config_file)

        return configs

    def run(self, request: BacktestRequest) -> BacktestResponse:
        """Run a backtest request and return the serialized response model."""
        config = self._load_config(request)
        return self.run_with_config(
            config=config,
            config_path=request.config_path or "configs/martingale.yaml",
            strategy_names=request.strategies,
            request_payload=request.model_dump(exclude_none=True),
            force_download=bool(request.force_download),
        )

    def run_with_config(
        self,
        *,
        config: AppConfig,
        config_path: str,
        strategy_names: list[str] | None = None,
        request_payload: dict[str, Any] | None = None,
        force_download: bool = False,
    ) -> BacktestResponse:
        """Run a backtest from a resolved config and persist the artifacts."""
        strategies_to_run = self._resolve_strategies(config, strategy_names)
        data = self._load_market_data(config, force_download=force_download)
        run_id = self._build_run_id()
        config_snapshot = self._build_config_snapshot(config)
        data_profile = self._build_data_profile(config, data)

        response = self._build_response(
            config=config,
            strategies_to_run=strategies_to_run,
            data=data,
        )
        response.run_info = {
            "run_id": run_id,
            "artifact_dir": str(self.runs_repository.base_dir / run_id),
            "data_fingerprint": data_profile["data_fingerprint"],
        }
        persisted = self._persist_run(
            run_id=run_id,
            request_payload=request_payload or {},
            response=response,
            config_path=config_path,
            config_snapshot=config_snapshot,
            data_profile=data_profile,
        )
        response.run_info.update(
            {
                "manifest_path": str(persisted.manifest_path),
                "response_path": str(persisted.response_path),
                "config_snapshot_path": str(persisted.config_snapshot_path),
                "data_profile_path": str(persisted.data_profile_path),
                "report_path": str(persisted.report_path),
            }
        )
        persisted.response_path.write_text(response.model_dump_json(indent=2), encoding="utf-8")
        return response

    def run_trial(
        self,
        *,
        config_path: str,
        strategy_name: str,
        parameter_overrides: dict[str, Any],
        request_payload: dict[str, Any] | None = None,
    ) -> BacktestResponse:
        """Run a single-strategy trial with arbitrary parameter overrides."""
        config = AppConfig.from_file(config_path)
        matching_strategy = next(
            (strategy for strategy in config.strategies if strategy.name == strategy_name),
            None,
        )
        if matching_strategy is None:
            raise ValueError(f"Strategy '{strategy_name}' not found in config: {config_path}")

        matching_strategy.parameters = {
            **deepcopy(matching_strategy.parameters),
            **parameter_overrides,
        }
        config.strategies = [matching_strategy]

        payload = request_payload or {}
        payload.update(
            {
                "config_path": config_path,
                "strategies": [strategy_name],
                "parameter_overrides": parameter_overrides,
            }
        )

        return self.run_with_config(
            config=config,
            config_path=config_path,
            strategy_names=[strategy_name],
            request_payload=payload,
        )

    def download_csv(self, strategy: str) -> str:
        """Download trades CSV for the latest persisted run containing a strategy."""
        run_id = self.runs_repository.find_latest_run_id_for_strategy(strategy)
        return self.runs_repository.build_trades_csv(run_id, strategy)

    def get_run_manifest(self, run_id: str) -> dict[str, object]:
        """Fetch a previously persisted run manifest."""
        return self.runs_repository.get_manifest(run_id)

    def get_run_response(self, run_id: str) -> dict[str, object]:
        """Fetch a previously persisted run response payload."""
        return self.runs_repository.get_response_payload(run_id)

    def get_run_config_snapshot(self, run_id: str) -> dict[str, object]:
        """Fetch the resolved config used by a persisted run."""
        return self.runs_repository.get_config_snapshot(run_id)

    def get_run_data_profile(self, run_id: str) -> dict[str, object]:
        """Fetch the persisted dataset profile for a run."""
        return self.runs_repository.get_data_profile(run_id)

    def get_run_html_report(self, run_id: str) -> str:
        """Fetch the persisted HTML report for a run."""
        return self.runs_repository.get_html_report(run_id)

    def list_runs(self) -> list[dict[str, object]]:
        """List persisted runs for history views."""
        return self.runs_repository.list_runs()

    def get_trades_csv(self, run_id: str, strategy_name: str) -> str:
        """Generate a trades CSV for a persisted run and strategy."""
        return self.runs_repository.build_trades_csv(run_id, strategy_name)

    def _load_config(self, request: BacktestRequest) -> AppConfig:
        config_path = request.config_path or "configs/martingale.yaml"
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        config = AppConfig.from_file(config_path)

        if request.start_date:
            config.backtest.start_date = request.start_date
        if request.end_date:
            config.backtest.end_date = request.end_date
        if request.initial_capital is not None:
            config.backtest.initial_capital = request.initial_capital
        if request.data_source is not None:
            config.backtest.data_source = request.data_source
        if request.cache_path is not None:
            config.backtest.cache_path = request.cache_path
        if request.apply_cash_yield is not None:
            config.backtest.apply_cash_yield = request.apply_cash_yield
        if request.selic_rate_annual is not None:
            config.backtest.selic_rate_annual = request.selic_rate_annual
        if request.use_real_selic is not None:
            config.backtest.use_real_selic = request.use_real_selic
        if request.selic_path is not None:
            config.backtest.selic_path = request.selic_path
        if request.selic_fallback_rate is not None:
            config.backtest.selic_fallback_rate = request.selic_fallback_rate

        if request.benchmarks is not None:
            config.backtest.benchmarks = [
                BenchmarkConfig(ticker=ticker, name=ticker, enabled=True)
                for ticker in request.benchmarks
            ]
        if request.include_selic_benchmark is not None:
            config.backtest.include_selic_benchmark = request.include_selic_benchmark
        if request.include_buy_hold_benchmark is not None:
            config.backtest.include_buy_hold_benchmark = request.include_buy_hold_benchmark

        if any(
            value is not None
            for value in (
                request.base_bet,
                request.multiplier,
                request.drop_step,
                request.take_profit,
                request.max_layers,
            )
        ):
            for strategy_config in config.strategies:
                if request.base_bet is not None:
                    strategy_config.parameters["base_bet"] = request.base_bet
                if request.multiplier is not None:
                    strategy_config.parameters["multiplier"] = request.multiplier
                if request.drop_step is not None:
                    strategy_config.parameters["drop_step"] = request.drop_step
                if request.take_profit is not None:
                    strategy_config.parameters["take_profit"] = request.take_profit
                if request.max_layers is not None:
                    strategy_config.parameters["max_layers"] = request.max_layers

        return config

    def _resolve_strategies(
        self,
        config: AppConfig,
        strategy_names: list[str] | None,
    ):
        strategies_to_run = config.strategies
        if strategy_names:
            strategies_to_run = [s for s in config.strategies if s.name in strategy_names]

        if not strategies_to_run:
            raise ValueError("No strategies to run")

        return strategies_to_run

    def _load_market_data(self, config: AppConfig, force_download: bool = False) -> pd.DataFrame:
        cache_path = None if force_download else config.backtest.cache_path
        stdout_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer):
            data = get_data(
                start=config.backtest.start_date,
                end=config.backtest.end_date,
                cache_path=cache_path,
            )
        for line in stdout_buffer.getvalue().splitlines():
            logger.info("market-data: %s", line)
        return data

    def _build_run_id(self) -> str:
        """Create a unique, sortable run identifier."""
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        suffix = uuid4().hex[:8]
        return f"run_{timestamp}_{suffix}"

    def _build_config_snapshot(self, config: AppConfig) -> dict[str, Any]:
        """Serialize the resolved config after request overrides are applied."""
        return asdict(config)

    def _build_data_profile(self, config: AppConfig, data: pd.DataFrame) -> dict[str, Any]:
        """Capture a lightweight, reproducible description of the dataset."""
        index_name = getattr(data.index, "name", None)
        return {
            "asset": config.backtest.data_source,
            "cache_path": config.backtest.cache_path,
            "row_count": len(data),
            "columns": list(data.columns),
            "index_name": index_name,
            "start_timestamp": data.index[0].isoformat(),
            "end_timestamp": data.index[-1].isoformat(),
            "data_fingerprint": self._build_data_fingerprint(data),
        }

    def _build_data_fingerprint(self, data: pd.DataFrame) -> str:
        """Build a stable fingerprint for the exact dataset used in the run."""
        hashed = pd.util.hash_pandas_object(data, index=True)
        return hashlib.sha256(hashed.values.tobytes()).hexdigest()

    def _build_buy_hold_curve(
        self, data: pd.DataFrame, initial_capital: float
    ) -> list[EquityPoint]:
        initial_price = float(data.iloc[0]["Close"])
        curve: list[EquityPoint] = []

        for timestamp, row in data.iterrows():
            current_price = float(row["Close"])
            buy_hold_value = initial_capital * (current_price / initial_price)
            curve.append(
                EquityPoint(
                    timestamp=timestamp.isoformat(),
                    equity=buy_hold_value,
                    cash=initial_capital,
                )
            )

        return curve

    def _build_response(
        self,
        *,
        config: AppConfig,
        strategies_to_run,
        data: pd.DataFrame,
    ) -> BacktestResponse:
        buy_hold_equity = self._build_buy_hold_curve(data, config.backtest.initial_capital)
        results = self._run_strategies(config, strategies_to_run, data)
        benchmarks = self._process_benchmarks(config)

        return BacktestResponse(
            results=results,
            buy_hold_equity=buy_hold_equity,
            benchmarks=benchmarks if benchmarks else None,
            data_info={
                "start_date": data.index[0].isoformat(),
                "end_date": data.index[-1].isoformat(),
                "total_days": len(data),
                "initial_price": float(data.iloc[0]["Close"]),
                "final_price": float(data.iloc[-1]["Close"]),
            },
            run_info={},
        )

    def _run_strategies(
        self, config: AppConfig, strategies_to_run, data: pd.DataFrame
    ) -> dict[str, StrategyResult]:
        results: dict[str, StrategyResult] = {}

        for strategy_config in strategies_to_run:
            strategy = load_strategy(strategy_config)
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
            equity_points = [
                EquityPoint(
                    timestamp=timestamp.isoformat(),
                    equity=row["equity"],
                    cash=row["cash"],
                )
                for timestamp, row in result["equity"].iterrows()
            ]

            trades = [
                self._serialize_trade(trade_row) for _, trade_row in result["trades"].iterrows()
            ]
            metrics = calculate_metrics(
                result["equity"]["equity"],
                result["trades"],
                config.backtest.initial_capital,
                total_interest_earned=result.get("total_interest_earned", 0.0),
            )

            selic_rates_used = None
            selic_rates_dict = result.get("selic_rates_used", {})
            if selic_rates_dict:
                selic_rates_used = [
                    {"year": year, "month": month, "rate": rate}
                    for (year, month), rate in selic_rates_dict.items()
                ]

            results[strategy_config.name] = StrategyResult(
                strategy_name=strategy_config.name,
                equity=equity_points,
                trades=trades,
                metrics=StrategyMetrics(
                    total_return=metrics["total_return"],
                    cagr=metrics["cagr"],
                    sharpe_ratio=metrics["sharpe_ratio"],
                    sortino_ratio=metrics["sortino_ratio"],
                    max_drawdown=metrics["max_drawdown"],
                    hit_rate=metrics["hit_rate"],
                    profit_factor=metrics["profit_factor"],
                    total_trades=metrics["total_trades"],
                    avg_trade_pnl=metrics["avg_trade_pnl"],
                    volatility=metrics["volatility"],
                    total_interest_earned=metrics["total_interest_earned"],
                    selic_rates_used=selic_rates_used,
                ),
                start_price=float(data.iloc[0]["Close"]),
                end_price=float(data.iloc[-1]["Close"]),
            )

        return results

    def _process_benchmarks(self, config: AppConfig) -> dict[str, BenchmarkResult]:
        benchmark_results: dict[str, BenchmarkResult] = {}

        if not (
            config.backtest.benchmarks
            or config.backtest.include_selic_benchmark
            or config.backtest.include_buy_hold_benchmark
        ):
            return benchmark_results

        try:
            if config.backtest.benchmarks:
                enabled_benchmarks = [b for b in config.backtest.benchmarks if b.enabled]
                if enabled_benchmarks:
                    tickers = [b.ticker for b in enabled_benchmarks]
                    benchmark_data = get_benchmark_data(
                        tickers=tickers,
                        start_date=config.backtest.start_date,
                        end_date=config.backtest.end_date or datetime.now().strftime("%Y-%m-%d"),
                        initial_capital=config.backtest.initial_capital,
                        cache_dir=config.backtest.cache_path.replace("/btc_brl.parquet", ""),
                    )

                    for ticker, benchmark_data_frame in benchmark_data.items():
                        benchmark_config = next(b for b in enabled_benchmarks if b.ticker == ticker)
                        benchmark_results[benchmark_config.name] = self._serialize_benchmark(
                            name=benchmark_config.name,
                            ticker=ticker,
                            benchmark_data=benchmark_data_frame,
                        )

            if config.backtest.include_selic_benchmark:
                selic_data = get_selic_benchmark(
                    start_date=config.backtest.start_date,
                    end_date=config.backtest.end_date or datetime.now().strftime("%Y-%m-%d"),
                    initial_capital=config.backtest.initial_capital,
                    use_real_selic=config.backtest.use_real_selic,
                    selic_path=config.backtest.selic_path,
                    selic_fallback_rate=config.backtest.selic_fallback_rate,
                    cache_dir=config.backtest.cache_path.replace("/btc_brl.parquet", ""),
                )
                benchmark_results["SELIC"] = self._serialize_benchmark(
                    name="SELIC",
                    ticker="SELIC",
                    benchmark_data=selic_data,
                )
        except Exception:
            logger.exception("Failed to process benchmarks")

        return benchmark_results

    def _serialize_trade(self, trade_row: pd.Series) -> Trade:
        layer_value = trade_row.get("layer")
        if pd.isna(layer_value):
            layer_value = None
        elif isinstance(layer_value, float) and layer_value.is_integer():
            layer_value = int(layer_value)

        pnl_value = trade_row.get("pnl")
        if pd.isna(pnl_value):
            pnl_value = None

        return Trade(
            timestamp=trade_row["timestamp"].isoformat(),
            action=trade_row["action"],
            price=trade_row["price"],
            quantity=trade_row["quantity"],
            pnl=pnl_value,
            layer=layer_value,
        )

    def _serialize_benchmark(
        self, *, name: str, ticker: str, benchmark_data: dict[str, Any]
    ) -> BenchmarkResult:
        equity_points = [
            EquityPoint(
                timestamp=timestamp.isoformat(),
                equity=row["equity"],
                cash=0.0,
            )
            for timestamp, row in benchmark_data["equity_curve"].iterrows()
        ]

        metrics = benchmark_data["metrics"]
        return BenchmarkResult(
            name=name,
            ticker=ticker,
            equity=equity_points,
            metrics=StrategyMetrics(
                total_return=metrics["total_return"],
                cagr=metrics["cagr"],
                sharpe_ratio=metrics["sharpe_ratio"],
                sortino_ratio=0.0,
                max_drawdown=metrics["max_drawdown"],
                hit_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                avg_trade_pnl=0.0,
                volatility=metrics["volatility"],
                total_interest_earned=0.0,
                selic_rates_used=None,
            ),
        )

    def _persist_run(
        self,
        *,
        run_id: str,
        request_payload: dict[str, Any],
        response: BacktestResponse,
        config_path: str,
        config_snapshot: dict[str, Any],
        data_profile: dict[str, Any],
    ):
        benchmark_names = list(response.benchmarks.keys()) if response.benchmarks else []
        artifact_dir = self.runs_repository.base_dir / run_id
        manifest = RunManifest(
            run_id=run_id,
            created_at=datetime.now(UTC),
            config_path=config_path,
            artifact_dir=str(artifact_dir),
            strategy_names=list(response.results.keys()),
            benchmark_names=benchmark_names,
            request_payload=request_payload,
            data_info=response.data_info,
            config_snapshot_path=str(artifact_dir / "config_resolved.json"),
            data_profile_path=str(artifact_dir / "data_profile.json"),
            data_fingerprint=str(data_profile["data_fingerprint"]),
        )
        report_html = self.report_builder.build(
            manifest=manifest.to_dict(),
            response_payload=response.model_dump(mode="json"),
            config_snapshot=config_snapshot,
            data_profile=data_profile,
        )
        return self.runs_repository.persist_run(
            manifest=manifest,
            response=response,
            config_snapshot=config_snapshot,
            data_profile=data_profile,
            report_html=report_html,
        )
