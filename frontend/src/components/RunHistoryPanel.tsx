import { History, RefreshCw } from 'lucide-react';
import { RunSummary } from '../types/api';

interface RunHistoryPanelProps {
  runs: RunSummary[];
  isLoading: boolean;
  onRefresh: () => void;
  onLoadRun: (runId: string) => void;
  selectedRunIds: string[];
  onToggleCompare: (runId: string) => void;
}

export default function RunHistoryPanel({
  runs,
  isLoading,
  onRefresh,
  onLoadRun,
  selectedRunIds,
  onToggleCompare,
}: RunHistoryPanelProps) {
  return (
    <div className="card mt-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <History className="h-4 w-4 mr-2" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Resultados recentes
          </h3>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          disabled={isLoading}
        >
          <RefreshCw className="h-3 w-3 inline mr-1" />
          Atualizar
        </button>
      </div>

      {runs.length === 0 ? (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Nenhum resultado salvo ainda.
        </div>
      ) : (
        <div className="space-y-3">
          {runs.slice(0, 8).map((run) => (
            <div
              key={run.run_id}
              className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <button type="button" onClick={() => onLoadRun(run.run_id)} className="w-full text-left">
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
                  Base: {run.data_fingerprint.slice(0, 12)}
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
              <button
                type="button"
                onClick={() => onToggleCompare(run.run_id)}
                className={`mt-3 text-xs px-2 py-1 rounded transition-colors ${
                  selectedRunIds.includes(run.run_id)
                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200'
                }`}
              >
                {selectedRunIds.includes(run.run_id) ? 'Selecionado para comparar' : 'Comparar'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
