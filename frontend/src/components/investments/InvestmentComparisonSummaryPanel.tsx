import { FileText } from 'lucide-react';
import { openPortfolioFactsheet } from '../../lib/portfolioFactsheet';
import { formatCurrency, formatPercent } from '../../lib/utils';
import type { InvestmentComparisonResponsePayload } from '../../types/api';

interface InvestmentComparisonSummaryPanelProps {
  comparison: InvestmentComparisonResponsePayload;
}

export default function InvestmentComparisonSummaryPanel({
  comparison,
}: InvestmentComparisonSummaryPanelProps) {
  const bestReal = comparison.highlights.best_real_cagr;

  return (
    <section className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
      <div className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50/70 px-4 py-2.5 dark:border-gray-800 dark:bg-gray-900/40">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300">
            Comparativo Geral
          </span>
          <button
            type="button"
            onClick={() => openPortfolioFactsheet(comparison)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-2.5 py-1 text-xs font-medium text-gray-700 shadow-sm hover:border-gray-400 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
          >
            <FileText className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
            Lâmina Executiva (PDF)
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
                <th className="px-4 py-3">Investimento</th>
                <th className="px-4 py-3">Classe</th>
                <th className="px-4 py-3">Valor final</th>
                <th className="px-4 py-3">Lucro</th>
                <th className="px-4 py-3">CAGR</th>
                <th className="px-4 py-3">DD max</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {comparison.results.map((row) => (
                <tr key={row.instrument_id}>
                  <td className="px-4 py-4 align-top">
                    <div className="font-semibold text-gray-900 dark:text-gray-100">
                      {row.label}
                    </div>
                    <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {row.description}
                    </div>
                    {row.component_breakdown.length > 0 ? (
                      <div className="mt-2 inline-flex rounded-full border border-emerald-300 px-2 py-1 text-[11px] font-medium text-emerald-800 dark:border-emerald-700 dark:text-emerald-200">
                        carteira rebalanceada
                      </div>
                    ) : null}
                  </td>
                  <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                    {row.category_label}
                  </td>
                  <td className="px-4 py-4 text-gray-900 dark:text-gray-100">
                    <div className="font-semibold">{formatCurrency(row.final_value)}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      real {formatCurrency(row.final_value_real)}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                    <div>{formatCurrency(row.net_profit)}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      real {formatCurrency(row.net_profit_real)}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                    <div>{formatPercent(row.cagr)}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      real {formatPercent(row.real_cagr)}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                    {formatPercent(row.max_drawdown)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-4">
        <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Leituras rapidas
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
            {comparison.highlights.insights?.map((insight) => (
              <li key={insight}>- {insight}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Inflacao e retorno real
          </div>
          <div className="mt-3 space-y-3 text-sm">
            <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
              <div className="font-semibold text-gray-900 dark:text-gray-100">
                {comparison.inflation.label}
              </div>
              <div className="mt-1 text-gray-600 dark:text-gray-300">
                acumulado {formatPercent(comparison.inflation.accumulated_rate)}
              </div>
              <div className="text-gray-500 dark:text-gray-400">
                perda de poder de compra{' '}
                {formatPercent(comparison.inflation.purchasing_power_loss)}
              </div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
              <div className="font-semibold text-gray-900 dark:text-gray-100">
                Melhor CAGR real
              </div>
              <div className="mt-1 text-gray-600 dark:text-gray-300">
                {bestReal?.label ?? 'n/a'}
              </div>
              <div className="text-gray-500 dark:text-gray-400">
                {bestReal ? formatPercent(bestReal.real_cagr) : 'n/a'}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Resumo por familia
          </div>
          <div className="mt-3 space-y-3">
            {comparison.class_summary.map((row) => (
              <div
                key={row.category_label}
                className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-900/60"
              >
                <div className="font-semibold text-gray-900 dark:text-gray-100">
                  {row.category_label}
                </div>
                <div className="mt-1 text-gray-600 dark:text-gray-300">
                  media final {formatCurrency(row.average_final_value)}
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  CAGR real medio {formatPercent(row.average_real_cagr)}
                </div>
                <div className="text-gray-500 dark:text-gray-400">lider: {row.leader_label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Benchmarks usados
          </div>
          <div className="mt-3 space-y-3">
            {comparison.benchmarks.map((benchmark) => (
              <div
                key={benchmark.benchmark_id}
                className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-900/60"
              >
                <div className="font-semibold text-gray-900 dark:text-gray-100">
                  {benchmark.label}
                </div>
                <div className="mt-1 text-gray-600 dark:text-gray-300">
                  final {formatCurrency(benchmark.final_value)}
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  real {formatCurrency(benchmark.final_value_real)}
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  CAGR {formatPercent(benchmark.cagr)} | real {formatPercent(benchmark.real_cagr)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
