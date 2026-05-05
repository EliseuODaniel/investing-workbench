import type { InvestmentMarketScreenersPayload } from '../../types/api';
import { formatCurrency, formatPercent } from '../../lib/utils';

interface InvestmentMarketScreenersPanelProps {
  screeners?: InvestmentMarketScreenersPayload;
}

export default function InvestmentMarketScreenersPanel({
  screeners,
}: InvestmentMarketScreenersPanelProps) {
  if (!screeners || screeners.presets.length === 0) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {screeners.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {screeners.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-gray-300 bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200">
          {screeners.universe_count} ativos
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {screeners.presets.map((preset) => (
          <article
            key={preset.preset_id}
            className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800"
          >
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-800 dark:bg-gray-950/50">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                    {preset.label}
                  </div>
                  <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {preset.rule_summary}
                  </div>
                </div>
                <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-[11px] font-medium text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
                  {preset.matched_count}/{preset.universe_count}
                </span>
              </div>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
              {preset.rows.length === 0 ? (
                <div className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">
                  Nenhum item passou neste filtro.
                </div>
              ) : (
                preset.rows.slice(0, 5).map((row) => (
                  <div
                    key={`${preset.preset_id}-${row.instrument_id}`}
                    className="grid grid-cols-[auto_1fr_auto] items-center gap-3 px-4 py-3 text-sm"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-200">
                      {row.rank}
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                        {row.label}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {row.category_label} · drawdown {formatPercent(row.max_drawdown)}
                      </div>
                    </div>
                    <div className="text-right text-xs font-semibold text-gray-900 dark:text-gray-100">
                      <div>real {formatPercent(row.real_cagr)}</div>
                      <div>{formatCurrency(row.net_profit)}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </article>
        ))}
      </div>

      <div className="mt-5 rounded-2xl border border-dashed border-gray-300 p-4 dark:border-gray-700">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Como usar estes filtros
        </div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          {screeners.methodology_notes.map((note) => (
            <li key={note}>- {note}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
