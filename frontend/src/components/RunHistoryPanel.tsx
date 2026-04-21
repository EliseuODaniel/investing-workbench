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
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                    {run.run_id}
                  </div>
                  {run.run_quality?.status === 'legacy_invalid' ? (
                    <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-200">
                      Legado invalido
                    </span>
                  ) : null}
                </div>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {run.config_path}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {new Date(run.created_at).toLocaleString('pt-BR')}
                </div>
                {run.run_quality?.status === 'legacy_invalid' ? (
                  <div className="mt-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2 py-2 text-xs text-amber-100">
                    {run.run_quality.message}
                  </div>
                ) : null}
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
              {run.run_quality?.status === 'legacy_invalid' ? (
                <div className="mt-3 text-xs text-amber-200">
                  Comparacao desativada para runs legados invalidados.
                </div>
              ) : (
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
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
