import { CalendarRange } from 'lucide-react';
import { formatPercent } from '../../lib/utils';
import { WalkForwardSummaryPanelProps } from './types';

export default function WalkForwardSummaryPanel({
  activeResults,
  selectedManifest,
  isLoadingSelected,
}: WalkForwardSummaryPanelProps) {
  return (
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
  );
}
