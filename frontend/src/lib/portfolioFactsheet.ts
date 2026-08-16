import type { InvestmentComparisonResponsePayload } from '../types/api';
import { formatCurrency, formatPercent } from './utils';

export function openPortfolioFactsheet(comparison: InvestmentComparisonResponsePayload) {
  const title = 'Lâmina Executiva de Carteira';
  const profile = comparison.request.decision_profile || {};
  const results = comparison.results || [];
  const highlights = comparison.highlights || {};

  const rowsHtml = results
    .map(
      (r) => `
      <tr>
        <td style="padding: 8px 12px; font-weight: 600; border-bottom: 1px solid #e2e8f0;">${r.label}</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; color: #64748b;">${r.category_label}</td>
        <td style="padding: 8px 12px; text-align: right; border-bottom: 1px solid #e2e8f0; font-weight: 600;">${formatCurrency(r.final_value)}</td>
        <td style="padding: 8px 12px; text-align: right; border-bottom: 1px solid #e2e8f0; color: #059669;">${formatPercent(r.cagr)}</td>
        <td style="padding: 8px 12px; text-align: right; border-bottom: 1px solid #e2e8f0; color: #dc2626;">${formatPercent(r.max_drawdown)}</td>
      </tr>
    `
    )
    .join('');

  const bestNominal = highlights.best_final_value?.label ?? 'n/a';
  const bestReal = highlights.best_real_cagr?.label ?? 'n/a';
  const lowestDd = highlights.most_defensive?.label ?? 'n/a';

  const objectiveLabel = profile.objective_label ?? profile.objective ?? 'Geral';
  const horizonLabel = profile.horizon_years ? `${profile.horizon_years} anos` : 'Longo Prazo';
  const liquidityLabel = profile.liquidity_need_label ?? profile.liquidity_need ?? 'Média';

  const htmlContent = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>${title} - Factsheet</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 32px;
      color: #0f172a;
      background-color: #ffffff;
      line-height: 1.5;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #0f172a;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }
    .logo {
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #1e293b;
    }
    .badge {
      display: inline-block;
      padding: 4px 8px;
      background-color: #e2e8f0;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      color: #334155;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .metric-card {
      padding: 14px;
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
    }
    .metric-title {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #64748b;
      font-weight: 600;
    }
    .metric-value {
      font-size: 18px;
      font-weight: 700;
      color: #0f172a;
      margin-top: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background-color: #f1f5f9;
      color: #334155;
      font-weight: 600;
      padding: 10px 12px;
      border-bottom: 2px solid #cbd5e1;
    }
    .footer {
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #e2e8f0;
      font-size: 11px;
      color: #64748b;
      line-height: 1.6;
    }
    @media print {
      body { padding: 0; }
      .no-print { display: none; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <div class="logo">SYSTEMS STUDIO / INVESTING WORKBENCH</div>
      <h1 style="margin: 6px 0 0 0; font-size: 22px;">${title}</h1>
    </div>
    <div style="text-align: right;">
      <span class="badge">Objetivo: ${objectiveLabel}</span>
      <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Horizonte: ${horizonLabel} · Liquidez: ${liquidityLabel}</div>
    </div>
  </div>

  <div class="metric-grid">
    <div class="metric-card">
      <div class="metric-title">Maior Acumulação</div>
      <div class="metric-value">${bestNominal}</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Maior Retorno Real</div>
      <div class="metric-value" style="color: #059669;">${bestReal}</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Menor Drawdown</div>
      <div class="metric-value" style="color: #4f46e5;">${lowestDd}</div>
    </div>
  </div>

  <h2 style="font-size: 16px; margin: 24px 0 12px 0; color: #1e293b;">Tabela Comparativa de Ativos e Carteiras</h2>
  <table>
    <thead>
      <tr>
        <th style="text-align: left;">Investimento</th>
        <th style="text-align: left;">Classe</th>
        <th style="text-align: right;">Valor Final</th>
        <th style="text-align: right;">CAGR</th>
        <th style="text-align: right;">Drawdown Máx</th>
      </tr>
    </thead>
    <tbody>
      ${rowsHtml}
    </tbody>
  </table>

  <div class="footer">
    <strong>Aviso Legal:</strong> Este relatório é gerado automaticamente para fins de simulação e aprendizado causal. Rentabilidade passada não representa garantia de retorno futuro. As simulações consideram tributação regressiva brasileira e premissas de aportes contínuos.
  </div>
</body>
</html>`;

  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, '_blank');
  if (!win) {
    const a = document.createElement('a');
    a.href = url;
    a.download = `lamina_carteira_${new Date().toISOString().slice(0, 10)}.html`;
    a.click();
  }
}
