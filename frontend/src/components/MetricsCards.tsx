import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Activity, Target, BarChart3 } from 'lucide-react';
import { StrategyResult, BenchmarkResult } from '../types/api';
import { formatCurrency, formatPercent, formatNumber } from '../lib/utils';

interface MetricsCardsProps {
  results: Record<string, StrategyResult>;
  benchmarks?: Record<string, BenchmarkResult>;
}

const MetricsCards: React.FC<MetricsCardsProps> = ({ results, benchmarks }) => {
  // Calculate top performers
  const getTopPerformer = (metric: string, higherIsBetter = true) => {
    const allItems = [
      ...Object.entries(results).map(([name, data]) => ({
        name,
        value: (data.metrics as any)[metric],
        type: 'strategy'
      })),
      ...(benchmarks ? Object.entries(benchmarks).map(([name, data]) => ({
        name,
        value: (data.metrics as any)[metric],
        type: 'benchmark'
      })) : [])
    ];

    if (allItems.length === 0) return null;

    return allItems.reduce((best, current) => {
      if (current.value === null || current.value === undefined) return best;
      if (best.value === null || best.value === undefined) return current;

      return higherIsBetter
        ? current.value > best.value ? current : best
        : current.value < best.value ? current : best;
    });
  };

  const topReturn = getTopPerformer('total_return');
  const topSharpe = getTopPerformer('sharpe_ratio');
  const topHitRate = getTopPerformer('hit_rate');
  const lowestDrawdown = getTopPerformer('max_drawdown', false);

  const MetricCard: React.FC<{
    title: string;
    value: string;
    subtitle?: string;
    trend?: 'up' | 'down' | 'neutral';
    icon?: React.ReactNode;
    isTopPerformer?: boolean;
    topPerformerLabel?: string;
  }> = ({ title, value, subtitle, trend, icon, isTopPerformer, topPerformerLabel }) => {
    const trendColors = {
      up: 'text-success-600',
      down: 'text-danger-600',
      neutral: 'text-gray-600'
    };

    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg border p-6 relative ${
        isTopPerformer
          ? 'border-yellow-300 bg-gradient-to-br from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 dark:border-yellow-600'
          : 'border-gray-200 dark:border-gray-700'
      }`}>
        {isTopPerformer && (
          <div className="absolute top-2 right-2">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200">
              🏆 {topPerformerLabel || 'Top'}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between">
          <div className={isTopPerformer ? 'pt-4' : ''}>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
            <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
            {subtitle && (
              <p className={`text-sm mt-1 ${trendColors[trend || 'neutral']}`}>
                {subtitle}
              </p>
            )}
          </div>
          {icon && (
            <div className={`text-gray-400 dark:text-gray-500 ${
              isTopPerformer ? 'text-yellow-500' : ''
            }`}>
              {icon}
            </div>
          )}
        </div>
      </div>
    );
  };

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

      {/* Top Performers Summary */}
      {(topReturn || topSharpe || topHitRate || lowestDrawdown) && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {topReturn && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="text-xs font-medium text-yellow-800 dark:text-yellow-200 mb-1">🏆 Melhor Retorno</div>
              <div className="text-lg font-semibold text-yellow-900 dark:text-yellow-100">
                {topReturn.name}
              </div>
              <div className="text-sm text-yellow-700 dark:text-yellow-300">
                {formatPercent(topReturn.value)}
              </div>
            </div>
          )}

          {topSharpe && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="text-xs font-medium text-blue-800 dark:text-blue-200 mb-1">📈 Melhor Sharpe</div>
              <div className="text-lg font-semibold text-blue-900 dark:text-blue-100">
                {topSharpe.name}
              </div>
              <div className="text-sm text-blue-700 dark:text-blue-300">
                {formatNumber(topSharpe.value, 2)}
              </div>
            </div>
          )}

          {topHitRate && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">🎯 Melhor Hit Rate</div>
              <div className="text-lg font-semibold text-green-900 dark:text-green-100">
                {topHitRate.name}
              </div>
              <div className="text-sm text-green-700 dark:text-green-300">
                {formatPercent(topHitRate.value)}
              </div>
            </div>
          )}

          {lowestDrawdown && lowestDrawdown.value < -0.1 && (
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
              <div className="text-xs font-medium text-purple-800 dark:text-purple-200 mb-1">🛡️ Menor Drawdown</div>
              <div className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                {lowestDrawdown.name}
              </div>
              <div className="text-sm text-purple-700 dark:text-purple-300">
                {formatPercent(Math.abs(lowestDrawdown.value))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="space-y-6">
        {/* Strategies Section */}
        <div>
          <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-primary-600" />
            Estratégias
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(results).map(([strategyName, result]) => (
              <div key={strategyName} className="space-y-4">
                {/* Strategy Header */}
                <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4 border border-primary-200 dark:border-primary-800">
                  <h4 className="font-semibold text-primary-900 dark:text-primary-100">{strategyName}</h4>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-sm text-primary-700 dark:text-primary-300">Total Return</span>
                    <div className="flex items-center">
                      {result.metrics.total_return >= 0 ? (
                        <TrendingUp className="h-4 w-4 text-success-600 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-danger-600 mr-1" />
                      )}
                      <span className={`font-semibold ${
                        result.metrics.total_return >= 0 ? 'text-success-600' : 'text-danger-600'
                      }`}>
                        {formatPercent(result.metrics.total_return)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <MetricCard
                    title="CAGR"
                    value={formatPercent(result.metrics.cagr)}
                    icon={<TrendingUp className="h-5 w-5" />}
                    isTopPerformer={topReturn?.name === strategyName && topReturn?.type === 'strategy'}
                    topPerformerLabel="Top CAGR"
                  />

                  <MetricCard
                    title="Sharpe Ratio"
                    value={formatNumber(result.metrics.sharpe_ratio, 2)}
                    icon={<BarChart3 className="h-5 w-5" />}
                    isTopPerformer={topSharpe?.name === strategyName && topSharpe?.type === 'strategy'}
                    topPerformerLabel="Top Sharpe"
                  />

                  <MetricCard
                    title="Max Drawdown"
                    value={formatPercent(Math.abs(result.metrics.max_drawdown))}
                    subtitle={result.metrics.max_drawdown < 0 ? 'Loss' : 'Gain'}
                    trend={result.metrics.max_drawdown < 0 ? 'down' : 'up'}
                    icon={<Activity className="h-5 w-5" />}
                    isTopPerformer={lowestDrawdown?.name === strategyName && lowestDrawdown?.type === 'strategy' && lowestDrawdown.value < -0.1}
                    topPerformerLabel="Menor DD"
                  />

                  <MetricCard
                    title="Hit Rate"
                    value={formatPercent(result.metrics.hit_rate)}
                    icon={<Target className="h-5 w-5" />}
                    isTopPerformer={topHitRate?.name === strategyName && topHitRate?.type === 'strategy'}
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

                  {/* Cash Yield Interest - Only show if > 0 */}
                  {result.metrics.total_interest_earned > 0 && (
                    <MetricCard
                      title="Cash Yield Interest"
                      value={formatCurrency(result.metrics.total_interest_earned)}
                      icon={<TrendingUp className="h-5 w-5 text-success-600" />}
                    />
                  )}

                  {/* SELIC Rates Info - Only show if real SELIC data was used */}
                  {result.metrics.selic_rates_used && result.metrics.selic_rates_used.length > 0 && (
                    <div className="col-span-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                      <div className="flex items-center mb-2">
                        <svg className="h-4 w-4 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                        <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">SELIC Real Utilizada</h4>
                      </div>
                      <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                        <p>Foram utilizadas {result.metrics.selic_rates_used.length} taxas mensais reais do Banco Central.</p>
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          <div>
                            <span className="font-medium">Taxa Média:</span> {
                              formatPercent(
                                (result.metrics.selic_rates_used.reduce((sum, rate) => sum + rate.rate, 0) / result.metrics.selic_rates_used.length) * 12
                              )
                            } a.a.
                          </div>
                          <div>
                            <span className="font-medium">Período:</span> {
                              `${Math.min(...result.metrics.selic_rates_used.map(r => r.year))}/${String(Math.min(...result.metrics.selic_rates_used.map(r => r.month))).padStart(2, '0')} - ${Math.max(...result.metrics.selic_rates_used.map(r => r.year))}/${String(Math.max(...result.metrics.selic_rates_used.map(r => r.month))).padStart(2, '0')}`
                            }
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Additional Info */}
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
            ))}
          </div>
        </div>

        {/* Benchmarks Section */}
        {benchmarks && Object.keys(benchmarks).length > 0 && (
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <BarChart3 className="h-5 w-5 mr-2 text-gray-600 dark:text-gray-400" />
              Benchmarks de Mercado
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(benchmarks).map(([benchmarkName, benchmark]) => (
                <div key={benchmarkName} className="space-y-4">
                  {/* Benchmark Header */}
                  <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-amber-900 dark:text-amber-100">{benchmarkName}</h4>
                      <div className="flex items-center">
                        {benchmark.metrics.total_return >= 0 ? (
                          <TrendingUp className="h-4 w-4 text-success-600 mr-1" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-danger-600 mr-1" />
                        )}
                        <span className={`font-semibold text-sm ${
                          benchmark.metrics.total_return >= 0 ? 'text-success-600' : 'text-danger-600'
                        }`}>
                          {formatPercent(benchmark.metrics.total_return)}
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                      {benchmark.ticker} • Referência de mercado
                    </div>
                  </div>

                  {/* Benchmark Metrics */}
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
        )}
      </div>
    </div>
  );
};

export default MetricsCards;