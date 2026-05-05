import type { InvestmentProductRealismPayload } from '../../types/api';

interface InvestmentProductRealismPanelProps {
  realism?: InvestmentProductRealismPayload;
}

const STATUS_STYLES: Record<string, string> = {
  modeled:
    'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200',
  partial:
    'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-200',
  not_modeled:
    'border-slate-300 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200',
};

export default function InvestmentProductRealismPanel({
  realism,
}: InvestmentProductRealismPanelProps) {
  if (!realism || realism.coverage.length === 0) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {realism.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {realism.plain_language_summary}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {realism.product_types.map((item) => (
            <span
              key={item.source_kind}
              className="rounded-full border border-gray-300 bg-gray-50 px-3 py-1 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200"
            >
              {item.label}: {item.count}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {realism.coverage.map((dimension) => (
          <article
            key={dimension.dimension_id}
            className="rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                {dimension.label}
              </div>
              <span
                className={`rounded-full border px-2 py-1 text-[11px] font-medium uppercase tracking-[0.14em] ${
                  STATUS_STYLES[dimension.status] ?? STATUS_STYLES.not_modeled
                }`}
              >
                {dimension.status_label}
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-300">
              {dimension.summary}
            </p>

            {dimension.current_scope.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {dimension.current_scope.map((item) => (
                  <span
                    key={`${dimension.dimension_id}-${item}`}
                    className="rounded-full border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:bg-gray-900/80 dark:text-gray-300"
                  >
                    {item}
                  </span>
                ))}
              </div>
            ) : null}

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl bg-white px-3 py-3 text-xs leading-5 text-gray-500 dark:bg-gray-900/80 dark:text-gray-400">
                <span className="font-semibold text-gray-700 dark:text-gray-200">Limite: </span>
                {dimension.limitations}
              </div>
              <div className="rounded-xl bg-blue-50 px-3 py-3 text-xs leading-5 text-blue-800 dark:bg-blue-950/20 dark:text-blue-200">
                <span className="font-semibold">Proximo passo: </span>
                {dimension.next_step}
              </div>
            </div>
          </article>
        ))}
      </div>

      {realism.income_policy_examples?.length ? (
        <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
          <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
            Politica de renda e reinvestimento
          </div>
          <div className="mt-3 grid gap-3 xl:grid-cols-2">
            {realism.income_policy_examples.map((example) => (
              <article
                key={example.policy_id}
                className="rounded-xl border border-emerald-100 bg-white p-3 text-xs leading-5 text-emerald-900 dark:border-emerald-900/60 dark:bg-gray-950 dark:text-emerald-100"
              >
                <div className="text-sm font-semibold">{example.label}</div>
                <div className="mt-2 grid gap-2">
                  <p>{example.cashflow_treatment}</p>
                  <p>{example.tax_treatment}</p>
                  <p>{example.reinvestment_assumption}</p>
                  <p className="font-medium">{example.user_decision}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
        <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
          Fila metodologica
        </div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
          {realism.next_methodology_steps.map((step) => (
            <li key={step}>- {step}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
