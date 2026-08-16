"""Institutional portfolio factsheet and executive report generation."""

from __future__ import annotations

import html
from typing import Any


def build_portfolio_factsheet_html(
    *,
    study_title: str = "Lâmina Executiva de Carteira",
    profile: dict[str, Any] | None = None,
    results: list[dict[str, Any]] | None = None,
    metrics_summary: dict[str, Any] | None = None,
    smart_contributions: dict[str, Any] | None = None,
) -> str:
    """Generate a clean, printable HTML factsheet (Lâmina) for an investment portfolio study."""

    user_profile = profile or {}
    items = results or []
    metrics = metrics_summary or {}

    objective = str(user_profile.get("objective", "balanced")).capitalize()
    horizon = str(user_profile.get("horizon", "long_term")).replace("_", " ").capitalize()
    liquidity = str(user_profile.get("liquidity", "medium")).capitalize()

    final_val = float(metrics.get("final_value", 0.0) or 0.0)
    real_cagr = float(metrics.get("real_cagr", 0.0) or 0.0)
    max_dd = float(metrics.get("max_drawdown", 0.0) or 0.0)
    sharpe = float(metrics.get("sharpe_ratio", 0.0) or 0.0)

    rows_html = ""
    for item in items:
        label = html.escape(str(item.get("label", "Ativo")))
        cat = html.escape(str(item.get("category_id", "Geral")))
        val = float(item.get("final_value", 0.0) or 0.0)
        cagr = float(item.get("cagr", 0.0) or 0.0) * 100.0
        dd = float(item.get("max_drawdown", 0.0) or 0.0) * 100.0

        rows_html += (
            "<tr>"
            f"<td style='padding: 8px 12px; font-weight: 600;'>{label}</td>"
            f"<td style='padding: 8px 12px; color: #64748b;'>{cat}</td>"
            f"<td style='padding: 8px 12px; text-align: right;'>R$ {val:,.2f}</td>"
            f"<td style='padding: 8px 12px; text-align: right; color: #059669;'>{cagr:.2f}%</td>"
            f"<td style='padding: 8px 12px; text-align: right; color: #dc2626;'>{dd:.2f}%</td>"
            "</tr>\n"
        )

    smart_html = ""
    if smart_contributions and smart_contributions.get("allocations"):
        smart_rows = ""
        for alloc in smart_contributions["allocations"]:
            a_label = html.escape(str(alloc.get("label", "")))
            target_pct = float(alloc.get("target_weight_pct", 0.0))
            current_pct = float(alloc.get("current_weight_pct", 0.0))
            s_contrib = float(alloc.get("suggested_contribution", 0.0))
            status = html.escape(str(alloc.get("rebalance_status", "")))
            smart_rows += (
                "<tr>"
                f"<td style='padding: 6px 10px;'>{a_label}</td>"
                f"<td style='padding: 6px 10px; text-align: right;'>{target_pct:.1f}%</td>"
                f"<td style='padding: 6px 10px; text-align: right;'>{current_pct:.1f}%</td>"
                f"<td style='padding: 6px 10px; text-align: right;'>R$ {s_contrib:,.2f}</td>"
                f"<td style='padding: 6px 10px; text-align: center;'>{status}</td>"
                "</tr>\n"
            )
        smart_html = (
            "<div style='margin-top: 24px; padding: 16px; background: #f8fafc;'>"
            "<h3 style='margin: 0 0 8px 0; font-size: 14px;'>Plano de Aporte Inteligente</h3>"
            "<table style='width: 100%; border-collapse: collapse; font-size: 12px;'>"
            "<thead><tr>"
            "<th>Ativo</th><th>Meta</th><th>Atual</th><th>Aporte</th><th>Ação</th>"
            "</tr></thead>"
            f"<tbody>{smart_rows}</tbody></table></div>"
        )

    empty_row = (
        "<tr><td colspan='5' style='text-align: center; padding: 16px; color: #94a3b8;'>"
        "Nenhum ativo selecionado</td></tr>"
    )
    tbody_content = rows_html if rows_html else empty_row

    disclaimer = (
        "<strong>Aviso Legal & Metodologia:</strong> Documento gerado automaticamente para fins "
        "didaticos. Rentabilidade passada nao garante resultados futuros. Simulacoes consideram "
        "tributacao regressiva de renda fixa e regras legais de isencao."
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(study_title)} - Factsheet</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            margin: 0;
            padding: 32px;
            color: #0f172a;
            background-color: #ffffff;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0f172a;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .logo {{
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #1e293b;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            background-color: #e2e8f0;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            color: #334155;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            padding: 14px;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }}
        .metric-title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
            margin-top: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            padding: 10px 12px;
            border-bottom: 2px solid #cbd5e1;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
            font-size: 11px;
            color: #64748b;
            line-height: 1.6;
        }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="logo">SYSTEMS STUDIO / INVESTING WORKBENCH</div>
            <h1 style="margin: 6px 0 0 0; font-size: 22px;">{html.escape(study_title)}</h1>
        </div>
        <div style="text-align: right;">
            <span class="badge">Perfil: {html.escape(objective)}</span>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                Horizonte: {html.escape(horizon)} · Liquidez: {html.escape(liquidity)}
            </div>
        </div>
    </div>

    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-title">Valor Final Acumulado</div>
            <div class="metric-value">R$ {final_val:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">CAGR Real Líquido</div>
            <div class="metric-value" style="color: #059669;">{real_cagr * 100.0:.2f}% a.a.</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Drawdown Máximo</div>
            <div class="metric-value" style="color: #dc2626;">{max_dd * 100.0:.2f}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Índice Sharpe</div>
            <div class="metric-value">{sharpe:.2f}</div>
        </div>
    </div>

    <h2 style="font-size: 16px; margin: 24px 0 12px 0; color: #1e293b;">
        Alocação de Ativos e Resultados
    </h2>
    <table>
        <thead>
            <tr>
                <th style="text-align: left;">Ativo / Componente</th>
                <th style="text-align: left;">Classe</th>
                <th style="text-align: right;">Valor Final</th>
                <th style="text-align: right;">CAGR Nominal</th>
                <th style="text-align: right;">Drawdown Máx</th>
            </tr>
        </thead>
        <tbody>
            {tbody_content}
        </tbody>
    </table>

    {smart_html}

    <div class="footer">
        {disclaimer}
    </div>
</body>
</html>
"""
