import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import ResearchOverviewPanel from './ResearchOverviewPanel';

vi.mock('../hooks/useResearchOverview', () => ({
  useResearchOverview: () => ({
    experiments: [
      {
        experiment_id: 'run_1',
        experiment_type: 'run',
        created_at: '2026-03-24T10:00:00+00:00',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        artifact_dir: 'runs/run_1',
        status: 'completed',
        lineage: {},
        summary: { warnings: [] },
      },
    ],
    optimizations: [],
    walkForwardExecutions: [],
    monteCarloExecutions: [],
    isLoading: false,
    refresh: vi.fn(),
  }),
}));

vi.mock('../hooks/useExperimentContextDrilldown', () => ({
  useExperimentContextDrilldown: () => ({
    candidates: {
      optimization: [],
      walkforward: [],
      montecarlo: [],
    },
    targets: {
      anchorRunId: 'run_1',
      optimization: null,
      walkforward: null,
      montecarlo: null,
    },
    optimizationResults: null,
    walkForwardResults: null,
    monteCarloResults: null,
    isLoading: false,
  }),
}));

vi.mock('../lib/api', () => ({
  apiClient: {
    getExperiment: vi.fn().mockResolvedValue({
      record: {
        experiment_id: 'run_1',
        experiment_type: 'run',
        created_at: '2026-03-24T10:00:00+00:00',
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        artifact_dir: 'runs/run_1',
        status: 'completed',
        lineage: {},
        summary: { warnings: [] },
      },
      manifest: { run_id: 'run_1' },
      related_experiments: [],
    }),
  },
}));

describe('ResearchOverviewPanel', () => {
  it('opens the anchor run from contextual comparison', async () => {
    const user = userEvent.setup();
    const onLoadRun = vi.fn().mockResolvedValue(undefined);
    const onError = vi.fn();

    render(<ResearchOverviewPanel onError={onError} onLoadRun={onLoadRun} />);

    await user.click(await screen.findByRole('button', { name: 'Open Run' }));

    expect(onLoadRun).toHaveBeenCalledWith('run_1');
  });
});
