import { describe, expect, it } from 'vitest';
import { buildResearchTimeline, countResearchWarnings } from './researchOverview';

describe('researchOverview', () => {
  it('builds a cross-workflow timeline sorted by recency', () => {
    const timeline = buildResearchTimeline(
      [
        {
          optimization_id: 'opt_1',
          created_at: '2026-03-22T10:00:00+00:00',
          config_path: 'configs/test.yaml',
          objective: 'sharpe_ratio',
          direction: 'maximize',
          mode: 'grid',
          random_seed: 42,
          strategy_names: ['Simple Martingale'],
          trial_count: 4,
          completed_trial_count: 4,
          truncated: false,
          warnings: [],
        },
      ],
      [],
      [
        {
          montecarlo_id: 'mc_1',
          created_at: '2026-03-23T10:00:00+00:00',
          config_path: 'configs/test.yaml',
          source_run_id: 'run_1',
          strategy_names: ['Simple Martingale'],
          simulation_count: 100,
          random_seed: 42,
          method: 'bootstrap',
          ruin_threshold_pct: 0.3,
          warnings: ['warn'],
          strategy_summaries: [],
        },
      ]
    );

    expect(timeline[0].id).toBe('mc_1');
    expect(timeline[1].id).toBe('opt_1');
  });

  it('counts warnings across persisted research jobs', () => {
    const warningCount = countResearchWarnings(
      [
        {
          optimization_id: 'opt_1',
          created_at: '2026-03-22T10:00:00+00:00',
          config_path: 'configs/test.yaml',
          objective: 'sharpe_ratio',
          direction: 'maximize',
          mode: 'grid',
          random_seed: 42,
          strategy_names: ['Simple Martingale'],
          trial_count: 4,
          completed_trial_count: 4,
          truncated: false,
          warnings: ['a', 'b'],
        },
      ],
      [
        {
          montecarlo_id: 'mc_1',
          created_at: '2026-03-23T10:00:00+00:00',
          config_path: 'configs/test.yaml',
          source_run_id: 'run_1',
          strategy_names: ['Simple Martingale'],
          simulation_count: 100,
          random_seed: 42,
          method: 'bootstrap',
          ruin_threshold_pct: 0.3,
          warnings: ['c'],
          strategy_summaries: [],
        },
      ]
    );

    expect(warningCount).toBe(3);
  });
});
