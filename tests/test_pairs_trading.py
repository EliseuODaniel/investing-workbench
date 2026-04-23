import numpy as np
import pandas as pd

from src.investing_workbench.domain.pairs_trading import (
    CointegrationPairsBacktester,
    PairsTradingConfig,
    analyze_cointegration,
)
from src.investing_workbench.domain.pairs_trading.statistics import (
    apply_split_adjustment,
    estimate_pair_stability,
    estimate_short_borrow_profile,
)
from src.selic import save_daily_selic_data


def _synthetic_frame(close: np.ndarray, volume: float = 5_000_000.0) -> pd.DataFrame:
    index = pd.bdate_range("2021-01-01", periods=len(close))
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Adj Close": close,
            "Volume": np.full(len(close), volume),
            "Dividends": np.zeros(len(close)),
            "Stock Splits": np.zeros(len(close)),
        },
        index=index,
    )


def test_apply_split_adjustment_keeps_split_day_on_current_scale():
    df = pd.DataFrame(
        {
            "Open": [100.0, 52.0, 53.0],
            "High": [101.0, 53.0, 54.0],
            "Low": [99.0, 51.0, 52.0],
            "Close": [100.0, 52.0, 53.0],
            "Volume": [1_000_000, 1_000_000, 1_000_000],
            "Adj Close": [100.0, 52.0, 53.0],
            "Dividends": [0.0, 0.0, 0.0],
            "Stock Splits": [0.0, 2.0, 0.0],
        },
        index=pd.bdate_range("2021-01-01", periods=3),
    )
    adjusted = apply_split_adjustment(df)

    assert adjusted["Close_sa"].iloc[0] == 50.0
    assert adjusted["Close_sa"].iloc[1] == 52.0
    assert adjusted["Close_sa"].iloc[2] == 53.0


def test_estimate_short_borrow_profile_penalizes_low_liquidity_and_high_volatility():
    liquid_close = pd.Series(np.linspace(20.0, 22.0, 120))
    liquid_volume = pd.Series(np.full(120, 25_000_000.0))
    stressed_close = pd.Series(
        np.concatenate([np.linspace(20.0, 40.0, 60), np.linspace(40.0, 8.0, 60)])
    )
    stressed_volume = pd.Series(np.full(120, 20_000.0))

    good = estimate_short_borrow_profile(
        close=liquid_close,
        volume=liquid_volume,
        min_median_notional_brl=1_000_000.0,
        min_price=1.0,
        base_rate_annual=0.03,
        max_rate_annual=0.12,
        min_short_score=0.35,
    )
    bad = estimate_short_borrow_profile(
        close=stressed_close,
        volume=stressed_volume,
        min_median_notional_brl=1_000_000.0,
        min_price=1.0,
        base_rate_annual=0.03,
        max_rate_annual=0.12,
        min_short_score=0.35,
    )

    assert good.borrow_rate_annual < bad.borrow_rate_annual
    assert good.short_score > bad.short_score
    assert good.short_eligible
    assert not bad.short_eligible


def test_analyze_cointegration_detects_synthetic_pair():
    rng = np.random.default_rng(7)
    x = np.cumsum(rng.normal(0, 1, 400)) + 100
    y = 1.2 * x + rng.normal(0, 0.7, 400)
    result = analyze_cointegration(pd.Series(y), pd.Series(x))

    assert result.coint_pvalue < 0.05
    assert 1.0 < result.beta < 1.4
    assert result.half_life > 0


def test_estimate_pair_stability_scores_stable_pair_above_zero():
    rng = np.random.default_rng(17)
    x = np.cumsum(rng.normal(0, 1, 360)) + 90
    y = 1.1 * x + rng.normal(0, 0.5, 360)
    stability = estimate_pair_stability(
        pd.Series(y),
        pd.Series(x),
        max_coint_pvalue=0.20,
        min_half_life=1.0,
        max_half_life=80.0,
    )

    assert stability.window_count >= 1
    assert stability.stability_score > 0
    assert 0.0 <= stability.structural_break_risk <= 1.0


def test_backtester_produces_selection_and_trade_on_synthetic_pair():
    rng = np.random.default_rng(11)
    x = np.cumsum(rng.normal(0, 1, 420)) + 100
    spread = np.sin(np.linspace(0, 18, 420)) * 4 + rng.normal(0, 0.4, 420)
    y = 1.05 * x + spread

    data = {
        "AAA1": _synthetic_frame(y),
        "BBB1": _synthetic_frame(x),
    }
    sector_map = {"AAA1": "test", "BBB1": "test"}
    config = PairsTradingConfig(
        initial_capital=100000.0,
        formation_window=120,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_median_notional_brl=1_000_000.0,
        min_price=1.0,
        min_return_corr=-1.0,
        max_coint_pvalue=0.2,
        min_half_life=1.0,
        max_half_life=80.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
    )
    backtester = CointegrationPairsBacktester(
        data_by_ticker=data, sector_map=sector_map, config=config
    )
    result = backtester.run(require_cointegration=True)

    assert not result["selections"].empty
    assert not result["trades"].empty
    assert result["equity"]["equity"].iloc[-1] != config.initial_capital


