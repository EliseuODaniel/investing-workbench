import type { InvestmentStudyQualityPayload } from '../../types/api';
import { formatPercent } from '../../lib/utils';

interface InvestmentStudyQualityPanelProps {
  quality?: InvestmentStudyQualityPayload;
}

export default function InvestmentStudyQualityPanel({
  quality,
}: InvestmentStudyQualityPanelProps) {
  if (!quality) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5 dark:border-emerald-900/50 dark:bg-emerald-950/20">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
            {quality.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-emerald-900/90 dark:text-emerald-100/90">
            {quality.summary}
          </p>
        </div>
        <div className="rounded-full border border-emerald-300 bg-white px-3 py-2 text-xs font-semibold text-emerald-800 dark:border-emerald-700 dark:bg-gray-950/40 dark:text-emerald-200">
          {formatPercent(quality.readiness_score)} · {quality.status_label}
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {quality.checks.map((check) => (
          <article
            key={check.check_id}
            className={`rounded-xl border px-3 py-3 ${
              check.status === 'complete'
                ? 'border-emerald-200 bg-white dark:border-emerald-900/60 dark:bg-gray-950/40'
                : 'border-amber-200 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/20'
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-xs font-semibold text-gray-950 dark:text-gray-100">
                {check.label}
              </div>
              <span
                className={`rounded-full border px-2 py-1 text-[11px] font-medium ${
                  check.status === 'complete'
                    ? 'border-emerald-300 text-emerald-700 dark:border-emerald-700 dark:text-emerald-200'
                    : 'border-amber-300 text-amber-700 dark:border-amber-700 dark:text-amber-200'
                }`}
              >
                {check.status_label}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-gray-600 dark:text-gray-300">
              {check.detail}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
