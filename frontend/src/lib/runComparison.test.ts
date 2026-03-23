import { describe, expect, it } from 'vitest';
import { summarizeComparisonRun } from './runComparison';
import { ComparisonRun } from '../types/api';

const comparisonRun: ComparisonRun = {
  summary: {
    run_id: 'run_123',
    created_at: '2026-03-23T12:00:00Z',
    config_path: 'configs/test.yaml',
    artifact_dir: 'runs/run_123',
    strategy_names: ['A', 'B'],
    benchmark_names: [],
    request_payload: {},
    data_info: {},
    config_snapshot_path: 'runs/run_123/config_resolved.json',
    data_profile_path: 'runs/run_123/data_profile.json',
    data_fingerprint: 'abc123def456',
  },
  response: {
    results: {
      A: {
        strategy_name: 'A',
        equity: [],
        trades: [{ timestamp: '2026-03-23T12:00:00Z', action: 'BUY', price: 1, quantity: 1, layer: 1 }],
        metrics: {
          total_return: 0.1,
          cagr: 0.1,
          sharpe_ratio: 1.2,
          sortino_ratio: 1.1,
          max_drawdown: -0.2,
          hit_rate: 0.5,
          profit_factor: 1.4,
          total_trades: 1,
          avg_trade_pnl: 0,
          volatility: 0.2,
          total_interest_earned: 0,
        },
        start_price: 1,
        end_price: 1.1,
      },
      B: {
        strategy_name: 'B',
        equity: [],
        trades: [],
        metrics: {
          total_return: 0.2,
          cagr: 0.2,
          sharpe_ratio: 1.5,
          sortino_ratio: 1.3,
          max_drawdown: -0.1,
          hit_rate: 0.6,
          profit_factor: 2.1,
          total_trades: 0,
          avg_trade_pnl: 0,
          volatility: 0.15,
          total_interest_earned: 0,
        },
        start_price: 1,
        end_price: 1.2,
      },
    },
    buy_hold_equity: [],
    data_info: {
      start_date: '2026-01-01T00:00:00Z',
      end_date: '2026-03-01T00:00:00Z',
      total_days: 60,
      initial_price: 1,
      final_price: 1.2,
    },
  },
};

describe('runComparison', () => {
  it('summarizes a run using the best strategy and total trades', () => {
    const summary = summarizeComparisonRun(comparisonRun);

    expect(summary.runId).toBe('run_123');
    expect(summary.bestStrategyName).toBe('B');
    expect(summary.bestReturn).toBe(0.2);
    expect(summary.totalTrades).toBe(1);
    expect(summary.dataFingerprint).toBe('abc123def456');
  });
});
