import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import FixedIncomeDecisionGuidePanel from './FixedIncomeDecisionGuidePanel';
import InvestmentMethodologyPanel from './InvestmentMethodologyPanel';
import PortfolioObjectiveSummaryPanel from './PortfolioObjectiveSummaryPanel';

describe('investment decision panels', () => {
  it('explains methodology evidence and caveats in plain language', () => {
    render(
      <InvestmentMethodologyPanel
        guide={{
          title: 'Como ler este estudo',
          plain_language_summary: 'Compare evidencias diferentes no mesmo fluxo de dinheiro.',
          evidence_types: [
            {
              kind: 'fixed_income_index',
              label: 'Indice de renda fixa',
              description: 'Compara CDI e IDkA por duration.',
              limitations: 'Indice nao e produto compravel.',
              included_count: 2,
              included_labels: ['CDI', 'IDkA IPCA 2A'],
            },
          ],
          assumption_notes: ['Mesmo fluxo de aportes.'],
          caveats: ['Vencedor historico nao e recomendacao automatica.'],
        }}
      />
    );

    expect(screen.getByText('Como ler este estudo')).toBeTruthy();
    expect(screen.getByText('Indice de renda fixa')).toBeTruthy();
    expect(screen.getByText(/Vencedor historico nao e recomendacao automatica/)).toBeTruthy();
  });

  it('shows fixed-income decisions as objective cards', () => {
    render(
      <FixedIncomeDecisionGuidePanel
        guide={{
          title: 'Como decidir em renda fixa',
          plain_language_summary: 'CDI e liquidez; IPCA+ e poder de compra.',
          study_label: 'IDkA por duration',
          tax_treatment: 'gross',
          window_frequency: 'monthly',
          decision_cards: [
            {
              decision_id: 'real_return',
              label: 'Proteger poder de compra',
              when_it_fits: 'Horizonte de varios anos.',
              watch_out: 'Sofre marcacao a mercado.',
              best_match_id: 'IDKA_IPCA_2A',
              best_match_label: 'IDkA IPCA 2A',
              metric_label: 'CAGR real',
              metric_value: 0.061,
              metric_kind: 'percent',
            },
          ],
          next_questions: ['Quando eu preciso desse dinheiro de volta?'],
        }}
      />
    );

    expect(screen.getByText('Como decidir em renda fixa')).toBeTruthy();
    expect(screen.getByText('IDkA IPCA 2A')).toBeTruthy();
    expect(screen.getByText(/6\.10%/)).toBeTruthy();
  });

  it('summarizes portfolio objectives and portfolio rows', () => {
    render(
      <PortfolioObjectiveSummaryPanel
        summary={{
          title: 'Decisao por objetivo',
          plain_language_summary: 'Nao existe uma melhor escolha universal.',
          fixed_income_study_available: true,
          objectives: [
            {
              objective_id: 'compare_allocation',
              label: 'Comparar carteira',
              question: 'Minha combinacao ficou melhor?',
              best_match_id: 'CUSTOM',
              best_match_label: 'Minha carteira',
              reason: 'Mostra diversificacao e rebalanceamento.',
              tradeoff: 'Depende dos pesos escolhidos.',
              metric_label: 'Valor final',
              metric_value: 12500,
              metric_kind: 'currency',
            },
          ],
          portfolio_rows: [
            {
              instrument_id: 'CUSTOM',
              label: 'Minha carteira',
              source_kind: 'custom_portfolio',
              final_value: 12500,
              real_cagr: 0.04,
              max_drawdown: -0.08,
              component_count: 2,
              top_components: [
                {
                  label: 'CDI',
                  target_weight: 0.5,
                  ending_weight: 0.48,
                  final_value: 6000,
                },
              ],
              category_breakdown: [],
            },
          ],
          next_steps: ['Compare carteira contra ativos isolados.'],
        }}
      />
    );

    expect(screen.getByText('Decisao por objetivo')).toBeTruthy();
    expect(screen.getByText('Carteiras no estudo')).toBeTruthy();
    expect(screen.getAllByText('Minha carteira').length).toBeGreaterThan(0);
  });
});
