import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  applyExperimentContextOverrides,
  inferExperimentContext,
  listExperimentContextCandidates,
  type ExperimentContextCandidates,
  type ExperimentContextTargets,
  type ExperimentContextOverrides,
} from '../lib/researchDrilldown';
import {
  ExperimentDetailPayload,
  ExperimentRegistryRecord,
  MonteCarloResultsPayload,
  OptimizationResultsPayload,
  WalkForwardResultsPayload,
} from '../types/api';

interface ExperimentContextDrilldownState {
  candidates: ExperimentContextCandidates;
  targets: ExperimentContextTargets;
  optimizationResults: OptimizationResultsPayload | null;
  walkForwardResults: WalkForwardResultsPayload | null;
  monteCarloResults: MonteCarloResultsPayload | null;
  isLoading: boolean;
}

const EMPTY_TARGETS: ExperimentContextTargets = {
  anchorRunId: null,
  optimization: null,
  walkforward: null,
  montecarlo: null,
};

const EMPTY_CANDIDATES: ExperimentContextCandidates = {
  optimization: [],
  walkforward: [],
  montecarlo: [],
};

export function useExperimentContextDrilldown(
  detail: ExperimentDetailPayload | null,
  experiments: ExperimentRegistryRecord[],
  overrides: ExperimentContextOverrides,
  onError: (message: string | null) => void
): ExperimentContextDrilldownState {
  const [candidates, setCandidates] = useState<ExperimentContextCandidates>(EMPTY_CANDIDATES);
  const [targets, setTargets] = useState<ExperimentContextTargets>(EMPTY_TARGETS);
  const [optimizationResults, setOptimizationResults] =
    useState<OptimizationResultsPayload | null>(null);
  const [walkForwardResults, setWalkForwardResults] =
    useState<WalkForwardResultsPayload | null>(null);
  const [monteCarloResults, setMonteCarloResults] =
    useState<MonteCarloResultsPayload | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!detail) {
      setCandidates(EMPTY_CANDIDATES);
      setTargets(EMPTY_TARGETS);
      setOptimizationResults(null);
      setWalkForwardResults(null);
      setMonteCarloResults(null);
      return;
    }

    const contextualCandidates = listExperimentContextCandidates(detail, experiments);
    const nextTargets = applyExperimentContextOverrides(
      inferExperimentContext(detail, experiments),
      contextualCandidates,
      overrides
    );
    setCandidates(contextualCandidates);
    setTargets(nextTargets);

    let isCancelled = false;
    setIsLoading(true);

    Promise.all([
      nextTargets.optimization
        ? apiClient.getOptimizationResults(nextTargets.optimization.experiment_id)
        : Promise.resolve(null),
      nextTargets.walkforward
        ? apiClient.getWalkForwardResults(nextTargets.walkforward.experiment_id)
        : Promise.resolve(null),
      nextTargets.montecarlo
        ? apiClient.getMonteCarloResults(nextTargets.montecarlo.experiment_id)
        : Promise.resolve(null),
    ])
      .then(([optimizationPayload, walkForwardPayload, monteCarloPayload]) => {
        if (!isCancelled) {
          setOptimizationResults(optimizationPayload);
          setWalkForwardResults(walkForwardPayload);
          setMonteCarloResults(monteCarloPayload);
        }
      })
      .catch((error: any) => {
        if (!isCancelled) {
          onError(error.response?.data?.detail || 'Failed to load contextual research comparison');
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [detail, experiments, onError, overrides]);

  return {
    candidates,
    targets,
    optimizationResults,
    walkForwardResults,
    monteCarloResults,
    isLoading,
  };
}
