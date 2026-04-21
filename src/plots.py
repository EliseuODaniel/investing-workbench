"""Plotting utilities for backtest visualization."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

try:
    import mplfinance as mpf

    MPLFINANCE_AVAILABLE = True
except ImportError:
    MPLFINANCE_AVAILABLE = False
    print("Warning: mplfinance not available. Candlestick plots will be disabled.")


def plot_equity_comparison(
    equity_curves: Dict[str, pd.Series],
    benchmark: Optional[pd.Series] = None,
    title: str = "Strategy Performance Comparison",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot multiple equity curves with optional benchmark.

    Args:
        equity_curves: Dictionary mapping strategy names to equity series
        benchmark: Optional benchmark series
        title: Plot title
        save_path: Path to save plot

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot strategies
    for strategy_name, equity in equity_curves.items():
        ax.plot(equity.index, equity.values, label=strategy_name, linewidth=2)

    # Plot benchmark if provided
    if benchmark is not None:
        ax.plot(
            benchmark.index,
            benchmark.values,
            label="Buy & Hold",
            color="gray",
            linestyle="--",
            alpha=0.7,
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend()
    ax.grid(True, alpha=0.3)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Equity plot saved to {save_path}")

    return fig


def plot_price_with_trades(
    price_data: pd.Series,
    trades: pd.DataFrame,
    title: str = "Price Chart with Trading Signals",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot price data with buy/sell markers by layer.

    Args:
        price_data: Price time series
        trades: DataFrame with trade information
        title: Plot title
        save_path: Path to save plot

    Returns:
        matplotlib Figure object
    """
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )

    # Plot price
    ax1.plot(price_data.index, price_data.values, color="black", linewidth=1, alpha=0.7)
    ax1.set_title(title, fontsize=14, fontweight="bold")
    ax1.set_ylabel("Price ($)")
    ax1.grid(True, alpha=0.3)

    # Plot trades
    if len(trades) > 0:
        # Set timestamp as index for proper plotting
        trades_with_index = trades.set_index("timestamp")

        # Separate buys and sells
        buys = trades_with_index[trades_with_index["action"] == "BUY"]
        sells = trades_with_index[trades_with_index["action"] == "SELL"]

        # Plot buys with different colors per layer
        if len(buys) > 0:
            scatter = ax1.scatter(
                buys.index,
                buys["price"],
                c=buys.get("layer", 0),
                cmap="viridis",
                s=50,
                marker="^",
                label="Buy",
                alpha=0.8,
                zorder=5,
            )
            plt.colorbar(scatter, ax=ax1, label="Layer ID")

        # Plot sells with different colors per layer
        if len(sells) > 0:
            ax1.scatter(
                sells.index,
                sells["price"],
                c=sells.get("layer", 0),
                cmap="plasma",
                s=50,
                marker="v",
                label="Sell",
                alpha=0.8,
                zorder=5,
            )

        # Volume subplot (trade counts per period)
        trade_volume = trades_with_index.groupby(pd.Grouper(freq="ME")).size()
        if len(trade_volume) > 0:
            ax2.bar(trade_volume.index, trade_volume.values, alpha=0.6, color="blue")
            ax2.set_ylabel("Trade Count")
            ax2.set_title("Monthly Trade Volume")

    ax1.legend()

    # Format x-axis dates
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Price plot saved to {save_path}")

    return fig


