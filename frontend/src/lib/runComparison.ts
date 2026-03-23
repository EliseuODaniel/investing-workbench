import {
  ComparisonRun,
  ComparisonRunOverview,
  StrategyResult,
} from '../types/api';

function getBestStrategyEntry(results: Record<string, StrategyResult>): [string, StrategyResult] {
  const entries = Object.entries(results);
  if (entries.length === 0) {
    throw new Error('Cannot summarize a run without strategy results');
  }
  return entries.reduce((bestEntry, currentEntry) => {
    if (currentEntry[1].metrics.total_return > bestEntry[1].metrics.total_return) {
      return currentEntry;
    }
    return bestEntry;
  });
}

export function summarizeComparisonRun(run: ComparisonRun): ComparisonRunOverview {
  const [bestStrategyName, bestStrategy] = getBestStrategyEntry(run.response.results);
  const totalTrades = Object.values(run.response.results).reduce(
    (sum, strategy) => sum + strategy.trades.length,
    0
  );

  return {
    runId: run.summary.run_id,
    createdAt: run.summary.created_at,
    configPath: run.summary.config_path,
    strategyCount: Object.keys(run.response.results).length,
    totalTrades,
    bestStrategyName,
    bestReturn: bestStrategy.metrics.total_return,
    bestSharpe: bestStrategy.metrics.sharpe_ratio,
    bestDrawdown: bestStrategy.metrics.max_drawdown,
    dataFingerprint: run.summary.data_fingerprint,
  };
}
