import { useCallback, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  PAIRS_SETUP_HANDOFF_STORAGE_KEY,
  type PairsSetupHandoff,
} from '../lib/pairsPayload';
import {
  buildPairsDraftFromPlan,
  buildPairsRunHistoryItem,
  buildRunHistoryItem,
  mergeSetupRunHistory,
  readSetupRunHistory,
  type StrategySetupRunHistoryItem,
  writeSetupRunHistory,
} from '../lib/strategySetupHistory';
import type { SavedStrategyRadarItem } from './useSavedStrategyRadar';
import type {
  BacktestRequest,
  BacktestResponse,
  PairsBacktestRequestPayload,
  PairsBacktestResultsPayload,
  StrategySetupScorePayload,
  StrategySetupPlanPayload,
} from '../types/api';

const NAVIGATE_ADVANCED_EVENT = 'investing-workbench:navigate-advanced-tool';

export function useStrategySetupExecution() {
  const [setupPlans, setSetupPlans] = useState<Record<string, StrategySetupPlanPayload>>({});
  const [setupRunResults, setSetupRunResults] = useState<Record<string, BacktestResponse>>({});
  const [loadedRunResponses, setLoadedRunResponses] = useState<Record<string, BacktestResponse>>(
    {}
  );
  const [loadedPairsBacktestResults, setLoadedPairsBacktestResults] = useState<
    Record<string, PairsBacktestResultsPayload>
  >({});
  const [pairsRunResults, setPairsRunResults] = useState<
    Record<string, PairsBacktestResultsPayload>
  >({});
  const [setupRunErrors, setSetupRunErrors] = useState<Record<string, string>>({});
  const [handoffMessages, setHandoffMessages] = useState<Record<string, string>>({});
  const [loadingRunId, setLoadingRunId] = useState<string | null>(null);
  const [loadingPairsBacktestId, setLoadingPairsBacktestId] = useState<string | null>(null);
  const [setupRunHistory, setSetupRunHistory] = useState<StrategySetupRunHistoryItem[]>(() =>
    readSetupRunHistory()
  );
  const [remoteSetupScores, setRemoteSetupScores] = useState<StrategySetupScorePayload[]>([]);
  const [planningStrategyId, setPlanningStrategyId] = useState<string | null>(null);
  const [runningStrategyId, setRunningStrategyId] = useState<string | null>(null);

  const hydrateSetupRuns = useCallback(
    (
      remoteHistory: StrategySetupRunHistoryItem[],
      remoteScores: StrategySetupScorePayload[]
    ) => {
      const mergedHistory = mergeSetupRunHistory(remoteHistory, readSetupRunHistory());
      setSetupRunHistory(mergedHistory);
      writeSetupRunHistory(mergedHistory);
      setRemoteSetupScores(remoteScores);
    },
    []
  );

  const prepareSetupPlan = useCallback(async (item: SavedStrategyRadarItem) => {
    setPlanningStrategyId(item.strategy_id);
    try {
      const plan = await apiClient.buildStrategySetupPlan(item);
      setSetupPlans((current) => ({ ...current, [item.strategy_id]: plan }));
    } finally {
      setPlanningStrategyId(null);
    }
  }, []);

  const runCoreBacktestSetup = useCallback(
    async (plan: StrategySetupPlanPayload): Promise<StrategySetupRunHistoryItem> => {
      const response = await apiClient.runBacktest(plan.run_request as BacktestRequest);
      setSetupRunResults((current) => ({ ...current, [plan.strategy_id]: response }));
      return buildRunHistoryItem(plan, response);
    },
    []
  );

  const runPairsSetup = useCallback(
    async (plan: StrategySetupPlanPayload): Promise<StrategySetupRunHistoryItem> => {
      const response = await apiClient.runPairsBacktest(
        plan.run_request as PairsBacktestRequestPayload
      );
      setPairsRunResults((current) => ({ ...current, [plan.strategy_id]: response }));
      return buildPairsRunHistoryItem(plan, response);
    },
    []
  );

  const runPreparedSetup = useCallback(
    async (plan: StrategySetupPlanPayload) => {
      if (plan.route_hint !== '/backtest' && plan.route_hint !== '/pairs/backtests') {
        setSetupRunErrors((current) => ({
          ...current,
          [plan.strategy_id]: 'Este setup usa o laboratorio avancado indicado no plano.',
        }));
        return;
      }
      setRunningStrategyId(plan.strategy_id);
      setSetupRunErrors((current) => {
        const next = { ...current };
        delete next[plan.strategy_id];
        return next;
      });
      try {
        const historyItem =
          plan.route_hint === '/pairs/backtests'
            ? await runPairsSetup(plan)
            : await runCoreBacktestSetup(plan);
        setSetupRunHistory((current) => {
          const next = [historyItem, ...current].slice(0, 30);
          writeSetupRunHistory(next);
          void apiClient.saveStrategySetupRun(historyItem).catch(() => undefined);
          void apiClient
            .listStrategySetupScores()
            .then((scores) => setRemoteSetupScores(scores))
            .catch(() => undefined);
          return next;
        });
      } catch (err: any) {
        setSetupRunErrors((current) => ({
          ...current,
          [plan.strategy_id]:
            err?.response?.data?.detail || 'Nao foi possivel executar este setup.',
        }));
      } finally {
        setRunningStrategyId(null);
      }
    },
    [runCoreBacktestSetup, runPairsSetup]
  );

  const loadRunResponse = useCallback(async (runId: string) => {
    setLoadingRunId(runId);
    try {
      const response = await apiClient.getRunResponse(runId);
      setLoadedRunResponses((current) => ({ ...current, [runId]: response }));
    } finally {
      setLoadingRunId(null);
    }
  }, []);

  const loadPairsBacktestResults = useCallback(async (pairsBacktestId: string) => {
    setLoadingPairsBacktestId(pairsBacktestId);
    try {
      const response = await apiClient.getPairsBacktestResults(pairsBacktestId);
      setLoadedPairsBacktestResults((current) => ({
        ...current,
        [pairsBacktestId]: response,
      }));
    } finally {
      setLoadingPairsBacktestId(null);
    }
  }, []);

  const sendPairsHandoff = useCallback((plan: StrategySetupPlanPayload) => {
    const handoff: PairsSetupHandoff = {
      source: 'strategy_setup_radar',
      strategy_id: plan.strategy_id,
      label: plan.label,
      created_at: new Date().toISOString(),
      draft: buildPairsDraftFromPlan(plan),
    };
    window.localStorage.setItem(PAIRS_SETUP_HANDOFF_STORAGE_KEY, JSON.stringify(handoff));
    window.dispatchEvent(
      new CustomEvent(NAVIGATE_ADVANCED_EVENT, { detail: { tool: 'pairs' } })
    );
    setHandoffMessages((current) => ({
      ...current,
      [plan.strategy_id]: 'Setup enviado para o laboratorio de Pairs.',
    }));
  }, []);

  return {
    setupPlans,
    setupRunResults,
    loadedRunResponses,
    loadedPairsBacktestResults,
    pairsRunResults,
    setupRunErrors,
    handoffMessages,
    loadingRunId,
    loadingPairsBacktestId,
    setupRunHistory,
    remoteSetupScores,
    planningStrategyId,
    runningStrategyId,
    hydrateSetupRuns,
    prepareSetupPlan,
    runPreparedSetup,
    loadRunResponse,
    loadPairsBacktestResults,
    sendPairsHandoff,
  };
}
