"""Interactive HTML report generation for backtest results."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import base64
from io import BytesIO
import matplotlib.pyplot as plt

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not available. Interactive charts will be disabled.")


class HTMLReportGenerator:
    """Generate interactive HTML reports for backtest results."""

    def __init__(self, output_dir: str = "reports"):
        """Initialize HTML report generator.

        Args:
            output_dir: Directory to save HTML reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_comprehensive_report(
        self,
        results: Dict[str, Dict[str, Any]],
        price_data: pd.DataFrame,
        config_info: Optional[Dict[str, Any]] = None,
        filename: str = "backtest_report.html"
    ) -> str:
        """Generate comprehensive interactive HTML report.

        Args:
            results: Dictionary mapping strategy names to their results
            price_data: OHLCV DataFrame with price data
            config_info: Configuration information
            filename: Output HTML filename

        Returns:
            Path to generated HTML file
        """
        report_data = {
            "title": "Bitcoin Trading Strategy Backtest Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": self._create_summary_stats(results),
            "strategies": [],
            "comparisons": self._create_comparison_data(results),
            "config": config_info or {}
        }

        # Process each strategy
        for strategy_name, result in results.items():
            strategy_data = self._process_strategy_data(strategy_name, result, price_data)
            report_data["strategies"].append(strategy_data)

        # Generate HTML
        html_content = self._generate_html_template(report_data)

        # Save report
        report_path = self.output_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Interactive HTML report saved to {report_path}")
        return str(report_path)

    def _create_summary_stats(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary statistics across all strategies.

        Args:
            results: Strategy results dictionary

        Returns:
            Summary statistics dictionary
        """
        summary = {
            "total_strategies": len(results),
            "strategies": [],
            "best_return": {"strategy": "", "value": -float("inf")},
            "best_sharpe": {"strategy": "", "value": -float("inf")},
            "lowest_drawdown": {"strategy": "", "value": float("inf")},
            "total_trades": 0
        }

        for strategy_name, result in results.items():
            if "metrics" not in result:
                continue

            metrics = result["metrics"]
            strategy_info = {
                "name": strategy_name,
                "total_return": metrics.get("total_return_pct", 0),
                "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                "max_drawdown": metrics.get("max_drawdown_pct", 0),
                "total_trades": metrics.get("total_trades", 0),
                "win_rate": metrics.get("win_rate_pct", 0),
                "profit_factor": metrics.get("profit_factor", 0)
            }

            summary["strategies"].append(strategy_info)
            summary["total_trades"] += strategy_info["total_trades"]

            # Update best performers
            if strategy_info["total_return"] > summary["best_return"]["value"]:
                summary["best_return"] = {"strategy": strategy_name, "value": strategy_info["total_return"]}

            if strategy_info["sharpe_ratio"] > summary["best_sharpe"]["value"]:
                summary["best_sharpe"] = {"strategy": strategy_name, "value": strategy_info["sharpe_ratio"]}

            if abs(strategy_info["max_drawdown"]) < abs(summary["lowest_drawdown"]["value"]):
                summary["lowest_drawdown"] = {"strategy": strategy_name, "value": strategy_info["max_drawdown"]}

        return summary

    def _create_comparison_data(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create comparison data for interactive charts.

        Args:
            results: Strategy results dictionary

        Returns:
            Comparison data dictionary
        """
        comparison = {
            "equity_curves": {},
            "metrics_comparison": {},
            "trade_analysis": {}
        }

        # Equity curves comparison
        for strategy_name, result in results.items():
            if "equity" in result and len(result["equity"]) > 0:
                equity_data = result["equity"]
                comparison["equity_curves"][strategy_name] = {
                    "dates": equity_data.index.strftime("%Y-%m-%d").tolist(),
                    "values": equity_data["equity"].tolist(),
                    "cash": equity_data["cash"].tolist(),
                    "btc": equity_data["btc"].tolist()
                }

        # Metrics comparison
        metrics_list = ["total_return_pct", "sharpe_ratio", "max_drawdown_pct", "win_rate_pct", "profit_factor"]
        for metric in metrics_list:
            comparison["metrics_comparison"][metric] = {}
            for strategy_name, result in results.items():
                if "metrics" in result and metric in result["metrics"]:
                    comparison["metrics_comparison"][metric][strategy_name] = result["metrics"][metric]

        return comparison

    def _process_strategy_data(self, strategy_name: str, result: Dict[str, Any], price_data: pd.DataFrame) -> Dict[str, Any]:
        """Process strategy data for HTML report.

        Args:
            strategy_name: Strategy name
            result: Strategy result dictionary
            price_data: Price data

        Returns:
            Processed strategy data
        """
        strategy_data = {
            "name": strategy_name,
            "metrics": result.get("metrics", {}),
            "trades": [],
            "charts": {}
        }

        # Process trades
        trades_df = result.get("trades", pd.DataFrame())
        if len(trades_df) > 0:
            strategy_data["trades"] = trades_df.to_dict('records')

        # Generate charts if plotly is available
        if PLOTLY_AVAILABLE:
            strategy_data["charts"] = self._create_strategy_charts(strategy_name, result, price_data)

        return strategy_data

    def _create_strategy_charts(self, strategy_name: str, result: Dict[str, Any], price_data: pd.DataFrame) -> Dict[str, str]:
        """Create interactive charts for a strategy.

        Args:
            strategy_name: Strategy name
            result: Strategy result
            price_data: Price data

        Returns:
            Dictionary with chart JSON data
        """
        charts = {}

        # Equity curve chart
        if "equity" in result and len(result["equity"]) > 0:
            equity_data = result["equity"]
            charts["equity"] = self._create_equity_chart(equity_data, strategy_name)

        # Price chart with trades
        if len(result.get("trades", pd.DataFrame())) > 0:
            charts["price_trades"] = self._create_price_trades_chart(price_data, result["trades"], strategy_name)

        # Drawdown chart
        if "equity" in result and len(result["equity"]) > 0:
            equity_data = result["equity"]
            charts["drawdown"] = self._create_drawdown_chart(equity_data, strategy_name)

        # Metrics radar chart
        if "metrics" in result:
            charts["metrics_radar"] = self._create_metrics_radar_chart(result["metrics"], strategy_name)

        return charts

    def _create_equity_chart(self, equity_data: pd.DataFrame, strategy_name: str) -> str:
        """Create interactive equity curve chart.

        Args:
            equity_data: Equity DataFrame
            strategy_name: Strategy name

        Returns:
            JSON representation of plotly chart
        """
        fig = go.Figure()

        # Add equity curve
        fig.add_trace(go.Scatter(
            x=equity_data.index,
            y=equity_data["equity"],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='blue', width=2)
        ))

        # Add cash line
        fig.add_trace(go.Scatter(
            x=equity_data.index,
            y=equity_data["cash"],
            mode='lines',
            name='Available Cash',
            line=dict(color='green', width=1, dash='dash')
        ))

        fig.update_layout(
            title=f'{strategy_name} - Portfolio Performance',
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            hovermode='x unified',
            showlegend=True
        )

        return fig.to_json()

    def _create_price_trades_chart(self, price_data: pd.DataFrame, trades: pd.DataFrame, strategy_name: str) -> str:
        """Create interactive price chart with trade markers.

        Args:
            price_data: OHLCV DataFrame
            trades: Trades DataFrame
            strategy_name: Strategy name

        Returns:
            JSON representation of plotly chart
        """
        fig = go.Figure()

        # Add candlestick chart
        if all(col in price_data.columns for col in ['Open', 'High', 'Low', 'Close']):
            fig.add_trace(go.Candlestick(
                x=price_data.index,
                open=price_data['Open'],
                high=price_data['High'],
                low=price_data['Low'],
                close=price_data['Close'],
                name='Price'
            ))
        else:
            # Fallback to line chart
            fig.add_trace(go.Scatter(
                x=price_data.index,
                y=price_data['Close'],
                mode='lines',
                name='Price',
                line=dict(color='black', width=1)
            ))

        # Add trade markers
        if len(trades) > 0:
            buys = trades[trades["action"] == "BUY"]
            sells = trades[trades["action"] == "SELL"]

            if len(buys) > 0:
                fig.add_trace(go.Scatter(
                    x=buys["timestamp"],
                    y=buys["price"],
                    mode='markers',
                    name='Buy',
                    marker=dict(symbol='triangle-up', size=10, color='green')
                ))

            if len(sells) > 0:
                fig.add_trace(go.Scatter(
                    x=sells["timestamp"],
                    y=sells["price"],
                    mode='markers',
                    name='Sell',
                    marker=dict(symbol='triangle-down', size=10, color='red')
                ))

        fig.update_layout(
            title=f'{strategy_name} - Trading Signals',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            hovermode='x unified',
            showlegend=True
        )

        return fig.to_json()

    def _create_drawdown_chart(self, equity_data: pd.DataFrame, strategy_name: str) -> str:
        """Create interactive drawdown chart.

        Args:
            equity_data: Equity DataFrame
            strategy_name: Strategy name

        Returns:
            JSON representation of plotly chart
        """
        # Calculate drawdown
        peak = equity_data["equity"].expanding().max()
        drawdown = (equity_data["equity"] - peak) / peak * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            mode='lines',
            name='Drawdown',
            fill='tonexty',
            line=dict(color='red', width=1),
            fillcolor='rgba(255,0,0,0.3)'
        ))

        fig.update_layout(
            title=f'{strategy_name} - Drawdown Analysis',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            hovermode='x unified'
        )

        return fig.to_json()

    def _create_metrics_radar_chart(self, metrics: Dict[str, Any], strategy_name: str) -> str:
        """Create radar chart for strategy metrics.

        Args:
            metrics: Metrics dictionary
            strategy_name: Strategy name

        Returns:
            JSON representation of plotly chart
        """
        # Select and normalize metrics for radar chart
        radar_metrics = {
            "Return": min(max(metrics.get("total_return_pct", 0) / 100, -1), 1),  # Normalize to -1 to 1
            "Sharpe": min(max(metrics.get("sharpe_ratio", 0) / 3, -1), 1),  # Assuming max Sharpe of 3
            "Win Rate": metrics.get("win_rate_pct", 0) / 100,
            "Profit Factor": min(max(metrics.get("profit_factor", 0) / 5, 0), 1),  # Assuming max PF of 5
            "Stability": 1 - abs(metrics.get("max_drawdown_pct", 0)) / 100  # Inverse of drawdown
        }

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=list(radar_metrics.values()),
            theta=list(radar_metrics.keys()),
            fill='toself',
            name=strategy_name
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title=f'{strategy_name} - Performance Metrics'
        )

        return fig.to_json()

    def _generate_html_template(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML template with embedded data.

        Args:
            report_data: Report data dictionary

        Returns:
            Complete HTML content
        """
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 40px; border-bottom: 2px solid #007bff; padding-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .strategy-section {{ margin-bottom: 40px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        .strategy-header {{ background: #007bff; color: white; padding: 15px; font-size: 18px; font-weight: bold; }}
        .strategy-content {{ padding: 20px; }}
        .chart-container {{ margin: 20px 0; height: 400px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .tabs {{ display: flex; border-bottom: 1px solid #ddd; margin-bottom: 20px; }}
        .tab {{ padding: 10px 20px; cursor: pointer; border: none; background: #f8f9fa; margin-right: 5px; border-radius: 5px 5px 0 0; }}
        .tab.active {{ background: #007bff; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .trade-buy {{ color: #28a745; font-weight: bold; }}
        .trade-sell {{ color: #dc3545; font-weight: bold; }}
        .comparison-table {{ margin: 20px 0; }}
        .best-performer {{ background-color: #d4edda; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Generated on {generated_at}</p>
        </div>

        <div class="summary">
            <div class="metric-card">
                <h3>{summary[total_strategies]}</h3>
                <p>Strategies Tested</p>
            </div>
            <div class="metric-card">
                <h3>{summary[best_return][strategy]}</h3>
                <p>Best Return: {summary[best_return][value]:.2%}</p>
            </div>
            <div class="metric-card">
                <h3>{summary[best_sharpe][strategy]}</h3>
                <p>Best Sharpe: {summary[best_sharpe][value]:.2f}</p>
            </div>
            <div class="metric-card">
                <h3>{summary[total_trades]}</h3>
                <p>Total Trades</p>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('strategies')">Strategy Details</button>
            <button class="tab" onclick="showTab('comparison')">Comparison</button>
        </div>

        <div id="overview" class="tab-content active">
            <h2>Portfolio Performance Comparison</h2>
            <div class="chart-container" id="equity-comparison-chart"></div>

            <h2>Performance Metrics Comparison</h2>
            <div class="comparison-table">
                <table>
                    <thead>
                        <tr>
                            <th>Strategy</th>
                            <th>Total Return</th>
                            <th>Sharpe Ratio</th>
                            <th>Max Drawdown</th>
                            <th>Win Rate</th>
                            <th>Profit Factor</th>
                            <th>Total Trades</th>
                        </tr>
                    </thead>
                    <tbody>
                        {strategy_comparison_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <div id="strategies" class="tab-content">
            {strategy_sections}
        </div>

        <div id="comparison" class="tab-content">
            <h2>Metrics Comparison</h2>
            <div class="chart-container" id="metrics-radar-chart"></div>
            <div class="chart-container" id="bar-charts-container"></div>
        </div>
    </div>

    <script>
        // Report data
        const reportData = {report_data_json};

        // Tab functionality
        function showTab(tabName) {{
            const tabs = document.querySelectorAll('.tab');
            const contents = document.querySelectorAll('.tab-content');

            tabs.forEach(tab => tab.classList.remove('active'));
            contents.forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');

            // Initialize charts when tab is shown
            if (tabName === 'overview') {{
                initializeOverviewCharts();
            }} else if (tabName === 'comparison') {{
                initializeComparisonCharts();
            }}
        }}

        // Initialize overview charts
        function initializeOverviewCharts() {{
            const equityData = reportData.comparisons.equity_curves;
            const traces = [];

            for (const [strategy, data] of Object.entries(equityData)) {{
                traces.push({{
                    x: data.dates,
                    y: data.values,
                    mode: 'lines',
                    name: strategy,
                    line: {{ width: 2 }}
                }});
            }}

            const layout = {{
                title: 'Strategy Performance Comparison',
                xaxis: {{ title: 'Date' }},
                yaxis: {{ title: 'Portfolio Value ($)' }},
                hovermode: 'x unified',
                showlegend: true,
                height: 400
            }};

            Plotly.newPlot('equity-comparison-chart', traces, layout);
        }}

        // Initialize comparison charts
        function initializeComparisonCharts() {{
            const metrics = reportData.comparisons.metrics_comparison;
            const strategies = Object.keys(metrics.total_return_pct || {{}});

            // Create bar charts for each metric
            const barChartsContainer = document.getElementById('bar-charts-container');
            barChartsContainer.innerHTML = '';

            const metricsToPlot = ['total_return_pct', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate_pct'];
            const metricLabels = {{
                'total_return_pct': 'Total Return (%)',
                'sharpe_ratio': 'Sharpe Ratio',
                'max_drawdown_pct': 'Max Drawdown (%)',
                'win_rate_pct': 'Win Rate (%)'
            }};

            metricsToPlot.forEach(metric => {{
                if (metrics[metric]) {{
                    const div = document.createElement('div');
                    div.className = 'chart-container';
                    div.style.height = '300px';

                    const data = [{{
                        x: strategies,
                        y: strategies.map(s => metrics[metric][s] || 0),
                        type: 'bar',
                        marker: {{ color: 'rgba(54, 162, 235, 0.8)' }}
                    }}];

                    const layout = {{
                        title: metricLabels[metric],
                        xaxis: {{ title: 'Strategy' }},
                        yaxis: {{ title: metricLabels[metric] }},
                        height: 300
                    }};

                    Plotly.newPlot(div, data, layout);
                    barChartsContainer.appendChild(div);
                }}
            }});
        }}

        // Initialize strategy charts
        function initializeStrategyCharts(strategyName, charts) {{
            for (const [chartType, chartData] of Object.entries(charts)) {{
                try {{
                    const chartId = `chart-${{strategyName.replace(/\\s+/g, '-')}}-${{chartType}}`;
                    const element = document.getElementById(chartId);
                    if (element) {{
                        Plotly.newPlot(chartId, JSON.parse(chartData));
                    }}
                }} catch (error) {{
                    console.error(`Error initializing chart ${{chartType}} for ${{strategyName}}:`, error);
                }}
            }}
        }}

        // Initialize all strategy charts on page load
        document.addEventListener('DOMContentLoaded', function() {{
            // Initialize overview charts
            initializeOverviewCharts();

            // Initialize individual strategy charts
            {strategy_chart_initializers}
        }});
    </script>
</body>
</html>
        """

        # Generate strategy comparison rows
        comparison_rows = ""
        for strategy_info in report_data["summary"]["strategies"]:
            comparison_rows += f"""
            <tr>
                <td><strong>{strategy_info["name"]}</strong></td>
                <td>{strategy_info["total_return"]:.2%}</td>
                <td>{strategy_info["sharpe_ratio"]:.2f}</td>
                <td>{strategy_info["max_drawdown"]:.2%}</td>
                <td>{strategy_info["win_rate"]:.1%}</td>
                <td>{strategy_info["profit_factor"]:.2f}</td>
                <td>{strategy_info["total_trades"]}</td>
            </tr>
            """

        # Generate strategy sections
        strategy_sections = ""
        strategy_chart_initializers = ""

        for i, strategy in enumerate(report_data["strategies"]):
            strategy_id = strategy["name"].replace(" ", "-").lower()

            # Metrics grid
            metrics_grid = ""
            if strategy["metrics"]:
                metrics_grid += "<div class='metrics-grid'>"
                key_metrics = {
                    "Total Return": strategy["metrics"].get("total_return_pct", 0),
                    "Sharpe Ratio": strategy["metrics"].get("sharpe_ratio", 0),
                    "Max Drawdown": strategy["metrics"].get("max_drawdown_pct", 0),
                    "Win Rate": strategy["metrics"].get("win_rate_pct", 0),
                    "Total Trades": strategy["metrics"].get("total_trades", 0),
                    "Profit Factor": strategy["metrics"].get("profit_factor", 0)
                }
                for metric_name, value in key_metrics.items():
                    display_value = f"{value:.2%}" if "Rate" in metric_name or "Return" in metric_name or "Drawdown" in metric_name else f"{value:.2f}"
                    metrics_grid += f"<div class='metric'><h4>{metric_name}</h4><p>{display_value}</p></div>"
                metrics_grid += "</div>"

            # Charts section
            charts_section = ""
            chart_initializers = ""
            if strategy["charts"]:
                for chart_type, chart_data in strategy["charts"].items():
                    chart_id = f"chart-{strategy_id}-{chart_type}"
                    chart_title = chart_type.replace("_", " ").title()
                    charts_section += f"""
                    <h3>{chart_title}</h3>
                    <div class="chart-container" id="{chart_id}"></div>
                    """
                    chart_initializers += f"""
                    initializeStrategyCharts('{strategy["name"]}', {json.dumps(strategy["charts"])});
                    """

            # Recent trades table
            trades_table = ""
            if strategy["trades"]:
                recent_trades = strategy["trades"][-10:]  # Last 10 trades
                trades_table += """
                <h3>Recent Trades</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Action</th>
                            <th>Price</th>
                            <th>Quantity</th>
                            <th>P&L</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for trade in recent_trades:
                    action_class = "trade-buy" if trade["action"] == "BUY" else "trade-sell"
                    pnl = trade.get("pnl", 0)
                    pnl_display = f"${pnl:.2f}" if pnl != 0 else "-"
                    trades_table += f"""
                    <tr>
                        <td>{trade.get('timestamp', 'N/A')}</td>
                        <td class="{action_class}">{trade["action"]}</td>
                        <td>${trade["price"]:.2f}</td>
                        <td>{trade["quantity"]:.6f}</td>
                        <td>{pnl_display}</td>
                        <td>{trade.get('reason', 'N/A')[:50]}{'...' if len(trade.get('reason', '')) > 50 else ''}</td>
                    </tr>
                    """
                trades_table += "</tbody></table>"

            strategy_sections += f"""
            <div class="strategy-section">
                <div class="strategy-header">{strategy["name"]}</div>
                <div class="strategy-content">
                    {metrics_grid}
                    {charts_section}
                    {trades_table}
                </div>
            </div>
            """

        # Format the template
        return html_template.format(
            title=report_data["title"],
            generated_at=report_data["generated_at"],
            summary=json.dumps(report_data["summary"]),
            strategy_comparison_rows=comparison_rows,
            strategy_sections=strategy_sections,
            strategy_chart_initializers=strategy_chart_initializers,
            report_data_json=json.dumps(report_data)
        )