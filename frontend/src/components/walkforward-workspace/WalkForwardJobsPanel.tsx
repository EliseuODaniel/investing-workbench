import { WalkForwardJobsPanelProps } from './types';

export default function WalkForwardJobsPanel({
  executions,
  selectedExecutionId,
  onLoadExecution,
}: WalkForwardJobsPanelProps) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Persisted Jobs</h4>
        <span className="text-xs text-gray-500 dark:text-gray-400">{executions.length} total</span>
      </div>
      <div className="space-y-2 max-h-72 overflow-auto">
        {executions.map((execution) => (
          <button
            key={execution.walkforward_id}
            type="button"
            onClick={() => onLoadExecution(execution.walkforward_id)}
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
  );
}
