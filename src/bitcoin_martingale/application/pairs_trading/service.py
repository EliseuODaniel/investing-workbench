"""Application service for B3 cointegration pairs-trading workflows."""

from __future__ import annotations

from dataclasses import asdict, fields, replace
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal, overload
from uuid import uuid4

import numpy as np
import pandas as pd

from src.bitcoin_martingale.application.datasets import DatasetCatalogService
from src.bitcoin_martingale.domain.pairs_trading import (
    BorrowOverride,
    CointegrationPairsBacktester,
    PairsTradingConfig,
)
from src.bitcoin_martingale.domain.pairs_trading.statistics import (
    estimate_pair_stability,
    evaluate_pair_orientations,
)
from src.bitcoin_martingale.infrastructure.persistence.pairs_repo import (
    LocalPairsBacktestsRepository,
)
from src.data import get_data

from .artifacts import PairsArtifactsService
from .benchmarks import PairsBenchmarkService
from .borrow import PairsBorrowSnapshotService
from .catalog import (
    SECTOR_MAP,
    SECTOR_RATIONALE,
    list_universe_presets,
    resolve_preset_metadata,
)
from .contracts import (
    DEFAULT_START_DATE,
    PairsContext,
    PairsExecutionCancelledError,
    ProgressCallback,
    ReconstitutionSegment,
)
from .dto import (
    BorrowSnapshotRegistration,
    PairsScreeningResult,
    PairsUniverseResolution,
)
from .execution import PairsScenarioExecutionService
from .ibov_history import B3IbovUniverseHistoryService, iter_rebalance_anchor_dates
from .reporting import PairsReportingService


