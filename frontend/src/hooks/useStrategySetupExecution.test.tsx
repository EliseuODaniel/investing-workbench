import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { SETUP_RUN_HISTORY_STORAGE_KEY } from '../lib/strategySetupHistory';
import type { StrategySetupPlanPayload } from '../types/api';
import { useStrategySetupExecution } from './useStrategySetupExecution';

describe('useStrategySetupExecution', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(apiClient.buildStrategySetupPlan).mockClear();
    vi.mocked(apiClient.saveStrategySetupRun).mockClear();
    vi.mocked(apiClient.listStrategySetupScores).mockClear();
  });

  it('hydrates setup history and remote scores while preserving local fallback entries', () => {
    window.localStorage.setItem(
      SETUP_RUN_HISTORY_STORAGE_KEY,
      JSON.stringify([
        {
          strategy_id: 'local_setup',
          run_id: 'run_local',
          ran_at: '2026-04-27T12:00:00Z',
          strategy_count: 1,
          route_hint: '/backtest',
        },
      ])
    );
    const { result } = renderHook(() => useStrategySetupExecution());

    act(() => {
      result.current.hydrateSetupRuns(
        [
          {
            strategy_id: 'remote_setup',
            pairs_backtest_id: 'pairs_1',
            ran_at: '2026-04-28T12:00:00Z',
            strategy_count: 2,
            route_hint: '/pairs/backtests',
          },
        ],
        [
          {
            strategy_id: 'remote_setup',
            label: 'Remote',
            score: 10,
            total_return: 0.1,
            max_drawdown: -0.02,
            trade_count: 2,
            run_count: 1,
            route_hint: '/pairs/backtests',
            run_id: null,
            pairs_backtest_id: 'pairs_1',
            return_score: 10,
            drawdown_penalty: 1,
            execution_score: 0.5,
            robustness_score: 0.5,
            data_validity_score: 2,
            ran_at: '2026-04-28T12:00:00Z',
            methodology: 'score',
          },
        ]
      );
    });

    expect(result.current.setupRunHistory.map((item) => item.strategy_id)).toEqual([
      'remote_setup',
      'local_setup',
    ]);
    expect(result.current.remoteSetupScores[0].strategy_id).toBe('remote_setup');
    expect(window.localStorage.getItem(SETUP_RUN_HISTORY_STORAGE_KEY)).toContain(
      'remote_setup'
    );
  });

  it('prepares a setup plan and reports unsupported execution routes', async () => {
    const { result } = renderHook(() => useStrategySetupExecution());

    await act(async () => {
      await result.current.prepareSetupPlan({
        strategy_id: 'custom_lab',
        label: 'Custom lab',
        family: 'research',
        direction: 'long',
      });
    });

    expect(apiClient.buildStrategySetupPlan).toHaveBeenCalledWith(
      expect.objectContaining({ strategy_id: 'custom_lab' })
    );
    expect(result.current.setupPlans.custom_lab).toBeTruthy();

    await act(async () => {
      await result.current.runPreparedSetup({
        strategy_id: 'custom_lab',
        route_hint: '/advanced-only',
      } as StrategySetupPlanPayload);
    });

    expect(result.current.setupRunErrors.custom_lab).toContain('laboratorio avancado');
  });

  it('dispatches a Pairs handoff event from a prepared setup plan', async () => {
    const { result } = renderHook(() => useStrategySetupExecution());
    const navigationListener = vi.fn();
    window.addEventListener('investing-workbench:navigate-advanced-tool', navigationListener);

    act(() => {
      result.current.sendPairsHandoff(({
        strategy_id: 'pairs_cointegration',
        label: 'Pairs',
        run_request: {
          preset_id: 'custom',
          tickers: ['PETR4', 'VALE3'],
          formation_window: 126,
        },
      } as unknown) as StrategySetupPlanPayload);
    });

    await waitFor(() => {
      expect(result.current.handoffMessages.pairs_cointegration).toContain(
        'laboratorio de Pairs'
      );
    });
    expect(window.localStorage.getItem('investing-workbench.pairs-setup-handoff.v1')).toContain(
      'PETR4, VALE3'
    );
    expect(navigationListener).toHaveBeenCalledTimes(1);
    window.removeEventListener('investing-workbench:navigate-advanced-tool', navigationListener);
  });
});
