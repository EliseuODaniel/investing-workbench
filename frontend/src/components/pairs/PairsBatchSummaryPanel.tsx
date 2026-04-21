import { PairsBacktestResultsPayload, PairsScenarioPayload } from '../../types/api';
import { formatCurrency, formatNumber, formatPercent } from './pairsFormat';

interface PairsBatchSummaryPanelProps {
  activeBacktest: PairsBacktestResultsPayload | null;
  isRunning: boolean;
  isLoadingSelected: boolean;
}

function benchmarkLabel(
  scenario: PairsScenarioPayload,
  benchmarkId: string | null | undefined
): string {
  const match = scenario.alpha_decomposition?.benchmark_comparison?.find(
    (item) => item.benchmark_id === benchmarkId
  );
  return match?.label ?? benchmarkId ?? 'n/a';
}

export function PairsBatchSummaryPanel({
  activeBacktest,
  isRunning,
  isLoadingSelected,
}: PairsBatchSummaryPanelProps) {
  const activeScenarios = activeBacktest?.scenarios ?? [];
  const activeBenchmarks = activeBacktest?.benchmarks ?? [];
  const robustnessDispersion = activeBacktest?.robustness_report.dispersion ?? {};
  const robustnessRankings = activeBacktest?.robustness_report.rankings ?? [];
  const reconstitutionPlan = activeBacktest?.universe.reconstitution_plan ?? [];

  return (
    <div className="card">
      <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
        Comparação de cenários
      </h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Decomposição do retorno, benchmark gaps, concentração do sleeve e ranking do batch.
      </p>
      {activeBacktest ? (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.3fr_0.7fr]">
            <div className="space-y-4">
              {activeScenarios.map((scenario) => {
                const metrics = scenario.metrics;
                const qualitySummary = scenario.quality_summary;
                const portfolioSummary = scenario.portfolio_summary;
                const alpha = scenario.alpha_decomposition;
                const topPairs = Array.isArray(scenario.pair_pnl) ? scenario.pair_pnl.slice(0, 3) : [];
                const worstPairs = Array.isArray(scenario.pair_pnl)
                  ? [...scenario.pair_pnl].slice(-3).reverse()
                  : [];
                return (
                  <div
                    key={String(scenario.scenario_id)}
                    className="rounded-2xl border border-gray-200 px-4 py-4 dark:border-gray-800"
                  >
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                          {String(scenario.label)}
                        </h4>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                          {String(scenario.scenario_id)} · trades=
                          {String(metrics.trade_count ?? '0')} · pares únicos=
                          {String(portfolioSummary.unique_pairs_traded ?? '0')}
                        </p>
                      </div>
                      <div className="text-right text-sm text-gray-500 dark:text-gray-400">
                        <div>Sharpe {formatNumber(Number(metrics.sharpe || 0), 2)}</div>
                        <div>Retorno {formatPercent(Number(metrics.return_total || 0))}</div>
                        <div>Equity final {formatCurrency(Number(metrics.final_equity || 0), 0)}</div>
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 xl:grid-cols-4">
                      <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 dark:text-gray-400">Alpha trades</div>
                        <div className="mt-1 text-sm font-semibold">
                          {formatCurrency(Number(alpha?.trade_net_pnl_total || 0), 0)}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {formatPercent(Number(alpha?.trade_return_total || 0))}
                        </div>
                      </div>
                      <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 dark:text-gray-400">Carry caixa</div>
                        <div className="mt-1 text-sm font-semibold">
                          {formatCurrency(Number(alpha?.cash_yield_total || 0), 0)}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {formatPercent(Number(alpha?.cash_return_total || 0))}
                        </div>
                      </div>
                      <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Gap vs {benchmarkLabel(scenario, alpha?.primary_benchmark_id)}
                        </div>
                        <div className="mt-1 text-sm font-semibold">
                          {formatCurrency(Number(alpha?.primary_benchmark_equity_gap || 0), 0)}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {formatPercent(Number(alpha?.primary_benchmark_excess_return || 0))}
                        </div>
                      </div>
                      <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
                        <div className="text-xs text-gray-500 dark:text-gray-400">Fricções</div>
                        <div className="mt-1 text-sm font-semibold">
                          {formatCurrency(
                            Number(alpha?.short_borrow_cost_total || 0) +
                              Number(alpha?.fees_total || 0) +
                              Number(alpha?.slippage_total || 0),
                            0
                          )}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          borrow {formatCurrency(Number(alpha?.short_borrow_cost_total || 0), 0)}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-gray-500 dark:text-gray-400 xl:grid-cols-5">
                      <div>Drawdown {formatPercent(Number(metrics.max_drawdown || 0))}</div>
                      <div>Win rate {formatPercent(Number(metrics.win_rate || 0))}</div>
                      <div>Turnover {formatNumber(Number(metrics.turnover || 0), 1)}x</div>
                      <div>Gross médio {formatPercent(Number(metrics.avg_gross_exposure_pct || 0))}</div>
                      <div>Cash yield {formatCurrency(Number(qualitySummary.cash_yield_total || 0), 0)}</div>
                    </div>

                    <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
                      <div className="rounded-xl border border-gray-200 px-3 py-3 dark:border-gray-800">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          Benchmarks
                        </div>
                        <div className="mt-2 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                          {(alpha?.benchmark_comparison ?? []).map((benchmark) => (
                            <div key={benchmark.benchmark_id}>
                              {benchmark.label}: {formatCurrency(benchmark.final_equity, 0)} · gap{' '}
                              {formatCurrency(benchmark.equity_gap, 0)}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-xl border border-gray-200 px-3 py-3 dark:border-gray-800">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          Top pares
                        </div>
                        <div className="mt-2 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                          {topPairs.length > 0 ? (
                            topPairs.map((pair) => (
                              <div key={String(pair.pair_label)}>
                                {String(pair.pair_label)}: {formatCurrency(Number(pair.net_pnl || 0), 0)}
                              </div>
                            ))
                          ) : (
                            <div>Sem trades fechados.</div>
                          )}
                        </div>
                      </div>

                      <div className="rounded-xl border border-gray-200 px-3 py-3 dark:border-gray-800">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          Piores pares
                        </div>
                        <div className="mt-2 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                          {worstPairs.length > 0 ? (
                            worstPairs.map((pair) => (
                              <div key={String(pair.pair_label)}>
                                {String(pair.pair_label)}: {formatCurrency(Number(pair.net_pnl || 0), 0)}
                              </div>
                            ))
                          ) : (
                            <div>Sem trades fechados.</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl border border-gray-200 px-4 py-4 dark:border-gray-800">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100">Benchmarks</h4>
                <div className="mt-3 space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  {activeBenchmarks.map((benchmark) => {
                    const finalPoint = benchmark.equity_curve[benchmark.equity_curve.length - 1];
                    return (
                      <div key={String(benchmark.benchmark_id)}>
                        {String(benchmark.label)} · final{' '}
                        {formatCurrency(Number(finalPoint?.equity || 0), 0)}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-2xl border border-gray-200 px-4 py-4 dark:border-gray-800">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100">Robustez</h4>
                <div className="mt-3 space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  <div>
                    Faixa de retorno: {formatNumber(Number(robustnessDispersion.return_total_range || 0), 3)}
                  </div>
                  <div>
                    Faixa de Sharpe: {formatNumber(Number(robustnessDispersion.sharpe_range || 0), 3)}
                  </div>
                  <div>
                    Faixa de drawdown:{' '}
                    {formatNumber(Number(robustnessDispersion.max_drawdown_range || 0), 3)}
                  </div>
                </div>
                {robustnessRankings.length > 0 && (
                  <div className="mt-4 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                    {robustnessRankings.map((ranking, index) => (
                      <div key={`${String(ranking.scenario_id)}_${index}`}>
                        {index + 1}. {String(ranking.label ?? ranking.scenario_id)} · Sharpe{' '}
                        {formatNumber(Number(ranking.sharpe || 0), 2)} · Retorno{' '}
                        {formatPercent(Number(ranking.return_total || 0))}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {reconstitutionPlan.length > 0 && (
                <div className="rounded-2xl border border-gray-200 px-4 py-4 dark:border-gray-800">
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                    Reconstituição do universo
                  </h4>
                  <div className="mt-3 space-y-2 text-sm text-gray-600 dark:text-gray-300">
                    {reconstitutionPlan.map((segment) => (
                      <div key={String(segment.segment_id)}>
                        {String(segment.segment_id)} · {String(segment.start_date)} até{' '}
                        {String(segment.end_date)} · snapshot {String(segment.resolved_as_of_date)} ·
                        elegíveis=
                        {String(segment.quality_report?.eligible_ticker_count ?? 'n/a')}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {activeBacktest.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
              {activeBacktest.warnings.join(' ')}
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
          {isRunning || isLoadingSelected
            ? 'Carregando resultados de pairs...'
            : 'Execute um backtest ou abra um batch persistido para ver o resumo.'}
        </div>
      )}
    </div>
  );
}
