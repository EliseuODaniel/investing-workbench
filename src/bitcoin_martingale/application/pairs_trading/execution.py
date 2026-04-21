"""Scenario execution helpers for pairs-trading workflows."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.bitcoin_martingale.domain.pairs_trading import (
    CointegrationPairsBacktester,
    PairsTradingConfig,
)

from .benchmarks import PairsBenchmarkService
from .contracts import PairsContext, ReconstitutionSegment
from .reporting import PairsReportingService


class PairsScenarioExecutionService:
    """Execute one or more pairs scenarios and build normalized payloads."""

    def __init__(
        self,
        *,
        benchmarks_service: PairsBenchmarkService,
        reporting_service: PairsReportingService,
    ) -> None:
        self.benchmarks_service = benchmarks_service
        self.reporting_service = reporting_service

    def run_scenario(
        self,
        *,
        label: str,
        scenario_id: str,
        context: PairsContext,
        config: PairsTradingConfig,
        require_cointegration: bool,
        benchmark_series: list[dict[str, Any]],
        candidate_pairs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run one scenario in a single resolved universe."""
        return self.execute_scenario_bundle(
            label=label,
            scenario_id=scenario_id,
            context=context,
            config=config,
            require_cointegration=require_cointegration,
            benchmark_series=benchmark_series,
            candidate_pairs=candidate_pairs,
        )["payload"]

    def execute_scenario_bundle(
        self,
        *,
        label: str,
        scenario_id: str,
        context: PairsContext,
        config: PairsTradingConfig,
        require_cointegration: bool,
        benchmark_series: list[dict[str, Any]],
        candidate_pairs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute one scenario and keep both payload and raw frames for reuse."""
        backtester = CointegrationPairsBacktester(
            data_by_ticker=context.data_by_ticker,
            sector_map={ticker: context.sector_map[ticker] for ticker in context.data_by_ticker},
            config=config,
            benchmark_data=(
                self.benchmarks_service.benchmark_dataframe_for_regime(context=context)
                if config.regime_filter != "none"
                else None
            ),
            borrow_overrides=context.borrow_overrides,
        )
        raw_result = backtester.run(require_cointegration=require_cointegration)
        equity_df = raw_result["equity"]
        trades_df = raw_result["trades"]
        selections_df = raw_result["selections"]
        benchmark_equity = self.benchmarks_service.benchmark_reference_equity(
            benchmark_series,
            equity_df.index,
        )
        metrics = self.reporting_service.performance_summary(
            equity_df=equity_df,
            trades_df=trades_df,
            initial_capital=config.initial_capital,
            benchmark_equity=benchmark_equity,
        )
        alpha_decomposition = self.reporting_service.build_alpha_decomposition(
            equity_df=equity_df,
            trades_df=trades_df,
            initial_capital=config.initial_capital,
            cash_yield_total=float(raw_result["cash_yield_total"]),
            benchmark_series=benchmark_series,
        )
        pair_summary = self.reporting_service.pair_selection_summary(selections_df)
        pair_pnl = self.reporting_service.pair_pnl_summary(trades_df)
        payload = {
            "scenario_id": scenario_id,
            "label": label,
            "require_cointegration": require_cointegration,
            "config": asdict(config),
            "metrics": metrics,
            "alpha_decomposition": alpha_decomposition,
            "portfolio_summary": self.reporting_service.build_portfolio_summary(
                equity_df=equity_df,
                trades_df=trades_df,
                selections_df=selections_df,
                config=config,
            ),
            "quality_summary": {
                "regime_blocked_entries": int(raw_result["regime_blocked_entries"]),
                "portfolio_cap_blocked_entries": int(raw_result["portfolio_cap_blocked_entries"]),
                "sector_cap_blocked_entries": int(raw_result["sector_cap_blocked_entries"]),
                "cash_yield_total": float(raw_result["cash_yield_total"]),
                "first_trade_date": str(raw_result["first_trade_date"]),
                "selected_pair_count": int(len(pair_summary)),
                "trade_count": int(len(trades_df)),
            },
            "equity_curve": self.benchmarks_service.serialize_equity_curve(equity_df),
            "trades": trades_df.to_dict(orient="records"),
            "selected_pairs": selections_df.to_dict(orient="records"),
            "pair_summary": pair_summary.to_dict(orient="records"),
            "pair_pnl": pair_pnl.to_dict(orient="records"),
            "top_candidate_pairs": candidate_pairs[:10],
        }
        return {
            "payload": payload,
            "equity_df": equity_df,
            "trades_df": trades_df,
            "selections_df": selections_df,
            "benchmark_equity": benchmark_equity,
        }

    def run_reconstituted_scenario(
        self,
        *,
        label: str,
        scenario_id: str,
        segments: list[ReconstitutionSegment],
        config: PairsTradingConfig,
        require_cointegration: bool,
        benchmark_series: list[dict[str, Any]],
        segment_benchmark_sets: list[list[dict[str, Any]]],
        candidate_pairs: list[dict[str, Any]],
        initial_capital: float,
    ) -> dict[str, Any]:
        """Run one scenario across a reconstituted official IBOV universe plan."""
        carry_capital = initial_capital
        segment_payloads: list[dict[str, Any]] = []
        equity_frames = []
        trades_frames = []
        selections_frames = []

        for index, segment in enumerate(segments):
            segment_config = PairsTradingConfig(
                **(asdict(config) | {"initial_capital": carry_capital})
            )
            segment_candidates = [
                item for item in candidate_pairs if item.get("segment_id") == segment.segment_id
            ]
            bundle = self.execute_scenario_bundle(
                label=label,
                scenario_id=scenario_id,
                context=segment.context,
                config=segment_config,
                require_cointegration=require_cointegration,
                benchmark_series=segment_benchmark_sets[index],
                candidate_pairs=segment_candidates,
            )
            payload = dict(bundle["payload"])
            payload["segment_id"] = segment.segment_id
            payload["start_date"] = segment.start_date
            payload["end_date"] = segment.end_date
            payload["requested_as_of_date"] = segment.requested_as_of_date
            payload["resolved_as_of_date"] = segment.resolved_as_of_date
            payload["requested_tickers"] = segment.context.requested_tickers
            payload["eligible_tickers"] = [
                row["ticker"] for row in segment.context.eligible_records
            ]
            segment_payloads.append(payload)
            equity_df = bundle["equity_df"]
            trades_df = bundle["trades_df"]
            selections_df = bundle["selections_df"]
            if not equity_df.empty:
                carry_capital = float(equity_df["equity"].iloc[-1])
                equity_frames.append(equity_df)
            if not trades_df.empty:
                trades_frames.append(trades_df)
            if not selections_df.empty:
                selections_frames.append(selections_df)

        equity_df = self.benchmarks_service.concat_equity_frames(equity_frames)
        trades_df = self.benchmarks_service.concat_tabular_frames(trades_frames)
        selections_df = self.benchmarks_service.concat_tabular_frames(selections_frames)
        benchmark_equity = self.benchmarks_service.benchmark_reference_equity(
            benchmark_series,
            equity_df.index,
        )
        metrics = self.reporting_service.performance_summary(
            equity_df=equity_df,
            trades_df=trades_df,
            initial_capital=initial_capital,
            benchmark_equity=benchmark_equity,
        )
        cash_yield_total = float(
            sum(
                float(((segment["quality_summary"] or {}).get("cash_yield_total", 0.0)))
                for segment in segment_payloads
            )
        )
        alpha_decomposition = self.reporting_service.build_alpha_decomposition(
            equity_df=equity_df,
            trades_df=trades_df,
            initial_capital=initial_capital,
            cash_yield_total=cash_yield_total,
            benchmark_series=benchmark_series,
        )
        pair_summary = self.reporting_service.pair_selection_summary(selections_df)
        pair_pnl = self.reporting_service.pair_pnl_summary(trades_df)
        return {
            "scenario_id": scenario_id,
            "label": label,
            "require_cointegration": require_cointegration,
            "config": asdict(config),
            "metrics": metrics,
            "alpha_decomposition": alpha_decomposition,
            "portfolio_summary": self.reporting_service.build_portfolio_summary(
                equity_df=equity_df,
                trades_df=trades_df,
                selections_df=selections_df,
                config=config,
            ),
            "quality_summary": {
                "regime_blocked_entries": int(
                    sum(
                        int(((segment["quality_summary"] or {}).get("regime_blocked_entries", 0)))
                        for segment in segment_payloads
                    )
                ),
                "portfolio_cap_blocked_entries": int(
                    sum(
                        int(
                            (
                                (segment["quality_summary"] or {}).get(
                                    "portfolio_cap_blocked_entries",
                                    0,
                                )
                            )
                        )
                        for segment in segment_payloads
                    )
                ),
                "sector_cap_blocked_entries": int(
                    sum(
                        int(
                            (
                                (segment["quality_summary"] or {}).get(
                                    "sector_cap_blocked_entries",
                                    0,
                                )
                            )
                        )
                        for segment in segment_payloads
                    )
                ),
                "cash_yield_total": cash_yield_total,
                "first_trade_date": (
                    str(equity_df.index.min().date())
                    if not equity_df.empty
                    else segments[0].start_date
                ),
                "selected_pair_count": int(len(pair_summary)),
                "trade_count": int(len(trades_df)),
                "reconstitution_segment_count": len(segment_payloads),
            },
            "equity_curve": self.benchmarks_service.serialize_equity_curve(equity_df),
            "trades": trades_df.to_dict(orient="records"),
            "selected_pairs": selections_df.to_dict(orient="records"),
            "pair_summary": pair_summary.to_dict(orient="records"),
            "pair_pnl": pair_pnl.to_dict(orient="records"),
            "top_candidate_pairs": candidate_pairs[:10],
            "segments": segment_payloads,
            "reconstitution_enabled": True,
        }
