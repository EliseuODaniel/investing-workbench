import { ResearchWorkspacePayload } from '../types/api';

export type ResearchWorkspaceSort =
  | 'created_desc'
  | 'created_asc'
  | 'name_asc'
  | 'name_desc';

export function filterAndSortResearchWorkspaces(
  workspaces: ResearchWorkspacePayload[],
  options: {
    query: string;
    sort: ResearchWorkspaceSort;
  }
): ResearchWorkspacePayload[] {
  const normalizedQuery = options.query.trim().toLowerCase();

  const filtered = normalizedQuery
    ? workspaces.filter((workspace) => buildSearchText(workspace).includes(normalizedQuery))
    : workspaces;

  return [...filtered].sort((left, right) => {
    switch (options.sort) {
      case 'created_asc':
        return left.created_at.localeCompare(right.created_at);
      case 'name_asc':
        return left.name.localeCompare(right.name);
      case 'name_desc':
        return right.name.localeCompare(left.name);
      case 'created_desc':
      default:
        return right.created_at.localeCompare(left.created_at);
    }
  });
}

function buildSearchText(workspace: ResearchWorkspacePayload): string {
  return [
    workspace.workspace_id,
    workspace.name,
    workspace.notes ?? '',
    workspace.selected_experiment.experiment_type,
    workspace.selected_experiment.experiment_id,
    workspace.selection.anchor_run_id ?? '',
    workspace.selection.optimization_id ?? '',
    workspace.selection.walkforward_id ?? '',
    workspace.selection.montecarlo_id ?? '',
  ]
    .join(' ')
    .toLowerCase();
}
