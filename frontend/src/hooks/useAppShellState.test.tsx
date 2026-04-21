import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useAppShellState } from './useAppShellState';

describe('useAppShellState', () => {
  it('builds result badges from the current workspace counts', () => {
    const { result } = renderHook(() =>
      useAppShellState({
        runsCount: 8,
        selectedRunCount: 2,
        workspaceCount: 3,
      })
    );

    expect(result.current.primaryTabs).toEqual([
      { id: 'home', label: 'Inicio' },
      { id: 'simulate', label: 'Simular' },
      { id: 'results', label: 'Resultados', badge: 8 },
      { id: 'advanced', label: 'Avancado' },
    ]);

    expect(result.current.resultsTabs).toEqual([
      { id: 'history', label: 'Recentes', badge: 8 },
      { id: 'compare', label: 'Comparar', badge: 2 },
      { id: 'workspaces', label: 'Estudos salvos', badge: 3 },
    ]);
  });

  it('opens a workspace directly in advanced research mode', () => {
    const workspace = {
      workspace_id: 'research_ws_1',
      created_at: '2026-04-20T15:00:00Z',
      name: 'Workspace 1',
      notes: null,
      selected_experiment: null,
      selection: {},
      records: {},
    };

    const { result } = renderHook(() =>
      useAppShellState({
        runsCount: 0,
        selectedRunCount: 0,
        workspaceCount: 0,
      })
    );

    act(() => {
      result.current.openWorkspaceInResearch(workspace as any);
    });

    expect(result.current.primarySection).toBe('advanced');
    expect(result.current.advancedTool).toBe('research');
    expect(result.current.workspaceToOpen).toMatchObject({ workspace_id: 'research_ws_1' });

    act(() => {
      result.current.clearWorkspaceToOpen();
    });

    expect(result.current.workspaceToOpen).toBeNull();
  });
});
