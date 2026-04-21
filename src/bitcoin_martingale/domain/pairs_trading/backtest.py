"""Walk-forward cointegration pairs-trading backtester."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.data import get_data
from src.selic import get_daily_rate, get_or_create_daily_selic_data

from .models import (
    BorrowOverride,
    ClosedPairTrade,
    OpenPairPosition,
    PairSelection,
    PendingOrder,
    UniverseAsset,
)
from .statistics import (
    apply_split_adjustment,
    compute_zscore,
    estimate_pair_stability,
    estimate_short_borrow_profile,
    evaluate_pair_orientations,
    fit_ols,
)


@dataclass(slots=True)
class PairsTradingConfig:
    initial_capital: float = 100000.0
    formation_window: int = 252
    test_window: int = 21
    step_window: int = 21
    entry_zscore: float = 2.0
    exit_zscore: float = 0.5
    stop_zscore: float = 4.0
    max_holding_days: int = 30
    max_pairs: int = 3
    pair_allocation_pct: float = 0.30
    min_median_notional_brl: float = 90_000_000.0
    min_price: float = 5.0
    min_return_corr: float = 0.25
    min_level_corr: float = 0.10
    max_coint_pvalue: float = 0.10
    min_half_life: float = 2.0
    max_half_life: float = 60.0
    min_stability_score: float = 0.35
    max_structural_break_risk: float = 0.75
    min_beta_abs: float = 0.10
    max_beta_abs: float = 3.00
    zscore_window: int = 60
    fee_rate: float = 0.0003
    slippage: float = 0.0005
    short_borrow_rate_annual: float = 0.05
    use_proxy_short_borrow: bool = False
    proxy_borrow_base_rate_annual: float = 0.03
    proxy_borrow_max_rate_annual: float = 0.12
    proxy_min_short_score: float = 0.35
    proxy_borrow_vol_floor: float = 0.20
    proxy_borrow_vol_cap: float = 0.80
    apply_cash_yield: bool = False
    use_real_selic: bool = False
    selic_path: str = "data/selic_daily.csv"
    selic_fallback_rate: float = 0.13
    cash_collateral_ratio: float = 1.0
    explicit_margin_model: bool = False
    short_margin_haircut: float = 0.50
    dynamic_beta: bool = False
    rolling_beta_window: int = 60
    regime_filter: str = "none"
    regime_ma_window: int = 63
    regime_max_deviation: float = 0.08
    regime_vol_window: int = 21
    regime_vol_lookback: int = 252
    regime_vol_quantile: float = 0.75
    portfolio_construction: str = "equal_notional"
    target_pair_volatility_annual: float = 0.18
    min_pair_allocation_pct: float = 0.08
    max_pair_allocation_pct: float = 0.40
    max_gross_exposure_pct: float = 1.50
    max_net_exposure_pct: float = 0.20
    max_sector_pairs: int = 1
    borrow_snapshot_path: str | None = None


class CointegrationPairsBacktester:
    def __init__(
        self,
        *,
        data_by_ticker: dict[str, pd.DataFrame],
        sector_map: dict[str, str],
        config: PairsTradingConfig,
        benchmark_data: pd.DataFrame | None = None,
        borrow_overrides: dict[str, BorrowOverride] | None = None,
    ) -> None:
        self.data_by_ticker = {
            ticker: apply_split_adjustment(df) for ticker, df in data_by_ticker.items()
        }
        self.sector_map = sector_map
        self.config = config
        self.regime_benchmark = (
            apply_split_adjustment(benchmark_data) if benchmark_data is not None else None
        )
        self.borrow_overrides = borrow_overrides or {}
        self.common_index = self._build_common_index()
        self.selic_data = self._load_selic_data()
        self.regime_ok = self._build_regime_filter()

    def _build_common_index(self) -> pd.DatetimeIndex:
        indexes = [pd.DatetimeIndex(df.index) for df in self.data_by_ticker.values()]
        if self.config.regime_filter != "none" and self.regime_benchmark is not None:
            indexes.append(pd.DatetimeIndex(self.regime_benchmark.index))
        common = indexes[0]
        for index in indexes[1:]:
            common = common.intersection(index)
        return pd.DatetimeIndex(sorted(common))

    def _load_selic_data(self) -> pd.DataFrame | None:
        if not self.config.apply_cash_yield or not self.config.use_real_selic:
            return None
        start_date = str(self.common_index.min().date())
        end_date = str(self.common_index.max().date())
        return get_or_create_daily_selic_data(
            path=self.config.selic_path,
            use_download=True,
            start_date=start_date,
            end_date=end_date,
        )

    def _build_regime_filter(self) -> pd.Series | None:
        if self.config.regime_filter == "none" or self.regime_benchmark is None:
            return None

        close = self.regime_benchmark.get("Adj Close", self.regime_benchmark["Close_sa"])
        aligned = pd.Series(close, dtype=float).reindex(self.common_index).ffill()
        ma = aligned.rolling(self.config.regime_ma_window).mean()
        deviation = (aligned / ma - 1.0).abs()
        realized_vol = aligned.pct_change().rolling(self.config.regime_vol_window).std(
            ddof=1
        ) * np.sqrt(252.0)
        vol_cap = realized_vol.rolling(
            self.config.regime_vol_lookback,
            min_periods=min(
                self.config.regime_vol_lookback, max(self.config.regime_vol_window * 2, 60)
            ),
        ).quantile(self.config.regime_vol_quantile)
        regime_ok = (deviation <= self.config.regime_max_deviation) & (realized_vol <= vol_cap)
        return regime_ok.fillna(False)

    def _estimate_borrow_profile(
        self,
        *,
        ticker: str,
        index: pd.DatetimeIndex,
    ):
        filtered = self.data_by_ticker[ticker].loc[index]
        profile = estimate_short_borrow_profile(
            close=filtered["Close_sa"],
            volume=filtered["Volume"],
            min_median_notional_brl=self.config.min_median_notional_brl,
            min_price=self.config.min_price,
            base_rate_annual=self.config.proxy_borrow_base_rate_annual,
            max_rate_annual=self.config.proxy_borrow_max_rate_annual,
            min_short_score=self.config.proxy_min_short_score,
            vol_floor=self.config.proxy_borrow_vol_floor,
            vol_cap=self.config.proxy_borrow_vol_cap,
        )
        override = self.borrow_overrides.get(ticker)
        if override is None:
            if self.config.use_proxy_short_borrow:
                return profile
            return type(profile)(
                median_notional_brl=profile.median_notional_brl,
                realized_vol_annual=profile.realized_vol_annual,
                liquidity_score=profile.liquidity_score,
                short_score=profile.short_score,
                borrow_rate_annual=self.config.short_borrow_rate_annual,
                short_eligible=profile.short_eligible,
                margin_haircut=self.config.short_margin_haircut,
                source="flat_rate",
            )
        return type(profile)(
            median_notional_brl=profile.median_notional_brl,
            realized_vol_annual=profile.realized_vol_annual,
            liquidity_score=profile.liquidity_score,
            short_score=profile.short_score,
            borrow_rate_annual=(
                float(override.borrow_rate_annual)
                if override.borrow_rate_annual is not None
                else profile.borrow_rate_annual
            ),
            short_eligible=(
                bool(override.short_eligible)
                if override.short_eligible is not None
                else profile.short_eligible
            ),
            margin_haircut=(
                float(override.margin_haircut)
                if override.margin_haircut is not None
                else self.config.short_margin_haircut
            ),
            source=override.source,
        )

    def _borrow_profiles_for_index(self, index: pd.DatetimeIndex) -> dict[str, Any]:
        return {
            ticker: self._estimate_borrow_profile(ticker=ticker, index=index)
            for ticker in self.data_by_ticker
        }

    def _borrow_constraint_active(self, ticker: str) -> bool:
        override = self.borrow_overrides.get(ticker)
        return self.config.use_proxy_short_borrow or (
            override is not None and override.short_eligible is not None
        )

    def build_universe(self) -> list[UniverseAsset]:
        assets: list[UniverseAsset] = []
        borrow_profiles = self._borrow_profiles_for_index(self.common_index)
        for ticker, dataframe in self.data_by_ticker.items():
            filtered = dataframe.loc[self.common_index]
            borrow_profile = borrow_profiles[ticker]
            median_notional = float((filtered["Close_sa"] * filtered["Volume"]).median())
            min_close = float(filtered["Close_sa"].min())
            max_close = float(filtered["Close_sa"].max())
            short_eligible = median_notional >= self.config.min_median_notional_brl
            if self._borrow_constraint_active(ticker):
                short_eligible = short_eligible and borrow_profile.short_eligible
            assets.append(
                UniverseAsset(
                    ticker=ticker,
                    sector_group=self.sector_map[ticker],
                    rows=len(filtered),
                    start=str(filtered.index.min().date()),
                    end=str(filtered.index.max().date()),
                    median_notional_brl=median_notional,
                    min_close=min_close,
                    max_close=max_close,
                    short_eligible=short_eligible,
                    borrow_proxy_rate_annual=borrow_profile.borrow_rate_annual,
                    short_score=borrow_profile.short_score,
                    realized_vol_annual=borrow_profile.realized_vol_annual,
                    margin_haircut=borrow_profile.margin_haircut,
                    borrow_source=borrow_profile.source,
                )
            )
        assets.sort(key=lambda item: item.median_notional_brl, reverse=True)
        return assets

    def eligible_universe(self) -> list[UniverseAsset]:
        return [
            asset
            for asset in self.build_universe()
            if asset.rows >= len(self.common_index) * 0.98
            and asset.median_notional_brl >= self.config.min_median_notional_brl
            and asset.min_close >= self.config.min_price
            and asset.short_eligible
            and (
                not self.config.use_proxy_short_borrow
                or asset.short_score >= self.config.proxy_min_short_score
            )
        ]

    def _selection_windows(self) -> list[tuple[str, pd.DatetimeIndex, pd.DatetimeIndex]]:
        windows: list[tuple[str, pd.DatetimeIndex, pd.DatetimeIndex]] = []
        cursor = self.config.formation_window
        window_number = 1
        while cursor < len(self.common_index):
            formation = self.common_index[cursor - self.config.formation_window : cursor]
            test = self.common_index[cursor : cursor + self.config.test_window]
            if len(test) == 0:
                break
            windows.append((f"window_{window_number:03d}", formation, test))
            cursor += self.config.step_window
            window_number += 1
        return windows

    def select_pairs(
        self,
        *,
        formation_index: pd.DatetimeIndex,
        test_index: pd.DatetimeIndex,
        require_cointegration: bool,
    ) -> list[PairSelection]:
        eligible_assets = self.eligible_universe()
        tickers = [asset.ticker for asset in eligible_assets]
        borrow_profiles = self._borrow_profiles_for_index(formation_index)
        candidates: list[PairSelection] = []

        for left_idx, left in enumerate(tickers):
            for right in tickers[left_idx + 1 :]:
                same_group = self.sector_map[left] == self.sector_map[right]
                if not same_group:
                    continue

                left_profile = borrow_profiles[left]
                right_profile = borrow_profiles[right]
                if (
                    self._borrow_constraint_active(left) or self._borrow_constraint_active(right)
                ) and (not left_profile.short_eligible or not right_profile.short_eligible):
                    continue

                left_series = self.data_by_ticker[left].loc[formation_index, "Close_sa"]
                right_series = self.data_by_ticker[right].loc[formation_index, "Close_sa"]
                orientation, metrics = evaluate_pair_orientations(left_series, right_series)
                stability = estimate_pair_stability(
                    left_series if orientation == "ab" else right_series,
                    right_series if orientation == "ab" else left_series,
                    max_coint_pvalue=self.config.max_coint_pvalue,
                    min_half_life=self.config.min_half_life,
                    max_half_life=self.config.max_half_life,
                )

                if metrics.beta <= 0:
                    continue
                if abs(metrics.beta) < self.config.min_beta_abs:
                    continue
                if abs(metrics.beta) > self.config.max_beta_abs:
                    continue
                if metrics.return_corr < self.config.min_return_corr:
                    continue
                if metrics.level_corr < self.config.min_level_corr:
                    continue
                if require_cointegration and metrics.coint_pvalue > self.config.max_coint_pvalue:
                    continue
                if not np.isfinite(metrics.half_life):
                    continue
                if (
                    metrics.half_life < self.config.min_half_life
                    or metrics.half_life > self.config.max_half_life
                ):
                    continue
                if stability.stability_score < self.config.min_stability_score:
                    continue
                if stability.structural_break_risk > self.config.max_structural_break_risk:
                    continue

                if orientation == "ab":
                    y_ticker, x_ticker = left, right
                else:
                    y_ticker, x_ticker = right, left

                beta_quality = float(
                    np.clip(
                        1.0
                        - (
                            abs(np.log(max(abs(metrics.beta), 1e-9)))
                            / max(np.log(max(self.config.max_beta_abs, 1.0001)), 1e-9)
                        ),
                        0.0,
                        1.0,
                    )
                )
                ranking_score = float(
                    np.clip(
                        (0.30 * (1.0 - min(max(metrics.coint_pvalue, 0.0), 1.0)))
                        + (0.15 * min(max(metrics.return_corr, -1.0), 1.0))
                        + (0.10 * min(max(metrics.level_corr, -1.0), 1.0))
                        + (0.30 * stability.stability_score)
                        + (0.15 * beta_quality),
                        0.0,
                        1.0,
                    )
                )

                candidates.append(
                    PairSelection(
                        y_ticker=y_ticker,
                        x_ticker=x_ticker,
                        sector_group=self.sector_map[y_ticker],
                        formation_start=str(formation_index[0].date()),
                        formation_end=str(formation_index[-1].date()),
                        trade_start=str(test_index[0].date()),
                        trade_end=str(test_index[-1].date()),
                        return_corr=metrics.return_corr,
                        level_corr=metrics.level_corr,
                        coint_t_stat=metrics.coint_t_stat,
                        coint_pvalue=metrics.coint_pvalue,
                        adf_stat=metrics.adf_stat,
                        adf_pvalue=metrics.adf_pvalue,
                        beta=metrics.beta,
                        intercept=metrics.intercept,
                        half_life=metrics.half_life,
                        same_group=same_group,
                        y_borrow_rate_annual=borrow_profiles[y_ticker].borrow_rate_annual,
                        x_borrow_rate_annual=borrow_profiles[x_ticker].borrow_rate_annual,
                        y_short_score=borrow_profiles[y_ticker].short_score,
                        x_short_score=borrow_profiles[x_ticker].short_score,
                        y_margin_haircut=borrow_profiles[y_ticker].margin_haircut,
                        x_margin_haircut=borrow_profiles[x_ticker].margin_haircut,
                        y_borrow_source=borrow_profiles[y_ticker].source,
                        x_borrow_source=borrow_profiles[x_ticker].source,
                        stability_score=stability.stability_score,
                        structural_break_risk=stability.structural_break_risk,
                        ranking_score=ranking_score,
                        spread_history_seed=metrics.spread_history,
                    )
                )

        if require_cointegration:
            candidates.sort(
                key=lambda item: (
                    -item.ranking_score,
                    item.coint_pvalue,
                    item.adf_pvalue,
                    item.structural_break_risk,
                    -item.return_corr,
                )
            )
        else:
            candidates.sort(
                key=lambda item: (
                    -item.ranking_score,
                    -item.return_corr,
                    item.coint_pvalue,
                    item.half_life,
                )
            )

        chosen: list[PairSelection] = []
        used_assets: set[str] = set()
        for candidate in candidates:
            if candidate.y_ticker in used_assets or candidate.x_ticker in used_assets:
                continue
            chosen.append(candidate)
            used_assets.add(candidate.y_ticker)
            used_assets.add(candidate.x_ticker)
            if len(chosen) >= self.config.max_pairs:
                break
        return chosen

    def run(self, *, require_cointegration: bool) -> dict[str, Any]:
        cash = self.config.initial_capital
        cash_yield_total = 0.0
        regime_blocked_entries = 0
        portfolio_cap_blocked_entries = 0
        sector_cap_blocked_entries = 0
        equity_records: list[dict[str, Any]] = []
        closed_trades: list[ClosedPairTrade] = []
        selections: list[PairSelection] = []
        pending_orders: dict[str, PendingOrder] = {}
        open_positions: dict[str, OpenPairPosition] = {}
        pair_histories: dict[str, list[float]] = {}
        selection_by_label: dict[str, PairSelection] = {}
        trade_counter = 1

        windows = self._selection_windows()
        market_calendar = self.common_index
        first_trade_date = windows[0][2][0] if windows else market_calendar[0]

        for calendar_idx, date in enumerate(market_calendar):
            if calendar_idx > 0:
                cash, interest_earned = self._apply_cash_yield(
                    date=date, cash=cash, open_positions=open_positions
                )
                cash_yield_total += interest_earned

            if calendar_idx < self.config.formation_window:
                equity_records.append(
                    self._equity_snapshot(date=date, cash=cash, open_positions=open_positions)
                )
                continue

            new_window = next(
                (window for window in windows if len(window[2]) > 0 and window[2][0] == date), None
            )
            if new_window is not None:
                _, formation_index, test_index = new_window
                current_selections = self.select_pairs(
                    formation_index=formation_index,
                    test_index=test_index,
                    require_cointegration=require_cointegration,
                )
                selections.extend(current_selections)
                pair_histories = {
                    selection.pair_label: list(selection.spread_history_seed)
                    for selection in current_selections
                }
                selection_by_label = {
                    selection.pair_label: selection for selection in current_selections
                }

            if pending_orders:
                cash, newly_closed, trade_counter, blocked_entries = self._execute_pending_orders(
                    date=date,
                    cash=cash,
                    pending_orders=pending_orders,
                    open_positions=open_positions,
                    selection_by_label=selection_by_label,
                    trade_counter=trade_counter,
                )
                closed_trades.extend(newly_closed)
                portfolio_cap_blocked_entries += blocked_entries["portfolio_cap"]
                sector_cap_blocked_entries += blocked_entries["sector_cap"]
                pending_orders = {}

            cash = self._apply_carry_costs(date=date, cash=cash, open_positions=open_positions)

            if selection_by_label:
                current_window_end = max(
                    pd.Timestamp(selection.trade_end) for selection in selection_by_label.values()
                )
                regime_allows_entries = self._regime_allows_trading(date)
                for pair_label, selection in selection_by_label.items():
                    beta, spread, zscore = self._signal_state(
                        date=date,
                        selection=selection,
                        pair_histories=pair_histories,
                    )
                    position = open_positions.get(pair_label)
                    if position is not None:
                        position.holding_days += 1
                        if not regime_allows_entries and self.config.regime_filter != "none":
                            pending_orders[pair_label] = PendingOrder(
                                pair_label=pair_label,
                                action="exit",
                                signal_date=str(date.date()),
                                execute_date=str(date.date()),
                                reason="regime_filter",
                                zscore=zscore,
                            )
                        elif zscore is not None and abs(zscore) <= self.config.exit_zscore:
                            pending_orders[pair_label] = PendingOrder(
                                pair_label=pair_label,
                                action="exit",
                                signal_date=str(date.date()),
                                execute_date=str(date.date()),
                                reason="mean_reversion",
                                zscore=zscore,
                            )
                        elif zscore is not None and abs(zscore) >= self.config.stop_zscore:
                            pending_orders[pair_label] = PendingOrder(
                                pair_label=pair_label,
                                action="exit",
                                signal_date=str(date.date()),
                                execute_date=str(date.date()),
                                reason="z_stop",
                                zscore=zscore,
                            )
                        elif position.holding_days >= self.config.max_holding_days:
                            pending_orders[pair_label] = PendingOrder(
                                pair_label=pair_label,
                                action="exit",
                                signal_date=str(date.date()),
                                execute_date=str(date.date()),
                                reason="time_stop",
                                zscore=zscore,
                            )
                    elif (
                        zscore is not None
                        and date < current_window_end
                        and len(open_positions) < self.config.max_pairs
                        and self._assets_available(
                            selection=selection, open_positions=open_positions
                        )
                    ):
                        if not regime_allows_entries and abs(zscore) >= self.config.entry_zscore:
                            regime_blocked_entries += 1
                        elif zscore >= self.config.entry_zscore:
                            pending_orders[pair_label] = PendingOrder(
                                pair_label=pair_label,
                                action="entry",
                                signal_date=str(date.date()),
                                execute_date=str(date.date()),
                                reason="zscore_entry",
                                direction="short_spread",
                                zscore=zscore,
                                beta_override=beta,
                            )
                        elif zscore <= -self.config.entry_zscore:
                            pending_orders[pair_label] = PendingOrder(
                                pair_label=pair_label,
                                action="entry",
                                signal_date=str(date.date()),
                                execute_date=str(date.date()),
                                reason="zscore_entry",
                                direction="long_spread",
                                zscore=zscore,
                                beta_override=beta,
                            )

                    if not self.config.dynamic_beta:
                        pair_histories.setdefault(pair_label, []).append(spread)

                window_end = max(
                    pd.Timestamp(selection.trade_end) for selection in selection_by_label.values()
                )
                if date == window_end and open_positions:
                    forced_closes: list[ClosedPairTrade] = []
                    for pair_label in list(open_positions):
                        trade = self._close_position(
                            date=date,
                            position=open_positions.pop(pair_label),
                            reason="window_rebalance",
                            z_exit=0.0,
                        )
                        cash += trade.cash_release - trade.exit_fees
                        forced_closes.append(trade)
                    closed_trades.extend(forced_closes)
                    pending_orders = {}
                    pair_histories = {}
                    selection_by_label = {}

            equity_records.append(
                self._equity_snapshot(date=date, cash=cash, open_positions=open_positions)
            )

        trades_df = pd.DataFrame([trade.to_dict() for trade in closed_trades])
        equity_df = pd.DataFrame(equity_records).set_index("date")
        selections_df = pd.DataFrame([selection.to_dict() for selection in selections])
        return {
            "equity": equity_df,
            "trades": trades_df,
            "selections": selections_df,
            "eligible_universe": pd.DataFrame(
                [asset.to_dict() for asset in self.eligible_universe()]
            ),
            "common_index": market_calendar,
            "first_trade_date": str(first_trade_date.date()),
            "cash_yield_total": cash_yield_total,
            "regime_blocked_entries": regime_blocked_entries,
            "portfolio_cap_blocked_entries": portfolio_cap_blocked_entries,
            "sector_cap_blocked_entries": sector_cap_blocked_entries,
        }

    def _regime_allows_trading(self, date: pd.Timestamp) -> bool:
        if self.regime_ok is None:
            return True
        if date not in self.regime_ok.index:
            return False
        return bool(self.regime_ok.loc[date])

    def _gross_exposure_value(
        self,
        *,
        date: pd.Timestamp,
        open_positions: dict[str, OpenPairPosition],
        price_field: str,
    ) -> float:
        gross_exposure = 0.0
        for position in open_positions.values():
            long_price = float(self.data_by_ticker[position.long_ticker].loc[date, price_field])
            short_price = float(self.data_by_ticker[position.short_ticker].loc[date, price_field])
            gross_exposure += position.long_shares * long_price
            gross_exposure += position.short_shares * short_price
        return gross_exposure

    def _cash_yield_base(
        self,
        *,
        date: pd.Timestamp,
        cash: float,
        open_positions: dict[str, OpenPairPosition],
    ) -> float:
        if cash <= 0:
            return 0.0
        if self.config.explicit_margin_model:
            return max(cash, 0.0)
        reserved = self._gross_exposure_value(
            date=date, open_positions=open_positions, price_field="Open_sa"
        )
        return max(cash - (reserved * self.config.cash_collateral_ratio), 0.0)

    def _apply_cash_yield(
        self,
        *,
        date: pd.Timestamp,
        cash: float,
        open_positions: dict[str, OpenPairPosition],
    ) -> tuple[float, float]:
        if not self.config.apply_cash_yield:
            return cash, 0.0
        base_cash = self._cash_yield_base(date=date, cash=cash, open_positions=open_positions)
        if base_cash <= 0:
            return cash, 0.0
        if self.config.use_real_selic and self.selic_data is not None and not self.selic_data.empty:
            daily_rate = get_daily_rate(
                self.selic_data,
                date,
                fallback_rate_annual=self.config.selic_fallback_rate,
            )
        else:
            daily_rate = (1.0 + self.config.selic_fallback_rate) ** (1.0 / 252.0) - 1.0
        interest = base_cash * daily_rate
        return cash + interest, interest

    def _signal_state(
        self,
        *,
        date: pd.Timestamp,
        selection: PairSelection,
        pair_histories: dict[str, list[float]],
    ) -> tuple[float, float, float | None]:
        if self.config.dynamic_beta:
            history_length = max(self.config.rolling_beta_window, self.config.zscore_window + 1)
            aligned = pd.concat(
                [
                    self.data_by_ticker[selection.y_ticker].loc[:date, "Close_sa"],
                    self.data_by_ticker[selection.x_ticker].loc[:date, "Close_sa"],
                ],
                axis=1,
            ).dropna()
            aligned.columns = ["y", "x"]
            aligned = aligned.tail(history_length)
            if len(aligned) >= max(20, min(self.config.rolling_beta_window, 20)):
                beta_window = aligned.tail(self.config.rolling_beta_window)
                regression = fit_ols(beta_window["y"], beta_window["x"])
                beta = (
                    regression.beta
                    if np.isfinite(regression.beta) and regression.beta > 0
                    else selection.beta
                )
                spread_series = aligned["y"] - (beta * aligned["x"])
                spread = float(spread_series.iloc[-1])
                history = spread_series.iloc[:-1].astype(float).tolist()
                zscore = compute_zscore(history, spread, self.config.zscore_window)
                return beta, spread, zscore

        y_close = float(self.data_by_ticker[selection.y_ticker].loc[date, "Close_sa"])
        x_close = float(self.data_by_ticker[selection.x_ticker].loc[date, "Close_sa"])
        spread = y_close - (selection.beta * x_close)
        zscore = compute_zscore(
            pair_histories.get(selection.pair_label, []), spread, self.config.zscore_window
        )
        return selection.beta, spread, zscore

    def _equity_snapshot(
        self,
        *,
        date: pd.Timestamp,
        cash: float,
        open_positions: dict[str, OpenPairPosition],
    ) -> dict[str, Any]:
        unrealized = 0.0
        gross_exposure = 0.0
        net_exposure = 0.0
        equity = cash
        for position in open_positions.values():
            long_close = float(self.data_by_ticker[position.long_ticker].loc[date, "Close_sa"])
            short_close = float(self.data_by_ticker[position.short_ticker].loc[date, "Close_sa"])
            long_value = position.long_shares * long_close
            short_value = position.short_shares * short_close
            unrealized += position.long_shares * (long_close - position.entry_long_price)
            unrealized += position.short_shares * (position.entry_short_price - short_close)
            gross_exposure += long_value + short_value
            net_exposure += long_value - short_value
            if self.config.explicit_margin_model:
                equity += (
                    position.margin_posted + long_value + position.short_notional - short_value
                )
        if not self.config.explicit_margin_model:
            equity = cash + unrealized
        return {
            "date": date,
            "cash": cash,
            "cash_yield_base": self._cash_yield_base(
                date=date, cash=cash, open_positions=open_positions
            ),
            "unrealized_pnl": unrealized,
            "gross_exposure": gross_exposure,
            "net_exposure": net_exposure,
            "open_positions": len(open_positions),
            "regime_ok": self._regime_allows_trading(date),
            "equity": equity,
        }

    def _assets_available(
        self,
        *,
        selection: PairSelection,
        open_positions: dict[str, OpenPairPosition],
    ) -> bool:
        busy_assets = {position.long_ticker for position in open_positions.values()} | {
            position.short_ticker for position in open_positions.values()
        }
        return selection.y_ticker not in busy_assets and selection.x_ticker not in busy_assets

    def _open_exposure_snapshot(
        self,
        *,
        date: pd.Timestamp,
        open_positions: dict[str, OpenPairPosition],
        price_field: str,
    ) -> tuple[float, float]:
        gross_exposure = 0.0
        net_exposure = 0.0
        for position in open_positions.values():
            long_price = float(self.data_by_ticker[position.long_ticker].loc[date, price_field])
            short_price = float(self.data_by_ticker[position.short_ticker].loc[date, price_field])
            long_value = position.long_shares * long_price
            short_value = position.short_shares * short_price
            gross_exposure += long_value + short_value
            net_exposure += long_value - short_value
        return gross_exposure, net_exposure

    def _pair_return_volatility(
        self,
        *,
        date: pd.Timestamp,
        selection: PairSelection,
        beta: float,
    ) -> float | None:
        history_length = max(self.config.zscore_window, 20)
        aligned = pd.concat(
            [
                self.data_by_ticker[selection.y_ticker].loc[:date, "Close_sa"].pct_change(),
                self.data_by_ticker[selection.x_ticker].loc[:date, "Close_sa"].pct_change(),
            ],
            axis=1,
        ).dropna()
        if aligned.empty:
            return None
        aligned.columns = ["y_ret", "x_ret"]
        tail = aligned.tail(history_length)
        if len(tail) < min(history_length, 20):
            return None
        spread_return = tail["y_ret"] - (beta * tail["x_ret"])
        volatility = float(spread_return.std(ddof=1) * np.sqrt(252.0))
        return volatility if np.isfinite(volatility) and volatility > 0 else None

    def _plan_entry_position(
        self,
        *,
        date: pd.Timestamp,
        current_equity: float,
        selection: PairSelection,
        direction: str,
        beta: float,
        open_positions: dict[str, OpenPairPosition],
    ) -> tuple[dict[str, float | str] | None, str | None]:
        if len(open_positions) >= self.config.max_pairs:
            return None, "portfolio_cap"
        if not self._assets_available(selection=selection, open_positions=open_positions):
            return None, "portfolio_cap"
        if (
            sum(
                1
                for position in open_positions.values()
                if position.sector_group == selection.sector_group
            )
            >= self.config.max_sector_pairs
        ):
            return None, "sector_cap"

        allocation_pct = self.config.pair_allocation_pct
        if self.config.portfolio_construction == "risk_parity":
            pair_volatility = self._pair_return_volatility(
                date=date,
                selection=selection,
                beta=beta,
            )
            if pair_volatility is not None:
                allocation_pct *= self.config.target_pair_volatility_annual / max(
                    pair_volatility,
                    1e-9,
                )
        allocation_pct = float(
            np.clip(
                allocation_pct,
                self.config.min_pair_allocation_pct,
                self.config.max_pair_allocation_pct,
            )
        )
        if allocation_pct <= 0:
            return None, "portfolio_cap"

        gross_open, net_open = self._open_exposure_snapshot(
            date=date,
            open_positions=open_positions,
            price_field="Open_sa",
        )
        gross_capacity = max(
            (current_equity * self.config.max_gross_exposure_pct) - gross_open, 0.0
        )
        if gross_capacity <= 0:
            return None, "portfolio_cap"
        allocation_value = min(current_equity * allocation_pct, gross_capacity)
        if allocation_value <= 0:
            return None, "portfolio_cap"

        long_notional = allocation_value / (1.0 + abs(beta))
        short_notional = allocation_value - long_notional
        if direction == "long_spread":
            long_ticker = selection.y_ticker
            short_ticker = selection.x_ticker
            margin_haircut = selection.x_margin_haircut
            short_borrow_rate = selection.x_borrow_rate_annual
            short_borrow_source = selection.x_borrow_source
        else:
            long_ticker = selection.x_ticker
            short_ticker = selection.y_ticker
            long_notional, short_notional = short_notional, long_notional
            margin_haircut = selection.y_margin_haircut
            short_borrow_rate = selection.y_borrow_rate_annual
            short_borrow_source = selection.y_borrow_source

        if not self.config.use_proxy_short_borrow:
            short_borrow_rate = self.config.short_borrow_rate_annual
            short_borrow_source = "flat_rate"

        pair_net_exposure = long_notional - short_notional
        current_net_abs = abs(net_open)
        projected_net_abs = abs(net_open + pair_net_exposure)
        net_capacity_abs = current_equity * self.config.max_net_exposure_pct
        if projected_net_abs > net_capacity_abs and projected_net_abs > current_net_abs:
            if abs(pair_net_exposure) <= 1e-9:
                return None, "portfolio_cap"
            scale = max((net_capacity_abs - current_net_abs) / abs(pair_net_exposure), 0.0)
            allocation_value *= scale
            if allocation_value <= 0:
                return None, "portfolio_cap"
            long_notional = allocation_value / (1.0 + abs(beta))
            short_notional = allocation_value - long_notional
            if direction == "short_spread":
                long_notional, short_notional = short_notional, long_notional

        realized_allocation_pct = allocation_value / max(current_equity, 1e-9)
        if realized_allocation_pct < self.config.min_pair_allocation_pct * 0.5:
            return None, "portfolio_cap"
        return (
            {
                "allocation_pct": realized_allocation_pct,
                "long_notional": long_notional,
                "short_notional": short_notional,
                "long_ticker": long_ticker,
                "short_ticker": short_ticker,
                "margin_haircut": margin_haircut,
                "short_borrow_rate_annual": short_borrow_rate,
                "short_borrow_source": short_borrow_source,
            },
            None,
        )

    def _apply_execution_price(self, *, price: float, side: str) -> tuple[float, float]:
        if side == "buy":
            effective = price * (1.0 + self.config.slippage)
            cost = price * self.config.slippage
        else:
            effective = price * (1.0 - self.config.slippage)
            cost = price * self.config.slippage
        return effective, cost

    def _execute_pending_orders(
        self,
        *,
        date: pd.Timestamp,
        cash: float,
        pending_orders: dict[str, PendingOrder],
        open_positions: dict[str, OpenPairPosition],
        selection_by_label: dict[str, PairSelection],
        trade_counter: int,
    ) -> tuple[float, list[ClosedPairTrade], int, dict[str, int]]:
        closed: list[ClosedPairTrade] = []
        blocked_entries = {"portfolio_cap": 0, "sector_cap": 0}
        current_equity = self._equity_snapshot(date=date, cash=cash, open_positions=open_positions)[
            "equity"
        ]

        for pair_label, order in pending_orders.items():
            if order.action == "exit" and pair_label in open_positions:
                trade = self._close_position(
                    date=date,
                    position=open_positions.pop(pair_label),
                    reason=order.reason,
                    z_exit=float(order.zscore or 0.0),
                )
                cash += trade.cash_release - trade.exit_fees
                closed.append(trade)

        for pair_label, order in pending_orders.items():
            if order.action != "entry" or pair_label in open_positions:
                continue
            selection = selection_by_label.get(pair_label)
            if selection is None or order.direction is None:
                continue
            if not self._assets_available(selection=selection, open_positions=open_positions):
                continue

            beta = float(order.beta_override or selection.beta)
            entry_plan, blocked_reason = self._plan_entry_position(
                date=date,
                current_equity=current_equity,
                selection=selection,
                direction=order.direction,
                beta=beta,
                open_positions=open_positions,
            )
            if entry_plan is None:
                if blocked_reason is not None:
                    blocked_entries[blocked_reason] += 1
                continue

            long_ticker = str(entry_plan["long_ticker"])
            short_ticker = str(entry_plan["short_ticker"])
            long_notional = float(entry_plan["long_notional"])
            short_notional = float(entry_plan["short_notional"])
            allocation_pct = float(entry_plan["allocation_pct"])
            short_borrow_rate_annual = float(entry_plan["short_borrow_rate_annual"])
            short_borrow_source = str(entry_plan["short_borrow_source"])
            margin_haircut = float(entry_plan["margin_haircut"])

            raw_long = float(self.data_by_ticker[long_ticker].loc[date, "Open_sa"])
            raw_short = float(self.data_by_ticker[short_ticker].loc[date, "Open_sa"])
            entry_long_price, long_slip = self._apply_execution_price(price=raw_long, side="buy")
            entry_short_price, short_slip = self._apply_execution_price(
                price=raw_short, side="sell"
            )
            long_shares = long_notional / entry_long_price
            short_shares = short_notional / entry_short_price
            entry_fees = (long_notional + short_notional) * self.config.fee_rate
            margin_posted = (
                short_notional * margin_haircut if self.config.explicit_margin_model else 0.0
            )
            if self.config.explicit_margin_model:
                cash -= long_notional + entry_fees + margin_posted
            else:
                cash -= entry_fees

            open_positions[pair_label] = OpenPairPosition(
                position_id=f"pair_{trade_counter:05d}",
                window_id=selection.trade_start,
                pair_label=pair_label,
                y_ticker=selection.y_ticker,
                x_ticker=selection.x_ticker,
                sector_group=selection.sector_group,
                long_ticker=long_ticker,
                short_ticker=short_ticker,
                direction=order.direction,
                beta=beta,
                z_entry=float(order.zscore or 0.0),
                entry_signal_date=order.signal_date,
                entry_date=str(date.date()),
                entry_long_price=entry_long_price,
                entry_short_price=entry_short_price,
                long_shares=long_shares,
                short_shares=short_shares,
                long_notional=long_notional,
                short_notional=short_notional,
                gross_exposure_entry=long_notional + short_notional,
                allocation_pct=allocation_pct,
                entry_fees=entry_fees,
                entry_slippage_cost=(long_shares * long_slip) + (short_shares * short_slip),
                margin_posted=margin_posted,
                margin_haircut=margin_haircut,
                short_borrow_rate_annual=short_borrow_rate_annual,
                short_borrow_source=short_borrow_source,
            )
            trade_counter += 1
        return cash, closed, trade_counter, blocked_entries

    def _apply_carry_costs(
        self,
        *,
        date: pd.Timestamp,
        cash: float,
        open_positions: dict[str, OpenPairPosition],
    ) -> float:
        for position in open_positions.values():
            daily_short_rate = position.short_borrow_rate_annual / 252.0
            long_dividend = float(
                self.data_by_ticker[position.long_ticker].loc[date, "Dividends"] or 0.0
            )
            short_dividend = float(
                self.data_by_ticker[position.short_ticker].loc[date, "Dividends"] or 0.0
            )
            if long_dividend > 0:
                credit = long_dividend * position.long_shares
                cash += credit
                position.dividend_pnl += credit
            if short_dividend > 0:
                debit = short_dividend * position.short_shares
                cash -= debit
                position.dividend_pnl -= debit

            short_close = float(self.data_by_ticker[position.short_ticker].loc[date, "Close_sa"])
            borrow_cost = position.short_shares * short_close * daily_short_rate
            cash -= borrow_cost
            position.short_borrow_cost += borrow_cost
        return cash

    def _close_position(
        self,
        *,
        date: pd.Timestamp,
        position: OpenPairPosition,
        reason: str,
        z_exit: float,
    ) -> ClosedPairTrade:
        raw_long = float(self.data_by_ticker[position.long_ticker].loc[date, "Close_sa"])
        raw_short = float(self.data_by_ticker[position.short_ticker].loc[date, "Close_sa"])
        exit_long_price, long_slip = self._apply_execution_price(price=raw_long, side="sell")
        exit_short_price, short_slip = self._apply_execution_price(price=raw_short, side="buy")

        long_exit_value = position.long_shares * exit_long_price
        short_exit_value = position.short_shares * exit_short_price
        gross_pnl = (position.long_shares * (exit_long_price - position.entry_long_price)) + (
            position.short_shares * (position.entry_short_price - exit_short_price)
        )
        gross_exposure_exit = long_exit_value + short_exit_value
        exit_fees = gross_exposure_exit * self.config.fee_rate
        total_fees = position.entry_fees + exit_fees
        net_pnl = gross_pnl + position.dividend_pnl - position.short_borrow_cost - total_fees
        cash_release = gross_pnl
        if self.config.explicit_margin_model:
            cash_release = (
                long_exit_value
                + position.short_notional
                - short_exit_value
                + position.margin_posted
            )

        return ClosedPairTrade(
            position_id=position.position_id,
            window_id=position.window_id,
            pair_label=position.pair_label,
            y_ticker=position.y_ticker,
            x_ticker=position.x_ticker,
            sector_group=position.sector_group,
            long_ticker=position.long_ticker,
            short_ticker=position.short_ticker,
            direction=position.direction,
            entry_signal_date=position.entry_signal_date,
            entry_date=position.entry_date,
            exit_date=str(date.date()),
            exit_reason=reason,
            beta=position.beta,
            z_entry=position.z_entry,
            z_exit=z_exit,
            entry_long_price=position.entry_long_price,
            entry_short_price=position.entry_short_price,
            exit_long_price=exit_long_price,
            exit_short_price=exit_short_price,
            long_shares=position.long_shares,
            short_shares=position.short_shares,
            long_notional=position.long_notional,
            short_notional=position.short_notional,
            gross_exposure_entry=position.gross_exposure_entry,
            gross_exposure_exit=gross_exposure_exit,
            allocation_pct=position.allocation_pct,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            entry_fees=position.entry_fees,
            exit_fees=exit_fees,
            fees_paid=total_fees,
            slippage_cost=position.entry_slippage_cost
            + (position.long_shares * long_slip)
            + (position.short_shares * short_slip),
            short_borrow_cost=position.short_borrow_cost,
            short_borrow_rate_annual=position.short_borrow_rate_annual,
            short_borrow_source=position.short_borrow_source,
            dividend_pnl=position.dividend_pnl,
            margin_posted=position.margin_posted,
            margin_haircut=position.margin_haircut,
            cash_release=cash_release,
            holding_days=position.holding_days,
        )


def load_b3_universe_data(
    *,
    tickers: list[str],
    start_date: str,
    end_date: str | None,
    force_download: bool,
) -> dict[str, pd.DataFrame]:
    data_by_ticker: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        cache_path = f"data/{ticker.lower()}_sa.parquet"
        data_by_ticker[ticker] = get_data(
            start=start_date,
            end=end_date,
            cache_path=cache_path,
            force_download=force_download,
            data_source=ticker,
            include_actions=True,
        )
    return data_by_ticker
