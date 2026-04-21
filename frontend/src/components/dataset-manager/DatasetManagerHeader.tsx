import { Database, Loader2, RefreshCw, RotateCcw } from 'lucide-react';
import { DatasetManagerHeaderProps } from './types';

export default function DatasetManagerHeader({
  dueCount,
  isLoadingDatasets,
  isRefreshingDueDatasets,
  onRefreshDatasets,
  onRefreshDueDatasets,
}: DatasetManagerHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 mb-4">
      <div>
        <div className="flex items-center mb-2">
          <Database className="h-4 w-4 mr-2 text-cyan-600 dark:text-cyan-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Dataset Manager
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Inspect local datasets and apply one to the current backtest request.
        </p>
      </div>
      <div className="flex items-center gap-2">
        {dueCount > 0 && (
          <button
            type="button"
            onClick={onRefreshDueDatasets}
            disabled={isRefreshingDueDatasets}
            className="text-xs px-2 py-1 rounded bg-amber-100 text-amber-800 hover:bg-amber-200 dark:bg-amber-950/40 dark:text-amber-200 transition-colors disabled:opacity-50"
          >
            {isRefreshingDueDatasets ? (
              <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
            ) : (
              <RotateCcw className="h-3 w-3 inline mr-1" />
            )}
            Refresh Due ({dueCount})
          </button>
        )}
        <button
          type="button"
          onClick={onRefreshDatasets}
          disabled={isLoadingDatasets}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          {isLoadingDatasets ? (
            <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3 inline mr-1" />
          )}
          Refresh
        </button>
      </div>
    </div>
  );
}
