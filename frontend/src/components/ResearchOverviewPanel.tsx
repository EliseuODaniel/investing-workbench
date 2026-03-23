import {
  AlertTriangle,
  BrainCircuit,
  CalendarRange,
  Dices,
  Loader2,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { useResearchOverview } from '../hooks/useResearchOverview';
import {
  buildResearchTimeline,
  countResearchWarnings,
} from '../lib/researchOverview';
import { formatPercent } from '../lib/utils';

interface ResearchOverviewPanelProps {
  onError: (message: string | null) => void;
}

export default function ResearchOverviewPanel({
  onError,
}: ResearchOverviewPanelProps) {
  const {
    optimizations,
    walkForwardExecutions,
    monteCarloExecutions,
    isLoading,
    refresh,
  } = useResearchOverview(onError);

  const latestOptimization = optimizations[0] ?? null;
  const latestWalkForward = walkForwardExecutions[0] ?? null;
  const latestMonteCarlo = monteCarloExecutions[0] ?? null;
  const timeline = buildResearchTimeline(
    optimizations,
    walkForwardExecutions,
    monteCarloExecutions
  );
  const warningCount = countResearchWarnings(optimizations, monteCarloExecutions);

  return (
    <div className="card bg-gradient-to-br from-amber-50 via-white to-rose-50 dark:from-amber-950/20 dark:via-gray-800 dark:to-rose-950/20">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center mb-2">
            <Sparkles className="h-4 w-4 mr-2 text-amber-600 dark:text-amber-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Research Overview
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Unified view of persisted optimization, walk-forward, and Monte Carlo work.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={isLoading}
          className="text-xs px-2 py-1 rounded bg-white/80 dark:bg-gray-700 hover:bg-white dark:hover:bg-gray-600 transition-colors"
        >
          {isLoading ? (
            <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3 inline mr-1" />
          )}
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
        <div className="rounded-lg border border-indigo-200 dark:border-indigo-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400 mb-2">
            <BrainCircuit className="h-3 w-3 mr-1" />
            Optimizations
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {optimizations.length}
          </div>
          {latestOptimization && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Latest best: {latestOptimization.best_objective_value?.toFixed(3) ?? 'n/a'}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-sky-200 dark:border-sky-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-400 mb-2">
            <CalendarRange className="h-3 w-3 mr-1" />
            Walk-Forward
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {walkForwardExecutions.length}
          </div>
          {latestWalkForward && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Latest windows: {latestWalkForward.window_count}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-rose-200 dark:border-rose-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-rose-600 dark:text-rose-400 mb-2">
            <Dices className="h-3 w-3 mr-1" />
            Monte Carlo
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {monteCarloExecutions.length}
          </div>
          {latestMonteCarlo && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Latest sims: {latestMonteCarlo.simulation_count}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-amber-200 dark:border-amber-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-400 mb-2">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Warnings
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {warningCount}
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Persisted research warnings across latest jobs
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Latest Signals
          </h4>
          <div className="space-y-3 text-sm">
            <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="text-xs uppercase tracking-wide text-indigo-500 mb-1">
                Optimization
              </div>
              {latestOptimization ? (
                <div className="text-gray-700 dark:text-gray-200">
                  Best objective for <span className="font-medium">{latestOptimization.objective}</span>:{' '}
                  <span className="font-semibold">
                    {latestOptimization.best_objective_value?.toFixed(3) ?? 'n/a'}
                  </span>
                </div>
              ) : (
                <div className="text-gray-500 dark:text-gray-400">No persisted optimization yet.</div>
              )}
            </div>

            <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="text-xs uppercase tracking-wide text-sky-500 mb-1">
                Walk-Forward
              </div>
              {latestWalkForward?.strategy_summaries[0] ? (
                <div className="text-gray-700 dark:text-gray-200">
                  Avg test return for{' '}
                  <span className="font-medium">
                    {latestWalkForward.strategy_summaries[0].strategy_name}
                  </span>
                  :{' '}
                  <span className="font-semibold">
                    {formatPercent(
                      latestWalkForward.strategy_summaries[0].avg_test_total_return
                    )}
                  </span>
                </div>
              ) : (
                <div className="text-gray-500 dark:text-gray-400">No persisted walk-forward yet.</div>
              )}
            </div>

            <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="text-xs uppercase tracking-wide text-rose-500 mb-1">
                Monte Carlo
              </div>
              {latestMonteCarlo?.strategy_summaries[0] ? (
                <div className="text-gray-700 dark:text-gray-200">
                  Loss probability for{' '}
                  <span className="font-medium">
                    {latestMonteCarlo.strategy_summaries[0].strategy_name}
                  </span>
                  :{' '}
                  <span className="font-semibold">
                    {formatPercent(
                      latestMonteCarlo.strategy_summaries[0].loss_probability
                    )}
                  </span>
                </div>
              ) : (
                <div className="text-gray-500 dark:text-gray-400">No persisted Monte Carlo yet.</div>
              )}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Recent Research Timeline
          </h4>
          <div className="space-y-3">
            {timeline.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Run research jobs to build a persisted timeline here.
              </p>
            )}
            {timeline.map((entry) => (
              <div
                key={`${entry.type}-${entry.id}`}
                className="rounded-md border border-gray-200 dark:border-gray-700 px-3 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {entry.title}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(entry.createdAt).toLocaleString('pt-BR')}
                  </div>
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 font-mono">
                  {entry.id}
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  {entry.subtitle}
                </div>
                {entry.warnings.length > 0 && (
                  <div className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                    {entry.warnings.join(' | ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
