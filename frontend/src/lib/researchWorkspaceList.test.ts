import { describe, expect, it } from 'vitest';
import {
  filterAndSortResearchWorkspaces,
  type ResearchWorkspaceSort,
} from './researchWorkspaceList';

function buildWorkspace(
  overrides: Partial<{
    workspace_id: string;
    created_at: string;
    name: string;
    notes: string | null;
    anchor_run_id: string | null;
  }>
) {
  return {
    workspace_id: overrides.workspace_id ?? 'research_ws_1',
    created_at: overrides.created_at ?? '2026-03-24T10:00:00+00:00',
    name: overrides.name ?? 'Default Workspace',
    notes: overrides.notes ?? null,
    selected_experiment: {
      experiment_type: 'run' as const,
      experiment_id: 'run_1',
    },
    selection: {
      anchor_run_id: overrides.anchor_run_id ?? 'run_1',
      optimization_id: null,
      walkforward_id: null,
      montecarlo_id: null,
    },
    records: {
      selected: {
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
      anchor_run: null,
      optimization: null,
      walkforward: null,
      montecarlo: null,
    },
  };
}

describe('filterAndSortResearchWorkspaces', () => {
  it('filters by free-text query', () => {
    const workspaces = [
      buildWorkspace({ name: 'Momentum Review', workspace_id: 'research_ws_a' }),
      buildWorkspace({
        name: 'Martingale Handoff',
        notes: 'share with team',
        workspace_id: 'research_ws_b',
      }),
    ];

    const result = filterAndSortResearchWorkspaces(workspaces, {
      query: 'team',
      sort: 'created_desc',
    });

    expect(result).toHaveLength(1);
    expect(result[0].workspace_id).toBe('research_ws_b');
  });

  it.each([
    ['created_desc', 'research_ws_new'],
    ['created_asc', 'research_ws_z'],
    ['name_asc', 'research_ws_a'],
    ['name_desc', 'research_ws_z'],
  ] satisfies [ResearchWorkspaceSort, string][])(
    'sorts workspaces with %s',
    (sort, expectedFirstId) => {
      const workspaces = [
        buildWorkspace({
          workspace_id: 'research_ws_old',
          created_at: '2026-03-24T10:00:00+00:00',
          name: 'Bravo',
        }),
        buildWorkspace({
          workspace_id: 'research_ws_new',
          created_at: '2026-03-24T12:00:00+00:00',
          name: 'Charlie',
        }),
        buildWorkspace({
          workspace_id: 'research_ws_a',
          created_at: '2026-03-24T11:00:00+00:00',
          name: 'Alpha',
        }),
        buildWorkspace({
          workspace_id: 'research_ws_z',
          created_at: '2026-03-24T09:00:00+00:00',
          name: 'Zulu',
        }),
      ];

      const result = filterAndSortResearchWorkspaces(workspaces, {
        query: '',
        sort,
      });

      expect(result[0].workspace_id).toBe(expectedFirstId);
    }
  );
});
