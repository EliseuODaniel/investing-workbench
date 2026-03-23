import { History, RefreshCw } from 'lucide-react';
import { RunSummary } from '../types/api';

interface RunHistoryPanelProps {
  runs: RunSummary[];
  isLoading: boolean;
  onRefresh: () => void;
  onLoadRun: (runId: string) => void;
}

export default function RunHistoryPanel({
  runs,
  isLoading,
  onRefresh,
  onLoadRun,
}: RunHistoryPanelProps) {
  return (
    <div className="card mt-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <History className="h-4 w-4 mr-2" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Recent Runs
          </h3>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          disabled={isLoading}
        >
          <RefreshCw className="h-3 w-3 inline mr-1" />
          Refresh
        </button>
      </div>

      {runs.length === 0 ? (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          No persisted runs yet.
        </div>
      ) : (
        <div className="space-y-3">
          {runs.slice(0, 8).map((run) => (
            <button
              key={run.run_id}
              type="button"
              onClick={() => onLoadRun(run.run_id)}
              className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="text-xs font-mono text-gray-500 dark:text-gray-400 mb-1">
                {run.run_id}
              </div>
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {run.config_path}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {new Date(run.created_at).toLocaleString('pt-BR')}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Data: {run.data_fingerprint.slice(0, 12)}
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {run.strategy_names.slice(0, 3).map((strategy) => (
                  <span
                    key={strategy}
                    className="px-2 py-1 rounded-full text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                  >
                    {strategy}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
