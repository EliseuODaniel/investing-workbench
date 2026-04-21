import { Loader2 } from 'lucide-react';
import { OptimizationJobsPanelProps } from './types';

export default function OptimizationJobsPanel({
  optimizations,
  selectedOptimizationId,
  isLoadingOptimizations,
  onLoadOptimization,
}: OptimizationJobsPanelProps) {
  return (
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
        <p className="text-sm text-gray-500 dark:text-gray-400">No optimization jobs yet.</p>
      ) : (
        <div className="space-y-2">
          {optimizations.slice(0, 6).map((optimization) => (
            <button
              key={optimization.optimization_id}
              type="button"
              onClick={() => onLoadOptimization(optimization.optimization_id)}
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
  );
}
