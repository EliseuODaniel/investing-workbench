"""Performance metrics calculation for backtesting."""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional


def calculate_metrics(
    equity: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
    benchmark: Optional[pd.Series] = None,
    total_interest_earned: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate comprehensive performance metrics.

    Args:
        equity: Equity time series
        trades: DataFrame of trades
        initial_capital: Starting capital
        benchmark: Optional benchmark equity series
        total_interest_earned: Optional total interest earned from cash yield

    Returns:
        Dictionary with calculated metrics
    """
    if len(equity) == 0:
        return {"error": "No equity data"}

    # Basic returns
    total_return = (equity.iloc[-1] - initial_capital) / initial_capital

    # Calculate daily returns
    daily_returns = equity.pct_change().dropna()

    # CAGR (Compound Annual Growth Rate)
    days = (equity.index[-1] - equity.index[0]).days
    years = days / 365.25
    if years > 0 and equity.iloc[0] > 0:
        cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
    else:
        cagr = 0.0

    # Maximum drawdown
    peak = equity.expanding().max()
    drawdown = (equity - peak) / peak
    max_drawdown = drawdown.min()

    # MAR ratio (CAGR / Max Drawdown)
    mar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0.0

    # Sharpe ratio (assuming 252 trading days, 5% risk-free rate)
    if len(daily_returns) > 1 and daily_returns.std() != 0:
        sharpe_ratio = (daily_returns.mean() * 252 - 0.05) / (daily_returns.std() * np.sqrt(252))
    else:
        sharpe_ratio = 0.0

    # Sortino ratio
    negative_returns = daily_returns[daily_returns < 0]
    if len(negative_returns) > 0 and negative_returns.std() != 0:
        sortino_ratio = (daily_returns.mean() * 252 - 0.05) / (negative_returns.std() * np.sqrt(252))
    else:
        sortino_ratio = 0.0

    # Trade statistics
    if len(trades) > 0:
        buy_trades = trades[trades["action"] == "BUY"]
        sell_trades = trades[trades["action"] == "SELL"]

        # Hit rate (winning trades)
        winning_trades = sell_trades[sell_trades["pnl"] > 0] if "pnl" in sell_trades.columns else pd.DataFrame()
        hit_rate = len(winning_trades) / len(sell_trades) if len(sell_trades) > 0 else 0.0

        # Average trade PnL
        avg_pnl = sell_trades["pnl"].mean() if "pnl" in sell_trades.columns and len(sell_trades) > 0 else 0.0

        # Profit factor
        gross_profit = sell_trades[sell_trades["pnl"] > 0]["pnl"].sum() if "pnl" in sell_trades.columns else 0.0
        gross_loss = abs(sell_trades[sell_trades["pnl"] < 0]["pnl"].sum()) if "pnl" in sell_trades.columns else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.99  # Use large finite number instead of infinity

        # PnL by layer
        layer_pnl = (
            sell_trades.groupby("layer")["pnl"].sum().to_dict() if "layer" in sell_trades.columns else {}
        )
    else:
        hit_rate = 0.0
        avg_pnl = 0.0
        profit_factor = 0.0
        layer_pnl = {}

    # Volatility
    volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0.0

    # Beta and Alpha (vs benchmark)
    beta = None
    alpha = None
    if benchmark is not None and len(benchmark) == len(equity):
        benchmark_returns = benchmark.pct_change().dropna()
        if len(benchmark_returns) > 1:
            # Align series
            aligned_returns = pd.DataFrame({"strategy": daily_returns, "benchmark": benchmark_returns}).dropna()
            if len(aligned_returns) > 10:  # Need enough data points
                try:
                    beta, alpha, _, _, _ = stats.linregress(
                        aligned_returns["benchmark"].values, aligned_returns["strategy"].values
                    )
                    alpha = alpha * 252  # Annualized alpha
                except (ValueError, TypeError):
                    # Handle case where regression fails
                    beta = None
                    alpha = None

    metrics = {
        "total_return": total_return,
        "total_return_pct": total_return,
        "cagr": cagr,
        "cagr_pct": cagr,
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown,
        "mar_ratio": mar_ratio,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "volatility": volatility,
        "hit_rate": hit_rate,
        "win_rate_pct": hit_rate,
        "avg_trade_pnl": avg_pnl,
        "profit_factor": profit_factor,
        "total_trades": len(trades),
        "buy_trades": len(buy_trades) if len(trades) > 0 else 0,
        "sell_trades": len(sell_trades) if len(trades) > 0 else 0,
        "layer_pnl": layer_pnl,
        "total_interest_earned": total_interest_earned or 0.0,
        "beta": beta,
        "alpha": alpha,
    }

    return metrics


def print_metrics(metrics: Dict[str, Any], strategy_name: str = "Strategy"):
    """Print formatted metrics to console.

    Args:
        metrics: Dictionary of calculated metrics
        strategy_name: Name of the strategy for display
    """
    print(f"\n=== {strategy_name} Performance ===")
    print(f"Total Return: {metrics['total_return']:.2%}")
    print(f"CAGR: {metrics['cagr']:.2%}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"MAR Ratio: {metrics['mar_ratio']:.2f}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"Volatility: {metrics['volatility']:.2%}")
    print(f"Hit Rate: {metrics['hit_rate']:.2%}")
    print(f"Average Trade PnL: ${metrics['avg_trade_pnl']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Total Trades: {metrics['total_trades']}")
    if metrics.get("total_interest_earned", 0) > 0:
        print(f"Total Interest Earned: ${metrics['total_interest_earned']:.2f}")
    if metrics["beta"] is not None:
        print(f"Beta: {metrics['beta']:.2f}")
        print(f"Alpha: {metrics['alpha']:.2%}")


def compare_strategies(
    results: Dict[str, Dict[str, Any]], initial_capital: float
) -> pd.DataFrame:
    """Compare multiple strategies side by side.

    Args:
        results: Dictionary mapping strategy names to their results
        initial_capital: Initial capital for all strategies

    Returns:
        DataFrame with comparison metrics
    """
    comparison_data = []

    for strategy_name, result in results.items():
        if "equity" not in result or len(result["equity"]) == 0:
            continue

        equity = result["equity"]["equity"]
        trades = result["trades"]

        # Calculate buy & hold benchmark
        if len(equity) > 0:
            start_price = result.get("start_price", 1.0)
            end_price = result.get("end_price", 1.0)
            bh_return = (end_price - start_price) / start_price
            bh_equity = initial_capital * (1 + bh_return)
        else:
            bh_equity = initial_capital

        benchmark = pd.Series([bh_equity] * len(equity), index=equity.index)

        metrics = calculate_metrics(equity, trades, initial_capital, benchmark)

        row = {"Strategy": strategy_name}
        row.update(metrics)
        comparison_data.append(row)

    if not comparison_data:
        return pd.DataFrame()

    comparison_df = pd.DataFrame(comparison_data)

    # Sort by total return
    comparison_df = comparison_df.sort_values("total_return", ascending=False)

    return comparison_df