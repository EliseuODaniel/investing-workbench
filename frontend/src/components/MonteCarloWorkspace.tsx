import {
  Activity,
  AlertTriangle,
  Dices,
  Loader2,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import { useMonteCarlo } from '../hooks/useMonteCarlo';
import { formatCurrency, formatPercent } from '../lib/utils';

interface MonteCarloWorkspaceProps {
  selectedConfigPath?: string;
  currentRunId?: string;
  defaultStrategies: string[];
  onError: (message: string | null) => void;
}

export default function MonteCarloWorkspace({
  selectedConfigPath,
  currentRunId,
  defaultStrategies,
  onError,
}: MonteCarloWorkspaceProps) {
  const {
    draft,
    latestExecution,
    executions,
    selectedExecutionId,
    selectedManifest,
    selectedResults,
    isExecuting,
    isLoadingExecutions,
    isLoadingSelected,
    canSubmit,
    updateDraft,
    refreshExecutions,
    runMonteCarlo,
    loadMonteCarloResults,
  } = useMonteCarlo(selectedConfigPath, currentRunId, defaultStrategies, onError);

  const activeResults = selectedResults ?? latestExecution;

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center mb-2">
            <Dices className="h-4 w-4 mr-2 text-rose-600 dark:text-rose-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Monte Carlo Lab
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Re-sample closed trades to inspect tail risk, loss probability, and drawdown stress.
          </p>
        </div>
        <button
          type="button"
          onClick={refreshExecutions}
          disabled={isLoadingExecutions}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <RefreshCw className="h-3 w-3 inline mr-1" />
          Refresh Jobs
        </button>
      </div>

      {!canSubmit && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          Load a persisted run or select a config before running Monte Carlo analysis.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => updateDraft('sourceMode', 'current-run')}
              className={`rounded-lg border px-3 py-2 text-sm ${
                draft.sourceMode === 'current-run'
                  ? 'border-rose-500 bg-rose-50 text-rose-700 dark:border-rose-400 dark:bg-rose-950/30 dark:text-rose-200'
                  : 'border-gray-200 text-gray-600 dark:border-gray-700 dark:text-gray-300'
              }`}
            >
              Current Run
            </button>
            <button
              type="button"
              onClick={() => updateDraft('sourceMode', 'config')}
              className={`rounded-lg border px-3 py-2 text-sm ${
                draft.sourceMode === 'config'
                  ? 'border-rose-500 bg-rose-50 text-rose-700 dark:border-rose-400 dark:bg-rose-950/30 dark:text-rose-200'
                  : 'border-gray-200 text-gray-600 dark:border-gray-700 dark:text-gray-300'
              }`}
            >
              Fresh Config Run
            </button>
          </div>

          <div className="rounded-lg bg-gray-50 dark:bg-gray-800 px-3 py-3 text-xs text-gray-600 dark:text-gray-300">
            {draft.sourceMode === 'current-run' ? (
              <span>
                Source run: <span className="font-mono">{currentRunId ?? 'none loaded'}</span>
              </span>
            ) : (
              <span>
                Source config: <span className="font-mono">{selectedConfigPath ?? 'none selected'}</span>
              </span>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
              Strategies
            </label>
            <input
              value={draft.strategiesText}
              onChange={(event) => updateDraft('strategiesText', event.target.value)}
              placeholder="Simple Martingale, Buy & Hold"
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Simulations
              </label>
              <input
                value={draft.simulationsText}
                onChange={(event) => updateDraft('simulationsText', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Random Seed
              </label>
              <input
                value={draft.seedText}
                onChange={(event) => updateDraft('seedText', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Method
              </label>
              <select
                value={draft.method}
                onChange={(event) => updateDraft('method', event.target.value as 'bootstrap' | 'shuffle')}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              >
                <option value="bootstrap">Bootstrap</option>
                <option value="shuffle">Shuffle</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Ruin Threshold
              </label>
              <input
                value={draft.ruinThresholdText}
                onChange={(event) => updateDraft('ruinThresholdText', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
          </div>

          <button
            type="button"
            onClick={runMonteCarlo}
            disabled={!canSubmit || isExecuting}
            className="inline-flex items-center px-4 py-2 rounded-lg bg-rose-600 text-white text-sm font-medium hover:bg-rose-700 disabled:opacity-50"
          >
            {isExecuting ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Activity className="h-4 w-4 mr-2" />
            )}
            Run Monte Carlo
          </button>

          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Persisted Jobs
              </h4>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {executions.length} total
              </span>
            </div>
            <div className="space-y-2 max-h-72 overflow-auto">
              {executions.map((execution) => (
                <button
                  key={execution.montecarlo_id}
                  type="button"
                  onClick={() => loadMonteCarloResults(execution.montecarlo_id)}
                  className={`w-full text-left rounded-md px-3 py-3 border transition-colors ${
                    selectedExecutionId === execution.montecarlo_id
                      ? 'border-rose-500 bg-rose-50 dark:border-rose-400 dark:bg-rose-950/30'
                      : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800'
                  }`}
                >
                  <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                    {execution.montecarlo_id}
                  </div>
                  <div className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">
                    {execution.simulation_count} simulations
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {execution.strategy_names.join(', ')}
                  </div>
                </button>
              ))}
              {executions.length === 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No persisted Monte Carlo jobs yet.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center mb-3">
              <ShieldAlert className="h-4 w-4 mr-2 text-rose-600 dark:text-rose-400" />
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Robustness Summary
              </h4>
            </div>

            {!activeResults ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Run or select a Monte Carlo job to inspect tail scenarios.
              </p>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Simulations</div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {activeResults.simulation_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Method</div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {activeResults.method}
                    </div>
                  </div>
                </div>

                <div className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                  Source run: {activeResults.source_run_id}
                </div>

                {selectedManifest && selectedManifest.warnings.length > 0 && (
                  <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-xs text-amber-800 dark:text-amber-200">
                    {selectedManifest.warnings.join(' | ')}
                  </div>
                )}

                {isLoadingSelected && (
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Loading persisted Monte Carlo results...
                  </div>
                )}

                <div className="space-y-3">
                  {activeResults.strategy_summaries.map((summary) => (
                    <div
                      key={summary.strategy_name}
                      className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {summary.strategy_name}
                        </div>
                        {summary.warnings.length > 0 && (
                          <AlertTriangle className="h-4 w-4 text-amber-500" />
                        )}
                      </div>
                      <div className="mt-2 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-gray-300">
                        <div>Loss Prob: {formatPercent(summary.loss_probability)}</div>
                        <div>Ruin Prob: {formatPercent(summary.ruin_probability)}</div>
                        <div>Median Return: {formatPercent(summary.median_total_return)}</div>
                        <div>95% DD Tail: {formatPercent(summary.percentile_95_max_drawdown)}</div>
                        <div>Worst Equity: {formatCurrency(summary.worst_final_equity)}</div>
                        <div>Best Equity: {formatCurrency(summary.best_final_equity)}</div>
                      </div>
                      {summary.warnings.length > 0 && (
                        <div className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                          {summary.warnings.join(' | ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {activeResults.results[0] && (
                  <div className="space-y-2">
                    {activeResults.results[0].simulations.slice(0, 3).map((simulation) => (
                      <div
                        key={simulation.simulation_number}
                        className="rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2"
                      >
                        <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
                          Simulation #{simulation.simulation_number}
                        </div>
                        <div className="mt-1 text-xs text-gray-600 dark:text-gray-300">
                          Final {formatCurrency(simulation.final_equity)} · Return{' '}
                          {formatPercent(simulation.total_return)} · Drawdown{' '}
                          {formatPercent(simulation.max_drawdown)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
