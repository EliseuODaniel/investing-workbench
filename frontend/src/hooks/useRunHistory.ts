import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  BacktestResponse,
  RunConfigSnapshot,
  RunDataProfile,
  RunSummary,
} from '../types/api';

export function useRunHistory(onError?: (message: string) => void) {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);

  const refreshRuns = useCallback(async () => {
    setIsLoadingRuns(true);
    try {
      const data = await apiClient.listRuns();
      setRuns(data);
    } catch (error) {
      console.error('Failed to load run history:', error);
      onError?.('Failed to load persisted runs');
    } finally {
      setIsLoadingRuns(false);
    }
  }, [onError]);

  useEffect(() => {
    refreshRuns();
  }, [refreshRuns]);

  const loadRunResponse = async (runId: string): Promise<BacktestResponse | null> => {
    try {
      return await apiClient.getRunResponse(runId);
    } catch (error) {
      console.error('Failed to load persisted run:', error);
      onError?.('Failed to load persisted run');
      return null;
    }
  };

  const loadRunArtifacts = async (
    runId: string
  ): Promise<{ configSnapshot: RunConfigSnapshot; dataProfile: RunDataProfile } | null> => {
    try {
      const [configSnapshot, dataProfile] = await Promise.all([
        apiClient.getRunConfig(runId),
        apiClient.getRunDataProfile(runId),
      ]);
      return { configSnapshot, dataProfile };
    } catch (error) {
      console.error('Failed to load persisted run artifacts:', error);
      onError?.('Failed to load persisted run artifacts');
      return null;
    }
  };

  return {
    runs,
    isLoadingRuns,
    refreshRuns,
    loadRunResponse,
    loadRunArtifacts,
  };
}