class PairsTradingService:
    """Orchestrate B3 universe resolution, screening, and persisted pairs backtests."""

    def __init__(
        self,
        repository: LocalPairsBacktestsRepository | None = None,
        ibov_history_service: B3IbovUniverseHistoryService | None = None,
        dataset_service: DatasetCatalogService | None = None,
    ) -> None:
        self.repository = repository or LocalPairsBacktestsRepository()
        self.ibov_history_service = ibov_history_service or B3IbovUniverseHistoryService()
        self.dataset_service = dataset_service or DatasetCatalogService()
        self.borrow_snapshot_service = PairsBorrowSnapshotService(self.dataset_service)
        self.artifacts_service = PairsArtifactsService(self.repository)
        self.benchmarks_service = PairsBenchmarkService()
        self.reporting_service = PairsReportingService()
        self.execution_service = PairsScenarioExecutionService(
            benchmarks_service=self.benchmarks_service,
            reporting_service=self.reporting_service,
        )

    def list_universe_presets(self) -> list[dict[str, object]]:
        """List curated B3 universe presets available to the platform."""
        return list_universe_presets()

    def list_ibov_snapshots(self) -> list[dict[str, Any]]:
        """List cached official IBOV snapshots."""
        return self.ibov_history_service.list_cached_snapshots()

    def get_ibov_snapshot(self, *, as_of_date: str) -> dict[str, Any]:
        """Return one cached official IBOV snapshot."""
        return self.ibov_history_service.get_cached_snapshot(as_of_date=as_of_date)

    def backfill_ibov_snapshots(
        self,
        *,
        start_date: str,
        end_date: str,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Backfill official IBOV snapshots around the B3 rebalance cadence."""
        snapshots = self.ibov_history_service.backfill_snapshots(
            start_date=start_date,
            end_date=end_date,
            force_refresh=force_refresh,
        )
        return {
            "index_id": "ibov",
            "start_date": start_date,
            "end_date": end_date,
            "snapshot_count": len(snapshots),
            "snapshots": snapshots,
        }

    def resolve_universe(
        self,
        *,
        preset_id: str = "ibov_proxy",
        tickers: list[str] | None = None,
        sector_overrides: dict[str, str] | None = None,
        as_of_date: str | None = None,
        start_date: str = DEFAULT_START_DATE,
        end_date: str | None = None,
        force_download: bool = False,
        min_price: float = 5.0,
        min_median_notional_brl: float = 90_000_000.0,
        use_proxy_short_borrow: bool = True,
        proxy_borrow_base_rate_annual: float = 0.03,
        proxy_borrow_max_rate_annual: float = 0.12,
        proxy_min_short_score: float = 0.35,
        proxy_borrow_vol_floor: float = 0.20,
        proxy_borrow_vol_cap: float = 0.80,
        borrow_snapshot_path: str | None = None,
        progress_callback: ProgressCallback = None,
        should_cancel: Any = None,
    ) -> dict[str, Any]:
        """Resolve one curated or custom B3 universe with diagnostics."""
        self._notify_progress(
            progress_callback,
            phase="resolve_universe",
            message="Resolving pairs universe.",
            percent=5.0,
        )
        context = self._build_context(
            preset_id=preset_id,
            tickers=tickers,
            sector_overrides=sector_overrides,
            as_of_date=as_of_date,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            min_price=min_price,
            min_median_notional_brl=min_median_notional_brl,
            use_proxy_short_borrow=use_proxy_short_borrow,
            proxy_borrow_base_rate_annual=proxy_borrow_base_rate_annual,
            proxy_borrow_max_rate_annual=proxy_borrow_max_rate_annual,
            proxy_min_short_score=proxy_min_short_score,
            proxy_borrow_vol_floor=proxy_borrow_vol_floor,
            proxy_borrow_vol_cap=proxy_borrow_vol_cap,
            borrow_snapshot_path=borrow_snapshot_path,
        )
        self._check_cancelled(should_cancel)
        payload = PairsUniverseResolution(
            preset=context.preset_metadata,
            requested_tickers=context.requested_tickers,
            as_of_date=as_of_date,
            resolved_as_of_date=context.resolved_as_of_date,
            start_date=start_date,
            end_date=end_date,
            common_index_start=(
                str(context.common_index.min().date()) if len(context.common_index) > 0 else None
            ),
            common_index_end=(
                str(context.common_index.max().date()) if len(context.common_index) > 0 else None
            ),
            common_index_days=int(len(context.common_index)),
            quality_report=context.quality_report,
            assets=context.universe_records,
            eligible_assets=context.eligible_records,
            unavailable_tickers=context.unavailable_tickers,
            warnings=context.warnings,
        )
        self._notify_progress(
            progress_callback,
            phase="resolve_universe",
            message="Pairs universe resolved.",
            percent=100.0,
        )
        return payload.to_dict()

    def screen_pairs(
        self,
        *,
        preset_id: str = "ibov_proxy",
        tickers: list[str] | None = None,
        sector_overrides: dict[str, str] | None = None,
        as_of_date: str | None = None,
        start_date: str = DEFAULT_START_DATE,
        end_date: str | None = None,
        force_download: bool = False,
        formation_window: int = 252,
        test_window: int = 21,
        max_pairs: int = 3,
        top_n: int = 20,
        min_price: float = 5.0,
        min_median_notional_brl: float = 90_000_000.0,
        min_return_corr: float = 0.25,
        min_level_corr: float = 0.10,
        max_coint_pvalue: float = 0.10,
        min_half_life: float = 2.0,
        max_half_life: float = 60.0,
        min_stability_score: float = 0.35,
        max_structural_break_risk: float = 0.75,
        min_beta_abs: float = 0.10,
        max_beta_abs: float = 3.0,
        use_proxy_short_borrow: bool = True,
        proxy_borrow_base_rate_annual: float = 0.03,
        proxy_borrow_max_rate_annual: float = 0.12,
        proxy_min_short_score: float = 0.35,
        proxy_borrow_vol_floor: float = 0.20,
        proxy_borrow_vol_cap: float = 0.80,
        borrow_snapshot_path: str | None = None,
        require_cointegration: bool = True,
        progress_callback: ProgressCallback = None,
        should_cancel: Any = None,
    ) -> dict[str, Any]:
        """Screen candidate B3 pairs and return ranked diagnostics."""
        self._notify_progress(
            progress_callback,
            phase="screen_pairs",
            message="Resolving pairs universe for screening.",
            percent=5.0,
        )
        context = self._build_context(
            preset_id=preset_id,
            tickers=tickers,
            sector_overrides=sector_overrides,
            as_of_date=as_of_date,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            formation_window=formation_window,
            test_window=test_window,
            max_pairs=max_pairs,
            min_price=min_price,
            min_median_notional_brl=min_median_notional_brl,
            min_return_corr=min_return_corr,
            min_level_corr=min_level_corr,
            max_coint_pvalue=max_coint_pvalue,
            min_half_life=min_half_life,
            max_half_life=max_half_life,
            min_stability_score=min_stability_score,
            max_structural_break_risk=max_structural_break_risk,
            min_beta_abs=min_beta_abs,
            max_beta_abs=max_beta_abs,
            use_proxy_short_borrow=use_proxy_short_borrow,
            proxy_borrow_base_rate_annual=proxy_borrow_base_rate_annual,
            proxy_borrow_max_rate_annual=proxy_borrow_max_rate_annual,
            proxy_min_short_score=proxy_min_short_score,
            proxy_borrow_vol_floor=proxy_borrow_vol_floor,
            proxy_borrow_vol_cap=proxy_borrow_vol_cap,
            borrow_snapshot_path=borrow_snapshot_path,
        )
        self._check_cancelled(should_cancel)
        formation_index, test_index = self._screening_windows(
            context.common_index,
            formation_window=context.config.formation_window,
            test_window=context.config.test_window,
        )
        candidate_pairs, rejected_pairs, rejection_summary = self._screen_pair_candidates(
            context=context,
            formation_index=formation_index,
            top_n=top_n,
            require_cointegration=require_cointegration,
            include_rejections=True,
        )
        self._notify_progress(
            progress_callback,
            phase="screen_pairs",
            message="Ranking candidate pairs.",
            percent=70.0,
        )
        selected_pairs = [
            selection.to_dict()
            for selection in context.backtester.select_pairs(
                formation_index=formation_index,
                test_index=test_index,
                require_cointegration=require_cointegration,
            )
        ]
        payload = PairsScreeningResult(
            preset=context.preset_metadata,
            requested_tickers=context.requested_tickers,
            resolved_as_of_date=context.resolved_as_of_date,
            screening_window={
                "formation_start": str(formation_index[0].date()),
                "formation_end": str(formation_index[-1].date()),
                "trade_start": str(test_index[0].date()),
                "trade_end": str(test_index[-1].date()),
                "formation_days": int(len(formation_index)),
                "test_days": int(len(test_index)),
            },
            criteria={
                "require_cointegration": require_cointegration,
                "top_n": top_n,
                "max_pairs": max_pairs,
                "max_coint_pvalue": max_coint_pvalue,
                "min_return_corr": min_return_corr,
                "min_level_corr": min_level_corr,
                "min_half_life": min_half_life,
                "max_half_life": max_half_life,
                "min_stability_score": min_stability_score,
                "max_structural_break_risk": max_structural_break_risk,
                "min_beta_abs": min_beta_abs,
                "max_beta_abs": max_beta_abs,
            },
            summary={
                "requested_ticker_count": len(context.requested_tickers),
                "loaded_ticker_count": len(context.data_by_ticker),
                "eligible_ticker_count": len(context.eligible_records),
                "candidate_pair_count": int(len(candidate_pairs)),
                "selected_pair_count": int(len(selected_pairs)),
                "rejected_pair_count": int(len(rejected_pairs)),
            },
            quality_report=context.quality_report,
            selected_pairs=selected_pairs,
            candidate_pairs=candidate_pairs,
            rejected_pairs=rejected_pairs,
            rejection_summary=rejection_summary,
            warnings=context.warnings,
        )
        self._notify_progress(
            progress_callback,
            phase="screen_pairs",
            message="Pairs screener completed.",
            percent=100.0,
        )
        return payload.to_dict()

    def run_backtest(
        self,
        *,
        preset_id: str = "ibov_proxy",
        tickers: list[str] | None = None,
        sector_overrides: dict[str, str] | None = None,
        as_of_date: str | None = None,
        start_date: str = DEFAULT_START_DATE,
        end_date: str | None = None,
        force_download: bool = False,
        formation_window: int = 252,
        test_window: int = 21,
        step_window: int = 21,
        top_n: int = 20,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        stop_zscore: float = 4.0,
        max_holding_days: int = 30,
        max_pairs: int = 3,
        pair_allocation_pct: float = 0.30,
        initial_capital: float = 100000.0,
        min_price: float = 5.0,
        min_median_notional_brl: float = 90_000_000.0,
        min_return_corr: float = 0.25,
        min_level_corr: float = 0.10,
        max_coint_pvalue: float = 0.10,
        min_half_life: float = 2.0,
        max_half_life: float = 60.0,
        min_stability_score: float = 0.35,
        max_structural_break_risk: float = 0.75,
        min_beta_abs: float = 0.10,
        max_beta_abs: float = 3.0,
        zscore_window: int = 60,
        fee_rate: float = 0.0003,
        slippage: float = 0.0005,
        short_borrow_rate_annual: float = 0.05,
        use_proxy_short_borrow: bool = True,
        proxy_borrow_base_rate_annual: float = 0.03,
        proxy_borrow_max_rate_annual: float = 0.12,
        proxy_min_short_score: float = 0.35,
        proxy_borrow_vol_floor: float = 0.20,
        proxy_borrow_vol_cap: float = 0.80,
        apply_cash_yield: bool = False,
        use_real_selic: bool = False,
        selic_path: str = "data/selic_daily.csv",
        selic_fallback_rate: float = 0.13,
        cash_collateral_ratio: float = 1.0,
        explicit_margin_model: bool = False,
        short_margin_haircut: float = 0.50,
        dynamic_beta: bool = False,
        rolling_beta_window: int = 60,
        regime_filter: str = "none",
        regime_ma_window: int = 63,
        regime_max_deviation: float = 0.08,
        regime_vol_window: int = 21,
        regime_vol_lookback: int = 252,
        regime_vol_quantile: float = 0.75,
        portfolio_construction: str = "equal_notional",
        target_pair_volatility_annual: float = 0.18,
        max_gross_exposure_pct: float = 1.50,
        max_net_exposure_pct: float = 0.20,
        max_sector_pairs: int = 1,
        borrow_snapshot_path: str | None = None,
        benchmark_ids: list[str] | None = None,
        require_cointegration: bool = True,
        scenario_label: str = "Realistic cointegration",
        scenario_id: str = "realistic_cointegration",
        scenario_variants: list[dict[str, Any]] | None = None,
        batch_mode: bool = False,
        progress_callback: ProgressCallback = None,
        should_cancel: Any = None,
    ) -> dict[str, Any]:
        """Run and persist one or more B3 pairs-trading scenarios."""
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Resolving pairs universe.",
            percent=5.0,
        )
        context = self._build_context(
            preset_id=preset_id,
            tickers=tickers,
            sector_overrides=sector_overrides,
            as_of_date=as_of_date,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
            initial_capital=initial_capital,
            formation_window=formation_window,
            test_window=test_window,
            step_window=step_window,
            entry_zscore=entry_zscore,
            exit_zscore=exit_zscore,
            stop_zscore=stop_zscore,
            max_holding_days=max_holding_days,
            max_pairs=max_pairs,
            pair_allocation_pct=pair_allocation_pct,
            min_price=min_price,
            min_median_notional_brl=min_median_notional_brl,
            min_return_corr=min_return_corr,
            min_level_corr=min_level_corr,
            max_coint_pvalue=max_coint_pvalue,
            min_half_life=min_half_life,
            max_half_life=max_half_life,
            min_stability_score=min_stability_score,
            max_structural_break_risk=max_structural_break_risk,
            min_beta_abs=min_beta_abs,
            max_beta_abs=max_beta_abs,
            zscore_window=zscore_window,
            fee_rate=fee_rate,
            slippage=slippage,
            short_borrow_rate_annual=short_borrow_rate_annual,
            use_proxy_short_borrow=use_proxy_short_borrow,
            proxy_borrow_base_rate_annual=proxy_borrow_base_rate_annual,
            proxy_borrow_max_rate_annual=proxy_borrow_max_rate_annual,
            proxy_min_short_score=proxy_min_short_score,
            proxy_borrow_vol_floor=proxy_borrow_vol_floor,
            proxy_borrow_vol_cap=proxy_borrow_vol_cap,
            apply_cash_yield=apply_cash_yield,
            use_real_selic=use_real_selic,
            selic_path=selic_path,
            selic_fallback_rate=selic_fallback_rate,
            cash_collateral_ratio=cash_collateral_ratio,
            explicit_margin_model=explicit_margin_model,
            short_margin_haircut=short_margin_haircut,
            dynamic_beta=dynamic_beta,
            rolling_beta_window=rolling_beta_window,
            regime_filter=regime_filter,
            regime_ma_window=regime_ma_window,
            regime_max_deviation=regime_max_deviation,
            regime_vol_window=regime_vol_window,
            regime_vol_lookback=regime_vol_lookback,
            regime_vol_quantile=regime_vol_quantile,
            portfolio_construction=portfolio_construction,
            target_pair_volatility_annual=target_pair_volatility_annual,
            max_gross_exposure_pct=max_gross_exposure_pct,
            max_net_exposure_pct=max_net_exposure_pct,
            max_sector_pairs=max_sector_pairs,
            borrow_snapshot_path=borrow_snapshot_path,
        )
        self._check_cancelled(should_cancel)
        formation_index, _ = self._screening_windows(
            context.common_index,
            formation_window=context.config.formation_window,
            test_window=context.config.test_window,
        )
        candidate_pairs = self._screen_pair_candidates(
            context=context,
            formation_index=formation_index,
            top_n=top_n,
            require_cointegration=require_cointegration,
        )
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Candidate pairs ranked.",
            percent=25.0,
        )
        scenario_plan = self._resolve_scenario_plan(
            base_config=context.config,
            require_cointegration=require_cointegration,
            scenario_label=scenario_label,
            scenario_id=scenario_id,
            scenario_variants=scenario_variants,
            batch_mode=batch_mode,
        )

        effective_end_date = end_date or (
            str(context.common_index.max().date()) if len(context.common_index) > 0 else start_date
        )
        benchmark_keys = benchmark_ids or self.benchmarks_service.default_benchmark_ids(
            context.preset_metadata
        )
        if self._is_official_ibov_preset(context.preset_metadata):
            return self._run_backtest_with_reconstitution(
                initial_context=context,
                preset_id=preset_id,
                sector_overrides=sector_overrides,
                start_date=start_date,
                end_date=effective_end_date,
                force_download=force_download,
                scenario_plan=scenario_plan,
                batch_mode=batch_mode,
                benchmark_ids=benchmark_keys,
                top_n=top_n,
                use_real_selic=use_real_selic,
                selic_path=selic_path,
                selic_fallback_rate=selic_fallback_rate,
                initial_capital=initial_capital,
                require_cointegration=require_cointegration,
                progress_callback=progress_callback,
                should_cancel=should_cancel,
            )

        benchmark_series, benchmark_warnings = self.benchmarks_service.build_benchmarks(
            benchmark_ids=benchmark_keys,
            start_date=start_date,
            end_date=effective_end_date,
            common_index=context.common_index,
            data_by_ticker=context.data_by_ticker,
            initial_capital=initial_capital,
            use_real_selic=use_real_selic,
            selic_path=selic_path,
            selic_fallback_rate=selic_fallback_rate,
            force_download=force_download,
        )
        warnings = [*context.warnings, *benchmark_warnings]
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Benchmarks prepared. Executing scenarios.",
            percent=40.0,
        )

        scenario_results: list[dict[str, Any]] = []
        total_scenarios = max(len(scenario_plan), 1)
        for index, scenario in enumerate(scenario_plan, start=1):
            self._check_cancelled(should_cancel)
            config = self._apply_config_overrides(context.config, scenario["overrides"])
            scenario_result = self.execution_service.run_scenario(
                label=str(scenario["label"]),
                scenario_id=str(scenario["scenario_id"]),
                context=context,
                config=config,
                require_cointegration=bool(scenario["require_cointegration"]),
                benchmark_series=benchmark_series,
                candidate_pairs=candidate_pairs,
            )
            scenario_results.append(scenario_result)
            self._notify_progress(
                progress_callback,
                phase="pairs_backtest",
                message=f"Executed scenario {index}/{total_scenarios}: {scenario['scenario_id']}",
                percent=40.0 + (50.0 * (index / total_scenarios)),
                current_step=index,
                total_steps=total_scenarios,
            )

        robustness_report = self.reporting_service.build_robustness_report(scenario_results)
        self._check_cancelled(should_cancel)
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Persisting pairs backtest artifacts.",
            percent=95.0,
        )
        payload = self._persist_pairs_backtest(
            context=context,
            start_date=start_date,
            end_date=effective_end_date,
            batch_mode=batch_mode,
            benchmark_ids=benchmark_keys,
            benchmark_series=benchmark_series,
            scenario_results=scenario_results,
            candidate_pairs=candidate_pairs,
            robustness_report=robustness_report,
            warnings=warnings,
            reconstitution_plan=[],
        )
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Pairs backtest completed.",
            percent=100.0,
        )
        return payload

    def run_batch(self, **kwargs: Any) -> dict[str, Any]:
        """Run a default multi-scenario sensitivity batch for one B3 pairs universe."""
        return self.run_backtest(batch_mode=True, **kwargs)

    def list_backtests(self) -> list[dict[str, Any]]:
        """List persisted pairs-trading manifests."""
        return self.artifacts_service.list_backtests()

    def get_manifest(self, backtest_id: str) -> dict[str, Any]:
        """Load one persisted pairs-trading manifest."""
        return self.artifacts_service.get_manifest(backtest_id)

    def get_results(self, backtest_id: str) -> dict[str, Any]:
        """Load one persisted pairs-trading result set."""
        return self.artifacts_service.get_results(backtest_id)

    def _notify_progress(
        self,
        callback: ProgressCallback,
        *,
        phase: str,
        message: str,
        percent: float,
        current_step: int | None = None,
        total_steps: int | None = None,
    ) -> None:
        if callback is None:
            return
        payload: dict[str, Any] = {
            "phase": phase,
            "message": message,
            "percent": round(percent, 2),
        }
        if current_step is not None:
            payload["current_step"] = current_step
        if total_steps is not None:
            payload["total_steps"] = total_steps
        callback(payload)

    def _check_cancelled(self, should_cancel: Any) -> None:
        if callable(should_cancel) and should_cancel():
            raise PairsExecutionCancelledError("Pairs backtest cancelled before completion")

    def _is_official_ibov_preset(self, preset_metadata: dict[str, Any] | None) -> bool:
        if preset_metadata is None:
            return False
        return str(preset_metadata.get("history_mode")) == "official_b3_bdi"

    def _run_backtest_with_reconstitution(
        self,
        *,
        initial_context: PairsContext,
        preset_id: str,
        sector_overrides: dict[str, str] | None,
        start_date: str,
        end_date: str,
        force_download: bool,
        scenario_plan: list[dict[str, Any]],
        batch_mode: bool,
        benchmark_ids: list[str],
        top_n: int,
        use_real_selic: bool,
        selic_path: str,
        selic_fallback_rate: float,
        initial_capital: float,
        require_cointegration: bool,
        progress_callback: ProgressCallback = None,
        should_cancel: Any = None,
    ) -> dict[str, Any]:
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Resolving IBOV reconstitution segments.",
            percent=30.0,
        )
        segments, segment_warnings = self._build_reconstitution_segments(
            initial_context=initial_context,
            preset_id=preset_id,
            sector_overrides=sector_overrides,
            start_date=start_date,
            end_date=end_date,
            force_download=force_download,
        )
        if len(segments) <= 1:
            self._check_cancelled(should_cancel)
            benchmark_series, benchmark_warnings = self.benchmarks_service.build_benchmarks(
                benchmark_ids=benchmark_ids,
                start_date=start_date,
                end_date=end_date,
                common_index=initial_context.common_index,
                data_by_ticker=initial_context.data_by_ticker,
                initial_capital=initial_capital,
                use_real_selic=use_real_selic,
                selic_path=selic_path,
                selic_fallback_rate=selic_fallback_rate,
                force_download=force_download,
            )
            warnings = [*initial_context.warnings, *segment_warnings, *benchmark_warnings]
            formation_index, _ = self._screening_windows(
                initial_context.common_index,
                formation_window=initial_context.config.formation_window,
                test_window=initial_context.config.test_window,
            )
            candidate_pairs = self._screen_pair_candidates(
                context=initial_context,
                formation_index=formation_index,
                top_n=top_n,
                require_cointegration=require_cointegration,
            )
            single_segment_results: list[dict[str, Any]] = []
            total_scenarios = max(len(scenario_plan), 1)
            for index, scenario in enumerate(scenario_plan, start=1):
                self._check_cancelled(should_cancel)
                config = self._apply_config_overrides(
                    initial_context.config,
                    scenario["overrides"],
                )
                single_segment_results.append(
                    self.execution_service.run_scenario(
                        label=str(scenario["label"]),
                        scenario_id=str(scenario["scenario_id"]),
                        context=initial_context,
                        config=config,
                        require_cointegration=bool(scenario["require_cointegration"]),
                        benchmark_series=benchmark_series,
                        candidate_pairs=candidate_pairs,
                    )
                )
                self._notify_progress(
                    progress_callback,
                    phase="pairs_backtest",
                    message=(
                        f"Executed scenario {index}/{total_scenarios}: "
                        f"{scenario['scenario_id']}"
                    ),
                    percent=45.0 + (40.0 * (index / total_scenarios)),
                    current_step=index,
                    total_steps=total_scenarios,
                )
            robustness_report = self.reporting_service.build_robustness_report(
                single_segment_results
            )
            payload = self._persist_pairs_backtest(
                context=initial_context,
                start_date=start_date,
                end_date=end_date,
                batch_mode=batch_mode,
                benchmark_ids=benchmark_ids,
                benchmark_series=benchmark_series,
                scenario_results=single_segment_results,
                candidate_pairs=candidate_pairs,
                robustness_report=robustness_report,
                warnings=warnings,
                reconstitution_plan=[],
            )
            self._notify_progress(
                progress_callback,
                phase="pairs_backtest",
                message="Pairs backtest completed.",
                percent=100.0,
            )
            return payload

        self._check_cancelled(should_cancel)
        benchmark_series, segment_benchmark_sets, benchmark_warnings = (
            self._build_reconstituted_benchmarks(
                segments=segments,
                benchmark_ids=benchmark_ids,
                initial_capital=initial_capital,
                use_real_selic=use_real_selic,
                selic_path=selic_path,
                selic_fallback_rate=selic_fallback_rate,
                force_download=force_download,
            )
        )
        warnings = [*initial_context.warnings, *segment_warnings, *benchmark_warnings]
        candidate_pairs = self._merge_segment_candidate_pairs(
            segments=segments,
            require_cointegration=require_cointegration,
            top_n=top_n,
        )
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Reconstituted benchmarks ready. Executing scenarios.",
            percent=45.0,
        )

        scenario_results: list[dict[str, Any]] = []
        total_scenarios = max(len(scenario_plan), 1)
        for index, scenario in enumerate(scenario_plan, start=1):
            self._check_cancelled(should_cancel)
            config = self._apply_config_overrides(initial_context.config, scenario["overrides"])
            scenario_results.append(
                self.execution_service.run_reconstituted_scenario(
                    label=str(scenario["label"]),
                    scenario_id=str(scenario["scenario_id"]),
                    segments=segments,
                    config=config,
                    require_cointegration=bool(scenario["require_cointegration"]),
                    benchmark_series=benchmark_series,
                    segment_benchmark_sets=segment_benchmark_sets,
                    candidate_pairs=candidate_pairs,
                    initial_capital=initial_capital,
                )
            )
            self._notify_progress(
                progress_callback,
                phase="pairs_backtest",
                message=f"Executed scenario {index}/{total_scenarios}: {scenario['scenario_id']}",
                percent=45.0 + (40.0 * (index / total_scenarios)),
                current_step=index,
                total_steps=total_scenarios,
            )

        robustness_report = self.reporting_service.build_robustness_report(scenario_results)
        reconstitution_plan = [
            {
                "segment_id": segment.segment_id,
                "start_date": segment.start_date,
                "end_date": segment.end_date,
                "requested_as_of_date": segment.requested_as_of_date,
                "resolved_as_of_date": segment.resolved_as_of_date,
                "requested_tickers": segment.context.requested_tickers,
                "eligible_tickers": [row["ticker"] for row in segment.context.eligible_records],
                "quality_report": segment.context.quality_report,
            }
            for segment in segments
        ]
        payload = self._persist_pairs_backtest(
            context=initial_context,
            start_date=start_date,
            end_date=end_date,
            batch_mode=batch_mode,
            benchmark_ids=benchmark_ids,
            benchmark_series=benchmark_series,
            scenario_results=scenario_results,
            candidate_pairs=candidate_pairs,
            robustness_report=robustness_report,
            warnings=warnings,
            reconstitution_plan=reconstitution_plan,
        )
        self._notify_progress(
            progress_callback,
            phase="pairs_backtest",
            message="Pairs backtest completed.",
            percent=100.0,
        )
        return payload

    def _build_context(
        self,
        *,
        preset_id: str,
        tickers: list[str] | None,
        sector_overrides: dict[str, str] | None = None,
        as_of_date: str | None = None,
        start_date: str = DEFAULT_START_DATE,
        end_date: str | None = None,
        force_download: bool = False,
        **config_overrides: Any,
    ) -> PairsContext:
        requested_tickers, preset_metadata, warnings, resolved_as_of_date = (
            self._resolve_requested_tickers(
                preset_id=preset_id,
                tickers=tickers,
                as_of_date=as_of_date,
                start_date=start_date,
                end_date=end_date,
                force_download=force_download,
            )
        )
        sector_map = self._resolve_sector_map(
            requested_tickers=requested_tickers,
            sector_overrides=sector_overrides or {},
        )
        unknown_sector_count = sum(
            1 for ticker in requested_tickers if sector_map[ticker] == "custom"
        )
        if unknown_sector_count > 0:
            warnings.append(
                f"{unknown_sector_count} ticker(s) are missing a curated sector mapping. "
                "They fall back to the generic 'custom' bucket during same-group screening."
            )
        data_by_ticker: dict[str, pd.DataFrame] = {}
        unavailable_tickers: dict[str, str] = {}
        for ticker in requested_tickers:
            try:
                data_by_ticker[ticker] = get_data(
                    start=start_date,
                    end=end_date,
                    cache_path=f"data/{ticker.lower()}_sa.parquet",
                    force_download=force_download,
                    data_source=ticker,
                    include_actions=True,
                )
            except Exception as exc:  # pragma: no cover - network/cache failures vary
                unavailable_tickers[ticker] = str(exc)

        if len(data_by_ticker) < 2:
            raise ValueError("Pairs trading requires at least two B3 assets with available data.")

        base_config = self._build_pairs_config(config_overrides)
        (
            borrow_overrides,
            borrow_warnings,
            borrow_snapshot_registration,
        ) = self._load_borrow_overrides(
            borrow_snapshot_path=base_config.borrow_snapshot_path,
            requested_tickers=requested_tickers,
        )
        warnings.extend(borrow_warnings)
        backtester = CointegrationPairsBacktester(
            data_by_ticker=data_by_ticker,
            sector_map={ticker: sector_map[ticker] for ticker in data_by_ticker},
            config=base_config,
            borrow_overrides=borrow_overrides,
        )
        common_index = backtester.common_index
        if len(common_index) < max(base_config.formation_window + base_config.test_window, 80):
            warnings.append(
                "Common history across the requested assets is short for robust formation/testing."
            )

        universe_records = self._serialize_universe_records(
            backtester=backtester,
            common_index=common_index,
        )
        eligible_records = [
            row for row in universe_records if row["eligibility_status"] == "eligible"
        ]
        quality_report = self._build_quality_report(
            requested_tickers=requested_tickers,
            unavailable_tickers=unavailable_tickers,
            universe_records=universe_records,
            eligible_records=eligible_records,
            common_index=common_index,
            borrow_override_count=len(borrow_overrides),
            borrow_snapshot_path=(
                borrow_snapshot_registration.source_path
                if borrow_snapshot_registration is not None
                else base_config.borrow_snapshot_path
            ),
            borrow_snapshot_managed_path=(
                borrow_snapshot_registration.managed_path
                if borrow_snapshot_registration is not None
                else None
            ),
            borrow_snapshot_dataset_id=(
                borrow_snapshot_registration.dataset_id
                if borrow_snapshot_registration is not None
                else None
            ),
        )

        return PairsContext(
            preset_metadata=preset_metadata,
            requested_tickers=requested_tickers,
            resolved_as_of_date=resolved_as_of_date,
            sector_map=sector_map,
            unavailable_tickers=unavailable_tickers,
            warnings=warnings,
            data_by_ticker=data_by_ticker,
            borrow_overrides=borrow_overrides,
            borrow_snapshot_registration=borrow_snapshot_registration,
            config=base_config,
            backtester=backtester,
            common_index=common_index,
            universe_records=universe_records,
            eligible_records=eligible_records,
            quality_report=quality_report,
        )

    def _resolve_requested_tickers(
        self,
        *,
        preset_id: str,
        tickers: list[str] | None,
        as_of_date: str | None,
        start_date: str,
        end_date: str | None,
        force_download: bool,
    ) -> tuple[list[str], dict[str, Any] | None, list[str], str | None]:
        warnings: list[str] = []
        if tickers:
            normalized = self._normalize_tickers(tickers)
            return normalized, None, warnings, as_of_date

        preset = resolve_preset_metadata(preset_id)
        if preset.history_mode == "official_b3_bdi":
            requested_snapshot_date = as_of_date or start_date
            if as_of_date is None:
                warnings.append(
                    "No as_of_date was provided for the official IBOV preset. "
                    "The universe snapshot was resolved from start_date to avoid look-ahead."
                )

            resolution = self.ibov_history_service.resolve_snapshot(
                as_of_date=requested_snapshot_date,
                force_refresh=force_download,
            )
            snapshot = resolution.snapshot
            resolved_as_of_date = resolution.resolved_as_of_date
            if resolved_as_of_date != resolution.requested_as_of_date:
                warnings.append(
                    "The requested official IBOV snapshot date did not have a published BDI PDF. "
                    f"Falling back to {resolved_as_of_date}."
                )
            if end_date is not None and end_date > resolved_as_of_date:
                warnings.append(
                    "Universe diagnostics resolve one official IBOV snapshot for the requested "
                    "date range. Backtest runs can reconstitute the universe across later B3 "
                    "review dates when the period spans multiple official snapshots."
                )

            preset_metadata = asdict(preset) | {
                "tickers": list(snapshot["tickers"]),
                "ticker_count": int(snapshot["ticker_count"]),
                "requested_as_of_date": resolution.requested_as_of_date,
                "resolved_as_of_date": resolved_as_of_date,
                "validity_label": snapshot.get("validity_label"),
                "source_kind": snapshot["source_kind"],
                "source_url": snapshot["source_url"],
                "cache_status": resolution.cache_status,
            }
            return list(snapshot["tickers"]), preset_metadata, warnings, resolved_as_of_date

        if as_of_date is not None and preset.history_mode == "curated_proxy":
            warnings.append(
                "The selected B3 universe is a curated IBOV proxy. "
                "The platform does not yet ship official historical IBOV rebalances, "
                "so the same proxy constituents are reused across as_of_date values."
            )
        return list(preset.tickers), asdict(preset), warnings, as_of_date

    def _build_reconstitution_segments(
        self,
        *,
        initial_context: PairsContext,
        preset_id: str,
        sector_overrides: dict[str, str] | None,
        start_date: str,
        end_date: str,
        force_download: bool,
    ) -> tuple[list[ReconstitutionSegment], list[str]]:
        warnings: list[str] = []
        base_config_overrides = asdict(initial_context.config)
        anchors = iter_rebalance_anchor_dates(start_date=start_date, end_date=end_date)
        segment_specs: list[tuple[str, str, list[str]]] = [
            (
                str(
                    initial_context.preset_metadata.get("requested_as_of_date")
                    if initial_context.preset_metadata
                    else initial_context.resolved_as_of_date or start_date
                ),
                str(initial_context.resolved_as_of_date or start_date),
                list(initial_context.requested_tickers),
            )
        ]
        last_resolved = str(initial_context.resolved_as_of_date or start_date)
        end_boundary = date.fromisoformat(end_date)

        for anchor in anchors[1:]:
            try:
                resolution = self.ibov_history_service.resolve_snapshot(
                    as_of_date=anchor,
                    force_refresh=force_download,
                    search_direction="forward",
                )
            except Exception as exc:
                warnings.append(
                    "IBOV reconstitution snapshot could not be resolved for " f"{anchor}: {exc}"
                )
                continue
            if resolution.resolved_as_of_date <= last_resolved:
                continue
            if date.fromisoformat(resolution.resolved_as_of_date) > end_boundary:
                continue
            segment_specs.append(
                (
                    resolution.requested_as_of_date,
                    resolution.resolved_as_of_date,
                    list(resolution.snapshot["tickers"]),
                )
            )
            last_resolved = resolution.resolved_as_of_date

        segments: list[ReconstitutionSegment] = []
        for index, (requested_as_of_date, resolved_as_of_date, segment_tickers) in enumerate(
            segment_specs,
            start=1,
        ):
            segment_start = start_date if index == 1 else resolved_as_of_date
            next_start = (
                date.fromisoformat(segment_specs[index][1]) if index < len(segment_specs) else None
            )
            segment_end = (
                min(end_boundary, next_start - timedelta(days=1)).isoformat()
                if next_start is not None
                else end_date
            )
            if segment_end < segment_start:
                continue
            try:
                context = self._build_context(
                    preset_id=preset_id,
                    tickers=segment_tickers,
                    sector_overrides=sector_overrides,
                    as_of_date=resolved_as_of_date,
                    start_date=segment_start,
                    end_date=segment_end,
                    force_download=force_download,
                    **base_config_overrides,
                )
            except Exception as exc:
                warnings.append(
                    f"IBOV segment {resolved_as_of_date} could not be built for "
                    f"{segment_start}..{segment_end}: {exc}"
                )
                continue
            segments.append(
                ReconstitutionSegment(
                    segment_id=f"segment_{index:03d}",
                    start_date=segment_start,
                    end_date=segment_end,
                    requested_as_of_date=requested_as_of_date,
                    resolved_as_of_date=resolved_as_of_date,
                    context=context,
                )
            )

        if not segments:
            segments.append(
                ReconstitutionSegment(
                    segment_id="segment_001",
                    start_date=start_date,
                    end_date=end_date,
                    requested_as_of_date=str(
                        initial_context.preset_metadata.get("requested_as_of_date")
                        if initial_context.preset_metadata
                        else initial_context.resolved_as_of_date or start_date
                    ),
                    resolved_as_of_date=str(initial_context.resolved_as_of_date or start_date),
                    context=initial_context,
                )
            )
        return segments, warnings

    def _merge_segment_candidate_pairs(
        self,
        *,
        segments: list[ReconstitutionSegment],
        require_cointegration: bool,
        top_n: int,
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for segment in segments:
            formation_index, _ = self._screening_windows(
                segment.context.common_index,
                formation_window=segment.context.config.formation_window,
                test_window=segment.context.config.test_window,
            )
            segment_candidates = self._screen_pair_candidates(
                context=segment.context,
                formation_index=formation_index,
                top_n=top_n,
                require_cointegration=require_cointegration,
            )
            for candidate in segment_candidates:
                merged.append(
                    candidate
                    | {
                        "segment_id": segment.segment_id,
                        "segment_start_date": segment.start_date,
                        "segment_end_date": segment.end_date,
                        "resolved_as_of_date": segment.resolved_as_of_date,
                    }
                )
        merged.sort(
            key=lambda item: (
                -float(item["ranking_score"]),
                float(item["coint_pvalue"]),
                -float(item["return_corr"]),
            )
        )
        return merged[:top_n]

    def _build_reconstituted_benchmarks(
        self,
        *,
        segments: list[ReconstitutionSegment],
        benchmark_ids: list[str],
        initial_capital: float,
        use_real_selic: bool,
        selic_path: str,
        selic_fallback_rate: float,
        force_download: bool,
    ) -> tuple[list[dict[str, Any]], list[list[dict[str, Any]]], list[str]]:
        warnings: list[str] = []
        segment_sets: list[list[dict[str, Any]]] = []
        capital_by_benchmark = {benchmark_id: initial_capital for benchmark_id in benchmark_ids}
        series_by_benchmark: dict[str, list[pd.Series]] = {
            benchmark_id: [] for benchmark_id in benchmark_ids
        }
        labels_by_benchmark: dict[str, str] = {}

        for segment in segments:
            segment_benchmarks: list[dict[str, Any]] = []
            for benchmark_id in benchmark_ids:
                built, benchmark_warnings = self.benchmarks_service.build_benchmarks(
                    benchmark_ids=[benchmark_id],
                    start_date=segment.start_date,
                    end_date=segment.end_date,
                    common_index=segment.context.common_index,
                    data_by_ticker=segment.context.data_by_ticker,
                    initial_capital=capital_by_benchmark[benchmark_id],
                    use_real_selic=use_real_selic,
                    selic_path=selic_path,
                    selic_fallback_rate=selic_fallback_rate,
                    force_download=force_download,
                )
                warnings.extend(benchmark_warnings)
                if not built:
                    continue
                benchmark = built[0]
                segment_benchmarks.append(benchmark)
                labels_by_benchmark[benchmark_id] = str(benchmark["label"])
                series = self.benchmarks_service.series_from_equity_curve(
                    benchmark["equity_curve"],
                    value_key="equity",
                )
                if series.empty:
                    continue
                series_by_benchmark[benchmark_id].append(series)
                capital_by_benchmark[benchmark_id] = float(series.iloc[-1])
            segment_sets.append(segment_benchmarks)

        merged_benchmarks: list[dict[str, Any]] = []
        for benchmark_id in benchmark_ids:
            merged_series = self.benchmarks_service.concat_series_segments(
                series_by_benchmark[benchmark_id]
            )
            if merged_series.empty:
                continue
            merged_benchmarks.append(
                {
                    "benchmark_id": benchmark_id,
                    "label": labels_by_benchmark.get(benchmark_id, benchmark_id),
                    "equity_curve": self.benchmarks_service.serialize_series(merged_series),
                }
            )
        return merged_benchmarks, segment_sets, warnings

    def _persist_pairs_backtest(
        self,
        *,
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
        return self.artifacts_service.persist_backtest(
            backtest_id=self._build_backtest_id(),
            context=context,
            start_date=start_date,
            end_date=end_date,
            batch_mode=batch_mode,
            benchmark_ids=benchmark_ids,
            benchmark_series=benchmark_series,
            scenario_results=scenario_results,
            candidate_pairs=candidate_pairs,
            robustness_report=robustness_report,
            warnings=warnings,
            reconstitution_plan=reconstitution_plan,
        )

    def _resolve_sector_map(
        self,
        *,
        requested_tickers: list[str],
        sector_overrides: dict[str, str],
    ) -> dict[str, str]:
        normalized_overrides = {
            ticker.upper().strip(): value for ticker, value in sector_overrides.items()
        }
        sector_map: dict[str, str] = {}
        for ticker in requested_tickers:
            sector_map[ticker] = normalized_overrides.get(
                ticker,
                SECTOR_MAP.get(ticker, "custom"),
            )
        return sector_map

    def _load_borrow_overrides(
        self,
        *,
        borrow_snapshot_path: str | None,
        requested_tickers: list[str],
    ) -> tuple[dict[str, BorrowOverride], list[str], BorrowSnapshotRegistration | None]:
        return self.borrow_snapshot_service.load_overrides(
            borrow_snapshot_path=borrow_snapshot_path,
            requested_tickers=requested_tickers,
        )

    def _build_pairs_config(self, overrides: dict[str, Any]) -> PairsTradingConfig:
        config_fields = {field.name for field in fields(PairsTradingConfig)}
        sanitized = {
            key: value
            for key, value in overrides.items()
            if key in config_fields and value is not None
        }
        return PairsTradingConfig(**sanitized)

    def _apply_config_overrides(
        self,
        config: PairsTradingConfig,
        overrides: dict[str, Any],
    ) -> PairsTradingConfig:
        allowed = {key: value for key, value in overrides.items() if value is not None}
        return replace(config, **allowed)

    def _serialize_universe_records(
        self,
        *,
        backtester: CointegrationPairsBacktester,
        common_index: pd.DatetimeIndex,
    ) -> list[dict[str, Any]]:
        eligible_tickers = {asset.ticker for asset in backtester.eligible_universe()}
        records: list[dict[str, Any]] = []
        for asset in backtester.build_universe():
            reasons: list[str] = []
            if asset.rows < len(common_index) * 0.98:
                reasons.append("coverage_gap")
            if asset.median_notional_brl < backtester.config.min_median_notional_brl:
                reasons.append("low_liquidity")
            if asset.min_close < backtester.config.min_price:
                reasons.append("low_price")
            if (
                backtester.config.use_proxy_short_borrow
                and asset.short_score < backtester.config.proxy_min_short_score
            ):
                reasons.append("short_score")
            record = asset.to_dict()
            record["eligibility_status"] = (
                "eligible" if asset.ticker in eligible_tickers else "ineligible"
            )
            record["eligibility_reasons"] = reasons
            record["coverage_pct"] = float(asset.rows / max(len(common_index), 1))
            record["sector_rationale"] = SECTOR_RATIONALE.get(asset.sector_group)
            records.append(record)
        return records

    def _build_quality_report(
        self,
        *,
        requested_tickers: list[str],
        unavailable_tickers: dict[str, str],
        universe_records: list[dict[str, Any]],
        eligible_records: list[dict[str, Any]],
        common_index: pd.DatetimeIndex,
        borrow_override_count: int,
        borrow_snapshot_path: str | None,
        borrow_snapshot_managed_path: str | None,
        borrow_snapshot_dataset_id: str | None,
    ) -> dict[str, Any]:
        issue_counts: dict[str, int] = {}
        for record in universe_records:
            for issue in record["eligibility_reasons"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        quality_score = 0.0
        if requested_tickers:
            quality_score = len(eligible_records) / len(requested_tickers)
            quality_score *= len(requested_tickers) / max(len(requested_tickers), 1)

        return {
            "requested_ticker_count": len(requested_tickers),
            "loaded_ticker_count": len(universe_records),
            "eligible_ticker_count": len(eligible_records),
            "unavailable_ticker_count": len(unavailable_tickers),
            "common_index_days": int(len(common_index)),
            "issue_counts": issue_counts,
            "coverage_quality_score": float(quality_score),
            "unavailable_tickers": unavailable_tickers,
            "borrow_override_count": int(borrow_override_count),
            "borrow_snapshot_path": borrow_snapshot_path,
            "borrow_snapshot_managed_path": borrow_snapshot_managed_path,
            "borrow_snapshot_dataset_id": borrow_snapshot_dataset_id,
        }

    def _screening_windows(
        self,
        common_index: pd.DatetimeIndex,
        *,
        formation_window: int,
        test_window: int,
    ) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
        if len(common_index) <= test_window + 1:
            return common_index[:-1], common_index[-1:]

        if len(common_index) < formation_window + test_window:
            formation_index = common_index[:-test_window]
            test_index = common_index[-test_window:]
            return formation_index, test_index

        formation_index = common_index[-(formation_window + test_window) : -test_window]
        test_index = common_index[-test_window:]
        return formation_index, test_index

    @overload
    def _screen_pair_candidates(
        self,
        *,
        context: PairsContext,
        formation_index: pd.DatetimeIndex,
        top_n: int,
        require_cointegration: bool,
        include_rejections: Literal[False] = False,
    ) -> list[dict[str, Any]]: ...

    @overload
    def _screen_pair_candidates(
        self,
        *,
        context: PairsContext,
        formation_index: pd.DatetimeIndex,
        top_n: int,
        require_cointegration: bool,
        include_rejections: Literal[True],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]: ...

    def _screen_pair_candidates(
        self,
        *,
        context: PairsContext,
        formation_index: pd.DatetimeIndex,
        top_n: int,
        require_cointegration: bool,
        include_rejections: bool = False,
    ) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
        eligible_assets = {row["ticker"]: row for row in context.eligible_records}
        tickers = sorted(eligible_assets)
        candidates: list[dict[str, Any]] = []
        rejected_pairs: list[dict[str, Any]] = []
        rejection_summary: dict[str, int] = {}

        for left_index, left in enumerate(tickers):
            for right in tickers[left_index + 1 :]:
                if context.sector_map.get(left) != context.sector_map.get(right):
                    continue

                adjusted_data = context.backtester.data_by_ticker
                left_series = adjusted_data[left].loc[formation_index, "Close_sa"]
                right_series = adjusted_data[right].loc[formation_index, "Close_sa"]
                orientation, metrics = evaluate_pair_orientations(left_series, right_series)
                y_ticker, x_ticker = (left, right) if orientation == "ab" else (right, left)

                stability = self._pair_stability(
                    y=left_series if orientation == "ab" else right_series,
                    x=right_series if orientation == "ab" else left_series,
                    max_coint_pvalue=context.config.max_coint_pvalue,
                    min_half_life=context.config.min_half_life,
                    max_half_life=context.config.max_half_life,
                )
                rejection_reasons = self._candidate_rejection_reasons(
                    metrics=metrics,
                    stability=stability,
                    config=context.config,
                    require_cointegration=require_cointegration,
                )
                ranking_components = self._candidate_ranking_components(
                    metrics=metrics,
                    stability=stability,
                    config=context.config,
                )
                ranking_score = float(ranking_components["ranking_score"])

                if rejection_reasons:
                    if include_rejections:
                        for reason in rejection_reasons:
                            rejection_summary[reason] = rejection_summary.get(reason, 0) + 1
                        rejected_pairs.append(
                            {
                                "pair_label": f"{y_ticker}~{x_ticker}",
                                "y_ticker": y_ticker,
                                "x_ticker": x_ticker,
                                "sector_group": context.sector_map[y_ticker],
                                "return_corr": float(metrics.return_corr),
                                "level_corr": float(metrics.level_corr),
                                "coint_pvalue": float(metrics.coint_pvalue),
                                "adf_pvalue": float(metrics.adf_pvalue),
                                "beta": float(metrics.beta),
                                "half_life": float(metrics.half_life),
                                "ranking_score": ranking_score,
                                "stability": stability,
                                "rejection_reasons": rejection_reasons,
                            }
                        )
                    continue

                candidates.append(
                    {
                        "pair_label": f"{y_ticker}~{x_ticker}",
                        "y_ticker": y_ticker,
                        "x_ticker": x_ticker,
                        "sector_group": context.sector_map[y_ticker],
                        "sector_rationale": SECTOR_RATIONALE.get(context.sector_map[y_ticker]),
                        "return_corr": float(metrics.return_corr),
                        "level_corr": float(metrics.level_corr),
                        "coint_t_stat": float(metrics.coint_t_stat),
                        "coint_pvalue": float(metrics.coint_pvalue),
                        "adf_stat": float(metrics.adf_stat),
                        "adf_pvalue": float(metrics.adf_pvalue),
                        "beta": float(metrics.beta),
                        "intercept": float(metrics.intercept),
                        "half_life": float(metrics.half_life),
                        "y_short_score": float(eligible_assets[y_ticker]["short_score"]),
                        "x_short_score": float(eligible_assets[x_ticker]["short_score"]),
                        "y_borrow_rate_annual": float(
                            eligible_assets[y_ticker]["borrow_proxy_rate_annual"]
                        ),
                        "x_borrow_rate_annual": float(
                            eligible_assets[x_ticker]["borrow_proxy_rate_annual"]
                        ),
                        "y_margin_haircut": float(eligible_assets[y_ticker]["margin_haircut"]),
                        "x_margin_haircut": float(eligible_assets[x_ticker]["margin_haircut"]),
                        "y_borrow_source": str(eligible_assets[y_ticker]["borrow_source"]),
                        "x_borrow_source": str(eligible_assets[x_ticker]["borrow_source"]),
                        "ranking_score": ranking_score,
                        "ranking_components": ranking_components,
                        "stability": stability,
                    }
                )

        candidates.sort(
            key=lambda item: (
                -float(item["ranking_score"]),
                float(item["coint_pvalue"]),
                -float(item["return_corr"]),
            )
        )
        if not include_rejections:
            return candidates[:top_n]

        rejected_pairs.sort(
            key=lambda item: (
                -float(item["ranking_score"]),
                float(item["coint_pvalue"]),
                -float(item["return_corr"]),
            )
        )
        return candidates[:top_n], rejected_pairs[:top_n], rejection_summary

    def _pair_stability(
        self,
        *,
        y: pd.Series,
        x: pd.Series,
        max_coint_pvalue: float,
        min_half_life: float,
        max_half_life: float,
    ) -> dict[str, Any]:
        return estimate_pair_stability(
            y,
            x,
            max_coint_pvalue=max_coint_pvalue,
            min_half_life=min_half_life,
            max_half_life=max_half_life,
        ).to_dict()

    def _candidate_rejection_reasons(
        self,
        *,
        metrics: Any,
        stability: dict[str, Any],
        config: PairsTradingConfig,
        require_cointegration: bool,
    ) -> list[str]:
        reasons: list[str] = []
        beta_abs = abs(float(metrics.beta))
        if not np.isfinite(metrics.beta) or metrics.beta <= 0:
            reasons.append("non_positive_beta")
        if beta_abs < config.min_beta_abs:
            reasons.append("beta_too_small")
        if beta_abs > config.max_beta_abs:
            reasons.append("beta_too_large")
        if float(metrics.return_corr) < config.min_return_corr:
            reasons.append("low_return_corr")
        if float(metrics.level_corr) < config.min_level_corr:
            reasons.append("low_level_corr")
        if require_cointegration and float(metrics.coint_pvalue) > config.max_coint_pvalue:
            reasons.append("weak_cointegration")
        if not np.isfinite(metrics.half_life):
            reasons.append("invalid_half_life")
        elif float(metrics.half_life) < config.min_half_life:
            reasons.append("half_life_too_short")
        elif float(metrics.half_life) > config.max_half_life:
            reasons.append("half_life_too_long")
        if float(stability.get("stability_score", 0.0)) < config.min_stability_score:
            reasons.append("low_stability")
        if float(stability.get("structural_break_risk", 1.0)) > config.max_structural_break_risk:
            reasons.append("structural_break_risk")
        return reasons

    def _candidate_ranking_components(
        self,
        *,
        metrics: Any,
        stability: dict[str, Any],
        config: PairsTradingConfig,
    ) -> dict[str, float]:
        beta_abs = abs(float(metrics.beta))
        beta_quality = float(
            np.clip(
                1.0
                - (
                    abs(np.log(max(beta_abs, 1e-9)))
                    / max(np.log(max(config.max_beta_abs, 1.0001)), 1e-9)
                ),
                0.0,
                1.0,
            )
        )
        coint_score = float(1.0 - min(max(float(metrics.coint_pvalue), 0.0), 1.0))
        return_corr_score = float(np.clip((float(metrics.return_corr) + 1.0) / 2.0, 0.0, 1.0))
        level_corr_score = float(np.clip((float(metrics.level_corr) + 1.0) / 2.0, 0.0, 1.0))
        stability_score = float(np.clip(float(stability.get("stability_score", 0.0)), 0.0, 1.0))
        structural_break_penalty = float(
            np.clip(float(stability.get("structural_break_risk", 1.0)), 0.0, 1.0)
        )
        ranking_score = float(
            np.clip(
                (0.28 * coint_score)
                + (0.16 * return_corr_score)
                + (0.10 * level_corr_score)
                + (0.31 * stability_score)
                + (0.15 * beta_quality)
                - (0.08 * structural_break_penalty),
                0.0,
                1.0,
            )
        )
        return {
            "coint_score": coint_score,
            "return_corr_score": return_corr_score,
            "level_corr_score": level_corr_score,
            "stability_score": stability_score,
            "beta_quality": beta_quality,
            "structural_break_penalty": structural_break_penalty,
            "ranking_score": ranking_score,
        }

    def _resolve_scenario_plan(
        self,
        *,
        base_config: PairsTradingConfig,
        require_cointegration: bool,
        scenario_label: str,
        scenario_id: str,
        scenario_variants: list[dict[str, Any]] | None,
        batch_mode: bool,
    ) -> list[dict[str, Any]]:
        if scenario_variants:
            return scenario_variants

        if not batch_mode:
            return [
                {
                    "scenario_id": scenario_id,
                    "label": scenario_label,
                    "require_cointegration": require_cointegration,
                    "overrides": {},
                }
            ]

        return [
            {
                "scenario_id": "realistic_cointegration",
                "label": "Realistic cointegration",
                "require_cointegration": True,
                "overrides": {},
            },
            {
                "scenario_id": "low_friction_cointegration",
                "label": "Low friction cointegration",
                "require_cointegration": True,
                "overrides": {
                    "fee_rate": 0.0,
                    "slippage": 0.0,
                    "short_borrow_rate_annual": 0.0,
                    "use_proxy_short_borrow": False,
                },
            },
            {
                "scenario_id": "no_cointegration_filter",
                "label": "No cointegration filter",
                "require_cointegration": False,
                "overrides": {},
            },
        ]

    def _normalize_tickers(self, tickers: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for ticker in tickers:
            clean = ticker.strip().upper()
            if not clean or clean in seen:
                continue
            normalized.append(clean)
            seen.add(clean)
        if not normalized:
            raise ValueError("At least one ticker must be provided")
        return normalized

    def _build_backtest_id(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        suffix = uuid4().hex[:8]
        return f"pairs_{timestamp}_{suffix}"
