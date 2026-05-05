import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { useStrategyCatalogData } from './useStrategyCatalogData';

describe('useStrategyCatalogData', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockClear();
    vi.mocked(apiClient.listSavedStrategySetupRuns).mockClear();
    vi.mocked(apiClient.listStrategySetupScores).mockClear();
  });

  it('loads catalog metadata and hydrates setup history and scores', async () => {
    const hydrateSetupRuns = vi.fn();
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockResolvedValueOnce({
      title: 'Catalogo',
      plain_language_summary: 'Resumo',
      generated_at: '2026-04-28T12:00:00Z',
      strategies: [
        {
          strategy_id: 'pairs_cointegration',
          label: 'Pairs',
          family: 'market_neutral',
          direction: 'long_short',
          required_inputs: [],
          supported_timeframes: ['daily'],
          risk_notes: [],
        },
        {
          strategy_id: 'buy_and_hold',
          label: 'Buy and hold',
          family: 'core',
          direction: 'long',
          required_inputs: [],
          supported_timeframes: ['daily'],
          risk_notes: [],
        },
      ],
      score_dimensions: [],
      radar_plan: [],
    });
    vi.mocked(apiClient.listSavedStrategySetupRuns).mockResolvedValueOnce([
      {
        strategy_id: 'pairs_cointegration',
        ran_at: '2026-04-28T12:00:00Z',
        strategy_count: 1,
        route_hint: '/pairs/backtests',
      },
    ]);
    vi.mocked(apiClient.listStrategySetupScores).mockResolvedValueOnce([
      {
        strategy_id: 'pairs_cointegration',
        label: 'Pairs',
        score: 10,
        total_return: 0.1,
        max_drawdown: -0.02,
        trade_count: 2,
        run_count: 1,
        route_hint: '/pairs/backtests',
        run_id: null,
        pairs_backtest_id: null,
        return_score: 10,
        drawdown_penalty: 1,
        execution_score: 0.5,
        robustness_score: 0.5,
        data_validity_score: 1,
        ran_at: '2026-04-28T12:00:00Z',
        methodology: 'score',
      },
    ]);

    const { result } = renderHook(() => useStrategyCatalogData({ hydrateSetupRuns }));

    await waitFor(() => {
      expect(result.current.catalog?.title).toBe('Catalogo');
    });
    expect(result.current.familyCount).toBe(2);
    expect(hydrateSetupRuns).toHaveBeenCalledWith(
      [expect.objectContaining({ strategy_id: 'pairs_cointegration' })],
      [expect.objectContaining({ strategy_id: 'pairs_cointegration' })]
    );
  });

  it('exposes a friendly catalog error message', async () => {
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockRejectedValue({
      response: { data: { detail: 'Catalogo offline' } },
    });

    const { result } = renderHook(() =>
      useStrategyCatalogData({ hydrateSetupRuns: vi.fn() })
    );

    await waitFor(() => {
      expect(result.current.error).toBe('Catalogo offline');
    });
  });
});
