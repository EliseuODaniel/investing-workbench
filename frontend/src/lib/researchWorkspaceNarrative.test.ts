import { describe, expect, it } from 'vitest';
import {
  buildResearchWorkspaceNarrative,
  buildResearchWorkspaceNarrativeFromReport,
} from './researchWorkspaceNarrative';

describe('buildResearchWorkspaceNarrative', () => {
  it('builds an executive snapshot with highlights and risks', () => {
    const narrative = buildResearchWorkspaceNarrative({
      workspace_id: 'research_ws_1',
      created_at: '2026-03-24T18:00:00+00:00',
      name: 'Martingale Review',
      notes: 'Cross-check before sharing.',
      selected_experiment: {
        experiment_type: 'optimization',
        experiment_id: 'opt_1',
      },
      selection: {
        optimization_id: 'opt_1',
        walkforward_id: 'wf_1',
        montecarlo_id: null,
        anchor_run_id: 'run_1',
      },
      records: {
        selected: {
          experiment_id: 'opt_1',
          experiment_type: 'optimization',
          created_at: '2026-03-24T18:00:00+00:00',
          config_path: 'configs/test.yaml',
          strategy_names: ['Simple Martingale'],
          artifact_dir: 'optimizations/opt_1',
          status: 'completed',
          lineage: { best_run_id: 'run_1' },
          summary: {
            objective: 'sharpe_ratio',
            warnings: ['Trial plan was truncated'],
          },
        },
        optimization: {
          experiment_id: 'opt_1',
          experiment_type: 'optimization',
          created_at: '2026-03-24T18:00:00+00:00',
          config_path: 'configs/test.yaml',
          strategy_names: ['Simple Martingale'],
          artifact_dir: 'optimizations/opt_1',
          status: 'completed',
          lineage: { best_run_id: 'run_1' },
          summary: {
            objective: 'sharpe_ratio',
            warnings: ['Trial plan was truncated'],
          },
        },
        walkforward: {
          experiment_id: 'wf_1',
          experiment_type: 'walkforward',
          created_at: '2026-03-24T18:10:00+00:00',
          config_path: 'configs/test.yaml',
          strategy_names: ['Simple Martingale'],
          artifact_dir: 'walkforward/wf_1',
          status: 'completed',
          lineage: {},
          summary: {
            window_count: 4,
            warnings: [],
          },
        },
        montecarlo: null,
        anchor_run: {
          experiment_id: 'run_1',
          experiment_type: 'run',
          created_at: '2026-03-24T17:50:00+00:00',
          config_path: 'configs/test.yaml',
          strategy_names: ['Simple Martingale'],
          artifact_dir: 'runs/run_1',
          status: 'completed',
          lineage: {},
          summary: {
            data_fingerprint: 'abc123',
            warnings: [],
          },
        },
      },
    });

    expect(narrative.executiveSummary).toContain('Martingale Review');
    expect(narrative.keyMetrics.some((item) => item.label === 'Optimization Objective')).toBe(true);
    expect(narrative.highlights.some((item) => item.includes('Optimization context'))).toBe(true);
    expect(narrative.risks.some((item) => item.includes('Tail-risk'))).toBe(true);
    expect(narrative.markdown).toContain('## Key Metrics');
    expect(narrative.markdown).toContain('## Highlights');
    expect(narrative.markdown).toContain('## Risks');
    expect(narrative.html).toContain('<!DOCTYPE html>');
    expect(narrative.html).toContain('Research Workspace Report');
  });

  it('normalizes the server-side report payload into the frontend narrative shape', () => {
    const narrative = buildResearchWorkspaceNarrativeFromReport({
      title: 'Server Report',
      executive_summary: 'Shared contract summary.',
      highlights: ['One highlight'],
      risks: ['One risk'],
      key_metrics: [{ label: 'Strategy Count', value: '1' }],
      markdown: '# Server Report',
      html: '<html><body>Server Report</body></html>',
    });

    expect(narrative.title).toBe('Server Report');
    expect(narrative.executiveSummary).toBe('Shared contract summary.');
    expect(narrative.keyMetrics[0]?.label).toBe('Strategy Count');
    expect(narrative.markdown).toContain('# Server Report');
  });
});
