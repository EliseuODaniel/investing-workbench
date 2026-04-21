import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  ExperimentRegistryRecord,
  MonteCarloManifest,
  OptimizationManifest,
  WalkForwardManifest,
} from '../types/api';

export function useResearchOverview(onError: (message: string | null) => void) {
  const [experiments, setExperiments] = useState<ExperimentRegistryRecord[]>([]);
  const [optimizations, setOptimizations] = useState<OptimizationManifest[]>([]);
  const [walkForwardExecutions, setWalkForwardExecutions] = useState<WalkForwardManifest[]>([]);
  const [monteCarloExecutions, setMonteCarloExecutions] = useState<MonteCarloManifest[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [experimentResponse, optimizationResponse, walkForwardResponse, monteCarloResponse] =
        await Promise.all([
          apiClient.listExperiments(),
          apiClient.listOptimizations(),
          apiClient.listWalkForwardExecutions(),
          apiClient.listMonteCarloExecutions(),
        ]);

      setExperiments(experimentResponse);
      setOptimizations(optimizationResponse);
      setWalkForwardExecutions(walkForwardResponse);
      setMonteCarloExecutions(monteCarloResponse);
      onError(null);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load research overview');
    } finally {
      setIsLoading(false);
    }
  }, [onError]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    experiments,
    optimizations,
    walkForwardExecutions,
    monteCarloExecutions,
    isLoading,
    refresh,
  };
}
