import {
  Activity,
  BarChart3,
  DollarSign,
  Target,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { formatCurrency, formatNumber, formatPercent } from '../../lib/utils';
import MetricCard from './MetricCard';
import { getSelicAverageAnnualRate, getSelicPeriodLabel } from './helpers';
import { StrategyMetricsSectionProps } from './types';

export default function StrategyMetricsSection({
  results,
  topReturn,
  topSharpe,
  topHitRate,
  lowestDrawdown,
}: StrategyMetricsSectionProps) {
  return (
    <div>
      <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
        <BarChart3 className="h-5 w-5 mr-2 text-primary-600" />
        Estratégias
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(results).map(([strategyName, result]) => {
          const selicAverageAnnualRate = getSelicAverageAnnualRate(result);
          const selicPeriodLabel = getSelicPeriodLabel(result);

          return (
            <div key={strategyName} className="space-y-4">
              <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4 border border-primary-200 dark:border-primary-800">
                <h4 className="font-semibold text-primary-900 dark:text-primary-100">
                  {strategyName}
                </h4>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-sm text-primary-700 dark:text-primary-300">
                    Total Return
                  </span>
                  <div className="flex items-center">
                    {result.metrics.total_return >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-success-600 mr-1" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-danger-600 mr-1" />
                    )}
                    <span
                      className={`font-semibold ${
                        result.metrics.total_return >= 0 ? 'text-success-600' : 'text-danger-600'
                      }`}
                    >
                      {formatPercent(result.metrics.total_return)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <MetricCard
                  title="CAGR"
                  value={formatPercent(result.metrics.cagr)}
                  icon={<TrendingUp className="h-5 w-5" />}
                  isTopPerformer={topReturn?.name === strategyName && topReturn.type === 'strategy'}
                  topPerformerLabel="Top CAGR"
                />

                <MetricCard
                  title="Sharpe Ratio"
                  value={formatNumber(result.metrics.sharpe_ratio, 2)}
                  icon={<BarChart3 className="h-5 w-5" />}
                  isTopPerformer={topSharpe?.name === strategyName && topSharpe.type === 'strategy'}
                  topPerformerLabel="Top Sharpe"
                />

                <MetricCard
                  title="Max Drawdown"
                  value={formatPercent(Math.abs(result.metrics.max_drawdown))}
                  subtitle={result.metrics.max_drawdown < 0 ? 'Loss' : 'Gain'}
                  trend={result.metrics.max_drawdown < 0 ? 'down' : 'up'}
                  icon={<Activity className="h-5 w-5" />}
                  isTopPerformer={
                    lowestDrawdown?.name === strategyName &&
                    lowestDrawdown.type === 'strategy' &&
                    lowestDrawdown.value < -0.1
                  }
                  topPerformerLabel="Menor DD"
                />

                <MetricCard
                  title="Hit Rate"
                  value={formatPercent(result.metrics.hit_rate)}
                  icon={<Target className="h-5 w-5" />}
                  isTopPerformer={
                    topHitRate?.name === strategyName && topHitRate.type === 'strategy'
                  }
                  topPerformerLabel="Top Hit Rate"
                />

                <MetricCard
                  title="Total Trades"
                  value={result.metrics.total_trades.toString()}
                  icon={<BarChart3 className="h-5 w-5" />}
                />

                <MetricCard
                  title="Avg Trade P&L"
                  value={formatCurrency(result.metrics.avg_trade_pnl)}
                  icon={<DollarSign className="h-5 w-5" />}
                />

                {result.metrics.total_interest_earned > 0 && (
                  <MetricCard
                    title="Cash Yield Interest"
                    value={formatCurrency(result.metrics.total_interest_earned)}
                    icon={<TrendingUp className="h-5 w-5 text-success-600" />}
                  />
                )}

                {result.metrics.selic_rates_used && result.metrics.selic_rates_used.length > 0 && (
                  <div className="col-span-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                    <div className="flex items-center mb-2">
                      <svg
                        className="h-4 w-4 text-blue-600 mr-2"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                        SELIC Real Utilizada
                      </h4>
                    </div>
                    <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                      <p>
                        Foram utilizadas {result.metrics.selic_rates_used.length} taxas mensais reais
                        do Banco Central.
                      </p>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <div>
                          <span className="font-medium">Taxa Média:</span>{' '}
                          {selicAverageAnnualRate !== null
                            ? formatPercent(selicAverageAnnualRate)
                            : 'n/a'}{' '}
                          a.a.
                        </div>
                        <div>
                          <span className="font-medium">Período:</span>{' '}
                          {selicPeriodLabel ?? 'n/a'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="text-sm text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700 pt-3">
                <div className="flex justify-between mb-1">
                  <span>Volatility:</span>
                  <span>{formatPercent(result.metrics.volatility)}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span>Profit Factor:</span>
                  <span>{formatNumber(result.metrics.profit_factor, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Sortino Ratio:</span>
                  <span>{formatNumber(result.metrics.sortino_ratio, 2)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
