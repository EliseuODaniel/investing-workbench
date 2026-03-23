import {
  Beaker,
  BrainCircuit,
  Loader2,
  PlayCircle,
  RefreshCw,
  Target,
} from 'lucide-react';
import { useOptimizations } from '../hooks/useOptimizations';
import { formatPercent } from '../lib/utils';

interface OptimizationWorkspaceProps {
  selectedConfigPath?: string;
  defaultStrategies: string[];
  onError: (message: string | null) => void;
}

export default function OptimizationWorkspace({
  selectedConfigPath,
  defaultStrategies,
  onError,
}: OptimizationWorkspaceProps) {
  const {
    draft,
    plan,
    latestExecution,
    optimizations,
    selectedOptimizationId,
    selectedManifest,
    selectedResults,
    isPlanning,
    isExecuting,
    isLoadingOptimizations,
    isLoadingSelected,
    canSubmit,
    updateDraft,
    previewPlan,
    runOptimization,
    refreshOptimizations,
    loadOptimizationResults,
  } = useOptimizations(selectedConfigPath, defaultStrategies, onError);

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center mb-2">
            <BrainCircuit className="h-4 w-4 mr-2 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Optimization Lab
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Preview and execute parameter searches against persisted backtest runs.
          </p>
        </div>
        <button
          type="button"
          onClick={refreshOptimizations}
          disabled={isLoadingOptimizations}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <RefreshCw className="h-3 w-3 inline mr-1" />
          Refresh Jobs
        </button>
      </div>

      {!canSubmit && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          Select a config in the sidebar before building an optimization plan.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="space-y-4">
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
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Comma or line-separated. Defaults to the strategies selected in the current form.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Objective
              </label>
              <select
                value={draft.objective}
                onChange={(event) => updateDraft('objective', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              >
                <option value="sharpe_ratio">Sharpe Ratio</option>
                <option value="total_return">Total Return</option>
                <option value="cagr">CAGR</option>
                <option value="max_drawdown">Max Drawdown</option>
                <option value="volatility">Volatility</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Direction
              </label>
              <select
                value={draft.direction}
                onChange={(event) =>
                  updateDraft('direction', event.target.value as 'maximize' | 'minimize')
                }
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              >
                <option value="maximize">Maximize</option>
                <option value="minimize">Minimize</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Mode
              </label>
              <select
                value={draft.mode}
                onChange={(event) => updateDraft('mode', event.target.value as 'grid' | 'random')}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              >
                <option value="grid">Grid</option>
                <option value="random">Random</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Max Trials
              </label>
              <input
                value={draft.maxTrialsText}
                onChange={(event) => updateDraft('maxTrialsText', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
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
              Global Search Space JSON
            </label>
            <textarea
              value={draft.globalSpaceText}
              onChange={(event) => updateDraft('globalSpaceText', event.target.value)}
              rows={10}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
              Strategy Overrides JSON
            </label>
            <textarea
              value={draft.strategySpaceText}
              onChange={(event) => updateDraft('strategySpaceText', event.target.value)}
              rows={10}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs font-mono"
            />
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={previewPlan}
              disabled={!canSubmit || isPlanning}
              className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {isPlanning ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Beaker className="h-4 w-4 mr-2" />}
              Preview Plan
            </button>
            <button
              type="button"
              onClick={runOptimization}
              disabled={!canSubmit || isExecuting}
              className="inline-flex items-center px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
            >
              {isExecuting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <PlayCircle className="h-4 w-4 mr-2" />
              )}
              Run Optimization
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center mb-3">
              <Target className="h-4 w-4 mr-2 text-indigo-600 dark:text-indigo-400" />
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Plan Preview
              </h4>
            </div>

            {!plan ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Preview a plan to inspect the generated trial space before execution.
              </p>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Trials</div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">{plan.trial_count}</div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Mode</div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">{plan.mode}</div>
                  </div>
                </div>
                {plan.warnings.length > 0 && (
                  <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-xs text-amber-800 dark:text-amber-200">
                    {plan.warnings.join(' | ')}
                  </div>
                )}
                <div className="space-y-2">
                  {plan.trials.slice(0, 4).map((trial) => (
                    <div
                      key={trial.trial_id}
                      className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-2"
                    >
                      <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                        {trial.trial_id}
                      </div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {trial.strategy_name}
                      </div>
                      <pre className="mt-2 text-xs text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                        {JSON.stringify(trial.parameters, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Persisted Optimization Jobs
              </h4>
              {isLoadingOptimizations && (
                <Loader2 className="h-4 w-4 animate-spin text-gray-500 dark:text-gray-400" />
              )}
            </div>

            {optimizations.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No optimization jobs yet.
              </p>
            ) : (
              <div className="space-y-2">
                {optimizations.slice(0, 6).map((optimization) => (
                  <button
                    key={optimization.optimization_id}
                    type="button"
                    onClick={() => loadOptimizationResults(optimization.optimization_id)}
                    className={`w-full text-left rounded-md border px-3 py-3 transition-colors ${
                      selectedOptimizationId === optimization.optimization_id
                        ? 'border-indigo-300 bg-indigo-50 dark:border-indigo-700 dark:bg-indigo-950/30'
                        : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                      {optimization.optimization_id}
                    </div>
                    <div className="mt-1 flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {optimization.objective}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {optimization.completed_trial_count}/{optimization.trial_count} trials
                      </div>
                    </div>
                    {optimization.best_objective_value !== null &&
                      optimization.best_objective_value !== undefined && (
                        <div className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                          Best: {optimization.best_objective_value.toFixed(4)}
                        </div>
                      )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {(latestExecution || selectedResults) && (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Optimization Results
                </h4>
                {isLoadingSelected && (
                  <Loader2 className="h-4 w-4 animate-spin text-gray-500 dark:text-gray-400" />
                )}
              </div>

              {selectedManifest && (
                <div className="mb-3 text-xs text-gray-500 dark:text-gray-400">
                  {selectedManifest.optimization_id} | {selectedManifest.direction} {selectedManifest.objective}
                </div>
              )}

              <div className="space-y-2">
                {(selectedResults ?? latestExecution)?.ranked_results.slice(0, 5).map((result) => (
                  <div
                    key={result.trial_id}
                    className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                          {result.trial_id}
                        </div>
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {result.strategy_name}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {result.objective}
                        </div>
                        <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                          {result.objective.includes('drawdown')
                            ? formatPercent(result.objective_value ?? 0)
                            : (result.objective_value ?? 0).toFixed(4)}
                        </div>
                      </div>
                    </div>
                    {result.run_id && (
                      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        Run: <span className="font-mono">{result.run_id}</span>
                      </div>
                    )}
                    <pre className="mt-2 text-xs text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                      {JSON.stringify(result.parameters, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
