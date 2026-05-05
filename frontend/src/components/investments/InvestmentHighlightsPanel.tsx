import type { InvestmentComparisonResponsePayload } from '../../types/api';
import { formatCurrency, formatPercent } from '../../lib/utils';

interface InvestmentHighlightsPanelProps {
  highlights: InvestmentComparisonResponsePayload['highlights'];
  resultCount: number;
}

export default function InvestmentHighlightsPanel({
  highlights,
  resultCount,
}: InvestmentHighlightsPanelProps) {
  const topPerformer = highlights.best_final_value;
  const bestReal = highlights.best_real_cagr;
  const mostDefensive = highlights.most_defensive;

  return (
    <div className="grid gap-4 xl:grid-cols-4">
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
          Melhor valor final
        </div>
        <div className="mt-2 text-xl font-semibold text-emerald-900 dark:text-emerald-100">
          {topPerformer?.label ?? 'n/a'}
        </div>
        <div className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
          {topPerformer ? formatCurrency(topPerformer.final_value) : 'n/a'}
        </div>
      </div>

      <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-4 dark:border-cyan-900/50 dark:bg-cyan-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-300">
          Melhor retorno real
        </div>
        <div className="mt-2 text-xl font-semibold text-cyan-900 dark:text-cyan-100">
          {bestReal?.label ?? 'n/a'}
        </div>
        <div className="mt-1 text-sm text-cyan-800 dark:text-cyan-200">
          {bestReal ? formatPercent(bestReal.real_cagr) : 'n/a'} ao ano
        </div>
      </div>

      <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700 dark:text-blue-300">
          Mais defensivo
        </div>
        <div className="mt-2 text-xl font-semibold text-blue-900 dark:text-blue-100">
          {mostDefensive?.label ?? 'n/a'}
        </div>
        <div className="mt-1 text-sm text-blue-800 dark:text-blue-200">
          drawdown maximo {mostDefensive ? formatPercent(mostDefensive.max_drawdown) : 'n/a'}
        </div>
      </div>

      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700 dark:text-amber-300">
          Acima da inflacao
        </div>
        <div className="mt-2 text-xl font-semibold text-amber-900 dark:text-amber-100">
          {highlights.beats_inflation_count ?? 0} / {resultCount}
        </div>
        <div className="mt-1 text-sm text-amber-800 dark:text-amber-200">
          comparativos preservaram poder de compra
        </div>
      </div>
    </div>
  );
}
