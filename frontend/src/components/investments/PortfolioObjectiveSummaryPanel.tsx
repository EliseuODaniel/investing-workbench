import type { InvestmentPortfolioObjectiveSummaryPayload } from '../../types/api';
import { formatCurrency, formatPercent } from '../../lib/utils';
import { formatInvestmentMetric } from './metricFormatting';

interface PortfolioObjectiveSummaryPanelProps {
  summary?: InvestmentPortfolioObjectiveSummaryPayload;
}

export default function PortfolioObjectiveSummaryPanel({
  summary,
}: PortfolioObjectiveSummaryPanelProps) {
  if (!summary) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-gray-200 p-5 dark:border-gray-800">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {summary.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {summary.plain_language_summary}
          </p>
        </div>
        {summary.fixed_income_study_available ? (
          <div className="rounded-full border border-blue-300 bg-blue-50 px-3 py-2 text-xs font-medium text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
            inclui leitura de renda fixa
          </div>
        ) : null}
      </div>

      {summary.profile_summary ? (
        <div className="mt-4 rounded-2xl border border-blue-200 bg-blue-50/70 px-4 py-3 text-sm leading-6 text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/20 dark:text-blue-100">
          {summary.profile_summary}
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-4">
        {summary.objectives.map((objective) => (
          <div
            key={objective.objective_id}
            className="rounded-2xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900/60"
          >
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
              {objective.label}
            </div>
            <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              {objective.question}
            </div>
            <div className="mt-3 text-xl font-semibold text-gray-950 dark:text-gray-50">
              {objective.best_match_label ?? 'n/a'}
            </div>
            {objective.metric_label ? (
              <div className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                {objective.metric_label}:{' '}
                {formatInvestmentMetric(objective.metric_value, objective.metric_kind)}
              </div>
            ) : null}
            {objective.fit_label ? (
              <div className="mt-3 rounded-full border border-blue-300 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
                {objective.fit_label}
              </div>
            ) : null}
            <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-300">
              {objective.reason}
            </p>
            {objective.profile_reason ? (
              <p className="mt-2 text-xs leading-5 text-blue-800 dark:text-blue-200">
                {objective.profile_reason}
              </p>
            ) : null}
            <div className="mt-3 rounded-xl bg-white px-3 py-3 text-xs leading-5 text-gray-500 dark:bg-gray-950/50 dark:text-gray-400">
              {objective.tradeoff}
            </div>
          </div>
        ))}
      </div>

      {summary.scenario_cards?.length ? (
        <div className="mt-5 rounded-2xl border border-cyan-200 bg-cyan-50/60 p-4 dark:border-cyan-900/50 dark:bg-cyan-950/20">
          <div className="text-sm font-semibold text-cyan-950 dark:text-cyan-100">
            Cenários de carteira e objetivo
          </div>
          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            {summary.scenario_cards.map((scenario) => (
              <div
                key={scenario.scenario_id}
                className="rounded-2xl border border-cyan-200 bg-white p-4 dark:border-cyan-900/50 dark:bg-gray-950/40"
              >
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {scenario.label}
                </div>
                <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
                  {scenario.description}
                </p>
                <div className="mt-3 text-lg font-semibold text-cyan-900 dark:text-cyan-100">
                  {scenario.best_match_label ?? 'n/a'}
                </div>
                <div className="mt-1 text-sm text-cyan-800 dark:text-cyan-200">
                  {scenario.metric_label}:{' '}
                  {formatInvestmentMetric(scenario.metric_value, scenario.metric_kind)}
                </div>
                {scenario.target_value && scenario.target_value > 0 ? (
                  <div
                    className={`mt-3 rounded-xl px-3 py-2 text-xs font-medium ${
                      scenario.target_met
                        ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-200'
                        : 'bg-amber-50 text-amber-800 dark:bg-amber-950/20 dark:text-amber-200'
                    }`}
                  >
                    {scenario.target_met
                      ? 'Atinge a meta de renda informada neste cálculo simples.'
                      : 'Fica abaixo da meta de renda informada neste cálculo simples.'}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {summary.portfolio_rows.length > 0 ? (
        <div className="mt-5 rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Carteiras no estudo
          </div>
          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            {summary.portfolio_rows.map((row) => (
              <div
                key={row.instrument_id ?? row.label}
                className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900/60"
              >
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {row.label}
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {row.component_count} sleeves | final {formatCurrency(row.final_value)} | CAGR
                  real {formatPercent(row.real_cagr)}
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {row.top_components.map((component) => (
                    <span
                      key={`${row.instrument_id}-${component.label}`}
                      className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200"
                    >
                      {component.label}: alvo {formatPercent(component.target_weight)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {summary.next_steps.length > 0 ? (
        <div className="mt-5 rounded-2xl border border-dashed border-gray-300 p-4 dark:border-gray-700">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Próximos passos de leitura
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
            {summary.next_steps.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
