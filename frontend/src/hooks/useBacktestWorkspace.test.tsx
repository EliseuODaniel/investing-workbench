import { describe, expect, it } from 'vitest';
import {
  deriveSuccessfulWorkspaceState,
  deriveVisibleBenchmarks,
  deriveVisibleStrategies,
} from './backtestWorkspaceState';

const response = {
  results: {
    'Simple Martingale': {
      strategy_name: 'Simple Martingale',
      equity: [],
      trades: [],
      metrics: {
        total_return: 0.12,
        cagr: 0.12,
        sharpe_ratio: 1.2,
        sortino_ratio: 1.5,
        max_drawdown: -0.08,
        hit_rate: 0.6,
        profit_factor: 1.4,
        total_trades: 0,
        avg_trade_pnl: 0,
        volatility: 0.2,
        total_interest_earned: 0,
      },
      start_price: 100,
      end_price: 110,
    },
  },
  buy_hold_equity: [],
  benchmarks: {
    SPY: {
      name: 'SPY',
      ticker: 'SPY',
      equity: [],
      metrics: {
        total_return: 0.1,
        cagr: 0.1,
        sharpe_ratio: 1.1,
        sortino_ratio: 1.2,
        max_drawdown: -0.05,
        hit_rate: 0,
        profit_factor: 0,
        total_trades: 0,
        avg_trade_pnl: 0,
        volatility: 0.15,
        total_interest_earned: 0,
      },
    },
  },
  run_info: {
    run_id: 'run_123',
    artifact_dir: 'runs/run_123',
  },
  data_info: {
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    total_days: 365,
    initial_price: 100,
    final_price: 110,
  },
} as const;

describe('useBacktestWorkspace state helpers', () => {
  it('normalizes successful runs back to the charts tab', () => {
    expect(deriveSuccessfulWorkspaceState(response as any)).toMatchObject({
      appState: 'success',
      activeTab: 'charts',
      backtestResponse: response,
    });
  });

  it('derives visible strategies and benchmarks from response plus request flags', () => {
    expect(deriveVisibleStrategies(response as any)).toEqual(['Simple Martingale']);
    expect(
      deriveVisibleBenchmarks(response as any, {
        include_selic_benchmark: true,
        include_buy_hold_benchmark: true,
      })
    ).toEqual(['Buy & Hold', 'SELIC', 'SPY']);
    expect(
      deriveVisibleBenchmarks(response as any, {
        include_buy_hold_benchmark: false,
      })
    ).toEqual(['SPY']);
  });
});
