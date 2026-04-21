import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { useSystemStatus } from './useSystemStatus';

describe('useSystemStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads the platform status once on mount', async () => {
    vi.mocked(apiClient.getSystemStatus).mockResolvedValue({
      status: 'ok',
      api_version: '1.0.0',
      checked_at: '2026-04-20T15:00:00Z',
      config_count: 2,
      dataset_count: 3,
      due_dataset_count: 1,
      artifact_counts: {
        runs: 4,
        optimizations: 1,
        walkforward: 1,
        montecarlo: 1,
        pairs_backtests: 1,
        research_workspaces: 2,
        allocation_workspaces: 1,
      },
      job_counts: {
        queued: 1,
        running: 1,
        completed: 2,
        failed: 0,
        cancelled: 0,
      },
      job_runtime: {
        execution_mode: 'inline',
        max_workers: 2,
        active_futures: 1,
      },
      pairs_job_counts: {
        queued: 0,
        running: 0,
        completed: 1,
        failed: 0,
        cancelled: 0,
      },
      pairs_job_runtime: {
        execution_mode: 'inline',
        max_workers: 1,
        active_futures: 0,
      },
      latest_run_id: 'run_4',
      latest_backtest_job_id: 'job_4',
      latest_pairs_backtest_job_id: 'pairs_job_1',
      latest_pairs_backtest_id: 'pairs_1',
      latest_research_workspace_id: 'research_ws_2',
      warnings: [],
    } as never);

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(apiClient.getSystemStatus).toHaveBeenCalledTimes(1);
    expect(result.current.status?.due_dataset_count).toBe(1);
    expect(result.current.error).toBeNull();
  });

  it('surfaces a compact error state when loading fails', async () => {
    vi.mocked(apiClient.getSystemStatus).mockRejectedValue(new Error('offline'));

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.status).toBeNull();
    expect(result.current.error).toBe('Status unavailable');
  });
});
