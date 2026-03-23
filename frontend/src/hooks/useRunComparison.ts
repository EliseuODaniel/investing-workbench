import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { ComparisonRun, RunSummary } from '../types/api';

const MAX_SELECTED_RUNS = 3;

export function useRunComparison(runs: RunSummary[], onError?: (message: string) => void) {
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [comparisonRuns, setComparisonRuns] = useState<ComparisonRun[]>([]);
  const [isLoadingComparison, setIsLoadingComparison] = useState(false);

  useEffect(() => {
    if (selectedRunIds.length === 0) {
      setComparisonRuns([]);
      return;
    }

    let isCancelled = false;

    async function loadComparisonRuns() {
      setIsLoadingComparison(true);
      try {
        const loadedRuns = await Promise.all(
          selectedRunIds.map(async (runId) => {
            const summary = runs.find((candidate) => candidate.run_id === runId);
            if (!summary) {
              throw new Error(`Run not found in history: ${runId}`);
            }

            const response = await apiClient.getRunResponse(runId);
            return { summary, response };
          })
        );

        if (!isCancelled) {
          setComparisonRuns(loadedRuns);
        }
      } catch (error) {
        console.error('Failed to load comparison runs:', error);
        if (!isCancelled) {
          setComparisonRuns([]);
        }
        onError?.('Failed to load comparison runs');
      } finally {
        if (!isCancelled) {
          setIsLoadingComparison(false);
        }
      }
    }

    loadComparisonRuns();

    return () => {
      isCancelled = true;
    };
  }, [onError, runs, selectedRunIds]);

  const toggleRunSelection = (runId: string) => {
    setSelectedRunIds((previous) => {
      if (previous.includes(runId)) {
        return previous.filter((candidate) => candidate !== runId);
      }

      if (previous.length >= MAX_SELECTED_RUNS) {
        onError?.('Select at most 3 runs for comparison');
        return previous;
      }

      return [...previous, runId];
    });
  };

  const clearComparison = () => {
    setSelectedRunIds([]);
    setComparisonRuns([]);
  };

  return {
    selectedRunIds,
    comparisonRuns,
    isLoadingComparison,
    toggleRunSelection,
    clearComparison,
  };
}
