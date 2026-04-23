"""Statistical helpers for cointegration-based pairs trading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint


@dataclass(slots=True)
class RegressionResult:
    beta: float
    intercept: float


@dataclass(slots=True)
class CointegrationResult:
    coint_t_stat: float
    coint_pvalue: float
    adf_stat: float
    adf_pvalue: float
    beta: float
    intercept: float
    half_life: float
    return_corr: float
    level_corr: float
    spread_history: list[float]


@dataclass(slots=True)
class ShortBorrowProfile:
    median_notional_brl: float
    realized_vol_annual: float
    liquidity_score: float
    short_score: float
    borrow_rate_annual: float
    short_eligible: bool
    margin_haircut: float = 0.50
    source: str = "proxy"


@dataclass(slots=True)
class PairStabilityResult:
    window_count: int
    pass_count: int
    pass_rate: float
    mean_coint_pvalue: float | None
    beta_dispersion: float | None
    half_life_dispersion: float | None
    return_corr_dispersion: float | None
    structural_break_risk: float
    stability_band: str
    stability_score: float

    def to_dict(self) -> dict[str, float | int | str | None]:
        return {
            "window_count": self.window_count,
            "pass_count": self.pass_count,
            "pass_rate": self.pass_rate,
            "mean_coint_pvalue": self.mean_coint_pvalue,
            "beta_dispersion": self.beta_dispersion,
            "half_life_dispersion": self.half_life_dispersion,
            "return_corr_dispersion": self.return_corr_dispersion,
            "structural_break_risk": self.structural_break_risk,
            "stability_band": self.stability_band,
            "stability_score": self.stability_score,
        }


def apply_split_adjustment(df: pd.DataFrame) -> pd.DataFrame:
    """Back-adjust OHLC prices only for stock splits, preserving dividends separately."""
    adjusted = df.copy()
    split = (
        adjusted.get("Stock Splits", pd.Series(1.0, index=adjusted.index))
        .replace(0, 1.0)
        .astype(float)
    )
    future_split_factor = split.shift(-1, fill_value=1.0)[::-1].cumprod()[::-1]
    for column in ["Open", "High", "Low", "Close"]:
        adjusted[f"{column}_sa"] = adjusted[column].astype(float) / future_split_factor
    adjusted["split_adjustment_factor"] = future_split_factor
    return adjusted


def fit_ols(y: pd.Series, x: pd.Series) -> RegressionResult:
    aligned = pd.concat([y, x], axis=1).dropna()
    aligned.columns = ["y", "x"]
    model = sm.OLS(aligned["y"].values, sm.add_constant(aligned["x"].values)).fit()
    intercept, beta = model.params
    return RegressionResult(beta=float(beta), intercept=float(intercept))


def estimate_half_life(spread: pd.Series) -> float:
    aligned = pd.concat([spread.diff(), spread.shift(1)], axis=1).dropna()
    if aligned.empty:
        return float("inf")

    delta = aligned.iloc[:, 0].values
    lagged = aligned.iloc[:, 1].values
    regression = sm.OLS(delta, sm.add_constant(lagged)).fit()
    speed = float(regression.params[1])
    if speed >= 0:
        return float("inf")
    return float(-np.log(2.0) / speed)


def analyze_cointegration(y: pd.Series, x: pd.Series) -> CointegrationResult:
    aligned = pd.concat([y, x], axis=1).dropna()
    aligned.columns = ["y", "x"]
    regression = fit_ols(aligned["y"], aligned["x"])
    spread = aligned["y"] - (regression.beta * aligned["x"])

    coint_t_stat, coint_pvalue, _ = coint(aligned["y"], aligned["x"])
    adf_stat, adf_pvalue, *_ = adfuller(spread.dropna(), autolag="AIC")
    half_life = estimate_half_life(spread)
    return_corr = float(aligned["y"].pct_change().corr(aligned["x"].pct_change()))
    level_corr = float(np.log(aligned["y"]).corr(np.log(aligned["x"])))

    return CointegrationResult(
        coint_t_stat=float(coint_t_stat),
        coint_pvalue=float(coint_pvalue),
        adf_stat=float(adf_stat),
        adf_pvalue=float(adf_pvalue),
        beta=regression.beta,
        intercept=regression.intercept,
        half_life=float(half_life),
        return_corr=return_corr,
        level_corr=level_corr,
        spread_history=spread.astype(float).tolist(),
    )


def evaluate_pair_orientations(
    series_a: pd.Series, series_b: pd.Series
) -> tuple[str, CointegrationResult]:
    result_ab = analyze_cointegration(series_a, series_b)
    result_ba = analyze_cointegration(series_b, series_a)

    candidates: list[tuple[str, CointegrationResult]] = []
    if np.isfinite(result_ab.beta) and result_ab.beta > 0:
        candidates.append(("ab", result_ab))
    if np.isfinite(result_ba.beta) and result_ba.beta > 0:
        candidates.append(("ba", result_ba))
    if not candidates:
        return ("ab", result_ab)

    candidates.sort(
        key=lambda item: (item[1].coint_pvalue, item[1].adf_pvalue, -item[1].return_corr)
    )
    return candidates[0]


def estimate_pair_stability(
    y: pd.Series,
    x: pd.Series,
    *,
    max_coint_pvalue: float,
    min_half_life: float,
    max_half_life: float,
) -> PairStabilityResult:
    aligned = pd.concat([y, x], axis=1).dropna()
    if len(aligned) < 120:
        return PairStabilityResult(
            window_count=0,
            pass_count=0,
            pass_rate=0.0,
            mean_coint_pvalue=None,
            beta_dispersion=None,
            half_life_dispersion=None,
            return_corr_dispersion=None,
            structural_break_risk=1.0,
            stability_band="low",
            stability_score=0.0,
        )

    # Keep each slice as a DataFrame; np.array_split(DataFrame, ...) coerces to ndarray.
    row_windows = np.array_split(np.arange(len(aligned)), 3)
    windows = [aligned.iloc[window_rows] for window_rows in row_windows if len(window_rows) > 0]
    coint_pvalues: list[float] = []
    betas: list[float] = []
    half_lives: list[float] = []
    return_corrs: list[float] = []
    pass_count = 0
    window_count = 0

    for window in windows:
        if len(window) < 40:
            continue
        window_count += 1
        metrics = analyze_cointegration(window.iloc[:, 0], window.iloc[:, 1])
        coint_pvalues.append(float(metrics.coint_pvalue))
        betas.append(float(metrics.beta))
        half_lives.append(float(metrics.half_life))
        return_corrs.append(float(metrics.return_corr))
        passes = (
            np.isfinite(metrics.beta)
            and metrics.beta > 0
            and metrics.coint_pvalue <= max_coint_pvalue
            and min_half_life <= metrics.half_life <= max_half_life
        )
        if passes:
            pass_count += 1

    if window_count == 0:
        return PairStabilityResult(
            window_count=0,
            pass_count=0,
            pass_rate=0.0,
            mean_coint_pvalue=None,
            beta_dispersion=None,
            half_life_dispersion=None,
            return_corr_dispersion=None,
            structural_break_risk=1.0,
            stability_band="low",
            stability_score=0.0,
        )

    pass_rate = float(pass_count / window_count)
    mean_coint_pvalue = float(np.mean(coint_pvalues))
    mean_beta = float(np.mean(np.abs(betas))) if betas else 0.0
    mean_half_life = float(np.mean(np.abs(half_lives))) if half_lives else 0.0
    beta_dispersion = float(np.clip(np.std(betas, ddof=0) / max(mean_beta, 1e-9), 0.0, 1.0))
    half_life_dispersion = float(
        np.clip(np.std(half_lives, ddof=0) / max(mean_half_life, 1e-9), 0.0, 1.0)
    )
    return_corr_dispersion = float(np.clip(np.std(return_corrs, ddof=0) / 0.5, 0.0, 1.0))

    structural_break_risk = float(
        np.clip(
            (0.50 * (1.0 - pass_rate))
            + (0.20 * beta_dispersion)
            + (0.20 * half_life_dispersion)
            + (0.10 * return_corr_dispersion),
            0.0,
            1.0,
        )
    )
    stability_score = float(
        np.clip(
            (0.50 * pass_rate)
            + (0.20 * (1.0 - min(max(mean_coint_pvalue, 0.0), 1.0)))
            + (0.15 * (1.0 - beta_dispersion))
            + (0.10 * (1.0 - half_life_dispersion))
            + (0.05 * (1.0 - return_corr_dispersion)),
            0.0,
            1.0,
        )
    )
    if stability_score >= 0.70:
        stability_band = "high"
    elif stability_score >= 0.45:
        stability_band = "medium"
    else:
        stability_band = "low"

    return PairStabilityResult(
        window_count=window_count,
        pass_count=pass_count,
        pass_rate=pass_rate,
        mean_coint_pvalue=mean_coint_pvalue,
        beta_dispersion=beta_dispersion,
        half_life_dispersion=half_life_dispersion,
        return_corr_dispersion=return_corr_dispersion,
        structural_break_risk=structural_break_risk,
        stability_band=stability_band,
        stability_score=stability_score,
    )


def estimate_short_borrow_profile(
    *,
    close: pd.Series,
    volume: pd.Series,
    min_median_notional_brl: float,
    min_price: float,
    base_rate_annual: float,
    max_rate_annual: float,
    min_short_score: float,
    vol_floor: float = 0.20,
    vol_cap: float = 0.80,
    liquidity_span_multiple: float = 25.0,
) -> ShortBorrowProfile:
    aligned = pd.concat([close, volume], axis=1).dropna()
    aligned.columns = ["close", "volume"]
    if aligned.empty:
        return ShortBorrowProfile(
            median_notional_brl=0.0,
            realized_vol_annual=float("inf"),
            liquidity_score=0.0,
            short_score=0.0,
            borrow_rate_annual=max_rate_annual,
            short_eligible=False,
            margin_haircut=0.50,
            source="proxy",
        )

    median_notional = float((aligned["close"] * aligned["volume"]).median())
    min_close = float(aligned["close"].min())
    realized_vol = float(aligned["close"].pct_change().std(ddof=1) * np.sqrt(252.0))
    realized_vol = realized_vol if np.isfinite(realized_vol) else vol_cap

    denom = max(np.log(liquidity_span_multiple), 1e-9)
    liquidity_score = float(
        np.clip(
            np.log(max(median_notional, 1.0) / max(min_median_notional_brl, 1.0)) / denom, 0.0, 1.0
        )
    )
    vol_score = float(
        np.clip((realized_vol - vol_floor) / max(vol_cap - vol_floor, 1e-9), 0.0, 1.0)
    )
    short_score = float(np.clip((0.7 * liquidity_score) + (0.3 * (1.0 - vol_score)), 0.0, 1.0))
    borrow_rate = float(
        base_rate_annual + ((max_rate_annual - base_rate_annual) * (1.0 - short_score))
    )
    short_eligible = bool(
        median_notional >= min_median_notional_brl
        and min_close >= min_price
        and short_score >= min_short_score
    )

    return ShortBorrowProfile(
        median_notional_brl=median_notional,
        realized_vol_annual=realized_vol,
        liquidity_score=liquidity_score,
        short_score=short_score,
        borrow_rate_annual=borrow_rate,
        short_eligible=short_eligible,
        margin_haircut=0.50,
        source="proxy",
    )


def compute_zscore(history: Iterable[float], current_spread: float, window: int) -> float | None:
    values = pd.Series(list(history), dtype=float).dropna()
    if values.empty:
        return None
    tail = values.iloc[-window:] if len(values) > window else values
    if len(tail) < max(20, min(window, 20)):
        return None
    std = float(tail.std(ddof=1))
    if std <= 1e-12:
        return None
    mean = float(tail.mean())
    return float((current_spread - mean) / std)
