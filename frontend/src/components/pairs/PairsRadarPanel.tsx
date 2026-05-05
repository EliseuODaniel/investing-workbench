import { Star, Trash2 } from 'lucide-react';
import { SavedPairsRadarItem } from '../../hooks/useSavedPairsRadar';

interface PairsRadarPanelProps {
  savedItems: SavedPairsRadarItem[];
  activeBacktestId?: string | null;
  hasActiveBacktest: boolean;
  isActiveSaved: boolean;
  onSaveActive: () => void;
  onRemoveSaved: (pairsBacktestId: string) => void;
  onLoadBacktestResults: (pairsBacktestId: string) => void;
}

export function PairsRadarPanel({
  savedItems,
  activeBacktestId,
  hasActiveBacktest,
  isActiveSaved,
  onSaveActive,
  onRemoveSaved,
  onLoadBacktestResults,
}: PairsRadarPanelProps) {
  return (
    <div className="card space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            Radar de pairs
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Favoritos locais para comparar cointegracao, robustez e universos candidatos.
          </p>
        </div>
        <button
          type="button"
          className="btn-secondary inline-flex items-center gap-2"
          onClick={onSaveActive}
          disabled={!hasActiveBacktest || isActiveSaved}
        >
          <Star className="h-4 w-4" />
          {isActiveSaved ? 'No radar' : 'Favoritar'}
        </button>
      </div>

      <div className="space-y-2">
        {savedItems.map((item) => (
          <div
            key={item.pairs_backtest_id}
            className={`rounded-xl border px-4 py-3 ${
              activeBacktestId === item.pairs_backtest_id
                ? 'border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/20'
                : 'border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900'
            }`}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <button
                type="button"
                className="min-w-0 flex-1 text-left"
                onClick={() => onLoadBacktestResults(item.pairs_backtest_id)}
              >
                <div className="truncate font-medium text-gray-900 dark:text-gray-100">
                  {item.label}
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {item.pairs_backtest_id} · cenários={item.scenario_count} · pares=
                  {item.candidate_pair_count}
                </div>
                {item.benchmark_ids.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {item.benchmark_ids.slice(0, 3).map((benchmarkId) => (
                      <span
                        key={`${item.pairs_backtest_id}-${benchmarkId}`}
                        className="rounded-full bg-gray-100 px-2 py-1 text-[11px] text-gray-600 dark:bg-gray-800 dark:text-gray-300"
                      >
                        {benchmarkId}
                      </span>
                    ))}
                  </div>
                ) : null}
              </button>
              <button
                type="button"
                className="rounded-lg border border-gray-200 p-2 text-gray-500 transition hover:border-red-300 hover:text-red-600 dark:border-gray-800 dark:text-gray-400 dark:hover:border-red-800 dark:hover:text-red-300"
                aria-label={`Remover ${item.label} do radar`}
                onClick={() => onRemoveSaved(item.pairs_backtest_id)}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {savedItems.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
            Rode ou abra um backtest e favorite os estudos que merecem acompanhamento.
          </div>
        ) : null}
      </div>
    </div>
  );
}
