import { formatCurrency, formatPercent } from '../../lib/utils';
import type { InvestmentComparisonResultPayload } from '../../types/api';

interface InvestmentPortfolioContributionPanelProps {
  portfolioResults: InvestmentComparisonResultPayload[];
}

export default function InvestmentPortfolioContributionPanel({
  portfolioResults,
}: InvestmentPortfolioContributionPanelProps) {
  if (portfolioResults.length === 0) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-gray-200 p-5 dark:border-gray-800">
      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
        Contribuicao por sleeve e por familia
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        {portfolioResults.map((row) => (
          <div key={row.instrument_id} className="rounded-2xl bg-gray-50 p-4 dark:bg-gray-900/60">
            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {row.label}
            </div>
            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              valor final {formatCurrency(row.final_value)} | real{' '}
              {formatCurrency(row.final_value_real)}
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {row.component_breakdown.map((component) => (
                <div
                  key={`${row.instrument_id}-${component.component_id}`}
                  className="rounded-xl border border-gray-200 bg-white px-3 py-3 text-sm dark:border-gray-800 dark:bg-gray-950/50"
                >
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    {component.label}
                  </div>
                  <div className="mt-1 text-gray-600 dark:text-gray-300">
                    alvo {formatPercent(component.target_weight)}
                  </div>
                  <div className="text-gray-500 dark:text-gray-400">
                    fim {formatPercent(component.ending_weight)}
                  </div>
                  <div className="text-gray-500 dark:text-gray-400">
                    contribuiu {formatCurrency(component.final_value)}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {row.category_breakdown.map((category) => (
                <div
                  key={`${row.instrument_id}-${category.category_label}`}
                  className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200"
                >
                  {category.category_label}: alvo {formatPercent(category.target_weight)} | fim{' '}
                  {formatPercent(category.ending_weight)}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
