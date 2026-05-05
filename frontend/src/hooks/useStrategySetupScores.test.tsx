import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type {
  SavedStrategyRadarItemPayload,
  SavedStrategySetupRunPayload,
  StrategySetupScorePayload,
} from '../types/api';
import { useStrategySetupScores } from './useStrategySetupScores';

const savedItems: SavedStrategyRadarItemPayload[] = [
  {
    strategy_id: 'pairs_cointegration',
    label: 'Pairs por cointegracao',
    family: 'market_neutral',
    direction: 'long_short',
  },
];

const setupRunHistory: SavedStrategySetupRunPayload[] = [
  {
    strategy_id: 'pairs_cointegration',
    pairs_backtest_id: 'pairs_123',
    ran_at: '2026-04-28T12:01:00Z',
    strategy_count: 1,
    total_return: 0.12,
    max_drawdown: -0.04,
    trade_count: 3,
    route_hint: '/pairs/backtests',
  },
];

const remoteScore: StrategySetupScorePayload = {
  strategy_id: 'remote_setup',
  label: 'Remote setup',
  score: 99,
  total_return: 0.5,
  max_drawdown: -0.01,
  trade_count: 10,
  run_count: 2,
  route_hint: '/backtest',
  run_id: 'run_remote',
  pairs_backtest_id: null,
  return_score: 50,
  drawdown_penalty: 0.5,
  execution_score: 2.5,
  robustness_score: 1,
  data_validity_score: 2,
  ran_at: '2026-04-28T12:02:00Z',
  methodology: 'remote score',
};

describe('useStrategySetupScores', () => {
  it('uses remote scores before local fallback scores', () => {
    const { result } = renderHook(() =>
      useStrategySetupScores({
        savedItems,
        setupRunHistory,
        remoteSetupScores: [remoteScore],
      })
    );

    expect(result.current.setupScores).toEqual([remoteScore]);
    expect(result.current.setupScoreInsights[0].setup_label).toBe('Remote setup');
  });

  it('builds local fallback scores when remote scores are empty', () => {
    const { result } = renderHook(() =>
      useStrategySetupScores({
        savedItems,
        setupRunHistory,
        remoteSetupScores: [],
      })
    );

    expect(result.current.setupScores[0]).toMatchObject({
      strategy_id: 'pairs_cointegration',
      score: 13.25,
    });
    expect(result.current.setupScoreInsights[0].setup_label).toBe(
      'Pairs por cointegracao'
    );
  });
});
