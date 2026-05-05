import { describe, expect, it } from 'vitest';
import {
  buildSetupScoreInsights,
  buildSetupScores,
  buildSetupScoresCsv,
} from './strategySetupScoring';
import type { SavedStrategyRadarItemPayload, SavedStrategySetupRunPayload } from '../types/api';

describe('strategySetupScoring', () => {
  const savedItems: SavedStrategyRadarItemPayload[] = [
    {
      strategy_id: 'pairs_cointegration',
      label: 'Pairs por cointegracao',
      family: 'market_neutral',
      direction: 'long_short',
    },
    {
      strategy_id: 'buy_and_hold',
      label: 'Buy and hold',
      family: 'benchmark',
      direction: 'long',
    },
  ];

  const history: SavedStrategySetupRunPayload[] = [
    {
      strategy_id: 'pairs_cointegration',
      pairs_backtest_id: 'pairs_123',
      ran_at: '2026-04-28T12:01:00Z',
      strategy_count: 1,
      best_strategy: 'Realistic cointegration',
      total_return: 0.12,
      max_drawdown: -0.04,
      trade_count: 3,
      route_hint: '/pairs/backtests',
    },
    {
      strategy_id: 'pairs_cointegration',
      pairs_backtest_id: 'pairs_122',
      ran_at: '2026-04-27T12:01:00Z',
      strategy_count: 1,
      total_return: 0.08,
      max_drawdown: -0.03,
      trade_count: 2,
      route_hint: '/pairs/backtests',
    },
    {
      strategy_id: 'buy_and_hold',
      run_id: 'run_123',
      ran_at: '2026-04-28T12:00:00Z',
      strategy_count: 1,
      total_return: 0.1,
      max_drawdown: -0.05,
      trade_count: 0,
      route_hint: '/backtest',
    },
  ];

  it('builds explainable setup scores with component values', () => {
    const scores = buildSetupScores(savedItems, history);

    expect(scores[0]).toMatchObject({
      strategy_id: 'pairs_cointegration',
      score: 13.75,
      return_score: 12,
      drawdown_penalty: 2,
      execution_score: 0.75,
      robustness_score: 1,
      data_validity_score: 2,
      run_count: 2,
      pairs_backtest_id: 'pairs_123',
    });
    expect(scores[1]).toMatchObject({
      strategy_id: 'buy_and_hold',
      score: 10,
      run_count: 1,
      run_id: 'run_123',
    });
  });

  it('builds quick comparison insights', () => {
    const insights = buildSetupScoreInsights(buildSetupScores(savedItems, history));

    expect(insights.map((insight) => insight.label)).toEqual([
      'Melhor score',
      'Maior retorno',
      'Menor drawdown',
      'Mais evidencia',
    ]);
    expect(insights[0].setup_label).toBe('Pairs por cointegracao');
    expect(insights[3].value_label).toBe('2 run(s) · 3 trade(s)');
  });

  it('exports setup scores as csv', () => {
    const csv = buildSetupScoresCsv(buildSetupScores(savedItems, history));

    expect(csv).toContain('rank,strategy_id,label,score');
    expect(csv).toContain('pairs_cointegration');
    expect(csv).toContain('pairs_123');
    expect(csv).toContain('"score = retorno_total');
  });
});
