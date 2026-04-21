import { describe, expect, it } from 'vitest';
import {
  buildMonteCarloReturnChart,
  buildOptimizationObjectiveChart,
  buildPairsEquityChart,
  buildWalkForwardTestChart,
} from './advancedCharts';

describe('advancedCharts builders', () => {
  it('builds walk-forward chart data grouped by window and strategy', () => {
    const chart = buildWalkForwardTestChart({
      walkforward_id: 'wf_1',
      config_path: 'configs/test.yaml',
      strategy_names: ['A', 'B'],
      train_window_days: 90,
      test_window_days: 30,
      step_days: 30,
      window_count: 2,
      strategy_summaries: [],
      results: [
        {
          window_id: 'w1',
          strategy_name: 'A',
          train_start: '2021-01-01',
          train_end: '2021-03-31',
          test_start: '2021-04-01',
          test_end: '2021-04-30',
          train_metrics: {},
          test_metrics: { total_return: 0.1 },
        },
        {
          window_id: 'w1',
          strategy_name: 'B',
          train_start: '2021-01-01',
          train_end: '2021-03-31',
          test_start: '2021-04-01',
          test_end: '2021-04-30',
          train_metrics: {},
          test_metrics: { total_return: 0.05 },
        },
      ],
    });

    expect(chart?.data).toEqual([{ label: 'w1', A: 0.1, B: 0.05 }]);
    expect(chart?.series.map((item) => item.label)).toEqual(['A', 'B']);
  });

  it('builds pairs chart data with benchmark reference', () => {
    const chart = buildPairsEquityChart({
      pairs_backtest_id: 'pairs_1',
      created_at: '2026-04-21T00:00:00Z',
      manifest: {},
      universe: {},
      candidate_pairs: [],
      warnings: [],
      robustness_report: { rankings: [], dispersion: {} },
      scenarios: [
        {
          scenario_id: 'scenario_a',
          label: 'Scenario A',
          metrics: {},
          portfolio_summary: {},
          quality_summary: {},
          equity_curve: [
            { date: '2021-01-04', equity: 100000 },
            { date: '2021-01-05', equity: 101000 },
          ],
        },
      ],
      benchmarks: [
        {
          benchmark_id: 'selic_cash',
          label: 'Caixa SELIC',
          equity_curve: [
            { date: '2021-01-04', equity: 100000 },
            { date: '2021-01-05', equity: 100050 },
          ],
        },
      ],
    });

    expect(chart?.referenceSeriesId).toBe('selic_cash');
    expect(chart?.series.map((item) => item.label)).toEqual(['Scenario A', 'Caixa SELIC']);
    expect(chart?.data).toHaveLength(2);
  });

  it('builds Monte Carlo chart comparing actual and percentile ranges', () => {
    const chart = buildMonteCarloReturnChart({
      montecarlo_id: 'mc_1',
      source_run_id: 'run_1',
      strategy_names: ['A'],
      simulation_count: 100,
      random_seed: 42,
      method: 'bootstrap',
      ruin_threshold_pct: 0.3,
      warnings: [],
      strategy_summaries: [
        {
          strategy_name: 'A',
          trade_count: 10,
          simulation_count: 100,
          method: 'bootstrap',
          actual_final_equity: 110000,
          actual_total_return: 0.1,
          actual_max_drawdown: -0.2,
          loss_probability: 0.2,
          ruin_probability: 0.05,
          percentile_05_final_equity: 80000,
          median_final_equity: 100000,
          percentile_95_final_equity: 130000,
          percentile_05_total_return: -0.1,
          median_total_return: 0.06,
          percentile_95_total_return: 0.2,
          percentile_05_max_drawdown: -0.4,
          median_max_drawdown: -0.2,
          percentile_95_max_drawdown: -0.05,
          worst_final_equity: 70000,
          best_final_equity: 150000,
          warnings: [],
        },
      ],
      results: [],
    });

    expect(chart?.data[0]).toMatchObject({
      label: 'A',
      actual_total_return: 0.1,
      median_total_return: 0.06,
      percentile_05_total_return: -0.1,
      percentile_95_total_return: 0.2,
    });
  });

  it('builds optimization chart from best trial by strategy', () => {
    const chart = buildOptimizationObjectiveChart({
      optimization_id: 'opt_1',
      objective: 'sharpe_ratio',
      direction: 'maximize',
      mode: 'grid',
      random_seed: 42,
      strategy_names: ['A', 'B'],
      trial_count: 4,
      completed_trial_count: 4,
      truncated: false,
      warnings: [],
      ranked_results: [
        {
          trial_id: 't1',
          strategy_name: 'A',
          parameters: {},
          objective: 'sharpe_ratio',
          objective_value: 1.2,
          metrics: {},
          status: 'completed',
        },
        {
          trial_id: 't2',
          strategy_name: 'B',
          parameters: {},
          objective: 'sharpe_ratio',
          objective_value: 0.8,
          metrics: {},
          status: 'completed',
        },
      ],
      results: [],
    });

    expect(chart?.series.map((item) => item.label)).toEqual(['Melhor objetivo']);
    expect(chart?.data).toEqual([
      { label: 'A', objective_value: 1.2 },
      { label: 'B', objective_value: 0.8 },
    ]);
  });
});
