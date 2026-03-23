import {
  AlertTriangle,
  BrainCircuit,
  CalendarRange,
  Dices,
  Loader2,
  Link2,
  RefreshCw,
} from 'lucide-react';
import { useResearchDrilldown } from '../hooks/useResearchDrilldown';
import { summarizeResearchAlignment } from '../lib/researchDrilldown';
import { formatCurrency, formatPercent } from '../lib/utils';

interface ResearchDrilldownPanelProps {
  onError: (message: string | null) => void;
}

export default function ResearchDrilldownPanel({
  onError,
}: ResearchDrilldownPanelProps) {
  const {
    latestOptimization,
    latestWalkForward,
    latestMonteCarlo,
    optimizationResults,
    walkForwardResults,
    monteCarloResults,
    isLoading,
    refresh,
  } = useResearchDrilldown(onError);

  const alignment = summarizeResearchAlignment(
    optimizationResults,
    walkForwardResults,
    monteCarloResults
  );
  const bestTrial = optimizationResults?.ranked_results[0] ?? null;
  const walkForwardSummary = walkForwardResults?.strategy_summaries[0] ?? null;
  const monteCarloSummary = monteCarloResults?.strategy_summaries[0] ?? null;

  if (
    !isLoading &&
    !latestOptimization &&
    !latestWalkForward &&
    !latestMonteCarlo
  ) {
    return null;
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center mb-2">
            <Link2 className="h-4 w-4 mr-2 text-violet-600 dark:text-violet-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Research Drilldown
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Cross-check return optimization against out-of-sample behavior and Monte Carlo tail risk.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={isLoading}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          {isLoading ? (
            <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3 inline mr-1" />
          )}
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <div className="rounded-lg border border-indigo-200 dark:border-indigo-900 p-4 bg-indigo-50/40 dark:bg-indigo-950/10">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400 mb-2">
            <BrainCircuit className="h-3 w-3 mr-1" />
            Best Optimization Trial
          </div>
          {bestTrial ? (
            <div className="space-y-2 text-sm">
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {bestTrial.strategy_name}
              </div>
              <div className="text-gray-600 dark:text-gray-300">
                Objective: {bestTrial.objective_value?.toFixed(3) ?? 'n/a'}
              </div>
              <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                {latestOptimization?.optimization_id}
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400">No optimization result yet.</div>
          )}
        </div>

        <div className="rounded-lg border border-sky-200 dark:border-sky-900 p-4 bg-sky-50/40 dark:bg-sky-950/10">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-400 mb-2">
            <CalendarRange className="h-3 w-3 mr-1" />
            Out-of-Sample
          </div>
          {walkForwardSummary ? (
            <div className="space-y-2 text-sm">
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {walkForwardSummary.strategy_name}
              </div>
              <div className="text-gray-600 dark:text-gray-300">
                Avg test return: {formatPercent(walkForwardSummary.avg_test_total_return)}
              </div>
              <div className="text-gray-600 dark:text-gray-300">
                Worst DD: {formatPercent(walkForwardSummary.worst_test_drawdown)}
              </div>
              <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                {latestWalkForward?.walkforward_id}
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400">No walk-forward result yet.</div>
          )}
        </div>

        <div className="rounded-lg border border-rose-200 dark:border-rose-900 p-4 bg-rose-50/40 dark:bg-rose-950/10">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-rose-600 dark:text-rose-400 mb-2">
            <Dices className="h-3 w-3 mr-1" />
            Tail Risk
          </div>
          {monteCarloSummary ? (
            <div className="space-y-2 text-sm">
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {monteCarloSummary.strategy_name}
              </div>
              <div className="text-gray-600 dark:text-gray-300">
                Loss prob: {formatPercent(monteCarloSummary.loss_probability)}
              </div>
              <div className="text-gray-600 dark:text-gray-300">
                Worst equity: {formatCurrency(monteCarloSummary.worst_final_equity)}
              </div>
              <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                {latestMonteCarlo?.montecarlo_id}
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400">No Monte Carlo result yet.</div>
          )}
        </div>

        <div className="rounded-lg border border-violet-200 dark:border-violet-900 p-4 bg-violet-50/40 dark:bg-violet-950/10">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-violet-600 dark:text-violet-400 mb-2">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Alignment
          </div>
          <div className="space-y-2 text-sm">
            <div className="font-medium text-gray-900 dark:text-gray-100">
              {alignment.runLinkAligned ? 'Runs aligned' : 'Runs not aligned'}
            </div>
            <div className="text-gray-600 dark:text-gray-300">
              OOS avg return: {alignment.walkForwardAvgTestReturn !== null ? formatPercent(alignment.walkForwardAvgTestReturn) : 'n/a'}
            </div>
            <div className="text-gray-600 dark:text-gray-300">
              Ruin prob: {alignment.monteCarloRuinProbability !== null ? formatPercent(alignment.monteCarloRuinProbability) : 'n/a'}
            </div>
            <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
              {alignment.bestRunId ?? 'no linked run'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
