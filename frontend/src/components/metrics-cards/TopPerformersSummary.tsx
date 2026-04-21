import { formatNumber, formatPercent } from '../../lib/utils';
import { TopPerformersSummaryProps } from './types';

export default function TopPerformersSummary({
  topReturn,
  topSharpe,
  topHitRate,
  lowestDrawdown,
}: TopPerformersSummaryProps) {
  if (!(topReturn || topSharpe || topHitRate || lowestDrawdown)) {
    return null;
  }

  return (
    <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {topReturn && (
        <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-900/20">
          <div className="text-xs font-medium text-yellow-800 dark:text-yellow-200 mb-1">
            🏆 Melhor Retorno
          </div>
          <div className="text-base font-semibold leading-tight text-yellow-900 dark:text-yellow-100">
            {topReturn.name}
          </div>
          <div className="mt-1 text-sm break-all text-yellow-700 dark:text-yellow-300">
            {formatPercent(topReturn.value)}
          </div>
        </div>
      )}

      {topSharpe && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
          <div className="text-xs font-medium text-blue-800 dark:text-blue-200 mb-1">
            📈 Melhor Sharpe
          </div>
          <div className="text-base font-semibold leading-tight text-blue-900 dark:text-blue-100">
            {topSharpe.name}
          </div>
          <div className="text-sm text-blue-700 dark:text-blue-300">
            {formatNumber(topSharpe.value, 2)}
          </div>
        </div>
      )}

      {topHitRate && (
        <div className="rounded-xl border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
          <div className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">
            🎯 Melhor Hit Rate
          </div>
          <div className="text-base font-semibold leading-tight text-green-900 dark:text-green-100">
            {topHitRate.name}
          </div>
          <div className="text-sm text-green-700 dark:text-green-300">
            {formatPercent(topHitRate.value)}
          </div>
        </div>
      )}

      {lowestDrawdown && lowestDrawdown.value < -0.1 && (
        <div className="rounded-xl border border-purple-200 bg-purple-50 p-4 dark:border-purple-800 dark:bg-purple-900/20">
          <div className="text-xs font-medium text-purple-800 dark:text-purple-200 mb-1">
            🛡️ Menor Drawdown
          </div>
          <div className="text-base font-semibold leading-tight text-purple-900 dark:text-purple-100">
            {lowestDrawdown.name}
          </div>
          <div className="text-sm text-purple-700 dark:text-purple-300">
            {formatPercent(Math.abs(lowestDrawdown.value))}
          </div>
        </div>
      )}
    </div>
  );
}
