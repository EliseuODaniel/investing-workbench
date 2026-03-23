import { describe, expect, it } from 'vitest';
import { summarizeResearchAlignment } from './researchDrilldown';

describe('researchDrilldown', () => {
  it('detects aligned run links between optimization and Monte Carlo', () => {
    const summary = summarizeResearchAlignment(
      {
        optimization_id: 'opt_1',
        objective: 'sharpe_ratio',
        direction: 'maximize',
        mode: 'grid',
        random_seed: 42,
        strategy_names: ['Simple Martingale'],
        trial_count: 2,
        completed_trial_count: 2,
        truncated: false,
        warnings: [],
        ranked_results: [
          {
            trial_id: 'trial_1',
            strategy_name: 'Simple Martingale',
            run_id: 'run_1',
            objective: 'sharpe_ratio',
            objective_value: 1.25,
            parameters: {},
            metrics: {},
            status: 'completed',
          },
        ],
        results: [],
      },
      {
        walkforward_id: 'wf_1',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        train_window_days: 90,
        test_window_days: 30,
        step_days: 30,
        window_count: 4,
        strategy_summaries: [
          {
            strategy_name: 'Simple Martingale',
            window_count: 4,
            avg_train_total_return: 0.2,
            avg_test_total_return: 0.1,
            avg_test_sharpe_ratio: 0.8,
            worst_test_drawdown: -0.15,
          },
        ],
        results: [],
      },
      {
        montecarlo_id: 'mc_1',
        config_path: 'configs/test.yaml',
        source_run_id: 'run_1',
        strategy_names: ['Simple Martingale'],
        simulation_count: 100,
        random_seed: 42,
        method: 'bootstrap',
        ruin_threshold_pct: 0.3,
        warnings: [],
        strategy_summaries: [
          {
            strategy_name: 'Simple Martingale',
            trade_count: 50,
            simulation_count: 100,
            method: 'bootstrap',
            actual_final_equity: 100,
            actual_total_return: 0.1,
            actual_max_drawdown: -0.1,
            loss_probability: 0.2,
            ruin_probability: 0.05,
            percentile_05_final_equity: 90,
            median_final_equity: 100,
            percentile_95_final_equity: 110,
            percentile_05_total_return: -0.1,
            median_total_return: 0.1,
            percentile_95_total_return: 0.2,
            percentile_05_max_drawdown: -0.2,
            median_max_drawdown: -0.1,
            percentile_95_max_drawdown: -0.05,
            worst_final_equity: 80,
            best_final_equity: 120,
            warnings: [],
          },
        ],
        results: [],
      }
    );

    expect(summary.runLinkAligned).toBe(true);
    expect(summary.walkForwardAvgTestReturn).toBe(0.1);
    expect(summary.monteCarloLossProbability).toBe(0.2);
  });
});
