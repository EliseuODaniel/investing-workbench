import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { useInvestmentsComparison } from './useInvestmentsComparison';

describe('useInvestmentsComparison', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
  });

  it('loads the catalog and applies the guided video preset when available', async () => {
    vi.mocked(apiClient.getInvestmentCatalog).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      categories: [
        { category_id: 'stocks_brazil', label: 'Acoes brasileiras', count: 1 },
        { category_id: 'fixed_income_b3', label: 'Renda fixa / juros na B3', count: 1 },
        { category_id: 'guided_portfolios', label: 'Carteiras guiadas', count: 1 },
      ],
      instruments: [
        {
          instrument_id: 'SARDINHA40_ORIGINAL',
          label: 'Carteira 40+ (video original)',
          category_id: 'guided_portfolios',
          category_label: 'Carteiras guiadas',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Media',
          region_label: 'Brasil + exterior',
          source_kind: 'model_portfolio',
          listed_on_b3: false,
          uses_adjusted_close: true,
          rebalance_frequency: 'monthly',
          implementation_note: 'note',
          components: [{ component_id: 'SELIC_PROXY', weight: 0.15 }],
          notes: [],
        },
        {
          instrument_id: 'WEGE3',
          label: 'WEGE3',
          category_id: 'stocks_brazil',
          category_label: 'Acoes brasileiras',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Alta',
          region_label: 'Brasil',
          source_kind: 'listed_security',
          listed_on_b3: true,
          uses_adjusted_close: true,
          components: [],
          notes: [],
        },
        {
          instrument_id: 'SELIC_PROXY',
          label: 'Tesouro Selic (proxy)',
          category_id: 'fixed_income_b3',
          category_label: 'Renda fixa / juros na B3',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Baixa',
          region_label: 'Brasil',
          source_kind: 'selic_proxy',
          listed_on_b3: false,
          uses_adjusted_close: false,
          components: [],
          notes: [],
        },
      ],
      presets: [
        {
          preset_id: 'sardinha_40_plus',
          label: 'Carteira 40+ (video)',
          description: 'desc',
          asset_ids: ['SARDINHA40_ORIGINAL', 'SELIC_PROXY'],
          goal_label: 'goal',
          default_benchmark_ids: null,
        },
        {
          preset_id: 'balanced_b3',
          label: 'Balanceado B3',
          description: 'desc',
          asset_ids: ['SELIC_PROXY', 'WEGE3'],
          goal_label: 'goal',
          default_benchmark_ids: null,
        },
      ],
      benchmark_options: [
        { benchmark_id: 'selic_cash', label: 'SELIC / caixa', description: 'desc' },
      ],
      notes: [],
      sources: [],
    } as any);

    const onError = vi.fn();
    const { result } = renderHook(() => useInvestmentsComparison(onError));

    await waitFor(() => {
      expect(result.current.catalog?.presets).toHaveLength(2);
    });

    expect(result.current.selectedPresetId).toBe('sardinha_40_plus');
    expect(result.current.request.asset_ids).toEqual(['SARDINHA40_ORIGINAL', 'SELIC_PROXY']);
  });

  it('applies preset request defaults for the fixed-income video scenario', async () => {
    vi.mocked(apiClient.getInvestmentCatalog).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      categories: [],
      instruments: [
        {
          instrument_id: 'CDI_INDEX',
          label: 'CDI',
          category_id: 'fixed_income_b3',
          category_label: 'Renda fixa / juros na B3',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Baixa',
          region_label: 'Brasil',
          source_kind: 'fixed_income_index',
          listed_on_b3: false,
          uses_adjusted_close: false,
          components: [],
          notes: [],
        },
        {
          instrument_id: 'IDKA_IPCA_2A',
          label: 'IDkA IPCA 2A',
          category_id: 'fixed_income_b3',
          category_label: 'Renda fixa / juros na B3',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Media',
          region_label: 'Brasil',
          source_kind: 'fixed_income_index',
          listed_on_b3: false,
          uses_adjusted_close: false,
          components: [],
          notes: [],
        },
      ],
      presets: [
        {
          preset_id: 'fixed_income_ipca_vs_cdi',
          label: 'IPCA+ vs CDI (video)',
          description: 'desc',
          asset_ids: ['CDI_INDEX', 'IDKA_IPCA_2A'],
          goal_label: 'goal',
          default_start_date: '2005-12-30',
          default_end_date: '2026-03-31',
          default_initial_capital: 1000,
          default_monthly_contribution: 0,
          default_benchmark_ids: [],
          default_fixed_income_study_mode: 'index_duration',
          default_fixed_income_tax_treatment: 'gross',
          default_fixed_income_window_frequency: 'monthly',
        },
      ],
      benchmark_options: [],
      notes: [],
      sources: [],
    } as any);

    const onError = vi.fn();
    const { result } = renderHook(() => useInvestmentsComparison(onError));

    await waitFor(() => {
      expect(result.current.selectedPresetId).toBe('fixed_income_ipca_vs_cdi');
    });

    expect(result.current.request.start_date).toBe('2005-12-30');
    expect(result.current.request.end_date).toBe('2026-03-31');
    expect(result.current.request.initial_capital).toBe(1000);
    expect(result.current.request.monthly_contribution).toBe(0);
    expect(result.current.request.fixed_income_study_mode).toBe('index_duration');
    expect(result.current.request.fixed_income_tax_treatment).toBe('gross');
    expect(result.current.request.fixed_income_window_frequency).toBe('monthly');
  });

  it('submits the selected assets to the comparison endpoint', async () => {
    vi.mocked(apiClient.getInvestmentCatalog).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      categories: [],
      instruments: [
        {
          instrument_id: 'SELIC_PROXY',
          label: 'Tesouro Selic (proxy)',
          category_id: 'fixed_income_b3',
          category_label: 'Renda fixa / juros na B3',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Baixa',
          region_label: 'Brasil',
          source_kind: 'selic_proxy',
          listed_on_b3: false,
          uses_adjusted_close: false,
          components: [],
          notes: [],
        },
        {
          instrument_id: 'WEGE3',
          label: 'WEGE3',
          category_id: 'stocks_brazil',
          category_label: 'Acoes brasileiras',
          description: 'desc',
          rationale: 'why',
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
          preset_id: 'sardinha_40_plus',
          label: 'Carteira 40+ (video)',
          description: 'desc',
          asset_ids: ['SELIC_PROXY', 'WEGE3'],
          goal_label: 'goal',
          default_benchmark_ids: null,
        },
        {
          preset_id: 'balanced_b3',
          label: 'Balanceado B3',
          description: 'desc',
          asset_ids: ['SELIC_PROXY', 'WEGE3'],
          goal_label: 'goal',
          default_benchmark_ids: null,
        },
      ],
      benchmark_options: [
        { benchmark_id: 'selic_cash', label: 'SELIC / caixa', description: 'desc' },
      ],
      notes: [],
      sources: [],
    } as any);
    vi.mocked(apiClient.compareInvestments).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      request: {},
      catalog_snapshot: {},
      assumptions: [],
      results: [],
      benchmarks: [],
      chart: { reference_series_id: 'selic_cash', series: [], points: [] },
      real_chart: { reference_series_id: 'selic_cash', series: [], points: [] },
      inflation: {
        label: 'IPCA acumulado',
        accumulated_rate: 0.12,
        purchasing_power_loss: 0.1,
        availability_start: '2021-01-01',
        availability_end: '2026-04-21',
        source_label: 'BCB',
      },
      class_summary: [],
      highlights: {},
      warnings: [],
    } as any);

    const onError = vi.fn();
    const { result } = renderHook(() => useInvestmentsComparison(onError));

    await waitFor(() => {
      expect(result.current.request.asset_ids).toEqual(['SELIC_PROXY', 'WEGE3']);
    });

    await act(async () => {
      await result.current.compare();
    });

    expect(apiClient.compareInvestments).toHaveBeenCalledWith(
      expect.objectContaining({
        asset_ids: ['SELIC_PROXY', 'WEGE3'],
        benchmark_ids: ['selic_cash', 'bova11'],
        fixed_income_study_mode: 'auto',
        fixed_income_tax_treatment: 'gross',
        fixed_income_window_frequency: 'monthly',
        custom_portfolios: [],
      })
    );
  });

  it('includes a custom portfolio when the user enables it with two sleeves', async () => {
    vi.mocked(apiClient.getInvestmentCatalog).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      categories: [],
      instruments: [
        {
          instrument_id: 'SELIC_PROXY',
          label: 'Tesouro Selic (proxy)',
          category_id: 'fixed_income_b3',
          category_label: 'Renda fixa / juros na B3',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Baixa',
          region_label: 'Brasil',
          source_kind: 'selic_proxy',
          listed_on_b3: false,
          uses_adjusted_close: false,
          components: [],
          notes: [],
        },
        {
          instrument_id: 'WEGE3',
          label: 'WEGE3',
          category_id: 'stocks_brazil',
          category_label: 'Acoes brasileiras',
          description: 'desc',
          rationale: 'why',
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
          preset_id: 'balanced_b3',
          label: 'Balanceado B3',
          description: 'desc',
          asset_ids: ['SELIC_PROXY', 'WEGE3'],
          goal_label: 'goal',
          default_benchmark_ids: [],
        },
      ],
      benchmark_options: [
        { benchmark_id: 'selic_cash', label: 'SELIC / caixa', description: 'desc' },
      ],
      notes: [],
      sources: [],
    } as any);
    vi.mocked(apiClient.compareInvestments).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      request: {},
      catalog_snapshot: {},
      assumptions: [],
      results: [],
      benchmarks: [],
      chart: { reference_series_id: 'selic_cash', series: [], points: [] },
      real_chart: { reference_series_id: 'selic_cash', series: [], points: [] },
      inflation: {
        label: 'IPCA acumulado',
        accumulated_rate: 0.12,
        purchasing_power_loss: 0.1,
        availability_start: '2021-01-01',
        availability_end: '2026-04-21',
        source_label: 'BCB',
      },
      class_summary: [],
      highlights: {},
      warnings: [],
    } as any);

    const onError = vi.fn();
    const { result } = renderHook(() => useInvestmentsComparison(onError));

    await waitFor(() => {
      expect(result.current.request.asset_ids).toEqual(['SELIC_PROXY', 'WEGE3']);
    });

    act(() => {
      result.current.setIsCustomPortfolioEnabled(true);
      result.current.setCustomPortfolioName('Minha carteira');
      result.current.updateCustomPortfolioWeight('SELIC_PROXY', 60);
      result.current.updateCustomPortfolioWeight('WEGE3', 40);
    });

    await act(async () => {
      await result.current.compare();
    });

    expect(apiClient.compareInvestments).toHaveBeenCalledWith(
      expect.objectContaining({
        custom_portfolios: [
          expect.objectContaining({
            label: 'Minha carteira',
            components: [
              { component_id: 'SELIC_PROXY', weight: 60 },
              { component_id: 'WEGE3', weight: 40 },
            ],
          }),
        ],
      })
    );
  });

  it('saves and reapplies reusable custom portfolios locally', async () => {
    vi.mocked(apiClient.getInvestmentCatalog).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      categories: [],
      instruments: [
        {
          instrument_id: 'SELIC_PROXY',
          label: 'Tesouro Selic (proxy)',
          category_id: 'fixed_income_b3',
          category_label: 'Renda fixa / juros na B3',
          description: 'desc',
          rationale: 'why',
          risk_label: 'Baixa',
          region_label: 'Brasil',
          source_kind: 'selic_proxy',
          listed_on_b3: false,
          uses_adjusted_close: false,
          components: [],
          notes: [],
        },
        {
          instrument_id: 'WEGE3',
          label: 'WEGE3',
          category_id: 'stocks_brazil',
          category_label: 'Acoes brasileiras',
          description: 'desc',
          rationale: 'why',
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
          preset_id: 'balanced_b3',
          label: 'Balanceado B3',
          description: 'desc',
          asset_ids: ['SELIC_PROXY', 'WEGE3'],
          goal_label: 'goal',
          default_benchmark_ids: [],
        },
      ],
      benchmark_options: [
        { benchmark_id: 'selic_cash', label: 'SELIC / caixa', description: 'desc' },
      ],
      notes: [],
      sources: [],
    } as any);

    const onError = vi.fn();
    const { result } = renderHook(() => useInvestmentsComparison(onError));

    await waitFor(() => {
      expect(result.current.request.asset_ids).toEqual(['SELIC_PROXY', 'WEGE3']);
    });

    act(() => {
      result.current.setIsCustomPortfolioEnabled(true);
      result.current.setCustomPortfolioName('Carteira renda e crescimento');
      result.current.updateCustomPortfolioWeight('SELIC_PROXY', 70);
      result.current.updateCustomPortfolioWeight('WEGE3', 30);
    });

    await act(async () => {
      await result.current.saveCurrentCustomPortfolio();
    });

    expect(result.current.savedPortfolios[0].label).toBe('Carteira renda e crescimento');
    expect(result.current.savedPortfolios[0].components).toEqual([
      { component_id: 'SELIC_PROXY', weight: 70 },
      { component_id: 'WEGE3', weight: 30 },
    ]);

    act(() => {
      result.current.updateCustomPortfolioWeight('SELIC_PROXY', 10);
      result.current.applySavedPortfolio(result.current.savedPortfolios[0]);
    });

    expect(result.current.isCustomPortfolioEnabled).toBe(true);
    expect(result.current.request.asset_ids).toEqual(['SELIC_PROXY', 'WEGE3']);
    expect(result.current.customPortfolioWeights).toMatchObject({
      SELIC_PROXY: 70,
      WEGE3: 30,
    });

    await act(async () => {
      await result.current.deleteSavedPortfolio(result.current.savedPortfolios[0].portfolio_id);
    });

    expect(result.current.savedPortfolios).toEqual([]);
  });
});
