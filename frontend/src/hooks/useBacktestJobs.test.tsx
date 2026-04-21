import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { useBacktestJobs } from './useBacktestJobs';

describe('useBacktestJobs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('queues a job, polls it, and hydrates the completed run once', async () => {
    const onLoadCompletedRun = vi.fn().mockResolvedValue(undefined);
    const refreshRuns = vi.fn();
    const onError = vi.fn();

    vi.mocked(apiClient.listBacktestJobs)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          job_id: 'job_1',
          job_type: 'backtest',
          status: 'queued',
          created_at: '2026-04-20T15:00:00Z',
          updated_at: '2026-04-20T15:00:00Z',
          attempt_count: 1,
          cancel_requested: false,
          request_payload: {},
          config_path: 'configs/test.yaml',
          strategy_names: ['Simple Martingale'],
          progress: {
            phase: 'queued',
            message: 'Queued',
            percent: 0,
            updated_at: '2026-04-20T15:00:00Z',
          },
          result_available: false,
          events: [],
        },
      ] as never);
    vi.mocked(apiClient.createBacktestJob).mockResolvedValue({
      job_id: 'job_1',
      job_type: 'backtest',
      status: 'queued',
      created_at: '2026-04-20T15:00:00Z',
      updated_at: '2026-04-20T15:00:00Z',
      attempt_count: 1,
      cancel_requested: false,
      request_payload: {},
      config_path: 'configs/test.yaml',
      strategy_names: ['Simple Martingale'],
      progress: {
        phase: 'queued',
        message: 'Queued',
        percent: 0,
        updated_at: '2026-04-20T15:00:00Z',
      },
      result_available: false,
      events: [],
    } as never);
    vi.mocked(apiClient.getBacktestJob)
      .mockResolvedValueOnce({
        job_id: 'job_1',
        job_type: 'backtest',
        status: 'running',
        created_at: '2026-04-20T15:00:00Z',
        updated_at: '2026-04-20T15:00:02Z',
        attempt_count: 1,
        cancel_requested: false,
        request_payload: {},
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        progress: {
          phase: 'strategy',
          message: 'Running strategy',
          percent: 55,
          updated_at: '2026-04-20T15:00:02Z',
          current_step: 1,
          total_steps: 1,
        },
        result_available: false,
        events: [],
      } as never)
      .mockResolvedValueOnce({
        job_id: 'job_1',
        job_type: 'backtest',
        status: 'completed',
        created_at: '2026-04-20T15:00:00Z',
        updated_at: '2026-04-20T15:00:04Z',
        attempt_count: 1,
        cancel_requested: false,
        request_payload: {},
        config_path: 'configs/test.yaml',
        strategy_names: ['Simple Martingale'],
        progress: {
          phase: 'completed',
          message: 'Completed',
          percent: 100,
          updated_at: '2026-04-20T15:00:04Z',
        },
        run_id: 'run_123',
        result_available: true,
        events: [],
      } as never);

    const { result } = renderHook(() =>
      useBacktestJobs({
        backtestRequest: {},
        selectedConfig: {
          name: 'test',
          path: 'configs/test.yaml',
          display_name: 'Test',
          strategies: ['Simple Martingale'],
        },
        onLoadCompletedRun,
        refreshRuns,
        onError,
      })
    );

    await waitFor(() => {
      expect(apiClient.listBacktestJobs).toHaveBeenCalledTimes(1);
    });

    await act(async () => {
      await result.current.startJob();
    });

    expect(result.current.activeJob?.job_id).toBe('job_1');

    await act(async () => {
      vi.advanceTimersByTime(1600);
    });

    await waitFor(() => {
      expect(apiClient.getBacktestJob).toHaveBeenCalledTimes(1);
    });

    await act(async () => {
      vi.advanceTimersByTime(1600);
    });

    await waitFor(() => {
      expect(onLoadCompletedRun).toHaveBeenCalledWith('run_123');
    });

    expect(refreshRuns).toHaveBeenCalledTimes(1);
    expect(onError).toHaveBeenLastCalledWith(null);
  });
});