def test_backtester_applies_cash_yield_to_idle_cash(tmp_path):
    rng = np.random.default_rng(5)
    x = np.cumsum(rng.normal(0, 1, 80)) + 50
    y = 1.1 * x + rng.normal(0, 0.3, 80)
    data = {
        "AAA1": _synthetic_frame(y),
        "BBB1": _synthetic_frame(x),
    }
    sector_map = {"AAA1": "test", "BBB1": "test"}

    selic_path = tmp_path / "selic_daily.csv"
    selic_df = pd.DataFrame(
        {
            "date": pd.bdate_range("2021-01-01", periods=80),
            "rate": np.full(80, 0.001),
        }
    )
    save_daily_selic_data(selic_df, str(selic_path))

    config = PairsTradingConfig(
        initial_capital=100000.0,
        formation_window=20,
        test_window=20,
        step_window=20,
        entry_zscore=10.0,
        exit_zscore=0.1,
        stop_zscore=12.0,
        max_holding_days=10,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_median_notional_brl=1_000_000.0,
        min_price=1.0,
        min_return_corr=-1.0,
        max_coint_pvalue=1.0,
        min_half_life=1.0,
        max_half_life=120.0,
        zscore_window=20,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
        apply_cash_yield=True,
        use_real_selic=True,
        selic_path=str(selic_path),
    )
    backtester = CointegrationPairsBacktester(
        data_by_ticker=data, sector_map=sector_map, config=config
    )
    result = backtester.run(require_cointegration=True)

    assert result["trades"].empty
    assert result["cash_yield_total"] > 0.0
    assert result["equity"]["equity"].iloc[-1] > config.initial_capital


def test_regime_filter_blocks_entries_when_market_is_outside_band():
    rng = np.random.default_rng(11)
    x = np.cumsum(rng.normal(0, 1, 420)) + 100
    spread = np.sin(np.linspace(0, 18, 420)) * 4 + rng.normal(0, 0.4, 420)
    y = 1.05 * x + spread
    benchmark = np.linspace(100.0, 200.0, 420)

    data = {
        "AAA1": _synthetic_frame(y),
        "BBB1": _synthetic_frame(x),
    }
    sector_map = {"AAA1": "test", "BBB1": "test"}
    config = PairsTradingConfig(
        initial_capital=100000.0,
        formation_window=120,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_median_notional_brl=1_000_000.0,
        min_price=1.0,
        min_return_corr=-1.0,
        max_coint_pvalue=0.2,
        min_half_life=1.0,
        max_half_life=80.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=5,
        regime_max_deviation=1e-12,
        regime_vol_window=5,
        regime_vol_lookback=20,
        regime_vol_quantile=0.5,
    )
    backtester = CointegrationPairsBacktester(
        data_by_ticker=data,
        sector_map=sector_map,
        config=config,
        benchmark_data=_synthetic_frame(benchmark),
    )
    result = backtester.run(require_cointegration=True)

    assert not result["selections"].empty
    assert result["trades"].empty
    assert result["regime_blocked_entries"] > 0


def test_explicit_margin_model_runs_and_encumbers_cash():
    rng = np.random.default_rng(19)
    x = np.cumsum(rng.normal(0, 1, 320)) + 80
    spread = np.sin(np.linspace(0, 14, 320)) * 3 + rng.normal(0, 0.3, 320)
    y = 0.95 * x + spread
    benchmark = np.linspace(100.0, 120.0, 320)

    data = {
        "AAA1": _synthetic_frame(y),
        "BBB1": _synthetic_frame(x),
    }
    sector_map = {"AAA1": "test", "BBB1": "test"}
    config = PairsTradingConfig(
        initial_capital=100000.0,
        formation_window=120,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_median_notional_brl=1_000_000.0,
        min_price=1.0,
        min_return_corr=-1.0,
        max_coint_pvalue=0.2,
        min_half_life=1.0,
        max_half_life=80.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
        apply_cash_yield=True,
        selic_fallback_rate=0.13,
        explicit_margin_model=True,
        short_margin_haircut=0.5,
        dynamic_beta=True,
        regime_filter="ma_deviation_and_vol",
        regime_ma_window=20,
        regime_max_deviation=0.5,
        regime_vol_window=10,
        regime_vol_lookback=40,
        regime_vol_quantile=1.0,
    )
    backtester = CointegrationPairsBacktester(
        data_by_ticker=data,
        sector_map=sector_map,
        config=config,
        benchmark_data=_synthetic_frame(benchmark),
    )
    result = backtester.run(require_cointegration=True)

    assert not result["trades"].empty
    assert result["equity"]["cash"].min() < config.initial_capital
    assert result["equity"]["equity"].iloc[-1] > 0.0


def test_backtester_uses_proxy_short_borrow_rate_on_trades():
    rng = np.random.default_rng(13)
    x = np.cumsum(rng.normal(0, 1, 420)) + 100
    spread = np.sin(np.linspace(0, 18, 420)) * 4 + rng.normal(0, 0.4, 420)
    y = 1.05 * x + spread

    data = {
        "AAA1": _synthetic_frame(y, volume=18_000_000.0),
        "BBB1": _synthetic_frame(x, volume=20_000_000.0),
    }
    sector_map = {"AAA1": "test", "BBB1": "test"}
    config = PairsTradingConfig(
        initial_capital=100000.0,
        formation_window=120,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_median_notional_brl=1_000_000.0,
        min_price=1.0,
        min_return_corr=-1.0,
        max_coint_pvalue=0.2,
        min_half_life=1.0,
        max_half_life=80.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        use_proxy_short_borrow=True,
        proxy_borrow_base_rate_annual=0.03,
        proxy_borrow_max_rate_annual=0.12,
        proxy_min_short_score=0.2,
    )
    backtester = CointegrationPairsBacktester(
        data_by_ticker=data, sector_map=sector_map, config=config
    )
    result = backtester.run(require_cointegration=True)

    assert not result["selections"].empty
    assert not result["trades"].empty
    assert result["trades"]["short_borrow_rate_annual"].between(0.03, 0.12).all()
    assert result["eligible_universe"]["short_score"].ge(0.2).all()
