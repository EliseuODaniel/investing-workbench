import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  MonteCarloManifest,
  OptimizationManifest,
  WalkForwardManifest,
} from '../types/api';

export function useResearchOverview(onError: (message: string | null) => void) {
  const [optimizations, setOptimizations] = useState<OptimizationManifest[]>([]);
  const [walkForwardExecutions, setWalkForwardExecutions] = useState<WalkForwardManifest[]>([]);
  const [monteCarloExecutions, setMonteCarloExecutions] = useState<MonteCarloManifest[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [optimizationResponse, walkForwardResponse, monteCarloResponse] =
        await Promise.all([
          apiClient.listOptimizations(),
          apiClient.listWalkForwardExecutions(),
          apiClient.listMonteCarloExecutions(),
        ]);

      setOptimizations(optimizationResponse);
      setWalkForwardExecutions(walkForwardResponse);
      setMonteCarloExecutions(monteCarloResponse);
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
    optimizations,
    walkForwardExecutions,
    monteCarloExecutions,
    isLoading,
    refresh,
  };
}
