import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import { buildMonteCarloPayload, MonteCarloDraft } from '../lib/monteCarloPayload';
import { MonteCarloManifest, MonteCarloResultsPayload } from '../types/api';

export function useMonteCarlo(
  selectedConfigPath: string | undefined,
  currentRunId: string | undefined,
  defaultStrategies: string[],
  onError: (message: string | null) => void
) {
  const [draft, setDraft] = useState<MonteCarloDraft>({
    sourceMode: currentRunId ? 'current-run' : 'config',
    strategiesText: defaultStrategies.join(', '),
    simulationsText: '250',
    seedText: '42',
    ruinThresholdText: '0.30',
    method: 'bootstrap',
  });
  const [latestExecution, setLatestExecution] = useState<MonteCarloResultsPayload | null>(null);
  const [executions, setExecutions] = useState<MonteCarloManifest[]>([]);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [selectedResults, setSelectedResults] = useState<MonteCarloResultsPayload | null>(null);
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

  useEffect(() => {
    if (currentRunId && draft.sourceMode === 'config') {
      return;
    }
    if (currentRunId) {
      setDraft((current) => ({ ...current, sourceMode: 'current-run' }));
    }
  }, [currentRunId, draft.sourceMode]);

  const canSubmit =
    draft.sourceMode === 'current-run' ? Boolean(currentRunId) : Boolean(selectedConfigPath);

  const selectedManifest = useMemo(
    () =>
      selectedExecutionId
        ? executions.find((item) => item.montecarlo_id === selectedExecutionId) ?? null
        : null,
    [executions, selectedExecutionId]
  );

  const updateDraft = <K extends keyof MonteCarloDraft>(key: K, value: MonteCarloDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const refreshExecutions = useCallback(async () => {
    setIsLoadingExecutions(true);
    try {
      const response = await apiClient.listMonteCarloExecutions();
      setExecutions(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load persisted Monte Carlo jobs');
    } finally {
      setIsLoadingExecutions(false);
    }
  }, [onError]);

  const runMonteCarlo = async () => {
    setIsExecuting(true);
    onError(null);
    try {
      const payload = buildMonteCarloPayload(
        selectedConfigPath,
        currentRunId,
        defaultStrategies,
        draft
      );
      const response = await apiClient.runMonteCarlo(payload);
      setLatestExecution(response);
      setSelectedExecutionId(response.montecarlo_id);
      setSelectedResults(response);
      await refreshExecutions();
    } catch (error: any) {
      onError(
        error.message || error.response?.data?.detail || 'Failed to execute Monte Carlo'
      );
    } finally {
      setIsExecuting(false);
    }
  };

  const loadMonteCarloResults = async (monteCarloId: string) => {
    setSelectedExecutionId(monteCarloId);
    setIsLoadingSelected(true);
    onError(null);
    try {
      const response = await apiClient.getMonteCarloResults(monteCarloId);
      setSelectedResults(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load persisted Monte Carlo results');
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
    runMonteCarlo,
    loadMonteCarloResults,
  };
}
