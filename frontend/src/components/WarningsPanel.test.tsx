import { describe, expect, it } from 'vitest';
import { generateWarnings } from './WarningsPanel';
import { BacktestRequest, BacktestResponse } from '../types/api';

const backtestRequest: BacktestRequest = {
  strategies: ['Simple Martingale'],
  initial_capital: 10000,
};

const backtestResponse: BacktestResponse = {
  results: {
    'Simple Martingale': {
      strategy_name: 'Simple Martingale',
      equity: [],
      trades: [],
      metrics: {
        total_return: 0.12,
        cagr: 0.12,
        sharpe_ratio: 1.1,
        sortino_ratio: 1.3,
        max_drawdown: -0.1,
        hit_rate: 0.6,
        profit_factor: 1.4,
        total_trades: 0,
        avg_trade_pnl: 0,
        volatility: 0.2,
        total_interest_earned: 0,
      },
      start_price: 100,
      end_price: 112,
      execution_summary: {
        fill_count: 1,
        partial_fill_count: 1,
        rejected_buy_count: 1,
        rejected_sell_count: 0,
        rejected_order_count: 1,
        liquidity_constrained: true,
        requested_quantity_total: 10,
        filled_quantity_total: 5,
      },
      warnings: ['One or more orders were partially filled due to configured liquidity limits.'],
    },
  },
  buy_hold_equity: [],
  data_info: {
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    total_days: 365,
    initial_price: 100,
    final_price: 112,
  },
  warnings: [
    'Simple Martingale: One or more buy orders were rejected because cash or liquidity was insufficient.',
  ],
};

describe('generateWarnings', () => {
  it('includes backend execution warnings and liquidity summaries', () => {
    const warnings = generateWarnings(backtestResponse, backtestRequest);

    expect(
      warnings.some(
        (warning) =>
          warning.title === 'Ordem rejeitada' && warning.strategy === 'Simple Martingale'
      )
    ).toBe(true);
    expect(
      warnings.some(
        (warning) =>
          warning.title === 'Liquidez limitou execucao' &&
          warning.strategy === 'Simple Martingale'
      )
    ).toBe(true);
  });
});
