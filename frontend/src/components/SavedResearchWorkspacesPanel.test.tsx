import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import SavedResearchWorkspacesPanel from './SavedResearchWorkspacesPanel';
import { ResearchWorkspacePayload } from '../types/api';

vi.mock('../lib/api', () => ({
  apiClient: {
    getResearchWorkspaceReport: vi.fn().mockResolvedValue({
      workspace: {
        workspace_id: 'workspace_alpha',
      },
      report: {
        title: 'Alpha Workspace',
        executive_summary: 'Server-side report summary.',
        highlights: ['Server highlight'],
        risks: ['Server risk'],
        key_metrics: [{ label: 'Primary Experiment', value: 'optimization:opt_1' }],
        markdown: '# Alpha Workspace',
        html: '<html><body>Alpha Workspace</body></html>',
      },
    }),
    exportResearchWorkspaceReport: vi.fn().mockResolvedValue('# Alpha Workspace'),
    updateResearchWorkspace: vi.fn().mockResolvedValue(undefined),
    importResearchWorkspace: vi.fn().mockResolvedValue(undefined),
  },
}));

const workspace: ResearchWorkspacePayload = {
  workspace_id: 'workspace_alpha',
  created_at: '2026-03-24T10:00:00+00:00',
  name: 'Alpha Workspace',
  notes: 'Walk-forward looks stable.',
  selected_experiment: {
    experiment_type: 'optimization',
    experiment_id: 'opt_1',
  },
  selection: {
    optimization_id: 'opt_1',
    walkforward_id: 'wf_1',
    montecarlo_id: 'mc_1',
    anchor_run_id: 'run_1',
  },
  records: {
    selected: {
      experiment_id: 'opt_1',
      experiment_type: 'optimization',
      created_at: '2026-03-24T10:00:00+00:00',
      config_path: 'configs/test.yaml',
      strategy_names: ['Simple Martingale'],
      artifact_dir: 'runs/opt_1',
      status: 'completed',
      lineage: {
        best_run_id: 'run_1',
      },
      summary: {
        objective: 'sharpe_ratio',
      },
    },
    optimization: {
      experiment_id: 'opt_1',
      experiment_type: 'optimization',
      created_at: '2026-03-24T10:00:00+00:00',
      config_path: 'configs/test.yaml',
      strategy_names: ['Simple Martingale'],
      artifact_dir: 'runs/opt_1',
      status: 'completed',
      lineage: {
        best_run_id: 'run_1',
      },
      summary: {
        objective: 'sharpe_ratio',
      },
    },
    walkforward: {
      experiment_id: 'wf_1',
      experiment_type: 'walkforward',
      created_at: '2026-03-24T10:00:00+00:00',
      config_path: 'configs/test.yaml',
      strategy_names: ['Simple Martingale'],
      artifact_dir: 'runs/wf_1',
      status: 'completed',
      lineage: {
        parent_optimization_id: 'opt_1',
      },
      summary: {
        window_count: 6,
      },
    },
    montecarlo: {
      experiment_id: 'mc_1',
      experiment_type: 'montecarlo',
      created_at: '2026-03-24T10:00:00+00:00',
      config_path: 'configs/test.yaml',
      strategy_names: ['Simple Martingale'],
      artifact_dir: 'runs/mc_1',
      status: 'completed',
      lineage: {
        source_run_id: 'run_1',
      },
      summary: {
        simulation_count: 1000,
      },
    },
    anchor_run: {
      experiment_id: 'run_1',
      experiment_type: 'run',
      created_at: '2026-03-24T10:00:00+00:00',
      config_path: 'configs/test.yaml',
      strategy_names: ['Simple Martingale'],
      artifact_dir: 'runs/run_1',
      status: 'completed',
      lineage: {},
      summary: {
        warnings: [],
      },
    },
  },
};

describe('SavedResearchWorkspacesPanel', () => {
  it('shows a dedicated report view for the selected workspace', async () => {
    const user = userEvent.setup();

    render(
      <SavedResearchWorkspacesPanel
        workspaces={[workspace]}
        isLoading={false}
        onRefresh={vi.fn()}
        onOpenWorkspace={vi.fn()}
        onLoadRun={vi.fn()}
        onError={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: 'Report View' }));

    expect(screen.getByText('Executive Summary')).toBeTruthy();
    expect(screen.getByText('Markdown Preview')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Copy Brief' })).toBeTruthy();
  });
});
