import { describe, expect, it } from 'vitest';
import { buildResultsInterpretation } from './result-narrative';
import { StrategyResult } from '../types/api';

function createStrategyResult(
  name: string,
  overrides: Partial<StrategyResult['metrics']>
): StrategyResult {
  return {
    strategy_name: name,
    equity: [],
    trades: [],
    start_price: 100,
    end_price: 120,
    execution_summary: {
      fill_count: 1,
      partial_fill_count: 0,
      rejected_buy_count: 0,
      rejected_sell_count: 0,
      rejected_order_count: 0,
      liquidity_constrained: false,
      requested_quantity_total: 1,
      filled_quantity_total: 1,
    },
    metrics: {
      total_return: 0.1,
      cagr: 0.1,
      sharpe_ratio: 1,
      sortino_ratio: 1.2,
      max_drawdown: 0.12,
      hit_rate: 0.55,
      profit_factor: 1.2,
      total_trades: 10,
      avg_trade_pnl: 25,
      volatility: 0.2,
      total_interest_earned: 0,
      ...overrides,
    },
  };
}

describe('buildResultsInterpretation', () => {
  it('highlights return vs sharpe trade-offs', () => {
    const interpretation = buildResultsInterpretation({
      Aggressive: createStrategyResult('Aggressive', {
        total_return: 0.32,
        sharpe_ratio: 0.8,
        max_drawdown: 0.34,
      }),
      Balanced: createStrategyResult('Balanced', {
        total_return: 0.2,
        sharpe_ratio: 1.45,
        max_drawdown: 0.16,
      }),
    });

    expect(interpretation).not.toBeNull();
    expect(interpretation?.bestReturnStrategy).toBe('Aggressive');
    expect(interpretation?.bestSharpeStrategy).toBe('Balanced');
    expect(
      interpretation?.insights.some((item) => item.title.includes('trade-off'))
    ).toBe(true);
    expect(
      interpretation?.insights.some((item) => item.body.includes('drawdown máximo'))
    ).toBe(true);
  });

  it('flags weak strategies and small sample sizes', () => {
    const interpretation = buildResultsInterpretation({
      ThinSample: createStrategyResult('ThinSample', {
        total_return: 0.14,
        sharpe_ratio: 1.5,
        total_trades: 3,
      }),
      Fragile: createStrategyResult('Fragile', {
        total_return: -0.05,
        sharpe_ratio: -0.4,
        profit_factor: 0.7,
        max_drawdown: 0.42,
      }),
    });

    expect(interpretation).not.toBeNull();
    expect(
      interpretation?.insights.some((item) => item.body.includes('apenas 3 trades'))
    ).toBe(true);
    expect(
      interpretation?.insights.some((item) => item.body.includes('Sharpe negativo'))
    ).toBe(true);
  });

  it('surfaces execution realism constraints when liquidity affected the run', () => {
    const constrained = createStrategyResult('Constrained', {
      total_return: 0.18,
      sharpe_ratio: 1.1,
    });
    constrained.execution_summary = {
      fill_count: 1,
      partial_fill_count: 2,
      rejected_buy_count: 1,
      rejected_sell_count: 0,
      rejected_order_count: 1,
      liquidity_constrained: true,
      requested_quantity_total: 10,
      filled_quantity_total: 6,
    };

    const interpretation = buildResultsInterpretation({
      Constrained: constrained,
      Baseline: createStrategyResult('Baseline', {
        total_return: 0.14,
        sharpe_ratio: 0.9,
      }),
    });

    expect(interpretation).not.toBeNull();
    expect(
      interpretation?.insights.some((item) => item.title.includes('Liquidez interferiu'))
    ).toBe(true);
  });
});