def plot_cash_allocation(
    cash_series: pd.Series,
    title: str = "Cash Allocation Over Time",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot cash allocation over time.

    Args:
        cash_series: Cash time series
        title: Plot title
        save_path: Path to save plot

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(cash_series.index, cash_series.values, color="blue", linewidth=2)
    ax.fill_between(cash_series.index, cash_series.values, alpha=0.3, color="blue")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel("Available Cash ($)")
    ax.grid(True, alpha=0.3)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Cash allocation plot saved to {save_path}")

    return fig


def plot_drawdown(
    equity_series: pd.Series,
    title: str = "Drawdown Analysis",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot drawdown chart.

    Args:
        equity_series: Equity time series
        title: Plot title
        save_path: Path to save plot

    Returns:
        matplotlib Figure object
    """
    # Calculate drawdown
    peak = equity_series.expanding().max()
    drawdown = (equity_series - peak) / peak

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    # Plot equity
    ax1.plot(equity_series.index, equity_series.values, color="green", linewidth=2)
    ax1.set_title("Portfolio Equity")
    ax1.set_ylabel("Portfolio Value ($)")
    ax1.grid(True, alpha=0.3)

    # Plot drawdown
    ax2.fill_between(drawdown.index, drawdown.values * 100, 0, color="red", alpha=0.6)
    ax2.plot(drawdown.index, drawdown.values * 100, color="red", linewidth=1)
    ax2.set_title(f"{title} - Max Drawdown: {drawdown.min():.2%}")
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)

    # Format x-axis dates
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Drawdown plot saved to {save_path}")

    return fig


def plot_layer_allocation_heatmap(
    trades: pd.DataFrame,
    title: str = "Layer Allocation Heatmap",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot heatmap of layer allocation over time.

    Args:
        trades: DataFrame with trade information
        title: Plot title
        save_path: Path to save plot

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    if len(trades) == 0:
        ax.text(
            0.5,
            0.5,
            "No trades to visualize",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
        )
        ax.set_title(title)
        ax.axis("off")
    else:
        # Create a simple monthly/layer heatmap
        trades_with_time = trades.set_index("timestamp")

        # Add month column
        trades_with_time["month"] = trades_with_time.index.to_period("M")

        # Create pivot table: layer vs month with trade counts
        if "layer" in trades_with_time.columns:
            pivot_data = trades_with_time.groupby(["month", "layer"]).size().unstack(fill_value=0)

            if not pivot_data.empty:
                try:
                    import seaborn as sns

                    sns.heatmap(pivot_data.T, annot=True, fmt="d", cmap="YlOrRd", ax=ax)
                except ImportError:
                    # Fallback to matplotlib heatmap
                    im = ax.imshow(pivot_data.T.values, cmap="YlOrRd", aspect="auto")
                    ax.set_xticks(range(len(pivot_data.columns)))
                    ax.set_xticklabels([str(col) for col in pivot_data.columns], rotation=45)
                    ax.set_yticks(range(len(pivot_data.index)))
                    ax.set_yticklabels(pivot_data.index)

                    # Add text annotations
                    for i in range(len(pivot_data.index)):
                        for j in range(len(pivot_data.columns)):
                            ax.text(j, i, str(pivot_data.iloc[i, j]), ha="center", va="center")

                    plt.colorbar(im, ax=ax)
                ax.set_title(title)
                ax.set_xlabel("Month")
                ax.set_ylabel("Layer ID")
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Insufficient layer data for heatmap",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    fontsize=12,
                )
                ax.set_title(title)
                ax.axis("off")
        else:
            ax.text(
                0.5,
                0.5,
                "No layer information available",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=12,
            )
            ax.set_title(title)
            ax.axis("off")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Layer heatmap saved to {save_path}")

    return fig


def plot_candlesticks_with_trades(
    ohlcv_data: pd.DataFrame,
    trades: pd.DataFrame,
    title: str = "Price Action with Trading Signals",
    save_path: Optional[str] = None,
    style: str = "yahoo",
    volume: bool = True,
    indicators: Optional[Dict[str, Any]] = None,
) -> plt.Figure:
    """Plot candlestick chart with trade markers and technical indicators.

    Args:
        ohlcv_data: DataFrame with OHLCV data
        trades: DataFrame with trade information
        title: Plot title
        save_path: Path to save plot
        style: mplfinance style ('yahoo', 'charles', 'nightclouds', etc.)
        volume: Whether to include volume subplot
        indicators: Dictionary with technical indicators to overlay

    Returns:
        matplotlib Figure object
    """
    # Prepare technical indicators for overlay
    addplot = []

    if indicators:
        # Moving Averages
        if "ma_short" in indicators:
            ma_short = mpf.make_addplot(
                indicators["ma_short"],
                type="line",
                color="blue",
                width=1.5,
                alpha=0.8,
                label=f"MA {indicators.get('ma_short_period', 'N/A')}",
            )
            addplot.append(ma_short)

        if "ma_long" in indicators:
            ma_long = mpf.make_addplot(
                indicators["ma_long"],
                type="line",
                color="red",
                width=1.5,
                alpha=0.8,
                label=f"MA {indicators.get('ma_long_period', 'N/A')}",
            )
            addplot.append(ma_long)

        # Bollinger Bands
        if "bb_upper" in indicators and "bb_lower" in indicators:
            bb_upper = mpf.make_addplot(
                indicators["bb_upper"],
                type="line",
                color="orange",
                width=1,
                alpha=0.6,
                label="BB Upper",
            )
            bb_lower = mpf.make_addplot(
                indicators["bb_lower"],
                type="line",
                color="orange",
                width=1,
                alpha=0.6,
                label="BB Lower",
            )
            bb_middle = mpf.make_addplot(
                indicators.get("bb_middle", indicators["bb_upper"]),
                type="line",
                color="gray",
                width=1,
                alpha=0.5,
                label="BB Middle",
            )
            addplot.extend([bb_upper, bb_middle, bb_lower])

        # Support/Resistance levels
        if "support_levels" in indicators:
            for i, level in enumerate(indicators["support_levels"]):
                support_line = mpf.make_addplot(
                    pd.Series(level, index=ohlcv_data.index),
                    type="line",
                    color="green",
                    width=1,
                    alpha=0.5,
                    linestyle="--",
                    label=f"Support {i+1}",
                )
                addplot.append(support_line)

        if "resistance_levels" in indicators:
            for i, level in enumerate(indicators["resistance_levels"]):
                resistance_line = mpf.make_addplot(
                    pd.Series(level, index=ohlcv_data.index),
                    type="line",
                    color="red",
                    width=1,
                    alpha=0.5,
                    linestyle="--",
                    label=f"Resistance {i+1}",
                )
                addplot.append(resistance_line)

    # Prepare trade markers for mplfinance
    if len(trades) > 0:
        trades_with_index = trades.set_index("timestamp")
        buys = trades_with_index[trades_with_index["action"] == "BUY"]
        sells = trades_with_index[trades_with_index["action"] == "SELL"]

        # Create scatter plots for trades
        if len(buys) > 0:
            # Align buy prices with OHLCV data
            buy_prices = pd.Series(index=ohlcv_data.index, dtype=float)
            buy_prices.loc[buys.index] = buys["price"]

            buy_scatter = mpf.make_addplot(
                buy_prices,
                type="scatter",
                markersize=80,
                marker="^",
                color="lime",
                alpha=0.8,
                label="Buy",
            )
            addplot.append(buy_scatter)

        if len(sells) > 0:
            # Align sell prices with OHLCV data
            sell_prices = pd.Series(index=ohlcv_data.index, dtype=float)
            sell_prices.loc[sells.index] = sells["price"]

            sell_scatter = mpf.make_addplot(
                sell_prices,
                type="scatter",
                markersize=80,
                marker="v",
                color="red",
                alpha=0.8,
                label="Sell",
            )
            addplot.append(sell_scatter)

    # If mplfinance is not available, fall back to matplotlib
    if not MPLFINANCE_AVAILABLE:
        return _plot_candlesticks_fallback(ohlcv_data, trades, title, save_path, indicators)

    # Try mplfinance plot first, limit addplots if too many
    try:
        # Limit addplots if too many to avoid mplfinance issues
        if len(addplot) > 8:
            # Keep only essential plots (first 8)
            addplot = addplot[:8]
            print("Warning: Limiting to 8 addplots for mplfinance compatibility")

        # Configure plot appearance
        kwargs = {
            "type": "candle",
            "style": style,
            "title": title,
            "ylabel": "Price ($)",
            "volume": volume,
            "figratio": (16, 10),
            "figscale": 1.1,
            "tight_layout": True,
            "warn_too_much_data": max(len(ohlcv_data) + 1, 10_000),
        }

        if addplot:
            kwargs["addplot"] = addplot

        # Plot using mplfinance
        fig, axes = mpf.plot(ohlcv_data, **kwargs, returnfig=True)

        # Add legend if we have indicators or trades
        if addplot and hasattr(axes[0], "legend"):
            handles, labels = axes[0].get_legend_handles_labels()
            if handles:  # Only add legend if there are items to show
                axes[0].legend(handles, labels, loc="upper left", framealpha=0.9)

        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Candlestick plot saved to {save_path}")

        return fig

    except Exception as e:
        print(f"Warning: mplfinance plotting failed ({e}), falling back to matplotlib")
        return _plot_candlesticks_fallback(ohlcv_data, trades, title, save_path, indicators)


def _plot_candlesticks_fallback(
    ohlcv_data: pd.DataFrame,
    trades: pd.DataFrame,
    title: str = "Price Action with Trading Signals",
    save_path: Optional[str] = None,
    indicators: Optional[Dict[str, Any]] = None,
) -> plt.Figure:
    """Fallback plotting function using matplotlib when mplfinance fails.

    Args:
        ohlcv_data: DataFrame with OHLCV data
        trades: DataFrame with trade information
        title: Plot title
        save_path: Path to save plot
        indicators: Dictionary with technical indicators to overlay

    Returns:
        matplotlib Figure object
    """
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )

    # Plot candlesticks as lines (simplified)
    ax1.plot(
        ohlcv_data.index,
        ohlcv_data["Close"],
        label="Close Price",
        linewidth=1.5,
        color="black",
        alpha=0.8,
    )

    # Add high-low range
    ax1.fill_between(
        ohlcv_data.index,
        ohlcv_data["High"],
        ohlcv_data["Low"],
        alpha=0.2,
        color="gray",
        label="High-Low Range",
    )

    # Add technical indicators
    if indicators:
        if "ma_short" in indicators:
            ax1.plot(
                ohlcv_data.index,
                indicators["ma_short"],
                color="blue",
                linewidth=1.5,
                alpha=0.8,
                label=f"MA {indicators.get('ma_short_period', 'N/A')}",
            )

        if "ma_long" in indicators:
            ax1.plot(
                ohlcv_data.index,
                indicators["ma_long"],
                color="red",
                linewidth=1.5,
                alpha=0.8,
                label=f"MA {indicators.get('ma_long_period', 'N/A')}",
            )

        if "bb_upper" in indicators and "bb_lower" in indicators:
            ax1.plot(
                ohlcv_data.index,
                indicators["bb_upper"],
                color="orange",
                linewidth=1,
                alpha=0.6,
                label="BB Upper",
            )
            ax1.plot(
                ohlcv_data.index,
                indicators["bb_lower"],
                color="orange",
                linewidth=1,
                alpha=0.6,
                label="BB Lower",
            )
            if "bb_middle" in indicators:
                ax1.plot(
                    ohlcv_data.index,
                    indicators["bb_middle"],
                    color="gray",
                    linewidth=1,
                    alpha=0.5,
                    label="BB Middle",
                )

    ax1.set_title(title, fontsize=14, fontweight="bold")
    ax1.set_ylabel("Price ($)")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")

    # Add trade markers
    if len(trades) > 0:
        trades_with_index = trades.set_index("timestamp")
        buys = trades_with_index[trades_with_index["action"] == "BUY"]
        sells = trades_with_index[trades_with_index["action"] == "SELL"]

        if len(buys) > 0:
            ax1.scatter(
                buys.index,
                buys["price"],
                marker="^",
                color="lime",
                s=120,
                label="Buy",
                alpha=0.9,
                zorder=5,
                edgecolors="darkgreen",
            )

        if len(sells) > 0:
            ax1.scatter(
                sells.index,
                sells["price"],
                marker="v",
                color="red",
                s=120,
                label="Sell",
                alpha=0.9,
                zorder=5,
                edgecolors="darkred",
            )

    # Volume subplot
    if "Volume" in ohlcv_data.columns:
        ax2.bar(ohlcv_data.index, ohlcv_data["Volume"], alpha=0.6, color="blue")
        ax2.set_ylabel("Volume")
        ax2.set_title("Trading Volume")
    else:
        ax2.axis("off")

    # Format x-axis dates
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Candlestick plot (fallback) saved to {save_path}")

    return fig


def create_strategy_report(
    results: Dict[str, Dict[str, Any]],
    price_data: pd.DataFrame,
    output_dir: str = "reports",
) -> None:
    """Create comprehensive visual report for strategies.

    Args:
        results: Dictionary mapping strategy names to their results
        price_data: OHLCV DataFrame with price data
        output_dir: Directory to save plots
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Collect equity curves
    equity_curves = {}
    for strategy_name, result in results.items():
        if "equity" in result and len(result["equity"]) > 0:
            equity_curves[strategy_name] = result["equity"]["equity"]

    if not equity_curves:
        print("No equity data to plot")
        return

    # 1. Equity comparison
    plot_equity_comparison(
        equity_curves,
        save_path=output_path / "equity_comparison.png",
        title="Strategy Performance Comparison",
    )

    # 2. Individual strategy plots
    for strategy_name, result in results.items():
        if "equity" not in result or len(result["equity"]) == 0:
            continue

        equity = result["equity"]["equity"]
        cash = result["equity"]["cash"]
        trades = result["trades"]

        # Strategy folder
        strategy_dir = output_path / strategy_name.replace(" ", "_").lower()
        strategy_dir.mkdir(exist_ok=True)

        # Price with trades
        plot_price_with_trades(
            price_data.loc[equity.index],
            trades,
            title=f"{strategy_name} - Trading Signals",
            save_path=strategy_dir / "price_with_trades.png",
        )

        # Enhanced candlestick chart with trades and indicators (if price_data is OHLCV)
        if all(col in price_data.columns for col in ["Open", "High", "Low", "Close"]):
            # Filter price_data to match equity period
            start_date = equity.index.min()
            end_date = equity.index.max()
            filtered_price_data = price_data.loc[start_date:end_date]

            if len(filtered_price_data) > 0:
                # Extract technical indicators from strategy if available
                indicators = _extract_strategy_indicators(
                    strategy_name, result, filtered_price_data
                )

                plot_candlesticks_with_trades(
                    filtered_price_data,
                    trades,
                    title=f"{strategy_name} - Price Action with Indicators",
                    save_path=strategy_dir / "candlesticks_with_indicators.png",
                    indicators=indicators,
                )

        # Cash allocation
        plot_cash_allocation(
            cash,
            title=f"{strategy_name} - Cash Allocation",
            save_path=strategy_dir / "cash_allocation.png",
        )

        # Drawdown
        plot_drawdown(
            equity,
            title=f"{strategy_name} - Drawdown",
            save_path=strategy_dir / "drawdown.png",
        )

    print(f"Report saved to {output_path}")


def create_interactive_html_report(
    results: Dict[str, Dict[str, Any]],
    price_data: pd.DataFrame,
    output_dir: str = "reports",
    config_info: Optional[Dict[str, Any]] = None,
    filename: str = "interactive_backtest_report.html",
) -> str:
    """Create interactive HTML report for backtest results.

    Args:
        results: Dictionary mapping strategy names to their results
        price_data: OHLCV DataFrame with price data
        output_dir: Directory to save HTML report
        config_info: Configuration information
        filename: Output HTML filename

    Returns:
        Path to generated HTML file
    """
    try:
        from .html_reports import HTMLReportGenerator

        generator = HTMLReportGenerator(output_dir)
        report_path = generator.generate_comprehensive_report(
            results=results, price_data=price_data, config_info=config_info, filename=filename
        )

        return report_path

    except ImportError:
        print("Warning: HTML report generation requires plotly. Install with: pip install plotly")
        print("Falling back to standard PNG reports...")
        create_strategy_report(results, price_data, output_dir)
        return str(Path(output_dir) / "index.html")


def create_comprehensive_backtest_report(
    results: Dict[str, Dict[str, Any]],
    price_data: pd.DataFrame,
    output_dir: str = "reports",
    config_info: Optional[Dict[str, Any]] = None,
    generate_html: bool = True,
    generate_pngs: bool = True,
) -> Dict[str, str]:
    """Create comprehensive backtest report with both HTML and PNG outputs.

    Args:
        results: Dictionary mapping strategy names to their results
        price_data: OHLCV DataFrame with price data
        output_dir: Directory to save reports
        config_info: Configuration information
        generate_html: Whether to generate interactive HTML report
        generate_pngs: Whether to generate PNG charts

    Returns:
        Dictionary with paths to generated report files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = {}

    # Generate interactive HTML report
    if generate_html:
        try:
            html_path = create_interactive_html_report(results, price_data, output_dir, config_info)
            generated_files["html_report"] = html_path
        except Exception as e:
            print(f"Warning: HTML report generation failed: {e}")

    # Generate PNG charts
    if generate_pngs:
        try:
            create_strategy_report(results, price_data, str(output_path / "png_charts"))
            generated_files["png_charts"] = str(output_path / "png_charts")
        except Exception as e:
            print(f"Warning: PNG chart generation failed: {e}")

    # Generate summary JSON file
    try:
        summary_data = {
            "generated_at": datetime.now().isoformat(),
            "strategies": list(results.keys()),
            "summary_stats": {},
        }

        for strategy_name, result in results.items():
            if "metrics" in result:
                summary_data["summary_stats"][strategy_name] = result["metrics"]

        summary_path = output_path / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary_data, f, indent=2, default=str)

        generated_files["summary_json"] = str(summary_path)
    except Exception as e:
        print(f"Warning: Summary JSON generation failed: {e}")

    print(f"Comprehensive report generated in: {output_path}")
    for file_type, file_path in generated_files.items():
        print(f"  {file_type}: {file_path}")

    return generated_files


def _extract_strategy_indicators(
    strategy_name: str, result: Dict[str, Any], price_data: pd.DataFrame
) -> Optional[Dict[str, Any]]:
    """Extract technical indicators from strategy results for plotting.

    Args:
        strategy_name: Name of the strategy
        result: Strategy result dictionary
        price_data: Price data for indicator calculation

    Returns:
        Dictionary with indicators or None if not available
    """
    indicators = {}

    # Extract indicators based on strategy type
    strategy_lower = strategy_name.lower()

    # Moving Average strategies
    if "ma cross" in strategy_lower or "trend" in strategy_lower:
        # Try to get MA data from strategy signals
        if "strategy" in result and "ma_history" in result["strategy"]:
            ma_history = result["strategy"]["ma_history"]
            if ma_history:
                ma_df = pd.DataFrame(ma_history).set_index("timestamp")
                ma_df = ma_df.reindex(price_data.index, method="ffill")

                if "short_ma" in ma_df.columns:
                    indicators["ma_short"] = ma_df["short_ma"]
                    indicators["ma_short_period"] = "Short"
                if "long_ma" in ma_df.columns:
                    indicators["ma_long"] = ma_df["long_ma"]
                    indicators["ma_long_period"] = "Long"

    # Mean Reversion strategies
    elif "mean reversion" in strategy_lower:
        # Try to get Bollinger Bands or MA data from strategy
        if "strategy" in result and "indicators_history" in result["strategy"]:
            ind_history = result["strategy"]["indicators_history"]
            if ind_history:
                ind_df = pd.DataFrame(ind_history).set_index("timestamp")
                ind_df = ind_df.reindex(price_data.index, method="ffill")

                if "sma" in ind_df.columns:
                    indicators["ma_short"] = ind_df["sma"]
                    indicators["ma_short_period"] = "SMA"

                if "upper_band" in ind_df.columns and "lower_band" in ind_df.columns:
                    indicators["bb_upper"] = ind_df["upper_band"]
                    indicators["bb_lower"] = ind_df["lower_band"]
                    indicators["bb_middle"] = (
                        ind_df["sma"] if "sma" in ind_df.columns else ind_df["upper_band"]
                    )

    # Breakout strategies
    elif "breakout" in strategy_lower:
        # Calculate support/resistance levels for breakout strategies
        if len(price_data) > 20:
            # Simple 20-period high/low as support/resistance
            indicators["resistance_levels"] = [price_data["High"].rolling(20).max().iloc[-1]]
            indicators["support_levels"] = [price_data["Low"].rolling(20).min().iloc[-1]]

    # ATR Martingale strategies
    elif "atr" in strategy_lower:
        # Try to get ATR data from strategy
        if "strategy" in result and "atr_history" in result["strategy"]:
            atr_history = result["strategy"]["atr_history"]
            if atr_history:
                atr_df = pd.DataFrame(atr_history).set_index("timestamp")
                atr_df = atr_df.reindex(price_data.index, method="ffill")

                if "atr" in atr_df.columns:
                    # Show ATR as bands around price (upper/lower volatility bands)
                    atr_values = atr_df["atr"]
                    indicators["bb_upper"] = price_data["Close"] + (2 * atr_values)
                    indicators["bb_lower"] = price_data["Close"] - (2 * atr_values)
                    indicators["bb_middle"] = price_data["Close"]

    # Calculate basic indicators if none found from strategy
    if not indicators and len(price_data) > 50:
        # Add default moving averages
        indicators["ma_short"] = price_data["Close"].rolling(10).mean()
        indicators["ma_short_period"] = "10"
        indicators["ma_long"] = price_data["Close"].rolling(30).mean()
        indicators["ma_long_period"] = "30"

    return indicators if indicators else None
