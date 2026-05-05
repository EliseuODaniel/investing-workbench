import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { PairsBacktestManifestPayload, PairsBacktestResultsPayload } from '../types/api';
import { useSavedPairsRadar } from './useSavedPairsRadar';

const MANIFEST: PairsBacktestManifestPayload = {
  pairs_backtest_id: 'pairs_1',
  created_at: '2026-04-20T15:00:00Z',
  preset_id: 'ibov_proxy',
  preset_label: 'IBOV Proxy',
  start_date: '2021-01-01',
  end_date: null,
  requested_tickers: ['PETR4', 'VALE3'],
  available_tickers: ['PETR4', 'VALE3'],
  eligible_tickers: ['PETR4', 'VALE3'],
  scenario_count: 2,
  batch_mode: true,
  benchmark_ids: ['equal_weight', 'selic_cash'],
  candidate_pair_count: 5,
  reconstitution_segment_count: 0,
  warnings: [],
};

const RESULT: PairsBacktestResultsPayload = {
  pairs_backtest_id: 'pairs_1',
  created_at: '2026-04-20T15:00:00Z',
  manifest: MANIFEST,
  preset: { preset_id: 'ibov_proxy' },
  universe: { reconstitution_plan: [] },
  candidate_pairs: [],
  benchmarks: [],
  scenarios: [],
  robustness_report: {
    rankings: [],
    dispersion: {},
  },
  warnings: [],
};

describe('useSavedPairsRadar', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('saves and removes the active pairs backtest locally', () => {
    const { result } = renderHook(() => useSavedPairsRadar([MANIFEST], RESULT));

    expect(result.current.savedItems).toHaveLength(0);
    expect(result.current.isActiveSaved).toBe(false);

    act(() => {
      result.current.saveActiveBacktest();
    });

    expect(result.current.savedItems).toHaveLength(1);
    expect(result.current.savedItems[0].pairs_backtest_id).toBe('pairs_1');
    expect(result.current.savedItems[0].scenario_count).toBe(2);
    expect(result.current.isActiveSaved).toBe(true);

    act(() => {
      result.current.removeSavedBacktest('pairs_1');
    });

    expect(result.current.savedItems).toHaveLength(0);
    expect(result.current.isActiveSaved).toBe(false);
  });

  it('hydrates saved radar items from localStorage', () => {
    window.localStorage.setItem(
      'investing-workbench.saved-pairs-radar.v1',
      JSON.stringify([
        {
          pairs_backtest_id: 'pairs_2',
          label: 'IBOV Proxy · 2022-01-01',
          preset_label: 'IBOV Proxy',
          created_at: '2026-04-21T15:00:00Z',
          saved_at: '2026-04-21T16:00:00Z',
          scenario_count: 1,
          candidate_pair_count: 3,
          benchmark_ids: ['selic_cash'],
        },
      ])
    );

    const { result } = renderHook(() => useSavedPairsRadar([], null));

    expect(result.current.savedItems).toHaveLength(1);
    expect(result.current.savedItems[0].pairs_backtest_id).toBe('pairs_2');
  });
});
