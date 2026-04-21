import { RefreshCw } from 'lucide-react';
import { PairsBacktestManifestPayload } from '../../types/api';

interface PairsHistoryCardProps {
  backtests: PairsBacktestManifestPayload[];
  selectedBacktestId: string | null;
  isLoadingBacktests: boolean;
  onRefreshBacktests: () => void;
  onLoadBacktestResults: (backtestId: string) => void;
}

export function PairsHistoryCard({
  backtests,
  selectedBacktestId,
  isLoadingBacktests,
  onRefreshBacktests,
  onLoadBacktestResults,
}: PairsHistoryCardProps) {
  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            Histórico persistido
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Backtests e batches de pairs já salvos localmente.
          </p>
        </div>
        <button
          type="button"
          className="btn-secondary inline-flex items-center gap-2"
          onClick={onRefreshBacktests}
          disabled={isLoadingBacktests}
        >
          <RefreshCw className="h-4 w-4" />
          Atualizar
        </button>
      </div>

      <div className="space-y-2">
        {backtests.map((backtest) => (
          <button
            key={backtest.pairs_backtest_id}
            type="button"
            className={`w-full rounded-xl border px-4 py-3 text-left transition ${
              selectedBacktestId === backtest.pairs_backtest_id
                ? 'border-emerald-400 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-950/30'
                : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-900'
            }`}
            onClick={() => onLoadBacktestResults(backtest.pairs_backtest_id)}
          >
            <div className="font-medium text-gray-900 dark:text-gray-100">
              {backtest.preset_label}
            </div>
            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {backtest.pairs_backtest_id} · cenários={backtest.scenario_count}
              {backtest.reconstitution_segment_count > 0
                ? ` · segmentos=${backtest.reconstitution_segment_count}`
                : ''}
            </div>
          </button>
        ))}
        {backtests.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
            Nenhum backtest de pairs persistido ainda.
          </div>
        )}
      </div>
    </div>
  );
}
