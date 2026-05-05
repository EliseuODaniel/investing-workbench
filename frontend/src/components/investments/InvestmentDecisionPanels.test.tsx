import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { apiClient } from '../../lib/api';
import FixedIncomeDecisionGuidePanel from './FixedIncomeDecisionGuidePanel';
import InvestmentCacheStatusPanel from './InvestmentCacheStatusPanel';
import InvestmentComparisonSummaryPanel from './InvestmentComparisonSummaryPanel';
import InvestmentFixedIncomeBacktestPanel from './InvestmentFixedIncomeBacktestPanel';
import InvestmentHighlightsPanel from './InvestmentHighlightsPanel';
import InvestmentMarketExplorerPanel from './InvestmentMarketExplorerPanel';
import InvestmentMethodologyPanel from './InvestmentMethodologyPanel';
import InvestmentPortfolioContributionPanel from './InvestmentPortfolioContributionPanel';
import InvestmentProductRealismPanel from './InvestmentProductRealismPanel';
import InvestmentReviewStatsPanel from './InvestmentReviewStatsPanel';
import InvestmentResultFootnotesPanel from './InvestmentResultFootnotesPanel';
import InvestmentResultsPanel from './InvestmentResultsPanel';
import InvestmentResultStoriesPanel from './InvestmentResultStoriesPanel';
import PortfolioObjectiveSummaryPanel from './PortfolioObjectiveSummaryPanel';
import RetailFixedIncomeEquivalencePanel from './RetailFixedIncomeEquivalencePanel';

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

  it('shows product realism dimensions and methodology queue', () => {
    render(
      <InvestmentProductRealismPanel
        realism={{
          title: 'Realismo do produto investivel',
          plain_language_summary:
            'Mostra onde a comparacao se aproxima de uma experiencia compravel.',
          product_types: [
            {
              source_kind: 'fixed_income_index',
              label: 'Indice de renda fixa',
              count: 2,
            },
          ],
          coverage: [
            {
              dimension_id: 'taxes',
              label: 'IR, IOF e leitura liquida',
              status: 'partial',
              status_label: 'parcial',
              summary: 'Tesouro Direto ja estima impostos em algumas leituras.',
              current_scope: ['visao solicitada: net'],
              limitations: 'Ainda nao calcula regras completas de renda variavel.',
              next_step: 'Criar uma camada tributaria por produto.',
            },
          ],
          next_methodology_steps: ['Separar retorno bruto, liquido e renda distribuida.'],
        }}
      />
    );

    expect(screen.getByText('Realismo do produto investivel')).toBeTruthy();
    expect(screen.getByText('IR, IOF e leitura liquida')).toBeTruthy();
    expect(screen.getByText('Fila metodologica')).toBeTruthy();
  });

  it('shows the top comparison highlights', () => {
    const row = {
      instrument_id: 'PETR4',
      label: 'PETR4',
      ticker: 'PETR4',
      category_id: 'stocks_brazil',
      category_label: 'Acoes brasileiras',
      description: 'Petrobras',
      rationale: 'Teste',
      risk_label: 'Alta',
      region_label: 'Brasil',
      source_kind: 'listed_security',
      invested_total: 10000,
      final_value: 15000,
      net_profit: 5000,
      total_return_on_invested: 0.5,
      time_weighted_return: 0.5,
      cagr: 0.12,
      annual_volatility: 0.2,
      max_drawdown: -0.1,
      availability_start: '2021-01-01',
      availability_end: '2024-01-01',
      invested_total_real: 9000,
      final_value_real: 13000,
      net_profit_real: 4000,
      real_total_return_on_invested: 0.44,
      real_time_weighted_return: 0.4,
      real_cagr: 0.08,
      final_value_net: 15000,
      net_profit_net: 5000,
      cagr_net: 0.12,
      final_value_real_net: 13000,
      net_profit_real_net: 4000,
      real_cagr_net: 0.08,
      component_breakdown: [],
      category_breakdown: [],
    };

    render(
      <InvestmentHighlightsPanel
        highlights={{
          best_final_value: row,
          best_real_cagr: row,
          most_defensive: row,
          beats_inflation_count: 1,
        }}
        resultCount={2}
      />
    );

    expect(screen.getByText('Melhor valor final')).toBeTruthy();
    expect(screen.getByText('Melhor retorno real')).toBeTruthy();
    expect(screen.getByText('Mais defensivo')).toBeTruthy();
    expect(screen.getByText('1 / 2')).toBeTruthy();
  });

  it('shows the comparison result table and side readings', () => {
    const result = {
      instrument_id: 'WEGE3',
      label: 'WEGE3',
      ticker: 'WEGE3',
      category_id: 'stocks_brazil',
      category_label: 'Acoes brasileiras',
      description: 'Empresa da B3.',
      rationale: 'Teste.',
      risk_label: 'Alta',
      region_label: 'Brasil',
      source_kind: 'listed_security',
      invested_total: 10000,
      final_value: 15000,
      net_profit: 5000,
      total_return_on_invested: 0.5,
      time_weighted_return: 0.5,
      cagr: 0.12,
      annual_volatility: 0.2,
      max_drawdown: -0.1,
      availability_start: '2021-01-01',
      availability_end: '2024-01-01',
      invested_total_real: 9000,
      final_value_real: 13000,
      net_profit_real: 4000,
      real_total_return_on_invested: 0.44,
      real_time_weighted_return: 0.4,
      real_cagr: 0.08,
      final_value_net: 15000,
      net_profit_net: 5000,
      cagr_net: 0.12,
      final_value_real_net: 13000,
      net_profit_real_net: 4000,
      real_cagr_net: 0.08,
      component_breakdown: [],
      category_breakdown: [],
    };

    render(
      <InvestmentComparisonSummaryPanel
        comparison={{
          generated_at: '2026-04-24T00:00:00Z',
          request: {
            asset_ids: ['WEGE3'],
            custom_portfolios: [],
            start_date: '2021-01-01',
            end_date: '2024-01-01',
            initial_capital: 10000,
            monthly_contribution: 0,
            benchmark_ids: ['selic_cash'],
            fixed_income_study_mode: 'none',
            fixed_income_tax_treatment: 'gross',
            fixed_income_window_frequency: 'monthly',
            decision_profile: {
              objective: 'growth',
              horizon_years: 5,
              liquidity_need: 'low',
              mark_to_market_tolerance: 'medium',
              tax_view: 'net',
              monthly_income_target: 0,
            },
            force_download: false,
          },
          catalog_snapshot: {},
          assumptions: [],
          results: [result],
          benchmarks: [
            {
              ...result,
              instrument_id: 'selic_cash',
              benchmark_id: 'selic_cash',
              label: 'SELIC / caixa',
              equity_curve: [],
            },
          ],
          chart: { series: [], points: [] },
          real_chart: { series: [], points: [] },
          inflation: {
            label: 'IPCA',
            accumulated_rate: 0.2,
            purchasing_power_loss: 0.16,
            availability_start: '2021-01-01',
            availability_end: '2024-01-01',
            source_label: 'IBGE',
          },
          class_summary: [
            {
              category_label: 'Acoes brasileiras',
              asset_count: 1,
              average_final_value: 15000,
              average_cagr: 0.12,
              average_real_cagr: 0.08,
              average_max_drawdown: -0.1,
              leader_label: 'WEGE3',
            },
          ],
          highlights: {
            best_real_cagr: result,
            insights: ['WEGE3 ficou acima da inflacao.'],
          },
          warnings: [],
        }}
      />
    );

    expect(screen.getByText('Investimento')).toBeTruthy();
    expect(screen.getByText('Leituras rapidas')).toBeTruthy();
    expect(screen.getByText('Inflacao e retorno real')).toBeTruthy();
    expect(screen.getByText('Benchmarks usados')).toBeTruthy();
  });

  it('summarizes the investment review counts', () => {
    render(
      <InvestmentReviewStatsPanel
        selectedAssetCount={4}
        selectedBenchmarkCount={2}
        selectedGuidedPortfolioCount={1}
        entryMode="guided"
      />
    );

    expect(screen.getByText('Comparativos')).toBeTruthy();
    expect(screen.getByText('Benchmarks')).toBeTruthy();
    expect(screen.getByText('Carteiras guiadas')).toBeTruthy();
    expect(screen.getByText('Estudo pronto')).toBeTruthy();
  });

  it('shows retail fixed-income after-tax equivalence', () => {
    render(
      <RetailFixedIncomeEquivalencePanel
        equivalence={{
          title: 'Equivalencia liquida em renda fixa de varejo',
          plain_language_summary: 'Compara CDB tributado com LCI/LCA isenta.',
          reference_cdi_annual_rate: 0.105,
          profile_horizon_days: 720,
          profile_horizon_label: '2 ano(s), conforme o perfil de decisao',
          uses_fixed_income_backtest: true,
          rows: [
            {
              holding_days: 720,
              holding_years: 1.97,
              tax_exempt_product: 'LCI/LCA',
              tax_exempt_pct_cdi: 0.9,
              tax_exempt_annual_rate: 0.0945,
              ir_rate: 0.175,
              iof_rate: 0,
              net_gain_retention: 0.825,
              equivalent_cdb_pct_cdi: 1.08,
              equivalent_cdb_annual_rate: 0.1134,
              interpretation: 'Uma LCI/LCA a 90% do CDI equivale a um CDB a 108% do CDI.',
            },
          ],
          assumptions: ['Sem ofertas reais.'],
          next_steps: ['Adicionar CDB e LCI/LCA editaveis.'],
        }}
      />
    );

    expect(screen.getByText('Equivalencia liquida em renda fixa de varejo')).toBeTruthy();
    expect(screen.getByText('CDB equivalente')).toBeTruthy();
    expect(screen.getByText(/108\.00% do CDI/)).toBeTruthy();
    expect(screen.getByText('Próximas comparações')).toBeTruthy();
  });

  it('shows guided result stories and rankings', () => {
    render(
      <InvestmentResultStoriesPanel
        stories={{
          title: 'Leituras guiadas do resultado',
          plain_language_summary: 'Perguntas praticas sobre o resultado.',
          stories: [
            {
              story_id: 'beat_selic',
              label: 'Quem bateu a Selic',
              question: 'Quantas escolhas compensaram sair do caixa?',
              winner_id: null,
              winner_label: null,
              metric_label: 'Acima da Selic',
              metric_value: 2,
              metric_kind: 'count',
              interpretation: '2 de 3 comparativos terminaram acima da Selic.',
              caveat: 'Bater a Selic nao basta.',
            },
          ],
          rankings: [
            {
              ranking_id: 'final_value',
              label: 'Ranking por valor final',
              metric_label: 'Valor final',
              metric_kind: 'currency',
              rows: [
                {
                  rank: 1,
                  instrument_id: 'PETR4',
                  label: 'PETR4',
                  category_label: 'Acoes brasileiras',
                  value: 15000,
                },
              ],
            },
          ],
          next_questions: ['O risco fez sentido?'],
        }}
      />
    );

    expect(screen.getByText('Leituras guiadas do resultado')).toBeTruthy();
    expect(screen.getByText('Quem bateu a Selic')).toBeTruthy();
    expect(screen.getByText('Ranking por valor final')).toBeTruthy();
    expect(screen.getByText('Próximas perguntas')).toBeTruthy();
  });

  it('shows fixed-income backtest studies with leaders and rolling windows', () => {
    const result = {
      instrument_id: 'CDI_INDEX',
      label: 'CDI',
      category_id: 'fixed_income_b3',
      category_label: 'Renda fixa',
      description: 'Pós-fixado.',
      rationale: 'Base defensiva.',
      risk_label: 'Baixa',
      region_label: 'Brasil',
      source_kind: 'fixed_income_index',
      invested_total: 10000,
      final_value: 12000,
      net_profit: 2000,
      total_return_on_invested: 0.2,
      time_weighted_return: 0.2,
      cagr: 0.1,
      annual_volatility: 0.01,
      max_drawdown: -0.01,
      availability_start: '2020-01-01',
      availability_end: '2024-01-01',
      invested_total_real: 9500,
      final_value_real: 11200,
      net_profit_real: 1700,
      real_total_return_on_invested: 0.17,
      real_time_weighted_return: 0.17,
      real_cagr: 0.07,
      final_value_net: 11900,
      net_profit_net: 1900,
      cagr_net: 0.095,
      final_value_real_net: 11100,
      net_profit_real_net: 1600,
      real_cagr_net: 0.065,
      component_breakdown: [],
      category_breakdown: [],
      family_id: 'post_fixed',
      family_label: 'Pós-fixado',
      duration_years: null,
      title_type: 'post_fixed',
      selection_rule: 'benchmark',
      source_method_label: 'CDI acumulado',
      display_value: 11900,
      display_profit: 1900,
      display_cagr: 0.095,
      display_value_real: 11100,
      display_profit_real: 1600,
      display_real_cagr: 0.065,
      comparison_metric_label: 'Valor líquido',
      relative_gap_vs_benchmark: 0,
      value_gap_vs_benchmark: 0,
      relative_gap_vs_benchmark_real: 0,
      value_gap_vs_benchmark_real: 0,
      is_benchmark: true,
    };

    render(
      <InvestmentFixedIncomeBacktestPanel
        backtest={{
          requested_study_mode: 'all',
          methodology: {
            benchmark_instrument_id: 'CDI_INDEX',
            benchmark_label: 'CDI',
            series_source_label: 'BCB e Anbima',
            index_methodology_label: 'Índice teórico por duration.',
            rolling_window_note: 'Janelas móveis.',
            full_period_note: 'Período completo.',
            selected_fixed_income_ids: ['CDI_INDEX'],
            video_reference_match: true,
          },
          full_period: {
            start_date: '2020-01-01',
            end_date: '2024-01-01',
            initial_capital: 10000,
            monthly_contribution: 0,
            benchmark: result,
            results: [result],
            leaders: {
              overall: result,
              prefixado: result,
              ipca_plus: result,
              most_consistent: {
                study_id: 'fixed_income',
                instrument_id: 'CDI_INDEX',
                label: 'CDI',
                source_kind: 'fixed_income_index',
                family_id: 'post_fixed',
                family_label: 'Pós-fixado',
                duration_years: null,
                window_years: 5,
                window_frequency: 'yearly',
                windows_count: 4,
                win_rate: 0.75,
                average_excess_return: 0.01,
                median_excess_return: 0.01,
                best_excess_return: 0.03,
                worst_excess_return: -0.01,
                best_window_start: '2020-01-01',
                best_window_end: '2024-12-31',
              },
            },
          },
          rolling_windows: [],
          takeaways: [],
          studies: [
            {
              study_id: 'fixed_income',
              study_label: 'Renda fixa real',
              methodology: {
                study_id: 'fixed_income',
                study_label: 'Renda fixa real',
                benchmark_instrument_id: 'CDI_INDEX',
                benchmark_label: 'CDI',
                series_source_label: 'BCB e Anbima',
                index_methodology_label: 'Índice teórico por duration.',
                what_it_measures: 'Retorno histórico líquido.',
                what_it_does_not_measure: 'Oferta atual de corretora.',
                rolling_window_note: 'Janelas móveis.',
                full_period_note: 'Período completo.',
                comparison_metric_label: 'Valor líquido',
                selected_fixed_income_ids: ['CDI_INDEX'],
                video_reference_match: true,
              },
              full_period: {
                start_date: '2020-01-01',
                end_date: '2024-01-01',
                initial_capital: 10000,
                monthly_contribution: 0,
                benchmark: result,
                results: [result],
                leaders: {
                  overall: result,
                  prefixado: result,
                  ipca_plus: result,
                  most_consistent: {
                    study_id: 'fixed_income',
                    instrument_id: 'CDI_INDEX',
                    label: 'CDI',
                    source_kind: 'fixed_income_index',
                    family_id: 'post_fixed',
                    family_label: 'Pós-fixado',
                    duration_years: null,
                    window_years: 5,
                    window_frequency: 'yearly',
                    windows_count: 4,
                    win_rate: 0.75,
                    average_excess_return: 0.01,
                    median_excess_return: 0.01,
                    best_excess_return: 0.03,
                    worst_excess_return: -0.01,
                    best_window_start: '2020-01-01',
                    best_window_end: '2024-12-31',
                  },
                },
              },
              rolling_windows: [
                {
                  study_id: 'fixed_income',
                  instrument_id: 'CDI_INDEX',
                  label: 'CDI',
                  source_kind: 'fixed_income_index',
                  family_id: 'post_fixed',
                  family_label: 'Pós-fixado',
                  duration_years: null,
                  window_years: 5,
                  window_frequency: 'yearly',
                  windows_count: 4,
                  win_rate: 0.75,
                  average_excess_return: 0.01,
                  median_excess_return: 0.01,
                  best_excess_return: 0.03,
                  worst_excess_return: -0.01,
                  best_window_start: '2020-01-01',
                  best_window_end: '2024-12-31',
                },
              ],
              takeaways: ['CDI foi consistente nas janelas.'],
            },
          ],
          summary: {
            available_study_ids: ['fixed_income'],
            takeaways: ['A metodologia muda a leitura.'],
          },
        }}
      />
    );

    expect(screen.getByText('Backtests de renda fixa')).toBeTruthy();
    expect(screen.getByText('Renda fixa real')).toBeTruthy();
    expect(screen.getByText('Líder geral')).toBeTruthy();
    expect(screen.getByText('Janelas de 5 anos')).toBeTruthy();
  });

  it('shows investment cache readiness', () => {
    render(
      <InvestmentCacheStatusPanel
        status={{
          title: 'Cache e preparacao dos dados',
          plain_language_summary: 'Mostra preparo local.',
          status: 'warm',
          status_label: 'cache preparado',
          checked_at: '2026-04-24T00:00:00Z',
          caches: [
            {
              cache_id: 'listed_assets',
              label: 'Ativos listados',
              path: 'data/investments',
              exists: true,
              file_count: 2,
              total_size_bytes: 2048,
              latest_file_name: 'prices.parquet',
              latest_file_at: '2026-04-24T00:00:00Z',
              age_days: 0,
              freshness_status: 'fresh',
              freshness_label: 'atualizado recentemente',
              status: 'warm',
              status_label: 'com arquivos locais',
              cold_start_note: 'Pode baixar series historicas.',
              refresh_hint: 'Atualize quando for comparar janelas recentes.',
              used_in_current_result: true,
            },
          ],
          takeaways: ['Caches locais reduzem cold start.'],
        }}
      />
    );

    expect(screen.getByText('Cache e preparacao dos dados')).toBeTruthy();
    expect(screen.getByText('Ativos listados')).toBeTruthy();
    expect(screen.getByText('usado agora')).toBeTruthy();
    expect(screen.getByText('atualizado recentemente')).toBeTruthy();
    expect(screen.getByText('prices.parquet')).toBeTruthy();
    expect(screen.getByText('Leitura rápida')).toBeTruthy();
  });

  it('shows market explorer catalog facets', () => {
    render(
      <InvestmentMarketExplorerPanel
        explorer={{
          title: 'Explorador de mercado',
          plain_language_summary: 'Visao inicial do universo.',
          category_lists: [
            {
              list_id: 'fixed_income_b3',
              label: 'Renda fixa / juros na B3',
              count: 2,
              sample_instrument_ids: ['CDI_INDEX'],
              sample_labels: ['CDI'],
            },
          ],
          product_type_facets: [
            { source_kind: 'fixed_income_index', label: 'Indices de renda fixa', count: 2 },
          ],
          risk_facets: [{ facet_id: 'risk', label: 'Baixa', count: 2 }],
          region_facets: [{ facet_id: 'region', label: 'Brasil', count: 2 }],
          ranking_backlog: [{ ranking_id: 'drawdown', label: 'Quem caiu menos', status: 'planned' }],
        }}
      />
    );

    expect(screen.getByText('Explorador de mercado')).toBeTruthy();
    expect(screen.getByText('Tipos de produto')).toBeTruthy();
    expect(screen.getByText('Rankings de mercado')).toBeTruthy();
  });

  it('builds market explorer rankings on demand', async () => {
    vi.mocked(apiClient.buildInvestmentMarketRankings).mockResolvedValueOnce({
      generated_at: '2026-04-27T12:00:00Z',
      request: { preset_id: 'first_steps' },
      market_rankings: {
        title: 'Rankings de mercado',
        plain_language_summary: 'Rankings gerados.',
        universe_label: '2 alternativas',
        as_of_date: '2026-04-27',
        source_label: 'Dados locais',
        benchmark_context: [],
        rankings: [
          {
            ranking_id: 'momentum_6m',
            label: 'Momentum recente',
            metric_label: 'Retorno TWR 6m',
            metric_kind: 'percent',
            methodology: 'Ordena por momentum.',
            rows: [
              {
                rank: 1,
                instrument_id: 'PETR4',
                label: 'PETR4',
                category_label: 'Acoes',
                source_kind: 'listed_security',
                risk_label: 'Alta',
                value: 0.12,
                secondary_value: 12000,
              },
            ],
          },
        ],
        export_columns: [
          'ranking_id',
          'ranking_label',
          'rank',
          'instrument_id',
          'label',
          'category_label',
          'source_kind',
          'risk_label',
          'value',
          'secondary_value',
        ],
        methodology_notes: ['Usa o universo selecionado.'],
        generated_at: '2026-04-27T12:00:00Z',
      },
      market_screeners: {
        title: 'Screeners do universo comparado',
        plain_language_summary: 'Filtros gerados.',
        universe_count: 1,
        presets: [
          {
            preset_id: 'positive_real_return',
            label: 'Retorno real positivo',
            rule_summary: 'CAGR real maior que zero.',
            matched_count: 1,
            universe_count: 1,
            sort_key: 'real_cagr',
            rows: [
              {
                rank: 1,
                instrument_id: 'PETR4',
                label: 'PETR4',
                category_label: 'Acoes',
                real_cagr: 0.1,
                max_drawdown: -0.2,
                annual_volatility: 0.3,
                net_profit: 1000,
              },
            ],
          },
        ],
        methodology_notes: ['Cada filtro declara sua regra.'],
      },
      cache_status: {
        title: 'Cache e preparacao dos dados',
        plain_language_summary: 'Cache.',
        status: 'warm',
        status_label: 'cache preparado',
        checked_at: '2026-04-27T12:00:00Z',
        caches: [],
        takeaways: [],
      },
      warnings: [],
    });

    render(
      <InvestmentMarketExplorerPanel
        selectedPresetId="first_steps"
        explorer={{
          title: 'Explorador de mercado',
          plain_language_summary: 'Visao inicial do universo.',
          category_lists: [],
          product_type_facets: [],
          risk_facets: [],
          region_facets: [],
          ranking_backlog: [],
        }}
      />
    );

    fireEvent.click(screen.getByText('Gerar rankings'));

    await waitFor(() => {
      expect(apiClient.buildInvestmentMarketRankings).toHaveBeenCalledWith({
        preset_id: 'first_steps',
        benchmark_ids: ['selic_cash'],
      });
    });
    expect(await screen.findByText('Momentum recente')).toBeTruthy();
    expect(screen.getByText('Retorno real positivo')).toBeTruthy();
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

  it('shows portfolio contribution by sleeve and category', () => {
    render(
      <InvestmentPortfolioContributionPanel
        portfolioResults={[
          {
            instrument_id: 'CUSTOM',
            label: 'Minha carteira',
            category_id: 'custom',
            category_label: 'Carteira',
            description: 'Carteira customizada.',
            rationale: 'Teste.',
            risk_label: 'Media',
            region_label: 'Brasil',
            source_kind: 'custom_portfolio',
            invested_total: 10000,
            final_value: 12500,
            net_profit: 2500,
            total_return_on_invested: 0.25,
            time_weighted_return: 0.25,
            cagr: 0.1,
            annual_volatility: 0.08,
            max_drawdown: -0.05,
            availability_start: '2021-01-01',
            availability_end: '2024-01-01',
            invested_total_real: 9500,
            final_value_real: 11500,
            net_profit_real: 2000,
            real_total_return_on_invested: 0.2,
            real_time_weighted_return: 0.2,
            real_cagr: 0.06,
            final_value_net: 12500,
            net_profit_net: 2500,
            cagr_net: 0.1,
            final_value_real_net: 11500,
            net_profit_real_net: 2000,
            real_cagr_net: 0.06,
            component_breakdown: [
              {
                component_id: 'CDI_INDEX',
                label: 'CDI',
                category_id: 'fixed_income',
                category_label: 'Renda fixa',
                target_weight: 0.6,
                ending_weight: 0.58,
                final_value: 7000,
              },
            ],
            category_breakdown: [
              {
                label: 'Renda fixa',
                category_label: 'Renda fixa',
                target_weight: 0.6,
                ending_weight: 0.58,
                final_value: 7000,
              },
            ],
          },
        ]}
      />
    );

    expect(screen.getByText('Contribuicao por sleeve e por familia')).toBeTruthy();
    expect(screen.getByText('Minha carteira')).toBeTruthy();
    expect(screen.getByText('CDI')).toBeTruthy();
    expect(screen.getByText(/Renda fixa: alvo/)).toBeTruthy();
  });

  it('shows result warnings and data sources', () => {
    render(
      <InvestmentResultFootnotesPanel
        warnings={['Serie curta para alguns ativos.']}
        sources={[{ label: 'Banco Central do Brasil', url: 'https://www.bcb.gov.br/' }]}
      />
    );

    expect(screen.getByText('Atencoes sobre o recorte')).toBeTruthy();
    expect(screen.getByText(/Serie curta/)).toBeTruthy();
    expect(screen.getByText('Fontes e cobertura')).toBeTruthy();
    expect(screen.getByText('Banco Central do Brasil')).toBeTruthy();
  });

  it('shows the empty results state while no comparison has been run', () => {
    render(
      <InvestmentResultsPanel
        comparison={null}
        catalog={null}
        isLoadingCatalog={false}
        chartMode="nominal"
        onChartModeChange={() => undefined}
      />
    );

    expect(screen.getByText('Resultado didatico')).toBeTruthy();
    expect(screen.getByText('Escolha um objetivo, confirme os ativos e rode a comparacao.')).toBeTruthy();
  });
});
