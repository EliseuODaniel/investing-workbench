import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiClient } from '../lib/api';
import { BacktestJobPayload, BacktestRequest, ConfigInfo } from '../types/api';

interface UseBacktestJobsOptions {
  backtestRequest: BacktestRequest;
  selectedConfig: ConfigInfo | null;
  onLoadCompletedRun: (runId: string) => Promise<void>;
  refreshRuns: () => void;
  onError: (message: string | null) => void;
}

const ACTIVE_STATUSES: BacktestJobPayload['status'][] = ['queued', 'running'];

export function useBacktestJobs({
  backtestRequest,
  selectedConfig,
  onLoadCompletedRun,
  refreshRuns,
  onError,
}: UseBacktestJobsOptions) {
  const [jobs, setJobs] = useState<BacktestJobPayload[]>([]);
  const [activeJob, setActiveJob] = useState<BacktestJobPayload | null>(null);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [isSubmittingJob, setIsSubmittingJob] = useState(false);
  const [isCancellingJob, setIsCancellingJob] = useState(false);
  const handledCompletionRef = useRef<string | null>(null);

  const refreshJobs = useCallback(async () => {
    setIsLoadingJobs(true);
    try {
      const payload = await apiClient.listBacktestJobs({ limit: 12 });
      setJobs(payload);
    } catch (error) {
      console.error('Failed to load backtest jobs:', error);
      onError('Failed to load async backtest jobs');
    } finally {
      setIsLoadingJobs(false);
    }
  }, [onError]);

  const syncCompletedJob = useCallback(
    async (job: BacktestJobPayload) => {
      if (!job.run_id || handledCompletionRef.current === job.job_id) {
        return;
      }

      handledCompletionRef.current = job.job_id;
      refreshRuns();
      await onLoadCompletedRun(job.run_id);
    },
    [onLoadCompletedRun, refreshRuns]
  );

  const openJob = useCallback(
    async (jobId: string) => {
      try {
        const job = await apiClient.getBacktestJob(jobId);
        setActiveJob(job);
        if (job.status === 'completed' && job.run_id) {
          await syncCompletedJob(job);
        }
      } catch (error) {
        console.error('Failed to load async backtest job:', error);
        onError('Failed to load async backtest job');
      }
    },
    [onError, syncCompletedJob]
  );

  const startJob = useCallback(async () => {
    if (!selectedConfig) {
      onError('Select a config before starting a backtest job');
      return;
    }

    setIsSubmittingJob(true);
    onError(null);
    handledCompletionRef.current = null;
    try {
      const job = await apiClient.createBacktestJob({
        ...backtestRequest,
        config_path: selectedConfig.path,
      });
      setActiveJob(job);
      await refreshJobs();
    } catch (error: any) {
      console.error('Failed to queue async backtest job:', error);
      onError(error.response?.data?.detail || 'Failed to queue async backtest job');
    } finally {
      setIsSubmittingJob(false);
    }
  }, [backtestRequest, onError, refreshJobs, selectedConfig]);

  const cancelActiveJob = useCallback(async () => {
    if (!activeJob) {
      return;
    }

    setIsCancellingJob(true);
    try {
      const job = await apiClient.cancelBacktestJob(activeJob.job_id);
      setActiveJob(job);
      await refreshJobs();
    } catch (error: any) {
      console.error('Failed to cancel async backtest job:', error);
      onError(error.response?.data?.detail || 'Failed to cancel async backtest job');
    } finally {
      setIsCancellingJob(false);
    }
  }, [activeJob, onError, refreshJobs]);

  const resumeJob = useCallback(
    async (jobId: string) => {
      onError(null);
      handledCompletionRef.current = null;
      try {
        const job = await apiClient.resumeBacktestJob(jobId);
        setActiveJob(job);
        await refreshJobs();
      } catch (error: any) {
        console.error('Failed to resume async backtest job:', error);
        onError(error.response?.data?.detail || 'Failed to resume async backtest job');
      }
    },
    [onError, refreshJobs]
  );

  useEffect(() => {
    refreshJobs();
  }, [refreshJobs]);

  useEffect(() => {
    if (!activeJob || !ACTIVE_STATUSES.includes(activeJob.status)) {
      return;
    }

    const timeoutId = window.setTimeout(async () => {
      try {
        const nextJob = await apiClient.getBacktestJob(activeJob.job_id);
        setActiveJob(nextJob);
        if (nextJob.status === 'completed' && nextJob.run_id) {
          await syncCompletedJob(nextJob);
          await refreshJobs();
          onError(null);
          return;
        }
        if (nextJob.status === 'failed') {
          await refreshJobs();
          onError(nextJob.error || 'Async backtest job failed');
          return;
        }
        if (nextJob.status === 'cancelled') {
          await refreshJobs();
          onError('Async backtest job cancelled');
          return;
        }
      } catch (error) {
        console.error('Failed to poll async backtest job:', error);
        onError('Failed to refresh async backtest job');
      }
    }, 1500);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [activeJob, onError, refreshJobs, syncCompletedJob]);

  const isActiveJobRunning = useMemo(
    () => (activeJob ? ACTIVE_STATUSES.includes(activeJob.status) : false),
    [activeJob]
  );

  return {
    jobs,
    activeJob,
    isLoadingJobs,
    isSubmittingJob,
    isCancellingJob,
    isActiveJobRunning,
    startJob,
    openJob,
    refreshJobs,
    cancelActiveJob,
    resumeJob,
  };
}
