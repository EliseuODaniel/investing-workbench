import type {
  BacktestResponse,
  PairsBacktestResultsPayload,
  SavedStrategySetupRunPayload,
  StrategySetupPlanPayload,
} from '../types/api';
import type { PairsSetupHandoff } from './pairsPayload';

export const SETUP_RUN_HISTORY_STORAGE_KEY =
  'investing-workbench.strategy-setup-runs.v1';

export type StrategySetupRunHistoryItem = SavedStrategySetupRunPayload;

export function buildPairsRunHistoryItem(
  plan: StrategySetupPlanPayload,
  response: PairsBacktestResultsPayload
): StrategySetupRunHistoryItem {
  const rankedScenario =
    response.scenarios
      .slice()
      .sort(
        (left, right) =>
          (right.metrics.return_total ?? Number.NEGATIVE_INFINITY) -
          (left.metrics.return_total ?? Number.NEGATIVE_INFINITY)
      )[0] || null;
  return {
    strategy_id: plan.strategy_id,
    pairs_backtest_id: response.pairs_backtest_id,
    ran_at: new Date().toISOString(),
    strategy_count: response.scenarios.length,
    best_strategy: rankedScenario?.label || rankedScenario?.scenario_id,
    total_return: rankedScenario?.metrics.return_total,
    max_drawdown: rankedScenario?.metrics.max_drawdown,
    trade_count: rankedScenario?.metrics.trade_count,
    route_hint: plan.route_hint,
  };
}

export function buildRunHistoryItem(
  plan: StrategySetupPlanPayload,
  response: BacktestResponse
): StrategySetupRunHistoryItem {
  const entries = Object.entries(response.results);
  const [bestStrategy, bestResult] =
    entries
      .slice()
      .sort(
        ([, left], [, right]) =>
          (right.metrics.total_return ?? Number.NEGATIVE_INFINITY) -
          (left.metrics.total_return ?? Number.NEGATIVE_INFINITY)
      )[0] || [];
  return {
    strategy_id: plan.strategy_id,
    run_id: response.run_info?.run_id,
    ran_at: new Date().toISOString(),
    strategy_count: entries.length,
    best_strategy: bestStrategy,
    total_return: bestResult?.metrics.total_return,
    max_drawdown: bestResult?.metrics.max_drawdown,
    trade_count: bestResult?.metrics.total_trades,
    route_hint: plan.route_hint,
  };
}

export function readSetupRunHistory(): StrategySetupRunHistoryItem[] {
  if (typeof window === 'undefined') {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(SETUP_RUN_HISTORY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isSetupRunHistoryItem);
  } catch {
    return [];
  }
}

export function writeSetupRunHistory(items: StrategySetupRunHistoryItem[]) {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(SETUP_RUN_HISTORY_STORAGE_KEY, JSON.stringify(items));
}

export function mergeSetupRunHistory(
  remote: StrategySetupRunHistoryItem[],
  local: StrategySetupRunHistoryItem[]
) {
  const byKey = new Map<string, StrategySetupRunHistoryItem>();
  [...local, ...remote].forEach((item) => {
    byKey.set(setupRunHistoryKey(item), item);
  });
  return Array.from(byKey.values()).sort((left, right) =>
    right.ran_at.localeCompare(left.ran_at)
  );
}

export function buildPairsDraftFromPlan(
  plan: StrategySetupPlanPayload
): Partial<PairsSetupHandoff['draft']> {
  const request = plan.run_request;
  const tickers = Array.isArray(request.tickers)
    ? request.tickers.map((item) => String(item)).join(', ')
    : '';
  return {
    presetId: String(request.preset_id || 'custom'),
    tickersText: tickers,
    formationWindowText: String(request.formation_window ?? 252),
    entryZscoreText: String(request.entry_zscore ?? 2),
    exitZscoreText: String(request.exit_zscore ?? 0.5),
    stopZscoreText: String(request.stop_zscore ?? 3.5),
  };
}

function isSetupRunHistoryItem(value: unknown): value is StrategySetupRunHistoryItem {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as Partial<StrategySetupRunHistoryItem>;
  return (
    typeof candidate.strategy_id === 'string' &&
    typeof candidate.ran_at === 'string' &&
    typeof candidate.strategy_count === 'number' &&
    typeof candidate.route_hint === 'string'
  );
}

function setupRunHistoryKey(item: StrategySetupRunHistoryItem): string {
  return `${item.strategy_id}:${item.run_id || item.pairs_backtest_id || item.ran_at}`;
}
