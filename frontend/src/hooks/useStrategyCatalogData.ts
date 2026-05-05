import { useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import { readSetupRunHistory, type StrategySetupRunHistoryItem } from '../lib/strategySetupHistory';
import type {
  BacktestStrategyCatalogPayload,
  StrategySetupScorePayload,
} from '../types/api';

type UseStrategyCatalogDataOptions = {
  hydrateSetupRuns: (
    remoteHistory: StrategySetupRunHistoryItem[],
    remoteScores: StrategySetupScorePayload[]
  ) => void;
};

export function useStrategyCatalogData({
  hydrateSetupRuns,
}: UseStrategyCatalogDataOptions) {
  const [catalog, setCatalog] = useState<BacktestStrategyCatalogPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const localHistory = readSetupRunHistory();
    apiClient
      .getBacktestStrategyCatalog()
      .then(async (payload) => {
        if (!isMounted) return;
        setCatalog(payload);
        setError(null);
        const remoteHistory = await apiClient
          .listSavedStrategySetupRuns()
          .catch(() => localHistory);
        if (!isMounted) return;
        const remoteScores = await apiClient.listStrategySetupScores().catch(() => []);
        if (!isMounted) return;
        hydrateSetupRuns(remoteHistory, remoteScores);
      })
      .catch((err: any) => {
        if (!isMounted) return;
        setError(err?.response?.data?.detail || 'Catalogo de estrategias indisponivel.');
      });
    return () => {
      isMounted = false;
    };
  }, [hydrateSetupRuns]);

  const familyCount = useMemo(() => {
    if (!catalog) return 0;
    return new Set(catalog.strategies.map((strategy) => strategy.family)).size;
  }, [catalog]);

  return { catalog, error, familyCount };
}
