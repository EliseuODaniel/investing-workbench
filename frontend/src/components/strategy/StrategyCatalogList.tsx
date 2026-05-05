import { Star } from 'lucide-react';
import type { BacktestStrategyCatalogPayload } from '../../types/api';

type CatalogStrategy = BacktestStrategyCatalogPayload['strategies'][number];

type StrategyCatalogListProps = {
  strategies: CatalogStrategy[];
  savedStrategyIds: Set<string>;
  onSaveStrategy: (strategy: CatalogStrategy) => void;
  onRemoveStrategy: (strategyId: string) => void;
};

export function StrategyCatalogList({
  strategies,
  savedStrategyIds,
  onSaveStrategy,
  onRemoveStrategy,
}: StrategyCatalogListProps) {
  return (
    <div className="grid gap-3">
      {strategies.map((strategy) => {
        const isSaved = savedStrategyIds.has(strategy.strategy_id);
        return (
          <article
            key={strategy.strategy_id}
            className="rounded-xl border border-gray-200 bg-gray-50/70 p-3 dark:border-gray-800 dark:bg-gray-950/30"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {strategy.label}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-gray-300 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300">
                  {strategy.family}
                </span>
                <button
                  type="button"
                  className="rounded-full border border-gray-300 p-1.5 text-gray-500 transition hover:border-amber-300 hover:text-amber-600 dark:border-gray-700 dark:text-gray-400 dark:hover:border-amber-700 dark:hover:text-amber-200"
                  onClick={() =>
                    isSaved
                      ? onRemoveStrategy(strategy.strategy_id)
                      : onSaveStrategy(strategy)
                  }
                  aria-label={
                    isSaved
                      ? `Remover ${strategy.label} do radar`
                      : `Favoritar ${strategy.label}`
                  }
                >
                  <Star className={`h-3.5 w-3.5 ${isSaved ? 'fill-current' : ''}`} />
                </button>
              </div>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-gray-500 dark:text-gray-400">
              <span>{strategy.direction}</span>
              <span>{strategy.supported_timeframes.join(', ')}</span>
              <span>{strategy.required_inputs.length} parametros</span>
            </div>
            {strategy.parameter_defaults ? (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {Object.entries(strategy.parameter_defaults)
                  .slice(0, 5)
                  .map(([key, value]) => (
                    <span
                      key={key}
                      className="rounded-full border border-gray-200 bg-white px-2 py-0.5 text-[11px] text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"
                    >
                      {key}: {String(value)}
                    </span>
                  ))}
              </div>
            ) : null}
            <ul className="mt-2 space-y-1 text-xs leading-5 text-gray-600 dark:text-gray-300">
              {strategy.risk_notes.slice(0, 2).map((note) => (
                <li key={note}>- {note}</li>
              ))}
            </ul>
          </article>
        );
      })}
    </div>
  );
}
