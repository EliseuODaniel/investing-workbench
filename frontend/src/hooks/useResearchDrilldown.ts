import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  MonteCarloManifest,
  MonteCarloResultsPayload,
  OptimizationManifest,
  OptimizationResultsPayload,
  WalkForwardManifest,
  WalkForwardResultsPayload,
} from '../types/api';

export function useResearchDrilldown(onError: (message: string | null) => void) {
  const [latestOptimization, setLatestOptimization] = useState<OptimizationManifest | null>(null);
  const [latestWalkForward, setLatestWalkForward] = useState<WalkForwardManifest | null>(null);
  const [latestMonteCarlo, setLatestMonteCarlo] = useState<MonteCarloManifest | null>(null);
  const [optimizationResults, setOptimizationResults] =
    useState<OptimizationResultsPayload | null>(null);
  const [walkForwardResults, setWalkForwardResults] =
    useState<WalkForwardResultsPayload | null>(null);
  const [monteCarloResults, setMonteCarloResults] =
    useState<MonteCarloResultsPayload | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [optimizations, walkForwards, monteCarlos] = await Promise.all([
        apiClient.listOptimizations(),
        apiClient.listWalkForwardExecutions(),
        apiClient.listMonteCarloExecutions(),
      ]);

      const latestOptimizationManifest = optimizations[0] ?? null;
      const latestWalkForwardManifest = walkForwards[0] ?? null;
      const latestMonteCarloManifest = monteCarlos[0] ?? null;

      setLatestOptimization(latestOptimizationManifest);
      setLatestWalkForward(latestWalkForwardManifest);
      setLatestMonteCarlo(latestMonteCarloManifest);

      const [optimizationPayload, walkForwardPayload, monteCarloPayload] = await Promise.all([
        latestOptimizationManifest
          ? apiClient.getOptimizationResults(latestOptimizationManifest.optimization_id)
          : Promise.resolve(null),
        latestWalkForwardManifest
          ? apiClient.getWalkForwardResults(latestWalkForwardManifest.walkforward_id)
          : Promise.resolve(null),
        latestMonteCarloManifest
          ? apiClient.getMonteCarloResults(latestMonteCarloManifest.montecarlo_id)
          : Promise.resolve(null),
      ]);

      setOptimizationResults(optimizationPayload);
      setWalkForwardResults(walkForwardPayload);
      setMonteCarloResults(monteCarloPayload);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load research drilldown');
    } finally {
      setIsLoading(false);
    }
  }, [onError]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    latestOptimization,
    latestWalkForward,
    latestMonteCarlo,
    optimizationResults,
    walkForwardResults,
    monteCarloResults,
    isLoading,
    refresh,
  };
}
