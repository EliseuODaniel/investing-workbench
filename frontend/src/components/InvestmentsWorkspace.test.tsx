import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import InvestmentsWorkspace from './InvestmentsWorkspace';

const { useInvestmentsComparisonMock } = vi.hoisted(() => ({
  useInvestmentsComparisonMock: vi.fn(),
}));

vi.mock('../hooks/useInvestmentsComparison', () => ({
  useInvestmentsComparison: useInvestmentsComparisonMock,
}));

function buildHookState() {
  return {
    catalog: {
      categories: [
        { category_id: 'fixed_income_b3', label: 'Renda fixa / juros na B3', count: 1 },
        { category_id: 'stocks_brazil', label: 'Ações brasileiras', count: 1 },
      ],
      instruments: [
        {
          instrument_id: 'CDI_INDEX',
          label: 'CDI / taxa extramercado (proxy)',
          category_id: 'fixed_income_b3',
          category_label: 'Renda fixa / juros na B3',
          description: 'Pós-fixado que acompanha o CDI.',
          rationale: 'Base defensiva para comparar juros reais e risco baixo.',
          risk_label: 'Baixa',
          region_label: 'Brasil',
          source_kind: 'fixed_income_index',
          listed_on_b3: false,
          uses_adjusted_close: false,
          components: [],
          notes: [],
        },
        {
          instrument_id: 'WEGE3',
          label: 'WEGE3',
          category_id: 'stocks_brazil',
          category_label: 'Ações brasileiras',
          description: 'Empresa exportadora da B3.',
          rationale: 'Volatilidade alta para comparar com renda fixa.',
          risk_label: 'Alta',
          region_label: 'Brasil',
          source_kind: 'listed_security',
          listed_on_b3: true,
          uses_adjusted_close: true,
          components: [],
          notes: [],
        },
      ],
      presets: [
        {
          preset_id: 'fixed_income_ipca_vs_cdi',
          label: 'IPCA+ vs CDI (vídeo)',
          description: 'Compara pós-fixado com IPCA+ por duration.',
          asset_ids: ['CDI_INDEX', 'WEGE3'],
          goal_label: 'Entender o que mudou entre caixa e risco real.',
          default_start_date: '2006-01-01',
          default_benchmark_ids: ['selic_cash'],
        },
      ],
      benchmark_options: [
        { benchmark_id: 'selic_cash', label: 'SELIC / caixa', description: 'Referência básica' },
      ],
      market_explorer: {
        title: 'Explorador de mercado',
        plain_language_summary: 'Visao inicial do universo disponivel.',
        category_lists: [
          {
            list_id: 'fixed_income_b3',
            label: 'Renda fixa / juros na B3',
            count: 1,
            sample_instrument_ids: ['CDI_INDEX'],
            sample_labels: ['CDI / taxa extramercado (proxy)'],
          },
        ],
        product_type_facets: [
          { source_kind: 'fixed_income_index', label: 'Indices de renda fixa', count: 1 },
        ],
        risk_facets: [{ facet_id: 'risk', label: 'Baixa', count: 1 }],
        region_facets: [{ facet_id: 'region', label: 'Brasil', count: 2 }],
        ranking_backlog: [{ ranking_id: 'drawdown', label: 'Quem caiu menos', status: 'planned' }],
      },
      notes: ['Cada estudo usa o mesmo fluxo de caixa para todos os ativos.'],
      sources: [],
    },
    comparison: null,
    request: {
      asset_ids: ['CDI_INDEX', 'WEGE3'],
      benchmark_ids: ['selic_cash'],
      start_date: '2006-01-01',
      end_date: '2026-03-31',
      initial_capital: 1000,
      monthly_contribution: 0,
    },
    selectedPreset: {
      preset_id: 'fixed_income_ipca_vs_cdi',
      label: 'IPCA+ vs CDI (vídeo)',
      description: 'Compara pós-fixado com IPCA+ por duration.',
      asset_ids: ['CDI_INDEX', 'WEGE3'],
      goal_label: 'Entender o que mudou entre caixa e risco real.',
      default_start_date: '2006-01-01',
      default_benchmark_ids: ['selic_cash'],
    },
    selectedPresetId: 'fixed_income_ipca_vs_cdi',
    isLoadingCatalog: false,
    isComparing: false,
    isCustomPortfolioEnabled: false,
    customPortfolioName: 'Minha carteira',
    customPortfolioDescription: '',
    customPortfolioWeights: {},
    customPortfolioAssets: [],
    savedPortfolios: [],
    applyPreset: vi.fn(),
    updateRequest: vi.fn(),
    toggleAsset: vi.fn(),
    toggleBenchmark: vi.fn(),
    setIsCustomPortfolioEnabled: vi.fn(),
    setCustomPortfolioName: vi.fn(),
    setCustomPortfolioDescription: vi.fn(),
    updateCustomPortfolioWeight: vi.fn(),
    saveCurrentCustomPortfolio: vi.fn(),
    applySavedPortfolio: vi.fn(),
    deleteSavedPortfolio: vi.fn(),
    compare: vi.fn(),
  };
}

