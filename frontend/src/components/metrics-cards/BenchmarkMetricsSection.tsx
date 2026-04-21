import { Activity, BarChart3, TrendingDown, TrendingUp } from 'lucide-react';
import { formatNumber, formatPercent } from '../../lib/utils';
import MetricCard from './MetricCard';
import { BenchmarkMetricsSectionProps } from './types';

export default function BenchmarkMetricsSection({ benchmarks }: BenchmarkMetricsSectionProps) {
  if (!benchmarks || Object.keys(benchmarks).length === 0) {
    return null;
  }

  return (
    <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <BarChart3 className="h-5 w-5 mr-2 text-gray-600 dark:text-gray-400" />
        Benchmarks de Mercado
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(benchmarks).map(([benchmarkName, benchmark]) => (
          <div key={benchmarkName} className="space-y-4">
            <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-amber-900 dark:text-amber-100">
                  {benchmarkName}
                </h4>
                <div className="flex items-center">
                  {benchmark.metrics.total_return >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-success-600 mr-1" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-danger-600 mr-1" />
                  )}
                  <span
                    className={`font-semibold text-sm ${
                      benchmark.metrics.total_return >= 0
                        ? 'text-success-600'
                        : 'text-danger-600'
                    }`}
                  >
                    {formatPercent(benchmark.metrics.total_return)}
                  </span>
                </div>
              </div>
              <div className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                {benchmark.ticker} • Referência de mercado
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <MetricCard
                title="CAGR"
                value={formatPercent(benchmark.metrics.cagr)}
                icon={<TrendingUp className="h-5 w-5" />}
              />

              <MetricCard
                title="Sharpe Ratio"
                value={formatNumber(benchmark.metrics.sharpe_ratio, 2)}
                icon={<BarChart3 className="h-5 w-5" />}
              />

              <MetricCard
                title="Max Drawdown"
                value={formatPercent(Math.abs(benchmark.metrics.max_drawdown))}
                subtitle="Loss"
                trend="down"
                icon={<Activity className="h-5 w-5" />}
              />

              <MetricCard
                title="Volatilidade"
                value={formatPercent(benchmark.metrics.volatility)}
                icon={<BarChart3 className="h-5 w-5" />}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
