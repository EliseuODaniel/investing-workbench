import { useMemo } from 'react';
import BenchmarkMetricsSection from './metrics-cards/BenchmarkMetricsSection';
import StrategyMetricsSection from './metrics-cards/StrategyMetricsSection';
import TopPerformersSummary from './metrics-cards/TopPerformersSummary';
import { getTopPerformer } from './metrics-cards/helpers';
import { MetricsCardsProps } from './metrics-cards/types';

export default function MetricsCards({ results, benchmarks }: MetricsCardsProps) {
  const topReturn = useMemo(
    () => getTopPerformer(results, benchmarks, 'total_return'),
    [results, benchmarks],
  );
  const topSharpe = useMemo(
    () => getTopPerformer(results, benchmarks, 'sharpe_ratio'),
    [results, benchmarks],
  );
  const topHitRate = useMemo(
    () => getTopPerformer(results, benchmarks, 'hit_rate'),
    [results, benchmarks],
  );
  const lowestDrawdown = useMemo(
    () => getTopPerformer(results, benchmarks, 'max_drawdown', false),
    [results, benchmarks],
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          📊 Métricas de Performance
        </h3>
        <div className="flex items-center space-x-4 text-sm">
          {topReturn && (
            <div className="flex items-center text-yellow-600 dark:text-yellow-400">
              🏆 Top Retorno: <span className="font-medium">{topReturn.name}</span>
            </div>
          )}
          {topSharpe && (
            <div className="flex items-center text-blue-600 dark:text-blue-400">
              📈 Top Sharpe: <span className="font-medium">{topSharpe.name}</span>
            </div>
          )}
        </div>
      </div>

      <TopPerformersSummary
        topReturn={topReturn}
        topSharpe={topSharpe}
        topHitRate={topHitRate}
        lowestDrawdown={lowestDrawdown}
      />

      <div className="space-y-6">
        <StrategyMetricsSection
          results={results}
          topReturn={topReturn}
          topSharpe={topSharpe}
          topHitRate={topHitRate}
          lowestDrawdown={lowestDrawdown}
        />
        <BenchmarkMetricsSection benchmarks={benchmarks} />
      </div>
    </div>
  );
}
