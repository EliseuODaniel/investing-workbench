import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { useInvestmentsComparison } from './useInvestmentsComparison';

describe('useInvestmentsComparison', () => {
  it('loads the catalog and applies the default balanced preset', async () => {
    vi.mocked(apiClient.getInvestmentCatalog).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      categories: [
        { category_id: 'stocks_brazil', label: 'Acoes brasileiras', count: 1 },
        { category_id: 'fixed_income_b3', label: 'Renda fixa / juros na B3', count: 1 },
      ],
      instruments: [
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
      expect(result.current.catalog?.presets).toHaveLength(1);
    });

    expect(result.current.selectedPresetId).toBe('balanced_b3');
    expect(result.current.request.asset_ids).toEqual(['SELIC_PROXY', 'WEGE3']);
  });

  it('submits the selected assets to the comparison endpoint', async () => {
    vi.mocked(apiClient.getInvestmentCatalog).mockResolvedValueOnce({
      generated_at: '2026-04-21T12:00:00Z',
      categories: [],
      instruments: [],
      presets: [
        {
          preset_id: 'balanced_b3',
          label: 'Balanceado B3',
          description: 'desc',
          asset_ids: ['SELIC_PROXY', 'WEGE3'],
          goal_label: 'goal',
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
      })
    );
  });
});
