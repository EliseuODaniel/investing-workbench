import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  buildPairsDraftFromPlan,
  buildPairsRunHistoryItem,
  buildRunHistoryItem,
  mergeSetupRunHistory,
  readSetupRunHistory,
  SETUP_RUN_HISTORY_STORAGE_KEY,
  writeSetupRunHistory,
} from './strategySetupHistory';
import type {
  BacktestResponse,
  PairsBacktestResultsPayload,
  StrategySetupPlanPayload,
} from '../types/api';

describe('strategySetupHistory', () => {
  afterEach(() => {
    vi.useRealTimers();
    window.localStorage.clear();
  });

  it('builds a core backtest history item from the best strategy result', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-04-28T12:00:00Z'));

    const item = buildRunHistoryItem(
      {
        strategy_id: 'momentum_breakout',
        route_hint: '/backtest',
      } as StrategySetupPlanPayload,
      ({
        run_info: { run_id: 'run_123' },
        results: {
          slow: {
            metrics: {
              total_return: 0.08,
              max_drawdown: -0.05,
              total_trades: 3,
            },
          },
          fast: {
            metrics: {
              total_return: 0.14,
              max_drawdown: -0.08,
              total_trades: 9,
            },
          },
        },
      } as unknown) as BacktestResponse
    );

    expect(item).toMatchObject({
      strategy_id: 'momentum_breakout',
      run_id: 'run_123',
      ran_at: '2026-04-28T12:00:00.000Z',
      strategy_count: 2,
      best_strategy: 'fast',
      total_return: 0.14,
      max_drawdown: -0.08,
      trade_count: 9,
      route_hint: '/backtest',
    });
  });

  it('builds a pairs history item from the top-return scenario', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-04-28T12:00:00Z'));

    const item = buildPairsRunHistoryItem(
      {
        strategy_id: 'pairs_cointegration',
        route_hint: '/pairs/backtests',
      } as StrategySetupPlanPayload,
      {
        pairs_backtest_id: 'pairs_123',
        scenarios: [
          {
            scenario_id: 'base',
            label: 'Base',
            metrics: { return_total: 0.04, max_drawdown: -0.03, trade_count: 2 },
          },
          {
            scenario_id: 'aggressive',
            label: 'Agressivo',
            metrics: { return_total: 0.11, max_drawdown: -0.07, trade_count: 6 },
          },
        ],
      } as PairsBacktestResultsPayload
    );

    expect(item).toMatchObject({
      strategy_id: 'pairs_cointegration',
      pairs_backtest_id: 'pairs_123',
      best_strategy: 'Agressivo',
      total_return: 0.11,
      max_drawdown: -0.07,
      trade_count: 6,
      route_hint: '/pairs/backtests',
    });
  });

  it('merges local and remote history by persistent execution id', () => {
    const merged = mergeSetupRunHistory(
      [
        {
          strategy_id: 'setup_a',
          run_id: 'run_1',
          ran_at: '2026-04-28T12:00:00Z',
          strategy_count: 1,
          route_hint: '/backtest',
          total_return: 0.15,
        },
      ],
      [
        {
          strategy_id: 'setup_a',
          run_id: 'run_1',
          ran_at: '2026-04-27T12:00:00Z',
          strategy_count: 1,
          route_hint: '/backtest',
          total_return: 0.10,
        },
        {
          strategy_id: 'setup_b',
          pairs_backtest_id: 'pairs_1',
          ran_at: '2026-04-26T12:00:00Z',
          strategy_count: 2,
          route_hint: '/pairs/backtests',
        },
      ]
    );

    expect(merged).toHaveLength(2);
    expect(merged[0]).toMatchObject({ strategy_id: 'setup_a', total_return: 0.15 });
    expect(merged[1]).toMatchObject({ strategy_id: 'setup_b' });
  });

  it('persists only valid history items in browser storage', () => {
    writeSetupRunHistory([
      {
        strategy_id: 'setup_a',
        ran_at: '2026-04-28T12:00:00Z',
        strategy_count: 1,
        route_hint: '/backtest',
      },
    ]);
    const raw = window.localStorage.getItem(SETUP_RUN_HISTORY_STORAGE_KEY);
    window.localStorage.setItem(
      SETUP_RUN_HISTORY_STORAGE_KEY,
      JSON.stringify([...(raw ? JSON.parse(raw) : []), { strategy_id: 'broken' }])
    );

    expect(readSetupRunHistory()).toEqual([
      {
        strategy_id: 'setup_a',
        ran_at: '2026-04-28T12:00:00Z',
        strategy_count: 1,
        route_hint: '/backtest',
      },
    ]);
  });

  it('builds a Pairs draft from a prepared setup plan', () => {
    const draft = buildPairsDraftFromPlan(({
      run_request: {
        preset_id: 'custom',
        tickers: ['PETR4', 'VALE3'],
        formation_window: 126,
        entry_zscore: 1.8,
        exit_zscore: 0.4,
        stop_zscore: 3.2,
      },
    } as unknown) as StrategySetupPlanPayload);

    expect(draft).toEqual({
      presetId: 'custom',
      tickersText: 'PETR4, VALE3',
      formationWindowText: '126',
      entryZscoreText: '1.8',
      exitZscoreText: '0.4',
      stopZscoreText: '3.2',
    });
  });
});
