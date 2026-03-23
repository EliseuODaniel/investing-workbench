import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import { buildWalkForwardPayload, WalkForwardDraft } from '../lib/walkForwardPayload';
import { WalkForwardManifest, WalkForwardResultsPayload } from '../types/api';

export function useWalkForward(
  selectedConfigPath: string | undefined,
  defaultStrategies: string[],
  onError: (message: string | null) => void
) {
  const [draft, setDraft] = useState<WalkForwardDraft>({
    strategiesText: defaultStrategies.join(', '),
    trainDaysText: '90',
    testDaysText: '30',
    stepDaysText: '30',
  });
  const [latestExecution, setLatestExecution] = useState<WalkForwardResultsPayload | null>(null);
  const [executions, setExecutions] = useState<WalkForwardManifest[]>([]);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [selectedResults, setSelectedResults] = useState<WalkForwardResultsPayload | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isLoadingExecutions, setIsLoadingExecutions] = useState(false);
  const [isLoadingSelected, setIsLoadingSelected] = useState(false);

  useEffect(() => {
    if (!draft.strategiesText.trim() && defaultStrategies.length > 0) {
      setDraft((current) => ({
        ...current,
        strategiesText: defaultStrategies.join(', '),
      }));
    }
  }, [defaultStrategies, draft.strategiesText]);

  const canSubmit = Boolean(selectedConfigPath);

  const selectedManifest = useMemo(
    () =>
      selectedExecutionId
        ? executions.find((item) => item.walkforward_id === selectedExecutionId) ?? null
        : null,
    [executions, selectedExecutionId]
  );

  const updateDraft = <K extends keyof WalkForwardDraft>(key: K, value: WalkForwardDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const refreshExecutions = useCallback(async () => {
    setIsLoadingExecutions(true);
    try {
      const response = await apiClient.listWalkForwardExecutions();
      setExecutions(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load persisted walk-forward jobs');
    } finally {
      setIsLoadingExecutions(false);
    }
  }, [onError]);

  const runWalkForward = async () => {
    if (!selectedConfigPath) {
      onError('Select a config before running walk-forward validation');
      return;
    }

    setIsExecuting(true);
    onError(null);
    try {
      const payload = buildWalkForwardPayload(selectedConfigPath, defaultStrategies, draft);
      const response = await apiClient.runWalkForward(payload);
      setLatestExecution(response);
      setSelectedExecutionId(response.walkforward_id);
      setSelectedResults(response);
      await refreshExecutions();
    } catch (error: any) {
      onError(error.message || error.response?.data?.detail || 'Failed to execute walk-forward');
    } finally {
      setIsExecuting(false);
    }
  };

  const loadWalkForwardResults = async (walkforwardId: string) => {
    setSelectedExecutionId(walkforwardId);
    setIsLoadingSelected(true);
    onError(null);
    try {
      const response = await apiClient.getWalkForwardResults(walkforwardId);
      setSelectedResults(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load persisted walk-forward results');
    } finally {
      setIsLoadingSelected(false);
    }
  };

  useEffect(() => {
    refreshExecutions();
  }, [refreshExecutions]);

  return {
    draft,
    latestExecution,
    executions,
    selectedExecutionId,
    selectedManifest,
    selectedResults,
    isExecuting,
    isLoadingExecutions,
    isLoadingSelected,
    canSubmit,
    updateDraft,
    refreshExecutions,
    runWalkForward,
    loadWalkForwardResults,
  };
}
