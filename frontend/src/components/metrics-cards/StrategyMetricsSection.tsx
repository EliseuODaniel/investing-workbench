import { Activity, BarChart3 } from 'lucide-react';
import { formatCurrency, formatNumber, formatPercent } from '../../lib/utils';
import { getSelicAverageAnnualRate, getSelicPeriodLabel } from './helpers';
import { StrategyMetricsSectionProps, TopPerformer } from './types';

function isTopPerformer(
  performer: TopPerformer | null,
  strategyName: string,
  metric: 'strategy' | 'benchmark' = 'strategy',
) {
  return performer?.type === metric && performer.name === strategyName;
}

function StrategyBadge({
  label,
  tone,
}: {
  label: string;
  tone: 'yellow' | 'blue' | 'green' | 'purple';
}) {
  const styles = {
    yellow:
      'border-yellow-300 bg-yellow-50 text-yellow-800 dark:border-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-200',
    blue:
      'border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200',
    green:
      'border-green-300 bg-green-50 text-green-800 dark:border-green-700 dark:bg-green-950/30 dark:text-green-200',
    purple:
      'border-purple-300 bg-purple-50 text-purple-800 dark:border-purple-700 dark:bg-purple-950/30 dark:text-purple-200',
  } as const;

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${styles[tone]}`}
    >
      {label}
    </span>
  );
}

function DetailCell({
  label,
  value,
  tone = 'default',
}: {
  label: string;
  value: string;
  tone?: 'default' | 'danger' | 'success';
}) {
  const valueClass =
    tone === 'danger'
      ? 'text-red-500 dark:text-red-300'
      : tone === 'success'
        ? 'text-emerald-600 dark:text-emerald-300'
        : 'text-gray-900 dark:text-gray-100';

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-3 dark:border-gray-700 dark:bg-gray-800/70">
      <div className="text-[11px] uppercase tracking-wide text-gray-500 dark:text-gray-400">
        {label}
      </div>
      <div className={`mt-1 text-lg font-semibold leading-tight ${valueClass}`}>{value}</div>
    </div>
  );
}

export default function StrategyMetricsSection({
  results,
  topReturn,
  topSharpe,
  topHitRate,
  lowestDrawdown,
}: StrategyMetricsSectionProps) {
  return (
    <div>
      <h4 className="mb-4 flex items-center text-md font-semibold text-gray-900 dark:text-gray-100">
        <BarChart3 className="mr-2 h-5 w-5 text-primary-600" />
        Estratégias
      </h4>

      <div className="space-y-5">
        {Object.entries(results).map(([strategyName, result]) => {
          const selicAverageAnnualRate = getSelicAverageAnnualRate(result);
          const selicPeriodLabel = getSelicPeriodLabel(result);
          const hasCashYield = result.metrics.total_interest_earned > 0;
          const highlightBadges = [
            isTopPerformer(topReturn, strategyName) ? (
              <StrategyBadge key="return" label="🏆 Melhor retorno" tone="yellow" />
            ) : null,
            isTopPerformer(topSharpe, strategyName) ? (
              <StrategyBadge key="sharpe" label="📈 Melhor Sharpe" tone="blue" />
            ) : null,
            isTopPerformer(topHitRate, strategyName) ? (
              <StrategyBadge key="hit" label="🎯 Melhor hit rate" tone="green" />
            ) : null,
            isTopPerformer(lowestDrawdown, strategyName) &&
            (lowestDrawdown?.value ?? 0) < -0.1 ? (
              <StrategyBadge key="drawdown" label="🛡️ Menor drawdown" tone="purple" />
            ) : null,
          ].filter(Boolean);

          return (
            <section
              key={strategyName}
              className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-900/40"
            >
              <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div className="space-y-3">
                  <div>
                    <h5 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {strategyName}
                    </h5>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      Leitura rápida da estratégia, com os indicadores mais importantes em foco.
                    </p>
                  </div>
                  {highlightBadges.length > 0 ? (
                    <div className="flex flex-wrap gap-2">{highlightBadges}</div>
                  ) : null}
                </div>

                <div className="min-w-[220px] rounded-xl border border-primary-200 bg-primary-50 px-4 py-3 dark:border-primary-800 dark:bg-primary-900/20">
                  <div className="text-[11px] uppercase tracking-wide text-primary-700 dark:text-primary-300">
                    Retorno total
                  </div>
                  <div className="mt-1 text-2xl font-semibold leading-tight text-primary-950 dark:text-primary-100">
                    {formatPercent(result.metrics.total_return)}
                  </div>
                  <div className="mt-1 text-sm text-primary-700 dark:text-primary-300">
                    Sharpe {formatNumber(result.metrics.sharpe_ratio, 2)} · DD{' '}
                    {formatPercent(Math.abs(result.metrics.max_drawdown))}
                  </div>
                </div>
              </div>

              <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
                <DetailCell label="CAGR" value={formatPercent(result.metrics.cagr)} />
                <DetailCell
                  label="Max Drawdown"
                  value={formatPercent(Math.abs(result.metrics.max_drawdown))}
                  tone={result.metrics.max_drawdown < 0 ? 'danger' : 'success'}
                />
                <DetailCell label="Hit Rate" value={formatPercent(result.metrics.hit_rate)} />
                <DetailCell
                  label="Trades"
                  value={result.metrics.total_trades.toString()}
                />
              </div>

              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                <DetailCell
                  label="Trade médio"
                  value={formatCurrency(result.metrics.avg_trade_pnl)}
                />
                <DetailCell
                  label="Volatilidade"
                  value={formatPercent(result.metrics.volatility)}
                />
                <DetailCell
                  label="Sortino / Profit Factor"
                  value={`${formatNumber(result.metrics.sortino_ratio, 2)} · ${formatNumber(
                    result.metrics.profit_factor,
                    2
                  )}`}
                />
              </div>

              {hasCashYield ? (
                <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/70 px-4 py-4 dark:border-emerald-900/60 dark:bg-emerald-950/20">
                  <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-emerald-800 dark:text-emerald-200">
                    <Activity className="h-4 w-4" />
                    Caixa remunerado
                  </div>
                  <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-3">
                    <div>
                      <div className="text-[11px] uppercase tracking-wide text-emerald-700/80 dark:text-emerald-300/80">
                        Juros acumulados
                      </div>
                      <div className="mt-1 break-all text-xl font-semibold leading-tight text-emerald-950 dark:text-emerald-100">
                        {formatCurrency(result.metrics.total_interest_earned)}
                      </div>
                    </div>
                    {result.metrics.selic_rates_used && result.metrics.selic_rates_used.length > 0 ? (
                      <>
                        <div>
                          <div className="text-[11px] uppercase tracking-wide text-emerald-700/80 dark:text-emerald-300/80">
                            Taxa média anualizada
                          </div>
                          <div className="mt-1 text-base font-semibold text-emerald-950 dark:text-emerald-100">
                            {selicAverageAnnualRate !== null
                              ? formatPercent(selicAverageAnnualRate)
                              : 'n/a'}
                          </div>
                        </div>
                        <div>
                          <div className="text-[11px] uppercase tracking-wide text-emerald-700/80 dark:text-emerald-300/80">
                            Período usado
                          </div>
                          <div className="mt-1 text-base font-semibold text-emerald-950 dark:text-emerald-100">
                            {selicPeriodLabel ?? 'n/a'}
                          </div>
                        </div>
                      </>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </section>
          );
        })}
      </div>
    </div>
  );
}
