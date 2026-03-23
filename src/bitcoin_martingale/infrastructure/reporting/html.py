"""HTML reporting for persisted runs."""

from __future__ import annotations

from html import escape


class PersistedRunHTMLReportBuilder:
    """Build a lightweight HTML report from persisted run artifacts."""

    def build(
        self,
        *,
        manifest: dict[str, object],
        response_payload: dict[str, object],
        config_snapshot: dict[str, object],
        data_profile: dict[str, object],
    ) -> str:
        """Render a complete HTML report for a persisted run."""
        results = response_payload.get("results", {})
        strategy_cards = self._build_strategy_cards(results)
        run_id = escape(str(manifest.get("run_id", "")))
        created_at = escape(str(manifest.get("created_at", "")))
        config_path = escape(str(manifest.get("config_path", "")))
        fingerprint = escape(str(data_profile.get("data_fingerprint", "")))
        row_count = escape(str(data_profile.get("row_count", "")))
        columns_value = data_profile.get("columns", [])
        columns = (
            ", ".join(str(column) for column in columns_value)
            if isinstance(columns_value, list)
            else ""
        )
        strategy_names = manifest.get("strategy_names", [])
        strategies = (
            ", ".join(str(name) for name in strategy_names)
            if isinstance(strategy_names, list)
            else ""
        )
        initial_capital = self._read_nested(config_snapshot, "backtest", "initial_capital")
        start_timestamp = escape(str(data_profile.get("start_timestamp", "")))
        end_timestamp = escape(str(data_profile.get("end_timestamp", "")))

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Backtest Report {run_id}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      background: #f5f7fb;
      color: #1f2937;
    }}
    .page {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 64px; }}
    .hero {{
      background: linear-gradient(135deg, #0f766e, #14b8a6);
      color: white;
      padding: 24px;
      border-radius: 16px;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .card {{
      background: white;
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      margin-top: 18px;
    }}
    .section-title {{ font-size: 18px; font-weight: 700; margin: 0 0 14px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .metric {{ background: #f8fafc; padding: 12px; border-radius: 12px; }}
    .metric-label {{ font-size: 12px; color: #64748b; margin-bottom: 4px; }}
    .metric-value {{ font-size: 15px; font-weight: 600; }}
    .mono {{ font-family: monospace; word-break: break-all; }}
    .strategy {{ border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px; margin-top: 14px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #e5e7eb; }}
    th {{ color: #475569; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <h1>Persisted Backtest Report</h1>
      <p>Run <span class="mono">{run_id}</span></p>
      <div class="meta">
        <div><strong>Created</strong><br />{created_at}</div>
        <div><strong>Config</strong><br />{config_path}</div>
        <div><strong>Strategies</strong><br />{escape(strategies)}</div>
        <div><strong>Initial Capital</strong><br />{escape(str(initial_capital))}</div>
      </div>
    </div>

    <div class="card">
      <h2 class="section-title">Dataset</h2>
      <div class="grid">
        <div class="metric">
          <div class="metric-label">Rows</div>
          <div class="metric-value">{row_count}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Range</div>
          <div class="metric-value">{start_timestamp} - {end_timestamp}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Columns</div>
          <div class="metric-value">{escape(columns)}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Fingerprint</div>
          <div class="metric-value mono">{fingerprint}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2 class="section-title">Strategies</h2>
      {strategy_cards}
    </div>
  </div>
</body>
</html>"""

    def _build_strategy_cards(self, results: object) -> str:
        if not isinstance(results, dict) or not results:
            return "<p>No strategy results found.</p>"

        strategy_cards: list[str] = []
        for strategy_name, payload in results.items():
            if not isinstance(payload, dict):
                continue
            metrics = payload.get("metrics", {})
            trades = payload.get("trades", [])
            strategy_cards.append(f"""
                <div class="strategy">
                  <h3>{escape(str(strategy_name))}</h3>
                  {self._build_metrics_table(metrics)}
                  <p><strong>Trades:</strong> {len(trades) if isinstance(trades, list) else 0}</p>
                </div>
                """)

        return "".join(strategy_cards)

    def _build_metrics_table(self, metrics: object) -> str:
        if not isinstance(metrics, dict) or not metrics:
            return "<p>No metrics available.</p>"

        ordered_keys = [
            "total_return",
            "cagr",
            "sharpe_ratio",
            "sortino_ratio",
            "max_drawdown",
            "hit_rate",
            "profit_factor",
            "total_trades",
            "avg_trade_pnl",
            "volatility",
            "total_interest_earned",
        ]
        rows = []
        for key in ordered_keys:
            value = metrics.get(key, "-")
            rows.append(f"<tr><th>{escape(key)}</th><td>{escape(str(value))}</td></tr>")
        return f"<table>{''.join(rows)}</table>"

    def _read_nested(self, payload: dict[str, object], *keys: str) -> object:
        current: object = payload
        for key in keys:
            if not isinstance(current, dict):
                return ""
            current = current.get(key, "")
        return current