describe('InvestmentsWorkspace', () => {
  it('starts in the guided flow and treats step 3 as review before customization', () => {
    useInvestmentsComparisonMock.mockReturnValue(buildHookState());

    render(<InvestmentsWorkspace onError={vi.fn()} />);

    expect(screen.getByText('1. Escolha como quer começar')).toBeTruthy();
    expect(screen.getByText('Quero um estudo pronto')).toBeTruthy();
    expect(screen.getByText('Explorador de mercado')).toBeTruthy();
    expect(screen.queryByText('Estudo ativo: IPCA+ vs CDI (vídeo)')).toBeNull();
    expect(screen.queryByText('O que está entrando agora na comparação')).toBeNull();
    expect(screen.queryByText('Volatilidade alta para comparar com renda fixa.')).toBeNull();
  });

  it('switches between setup tabs to reduce visible information', async () => {
    const user = userEvent.setup();
    useInvestmentsComparisonMock.mockReturnValue(buildHookState());

    render(<InvestmentsWorkspace onError={vi.fn()} />);

    expect(screen.getByText('1. Escolha como quer começar')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: '2. Cenário' }));

    expect(screen.queryByText('1. Escolha como quer começar')).toBeNull();
    expect(screen.getByText('2. Defina o dinheiro e o periodo')).toBeTruthy();
    expect(screen.getByText('Perfil da decisão')).toBeTruthy();
  });

  it('guides the decision profile in wizard steps', async () => {
    const user = userEvent.setup();
    useInvestmentsComparisonMock.mockReturnValue(buildHookState());

    render(<InvestmentsWorkspace onError={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: '2. Cenário' }));

    expect(screen.getByText('1. Objetivo')).toBeTruthy();
    expect(screen.queryByText('Marcação a mercado')).toBeNull();

    await user.click(screen.getByRole('button', { name: '2. Prazo e risco' }));

    expect(screen.getByText('Marcação a mercado')).toBeTruthy();
    expect(screen.getByText('Etapa 2 de 3')).toBeTruthy();
  });

  it('switches to manual mode and opens the asset editor explicitly', async () => {
    const user = userEvent.setup();
    useInvestmentsComparisonMock.mockReturnValue(buildHookState());

    render(<InvestmentsWorkspace onError={vi.fn()} />);

    const manualModeCard = screen.getByText('Quero montar manualmente').closest('button');
    expect(manualModeCard).toBeTruthy();

    await user.click(manualModeCard!);

    expect(await screen.findByText('Você está montando a comparação manualmente')).toBeTruthy();
    expect(screen.getByText('Voltar para estudos prontos')).toBeTruthy();
    expect(screen.queryByText('Volatilidade alta para comparar com renda fixa.')).toBeNull();
  });

  it('reveals the review content only on the review tab', async () => {
    const user = userEvent.setup();
    useInvestmentsComparisonMock.mockReturnValue(buildHookState());

    render(<InvestmentsWorkspace onError={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: /3\. Revisão/i }));

    expect(screen.getByText('Estudo ativo: IPCA+ vs CDI (vídeo)')).toBeTruthy();
    expect(screen.getByText('O que está entrando agora na comparação')).toBeTruthy();
    expect(screen.getByText('Quer manter o roteiro ou personalizar?')).toBeTruthy();
  });

  it('shows the results on a separate internal tab', async () => {
    const user = userEvent.setup();
    useInvestmentsComparisonMock.mockReturnValue(buildHookState());

    render(<InvestmentsWorkspace onError={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Resultado' }));

    expect(screen.getByText('Resultado em uma aba separada')).toBeTruthy();
    expect(screen.queryByText('1. Escolha como quer começar')).toBeNull();
    expect(screen.getByText('Escolha um objetivo, confirme os ativos e rode a comparacao.')).toBeTruthy();
  });
});
