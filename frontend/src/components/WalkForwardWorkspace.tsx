import { Activity, CalendarRange, Loader2, RefreshCw } from 'lucide-react';
import { useWalkForward } from '../hooks/useWalkForward';
import { formatPercent } from '../lib/utils';

interface WalkForwardWorkspaceProps {
  selectedConfigPath?: string;
  defaultStrategies: string[];
  onError: (message: string | null) => void;
}

export default function WalkForwardWorkspace({
  selectedConfigPath,
  defaultStrategies,
  onError,
}: WalkForwardWorkspaceProps) {
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
    runWalkForward,
    loadWalkForwardResults,
  } = useWalkForward(selectedConfigPath, defaultStrategies, onError);

  const activeResults = selectedResults ?? latestExecution;

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center mb-2">
            <CalendarRange className="h-4 w-4 mr-2 text-sky-600 dark:text-sky-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Walk-Forward Lab
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Stress-test strategies across rolling train and test windows.
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
          Select a config in the sidebar before running walk-forward validation.
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
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Train Rows
              </label>
              <input
                value={draft.trainDaysText}
                onChange={(event) => updateDraft('trainDaysText', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Test Rows
              </label>
              <input
                value={draft.testDaysText}
                onChange={(event) => updateDraft('testDaysText', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
                Step Rows
              </label>
              <input
                value={draft.stepDaysText}
                onChange={(event) => updateDraft('stepDaysText', event.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
          </div>

          <button
            type="button"
            onClick={runWalkForward}
            disabled={!canSubmit || isExecuting}
            className="inline-flex items-center px-4 py-2 rounded-lg bg-sky-600 text-white text-sm font-medium hover:bg-sky-700 disabled:opacity-50"
          >
            {isExecuting ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Activity className="h-4 w-4 mr-2" />
            )}
            Run Walk-Forward
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
                  key={execution.walkforward_id}
                  type="button"
                  onClick={() => loadWalkForwardResults(execution.walkforward_id)}
                  className={`w-full text-left rounded-md px-3 py-3 border transition-colors ${
                    selectedExecutionId === execution.walkforward_id
                      ? 'border-sky-500 bg-sky-50 dark:border-sky-400 dark:bg-sky-950/30'
                      : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800'
                  }`}
                >
                  <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                    {execution.walkforward_id}
                  </div>
                  <div className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">
                    {execution.window_count} windows
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {execution.strategy_names.join(', ')}
                  </div>
                </button>
              ))}
              {executions.length === 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No persisted walk-forward jobs yet.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center mb-3">
              <CalendarRange className="h-4 w-4 mr-2 text-sky-600 dark:text-sky-400" />
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Validation Summary
              </h4>
            </div>

            {!activeResults ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Run or select a persisted job to inspect test-window behavior.
              </p>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Windows</div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {activeResults.window_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Train/Test</div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {activeResults.train_window_days}/{activeResults.test_window_days}
                    </div>
                  </div>
                </div>

                {selectedManifest && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                    {selectedManifest.walkforward_id}
                  </div>
                )}

                {isLoadingSelected && (
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Loading persisted walk-forward results...
                  </div>
                )}

                <div className="space-y-3">
                  {activeResults.strategy_summaries.map((summary) => (
                    <div
                      key={summary.strategy_name}
                      className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3"
                    >
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {summary.strategy_name}
                      </div>
                      <div className="mt-2 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-gray-300">
                        <div>Avg Train Return: {formatPercent(summary.avg_train_total_return)}</div>
                        <div>Avg Test Return: {formatPercent(summary.avg_test_total_return)}</div>
                        <div>Avg Test Sharpe: {summary.avg_test_sharpe_ratio.toFixed(2)}</div>
                        <div>Worst Test DD: {formatPercent(summary.worst_test_drawdown)}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="space-y-2">
                  {activeResults.results.slice(0, 3).map((result) => (
                    <div
                      key={`${result.window_id}-${result.strategy_name}`}
                      className="rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2"
                    >
                      <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        {result.window_id} · {result.strategy_name}
                      </div>
                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Test {new Date(result.test_start).toLocaleDateString()} to{' '}
                        {new Date(result.test_end).toLocaleDateString()}
                      </div>
                      <div className="mt-1 text-xs text-gray-600 dark:text-gray-300">
                        Return {formatPercent(result.test_metrics.total_return)} · Sharpe{' '}
                        {result.test_metrics.sharpe_ratio.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
