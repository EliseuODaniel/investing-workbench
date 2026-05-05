import { ShieldCheck } from 'lucide-react';
import type { BacktestStrategyCatalogPayload } from '../../types/api';

type StrategyScoreDimensionsPanelProps = {
  dimensions: BacktestStrategyCatalogPayload['score_dimensions'];
};

export function StrategyScoreDimensionsPanel({
  dimensions,
}: StrategyScoreDimensionsPanelProps) {
  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-3 dark:border-blue-900/50 dark:bg-blue-950/20">
      <div className="flex items-center gap-2 text-sm font-semibold text-blue-950 dark:text-blue-100">
        <ShieldCheck className="h-4 w-4" />
        Score planejado
      </div>
      <div className="mt-3 grid gap-2">
        {dimensions.map((dimension) => (
          <div
            key={dimension.dimension_id}
            className="text-xs leading-5 text-blue-900/90 dark:text-blue-100/90"
          >
            <span className="font-semibold">{dimension.label}:</span>{' '}
            {dimension.description}
          </div>
        ))}
      </div>
    </div>
  );
}
