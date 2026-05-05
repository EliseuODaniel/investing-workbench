import type { InvestmentRetailFixedIncomeEquivalencePayload } from '../../types/api';
import { formatPercent, formatNumber } from '../../lib/utils';

interface RetailFixedIncomeEquivalencePanelProps {
  equivalence?: InvestmentRetailFixedIncomeEquivalencePayload;
}

export default function RetailFixedIncomeEquivalencePanel({
  equivalence,
}: RetailFixedIncomeEquivalencePanelProps) {
  if (!equivalence || equivalence.rows.length === 0) {
    return null;
  }

  const profileRows = equivalence.rows.filter(
    (row) => row.holding_days === equivalence.profile_horizon_days
  );
  const fallbackRows = equivalence.rows.filter((row) => row.holding_days === 720);
  const visibleRows = profileRows.length ? profileRows : fallbackRows.slice(0, 5);

  return (
    <section className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5 dark:border-emerald-900/50 dark:bg-emerald-950/20">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
            {equivalence.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-emerald-900/90 dark:text-emerald-100/90">
            {equivalence.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-emerald-300 bg-white px-3 py-2 text-xs font-medium text-emerald-800 dark:border-emerald-700 dark:bg-gray-950/40 dark:text-emerald-200">
          CDI ref. {formatPercent(equivalence.reference_cdi_annual_rate)} a.a.
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-emerald-200 bg-white p-4 dark:border-emerald-800 dark:bg-gray-950/50">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Horizonte do perfil: {equivalence.profile_horizon_label}
          </div>
          {equivalence.uses_fixed_income_backtest ? (
            <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-[11px] font-medium text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
              estudo de renda fixa presente
            </span>
          ) : null}
        </div>

        <div className="mt-4 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr className="text-left text-xs uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
                  <th className="px-4 py-3">LCI/LCA</th>
                  <th className="px-4 py-3">CDB equivalente</th>
                  <th className="px-4 py-3">IR</th>
                  <th className="px-4 py-3">Retenção líquida</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                {visibleRows.map((row) => (
                  <tr
                    key={`${row.holding_days}-${row.tax_exempt_product}-${row.tax_exempt_pct_cdi}`}
                  >
                    <td className="px-4 py-4 text-gray-700 dark:text-gray-200">
                      <div className="font-semibold">
                        {formatPercent(row.tax_exempt_pct_cdi)} do CDI
                      </div>
                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {formatPercent(row.tax_exempt_annual_rate)} a.a. estimado
                      </div>
                    </td>
                    <td className="px-4 py-4 text-gray-900 dark:text-gray-100">
                      <div className="font-semibold">
                        {formatPercent(row.equivalent_cdb_pct_cdi)} do CDI
                      </div>
                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {formatPercent(row.equivalent_cdb_annual_rate)} a.a. bruto
                      </div>
                    </td>
                    <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                      <div>{formatPercent(row.ir_rate)}</div>
                      {row.iof_rate > 0 ? (
                        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          IOF {formatPercent(row.iof_rate)}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                      {formatPercent(row.net_gain_retention)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <p className="mt-3 text-xs leading-5 text-gray-500 dark:text-gray-400">
          Exemplo: {visibleRows[0]?.interpretation}
        </p>
      </div>

      {equivalence.taxable_product_examples?.length ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-white p-4 dark:border-emerald-800 dark:bg-gray-950/50">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Produtos tributados de referência
              </div>
              <p className="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">
                Comparação didática para enxergar o efeito de IR, IOF e taxa de administração
                antes de escolher entre liquidez, emissor e produto real.
              </p>
            </div>
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-[11px] font-medium text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
              prazo do perfil
            </span>
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
            {equivalence.taxable_product_examples.map((item) => (
              <article
                key={item.product_id}
                className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900/60"
              >
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {item.label}
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-300">
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Bruto</div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">
                      {formatPercent(item.gross_pct_cdi)} CDI
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Taxa</div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">
                      {formatPercent(item.annual_fee_rate)} a.a.
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Líquido</div>
                    <div className="font-semibold text-emerald-800 dark:text-emerald-200">
                      {formatPercent(item.net_pct_cdi)} CDI
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">IR</div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">
                      {formatPercent(item.ir_rate)}
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-xs leading-5 text-gray-600 dark:text-gray-300">
                  {item.interpretation}
                </p>
                <div className="mt-3 space-y-1 text-[11px] leading-4 text-gray-500 dark:text-gray-400">
                  <div>{item.liquidity}</div>
                  <div>{item.credit_note}</div>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <div className="rounded-2xl border border-emerald-200 bg-white p-4 dark:border-emerald-800 dark:bg-gray-950/50">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Premissas
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
            {equivalence.assumptions.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-blue-200 bg-blue-50/80 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
          <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
            Próximas comparações
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
            {equivalence.next_steps.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-3 text-xs text-emerald-900/70 dark:text-emerald-100/70">
        Prazo usado: {formatNumber(equivalence.profile_horizon_days, 0)} dias corridos.
      </div>
    </section>
  );
}
