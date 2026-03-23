import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import { buildOptimizationPayload, OptimizationDraft } from '../lib/optimizationPayload';
import {
  OptimizationManifest,
  OptimizationPlan,
  OptimizationResultsPayload,
} from '../types/api';

const DEFAULT_GLOBAL_SPACE = JSON.stringify(
  {
    base_bet: { values: [250, 500, 750] },
    multiplier: { values: [1.5, 2.0, 2.5] },
  },
  null,
  2
);

const DEFAULT_STRATEGY_SPACE = JSON.stringify(
  {
    'Simple Martingale': {
      max_layers: { values: [3, 4, 5] },
      take_profit: { values: [0.1, 0.15, 0.2] },
    },
  },
  null,
  2
);

export function useOptimizations(
  selectedConfigPath: string | undefined,
  defaultStrategies: string[],
  onError: (message: string | null) => void
) {
  const [draft, setDraft] = useState<OptimizationDraft>({
    strategiesText: defaultStrategies.join(', '),
    globalSpaceText: DEFAULT_GLOBAL_SPACE,
    strategySpaceText: DEFAULT_STRATEGY_SPACE,
    mode: 'grid',
    objective: 'sharpe_ratio',
    direction: 'maximize',
    maxTrialsText: '12',
    seedText: '42',
  });
  const [plan, setPlan] = useState<OptimizationPlan | null>(null);
  const [latestExecution, setLatestExecution] = useState<OptimizationResultsPayload | null>(null);
  const [optimizations, setOptimizations] = useState<OptimizationManifest[]>([]);
  const [selectedOptimizationId, setSelectedOptimizationId] = useState<string | null>(null);
  const [selectedResults, setSelectedResults] = useState<OptimizationResultsPayload | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isLoadingOptimizations, setIsLoadingOptimizations] = useState(false);
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
      selectedOptimizationId
        ? optimizations.find((item) => item.optimization_id === selectedOptimizationId) ?? null
        : null,
    [optimizations, selectedOptimizationId]
  );

  const updateDraft = <K extends keyof OptimizationDraft>(key: K, value: OptimizationDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const refreshOptimizations = useCallback(async () => {
    setIsLoadingOptimizations(true);
    try {
      const response = await apiClient.listOptimizations();
      setOptimizations(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load persisted optimizations');
    } finally {
      setIsLoadingOptimizations(false);
    }
  }, [onError]);

  const previewPlan = async () => {
    if (!selectedConfigPath) {
      onError('Select a config before planning an optimization');
      return;
    }

    setIsPlanning(true);
    onError(null);
    try {
      const payload = buildOptimizationPayload(selectedConfigPath, defaultStrategies, draft);
      const response = await apiClient.planOptimization(payload);
      setPlan(response);
    } catch (error: any) {
      onError(error.message || error.response?.data?.detail || 'Failed to preview optimization');
    } finally {
      setIsPlanning(false);
    }
  };

  const runOptimization = async () => {
    if (!selectedConfigPath) {
      onError('Select a config before running an optimization');
      return;
    }

    setIsExecuting(true);
    onError(null);
    try {
      const payload = buildOptimizationPayload(selectedConfigPath, defaultStrategies, draft);
      const response = await apiClient.runOptimization(payload);
      setLatestExecution(response);
      setSelectedOptimizationId(response.optimization_id);
      setSelectedResults(response);
      await refreshOptimizations();
    } catch (error: any) {
      onError(error.message || error.response?.data?.detail || 'Failed to execute optimization');
    } finally {
      setIsExecuting(false);
    }
  };

  const loadOptimizationResults = async (optimizationId: string) => {
    setSelectedOptimizationId(optimizationId);
    setIsLoadingSelected(true);
    onError(null);
    try {
      const response = await apiClient.getOptimizationResults(optimizationId);
      setSelectedResults(response);
    } catch (error: any) {
      onError(
        error.response?.data?.detail || 'Failed to load persisted optimization results'
      );
    } finally {
      setIsLoadingSelected(false);
    }
  };

  useEffect(() => {
    refreshOptimizations();
  }, [refreshOptimizations]);

  return {
    draft,
    plan,
    latestExecution,
    optimizations,
    selectedOptimizationId,
    selectedManifest,
    selectedResults,
    isPlanning,
    isExecuting,
    isLoadingOptimizations,
    isLoadingSelected,
    canSubmit,
    updateDraft,
    previewPlan,
    runOptimization,
    refreshOptimizations,
    loadOptimizationResults,
  };
}
