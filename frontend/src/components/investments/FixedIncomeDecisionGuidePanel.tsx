import type { InvestmentFixedIncomeDecisionGuidePayload } from '../../types/api';
import { formatInvestmentMetric } from './metricFormatting';

interface FixedIncomeDecisionGuidePanelProps {
  guide?: InvestmentFixedIncomeDecisionGuidePayload | null;
}

export default function FixedIncomeDecisionGuidePanel({
  guide,
}: FixedIncomeDecisionGuidePanelProps) {
  if (!guide) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-5 dark:border-emerald-900/50 dark:bg-emerald-950/20">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
            {guide.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-emerald-900/90 dark:text-emerald-100/90">
            {guide.plain_language_summary}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[11px] font-medium text-emerald-800 dark:text-emerald-200">
          {guide.study_label ? (
            <span className="rounded-full border border-emerald-300 bg-white/70 px-2 py-1 dark:border-emerald-700 dark:bg-emerald-950/40">
              {guide.study_label}
            </span>
          ) : null}
          {guide.tax_treatment ? (
            <span className="rounded-full border border-emerald-300 bg-white/70 px-2 py-1 dark:border-emerald-700 dark:bg-emerald-950/40">
              visão {guide.tax_treatment}
            </span>
          ) : null}
        </div>
      </div>

      {guide.profile_summary ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-white/70 px-4 py-3 text-sm leading-6 text-emerald-900 dark:border-emerald-900/50 dark:bg-gray-950/30 dark:text-emerald-100">
          {guide.profile_summary}
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-4">
        {guide.decision_cards.map((card) => (
          <div
            key={card.decision_id}
            className="rounded-2xl border border-emerald-200 bg-white p-4 dark:border-emerald-900/50 dark:bg-gray-950/40"
          >
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              {card.label}
            </div>
            {card.best_match_label ? (
              <div className="mt-2 text-lg font-semibold text-emerald-900 dark:text-emerald-100">
                {card.best_match_label}
              </div>
            ) : null}
            {card.metric_label ? (
              <div className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
                {card.metric_label}: {formatInvestmentMetric(card.metric_value, card.metric_kind)}
              </div>
            ) : null}
            {card.fit_label ? (
              <div className="mt-3 rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">
                {card.fit_label}
              </div>
            ) : null}
            <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-300">
              {card.when_it_fits}
            </p>
            {card.profile_reason ? (
              <p className="mt-2 text-xs leading-5 text-emerald-800 dark:text-emerald-200">
                {card.profile_reason}
              </p>
            ) : null}
            <div className="mt-3 rounded-xl bg-amber-50 px-3 py-3 text-xs leading-5 text-amber-800 dark:bg-amber-950/20 dark:text-amber-200">
              {card.watch_out}
            </div>
          </div>
        ))}
      </div>

      {guide.next_questions.length > 0 ? (
        <div className="mt-5 rounded-2xl border border-emerald-200 bg-white/70 p-4 dark:border-emerald-900/50 dark:bg-gray-950/30">
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            Antes de escolher, responda
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {guide.next_questions.map((question) => (
              <div
                key={question}
                className="rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100"
              >
                {question}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
