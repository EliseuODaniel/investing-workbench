import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { usePairsTrading } from './usePairsTrading';

describe('usePairsTrading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    vi.mocked(apiClient.listPairsUniverses).mockResolvedValue([
      {
        preset_id: 'ibov_proxy',
        label: 'IBOV Proxy',
        description: 'Proxy',
        universe_kind: 'b3_ibov_proxy',
        history_mode: 'curated_proxy',
        benchmark_tickers: ['BOVA11.SA'],
        tickers: ['PETR4', 'VALE3'],
        ticker_count: 2,
      },
    ]);
    vi.mocked(apiClient.listPairsBacktests).mockResolvedValue([]);
  });

  it('loads presets and persisted backtests on mount', async () => {
    const onError = vi.fn();
    const { result } = renderHook(() => usePairsTrading(onError));

    await waitFor(() => {
      expect(result.current.isLoadingPresets).toBe(false);
      expect(result.current.isLoadingBacktests).toBe(false);
    });

    expect(apiClient.listPairsUniverses).toHaveBeenCalledTimes(1);
    expect(apiClient.listPairsBacktests).toHaveBeenCalledTimes(1);
    expect(result.current.presets[0].preset_id).toBe('ibov_proxy');
  });

  it('hydrates a draft from a strategy setup handoff', async () => {
    window.localStorage.setItem(
      'investing-workbench.pairs-setup-handoff.v1',
      JSON.stringify({
        source: 'strategy_setup_radar',
        strategy_id: 'pairs_cointegration',
        label: 'Pairs por cointegracao',
        created_at: '2026-04-27T12:00:00Z',
        draft: {
          presetId: 'custom',
          tickersText: 'PETR4, VALE3',
          formationWindowText: '126',
          entryZscoreText: '1.8',
          exitZscoreText: '0.4',
        },
      })
    );

    const { result } = renderHook(() => usePairsTrading(vi.fn()));

    expect(result.current.draft.presetId).toBe('custom');
    expect(result.current.draft.tickersText).toBe('PETR4, VALE3');
    expect(result.current.draft.formationWindowText).toBe('126');
    expect(result.current.draft.entryZscoreText).toBe('1.8');
  });

  it('runs a pairs batch and refreshes persisted history', async () => {
    const onError = vi.fn();
    vi.mocked(apiClient.runPairsBatchBacktest).mockResolvedValue({
      pairs_backtest_id: 'pairs_1',
      created_at: '2026-04-20T15:00:00Z',
      manifest: { pairs_backtest_id: 'pairs_1' },
      preset: { preset_id: 'ibov_proxy' },
      universe: {
        reconstitution_plan: [],
      },
      candidate_pairs: [],
      benchmarks: [],
      scenarios: [
        {
          scenario_id: 'realistic_cointegration',
          label: 'Realistic cointegration',
          metrics: {
            return_total: 0.12,
            sharpe: 1.1,
            max_drawdown: -0.08,
            trade_count: 12,
          },
          portfolio_summary: {
            construction: 'equal_notional',
          },
          quality_summary: {
            trade_count: 12,
          },
        },
      ],
      robustness_report: {
        rankings: [],
        dispersion: {},
      },
      warnings: [],
    });
    vi.mocked(apiClient.listPairsBacktests)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          pairs_backtest_id: 'pairs_1',
          created_at: '2026-04-20T15:00:00Z',
          preset_id: 'ibov_proxy',
          preset_label: 'IBOV Proxy',
          start_date: '2021-01-01',
          end_date: null,
          requested_tickers: ['PETR4', 'VALE3'],
          available_tickers: ['PETR4', 'VALE3'],
          eligible_tickers: ['PETR4', 'VALE3'],
          scenario_count: 1,
          batch_mode: true,
          benchmark_ids: ['equal_weight'],
          candidate_pair_count: 1,
          reconstitution_segment_count: 0,
          warnings: [],
        },
      ]);

    const { result } = renderHook(() => usePairsTrading(onError));

    await waitFor(() => {
      expect(result.current.isLoadingPresets).toBe(false);
    });

    await act(async () => {
      await result.current.runBatch();
    });

    expect(apiClient.runPairsBatchBacktest).toHaveBeenCalledTimes(1);
    expect(result.current.latestBacktest?.pairs_backtest_id).toBe('pairs_1');
    expect(result.current.backtests[0].pairs_backtest_id).toBe('pairs_1');
    expect(onError).toHaveBeenLastCalledWith(null);
  });

  it('falls back to local presets when backend presets are unavailable', async () => {
    vi.mocked(apiClient.listPairsUniverses).mockRejectedValue({
      response: { data: { detail: 'temporariamente fora' } },
    });
    const onError = vi.fn();
    const { result } = renderHook(() => usePairsTrading(onError));

    await waitFor(() => {
      expect(result.current.isLoadingPresets).toBe(false);
    });

    expect(result.current.presets[0].preset_id).toBe('ibov_proxy');
    expect(result.current.presets[0].label).toBe('IBOV Proxy');
    expect(onError).not.toHaveBeenCalledWith(
      'temporariamente fora (fallback local aplicado)'
    );
    expect(result.current.presetsSource).toBe('fallback');
    expect(result.current.presetsLoadError).toContain('temporariamente fora');
  });
});
