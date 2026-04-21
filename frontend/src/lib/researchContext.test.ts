import { describe, expect, it } from 'vitest';
import {
  applyExperimentContextOverrides,
  inferExperimentContext,
  listExperimentContextCandidates,
} from './researchDrilldown';

describe('inferExperimentContext', () => {
  it('finds linked optimization, monte carlo, and matching walk-forward context', () => {
    const detail = {
      record: {
        experiment_id: 'run_1',
        experiment_type: 'run' as const,
        created_at: '2026-03-24T10:00:00+00:00',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        artifact_dir: 'runs/run_1',
        status: 'completed',
        lineage: {},
        summary: {},
      },
      manifest: { run_id: 'run_1' },
      related_experiments: [
        {
          relationship: 'best_run_for_optimization' as const,
          record: {
            experiment_id: 'opt_1',
            experiment_type: 'optimization' as const,
            created_at: '2026-03-24T11:00:00+00:00',
            config_path: 'configs/test.yaml',
            strategy_names: ['Simple Martingale'],
            artifact_dir: 'optimizations/opt_1',
            status: 'completed',
            lineage: { best_run_id: 'run_1' },
            summary: {},
          },
        },
        {
          relationship: 'source_run_for_montecarlo' as const,
          record: {
            experiment_id: 'mc_1',
            experiment_type: 'montecarlo' as const,
            created_at: '2026-03-24T12:00:00+00:00',
            config_path: 'configs/test.yaml',
            strategy_names: ['Simple Martingale'],
            artifact_dir: 'montecarlo/mc_1',
            status: 'completed',
            lineage: { source_run_id: 'run_1' },
            summary: {},
          },
        },
      ],
    };

    const experiments = [
      detail.record,
      detail.related_experiments[0].record,
      detail.related_experiments[1].record,
      {
        experiment_id: 'wf_1',
        experiment_type: 'walkforward' as const,
        created_at: '2026-03-24T13:00:00+00:00',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        artifact_dir: 'walkforward/wf_1',
        status: 'completed',
        lineage: {},
        summary: { window_count: 4 },
      },
    ];

    const context = inferExperimentContext(detail, experiments);

    expect(context.anchorRunId).toBe('run_1');
    expect(context.optimization?.experiment_id).toBe('opt_1');
    expect(context.montecarlo?.experiment_id).toBe('mc_1');
    expect(context.walkforward?.experiment_id).toBe('wf_1');
  });

  it('allows explicit overrides over the inferred context', () => {
    const detail = {
      record: {
        experiment_id: 'run_1',
        experiment_type: 'run' as const,
        created_at: '2026-03-24T10:00:00+00:00',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        artifact_dir: 'runs/run_1',
        status: 'completed',
        lineage: {},
        summary: {},
      },
      manifest: { run_id: 'run_1' },
      related_experiments: [],
    };

    const experiments = [
      detail.record,
      {
        experiment_id: 'wf_auto',
        experiment_type: 'walkforward' as const,
        created_at: '2026-03-24T11:00:00+00:00',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        artifact_dir: 'walkforward/wf_auto',
        status: 'completed',
        lineage: {},
        summary: {},
      },
      {
        experiment_id: 'wf_manual',
        experiment_type: 'walkforward' as const,
        created_at: '2026-03-24T12:00:00+00:00',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        artifact_dir: 'walkforward/wf_manual',
        status: 'completed',
        lineage: {},
        summary: {},
      },
    ];

    const inferred = inferExperimentContext(detail, experiments);
    const candidates = listExperimentContextCandidates(detail, experiments);
    const overridden = applyExperimentContextOverrides(inferred, candidates, {
      walkforwardId: 'wf_manual',
    });

    expect(inferred.walkforward?.experiment_id).toBe('wf_manual');
    expect(overridden.walkforward?.experiment_id).toBe('wf_manual');
  });
});
