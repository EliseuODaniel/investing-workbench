import type { InvestmentPortfolioLifecyclePayload } from '../../types/api';
import { formatInvestmentMetric } from './metricFormatting';

interface InvestmentPortfolioLifecyclePanelProps {
  lifecycle?: InvestmentPortfolioLifecyclePayload;
}

export default function InvestmentPortfolioLifecyclePanel({
  lifecycle,
}: InvestmentPortfolioLifecyclePanelProps) {
  if (!lifecycle || lifecycle.scenario_cards.length === 0) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {lifecycle.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {lifecycle.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-gray-300 bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200">
          {lifecycle.uses_portfolio_rows
            ? `${lifecycle.portfolio_count} carteira${lifecycle.portfolio_count === 1 ? '' : 's'}`
            : 'sem carteira dedicada'}
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        {lifecycle.scenario_cards.map((scenario) => (
          <article
            key={scenario.scenario_id}
            className="rounded-2xl border border-cyan-200 bg-cyan-50/60 p-4 dark:border-cyan-900/50 dark:bg-cyan-950/20"
          >
            <div className="text-sm font-semibold text-cyan-950 dark:text-cyan-100">
              {scenario.label}
            </div>
            <p className="mt-2 text-sm leading-6 text-cyan-900/80 dark:text-cyan-100/80">
              {scenario.description}
            </p>
            <div className="mt-4 rounded-xl bg-white px-3 py-3 dark:bg-gray-950/40">
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {scenario.best_match_label ?? 'n/a'}
              </div>
              <div className="mt-1 text-lg font-semibold text-gray-950 dark:text-gray-100">
                {scenario.metric_label}:{' '}
                {formatInvestmentMetric(scenario.metric_value, scenario.metric_kind)}
              </div>
              {scenario.comparison_label ? (
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  comparado com {scenario.comparison_label}
                </div>
              ) : null}
            </div>
            {scenario.target_value && scenario.target_value > 0 ? (
              <div
                className={`mt-3 rounded-xl px-3 py-2 text-xs font-medium ${
                  scenario.target_met
                    ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100'
                    : 'bg-amber-50 text-amber-800 dark:bg-amber-950/30 dark:text-amber-100'
                }`}
              >
                Meta: {formatInvestmentMetric(scenario.target_value, scenario.metric_kind)} ·{' '}
                {scenario.target_met ? 'atingida neste recorte' : 'abaixo neste recorte'}
              </div>
            ) : null}
          </article>
        ))}
      </div>

      {lifecycle.withdrawal_plan?.candidates.length ? (
        <div className="mt-5 rounded-2xl border border-indigo-200 bg-indigo-50/60 p-4 dark:border-indigo-900/50 dark:bg-indigo-950/20">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-indigo-950 dark:text-indigo-100">
                {lifecycle.withdrawal_plan.title}
              </div>
              <p className="mt-1 text-sm leading-6 text-indigo-900/80 dark:text-indigo-100/80">
                {lifecycle.withdrawal_plan.feasibility_label}
              </p>
            </div>
            <div className="rounded-full border border-indigo-300 bg-white px-3 py-2 text-xs font-medium text-indigo-800 dark:border-indigo-700 dark:bg-gray-950/40 dark:text-indigo-200">
              {formatInvestmentMetric(
                lifecycle.withdrawal_plan.withdrawal_rate,
                'percent'
              )}{' '}
              a.a.
            </div>
          </div>

          <div className="mt-4 overflow-hidden rounded-xl border border-indigo-200 bg-white dark:border-indigo-900/50 dark:bg-gray-950/40">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-indigo-100 text-sm dark:divide-indigo-900/50">
                <thead className="bg-indigo-50/80 dark:bg-indigo-950/30">
                  <tr className="text-left text-xs uppercase tracking-[0.14em] text-indigo-700/80 dark:text-indigo-200/80">
                    <th className="px-4 py-3">Alternativa</th>
                    <th className="px-4 py-3">Retirada mensal</th>
                    <th className="px-4 py-3">Gap da meta</th>
                    <th className="px-4 py-3">Risco historico</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-indigo-100 dark:divide-indigo-900/50">
                  {lifecycle.withdrawal_plan.candidates.map((candidate) => (
                    <tr key={candidate.instrument_id}>
                      <td className="px-4 py-4 text-gray-800 dark:text-gray-100">
                        <div className="font-semibold">{candidate.label}</div>
                        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          {formatInvestmentMetric(
                            candidate.final_value_real_net,
                            'currency'
                          )}{' '}
                          reais líquidos
                        </div>
                      </td>
                      <td className="px-4 py-4 font-semibold text-indigo-900 dark:text-indigo-100">
                        {formatInvestmentMetric(candidate.monthly_withdrawal, 'currency')}
                      </td>
                      <td className="px-4 py-4 text-gray-700 dark:text-gray-200">
                        {candidate.income_gap === null || candidate.income_gap === undefined ? (
                          'sem meta'
                        ) : (
                          <span
                            className={
                              candidate.target_met
                                ? 'font-semibold text-emerald-700 dark:text-emerald-200'
                                : 'font-semibold text-amber-700 dark:text-amber-200'
                            }
                          >
                            {formatInvestmentMetric(candidate.income_gap, 'currency')}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                        <div>
                          DD {formatInvestmentMetric(candidate.max_drawdown, 'percent')}
                        </div>
                        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          real {formatInvestmentMetric(candidate.real_cagr, 'percent')} a.a.
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {lifecycle.withdrawal_plan.stress_tests?.length ? (
            <div className="mt-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm font-semibold text-indigo-950 dark:text-indigo-100">
                  Stress test de aposentadoria
                </div>
                {lifecycle.withdrawal_plan.stress_summary ? (
                  <div className="max-w-2xl text-xs leading-5 text-indigo-900/80 dark:text-indigo-100/80">
                    {lifecycle.withdrawal_plan.stress_summary}
                  </div>
                ) : null}
              </div>
              <div className="mt-3 grid gap-3 lg:grid-cols-3">
                {lifecycle.withdrawal_plan.stress_tests.map((scenario) => (
                  <article
                    key={scenario.scenario_id}
                    className="rounded-xl border border-indigo-200 bg-white p-4 dark:border-indigo-900/50 dark:bg-gray-950/40"
                  >
                    <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                      {scenario.label}
                    </div>
                    <p className="mt-2 min-h-12 text-xs leading-5 text-gray-500 dark:text-gray-400">
                      {scenario.description}
                    </p>
                    <div className="mt-3 text-lg font-semibold text-indigo-950 dark:text-indigo-100">
                      {formatInvestmentMetric(
                        scenario.stressed_monthly_withdrawal,
                        'currency'
                      )}
                    </div>
                    <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      multiplicador{' '}
                      {formatInvestmentMetric(scenario.withdrawal_multiplier, 'percent')} ·
                      buffer DD {formatInvestmentMetric(scenario.drawdown_buffer, 'percent')}
                    </div>
                    <div
                      className={`mt-3 rounded-lg px-3 py-2 text-xs font-medium ${
                        scenario.target_met
                          ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100'
                          : 'bg-amber-50 text-amber-800 dark:bg-amber-950/30 dark:text-amber-100'
                      }`}
                    >
                      {scenario.interpretation}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ) : null}

          {lifecycle.withdrawal_plan.monte_carlo_preview?.scenarios.length ? (
            <div className="mt-4 rounded-2xl border border-violet-200 bg-violet-50/70 p-4 dark:border-violet-900/50 dark:bg-violet-950/20">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-violet-950 dark:text-violet-100">
                    {lifecycle.withdrawal_plan.monte_carlo_preview.title}
                  </div>
                  <p className="mt-1 max-w-4xl text-xs leading-5 text-violet-900/80 dark:text-violet-100/80">
                    {lifecycle.withdrawal_plan.monte_carlo_preview.methodology}
                  </p>
                </div>
                <div className="rounded-full border border-violet-300 bg-white px-3 py-2 text-xs font-medium text-violet-800 dark:border-violet-800 dark:bg-gray-950/40 dark:text-violet-200">
                  cobertura{' '}
                  {formatInvestmentMetric(
                    lifecycle.withdrawal_plan.monte_carlo_preview.coverage_score,
                    'percent'
                  )}
                </div>
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                {lifecycle.withdrawal_plan.monte_carlo_preview.scenarios.map((scenario) => (
                  <article
                    key={scenario.scenario_id}
                    className="rounded-xl border border-violet-200 bg-white p-4 dark:border-violet-900/50 dark:bg-gray-950/40"
                  >
                    <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                      {scenario.label}
                    </div>
                    <p className="mt-2 min-h-10 text-xs leading-5 text-gray-500 dark:text-gray-400">
                      {scenario.description}
                    </p>
                    <div className="mt-3 text-lg font-semibold text-violet-950 dark:text-violet-100">
                      {formatInvestmentMetric(scenario.monthly_withdrawal, 'currency')}
                    </div>
                    <div
                      className={`mt-3 rounded-lg px-3 py-2 text-xs font-medium ${
                        scenario.target_met
                          ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100'
                          : 'bg-amber-50 text-amber-800 dark:bg-amber-950/30 dark:text-amber-100'
                      }`}
                    >
                      Gap{' '}
                      {scenario.income_gap === null || scenario.income_gap === undefined
                        ? 'sem meta'
                        : formatInvestmentMetric(scenario.income_gap, 'currency')}
                    </div>
                  </article>
                ))}
              </div>

              <div className="mt-3 grid gap-3 text-xs text-violet-900/80 dark:text-violet-100/80 md:grid-cols-3">
                <div>
                  Retorno real{' '}
                  {formatInvestmentMetric(
                    lifecycle.withdrawal_plan.monte_carlo_preview.real_cagr,
                    'percent'
                  )}
                </div>
                <div>
                  Volatilidade{' '}
                  {formatInvestmentMetric(
                    lifecycle.withdrawal_plan.monte_carlo_preview.annual_volatility,
                    'percent'
                  )}
                </div>
                <div>
                  Anos na meta{' '}
                  {formatInvestmentMetric(
                    lifecycle.withdrawal_plan.monte_carlo_preview.years_of_income_at_target,
                    'number'
                  )}
                </div>
              </div>
              <p className="mt-3 text-xs leading-5 text-violet-900/70 dark:text-violet-100/70">
                {lifecycle.withdrawal_plan.monte_carlo_preview.caveat}
              </p>

              {lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence?.paths
                .length ? (
                <div className="mt-4 rounded-xl border border-violet-200 bg-white p-4 dark:border-violet-900/50 dark:bg-gray-950/40">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                        {
                          lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                            .title
                        }
                      </div>
                      <p className="mt-1 max-w-4xl text-xs leading-5 text-gray-500 dark:text-gray-400">
                        {
                          lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                            .methodology
                        }
                      </p>
                    </div>
                    <div className="rounded-full border border-violet-300 bg-violet-50 px-3 py-2 text-xs font-medium text-violet-800 dark:border-violet-800 dark:bg-violet-950/30 dark:text-violet-200">
                      sucesso{' '}
                      {formatInvestmentMetric(
                        lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                          .success_rate,
                        'percent'
                      )}
                    </div>
                  </div>
                  <div className="mt-3 grid gap-3 text-xs text-gray-600 dark:text-gray-300 md:grid-cols-3">
                    <div>
                      Retirada{' '}
                      {formatInvestmentMetric(
                        lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                          .monthly_withdrawal,
                        'currency'
                      )}
                    </div>
                    <div>
                      Retorno mensal base{' '}
                      {formatInvestmentMetric(
                        lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                          .monthly_base_return,
                        'percent'
                      )}
                    </div>
                    <div>
                      Horizonte{' '}
                      {
                        lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                          .horizon_years
                      }{' '}
                      anos
                    </div>
                  </div>
                  <div className="mt-3 grid gap-3 lg:grid-cols-3">
                    {lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence.paths.map(
                      (path) => (
                        <article
                          key={path.path_id}
                          className="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-800 dark:bg-gray-900/60"
                        >
                          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                            {path.label}
                          </div>
                          <div className="mt-2 text-xs leading-5 text-gray-500 dark:text-gray-400">
                            retorno mensal{' '}
                            {formatInvestmentMetric(path.monthly_return, 'percent')}
                            {path.early_shock > 0
                              ? ` · choque inicial ${formatInvestmentMetric(
                                  path.early_shock,
                                  'percent'
                                )}`
                              : ''}
                          </div>
                          <div
                            className={`mt-3 rounded-lg px-3 py-2 text-xs font-medium ${
                              path.survived_horizon
                                ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100'
                                : 'bg-rose-50 text-rose-800 dark:bg-rose-950/30 dark:text-rose-100'
                            }`}
                          >
                            {path.survived_horizon
                              ? `saldo final ${formatInvestmentMetric(
                                  path.final_balance,
                                  'currency'
                                )}`
                              : `exaure no ano ${formatInvestmentMetric(
                                  path.exhaustion_year,
                                  'number'
                                )}`}
                          </div>
                        </article>
                      )
                    )}
                  </div>
                  {lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence.stochastic ? (
                    <div className="mt-4 rounded-xl border border-violet-200 bg-violet-50/70 p-4 dark:border-violet-900/50 dark:bg-violet-950/20">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-violet-950 dark:text-violet-100">
                            {
                              lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                                .stochastic.title
                            }
                          </div>
                          <p className="mt-1 max-w-4xl text-xs leading-5 text-violet-900/80 dark:text-violet-100/80">
                            {
                              lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                                .stochastic.methodology
                            }
                          </p>
                        </div>
                        <div className="rounded-full border border-violet-300 bg-white px-3 py-2 text-xs font-medium text-violet-800 dark:border-violet-800 dark:bg-gray-950/40 dark:text-violet-200">
                          {
                            lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                              .stochastic.simulation_count
                          }{' '}
                          trajetórias
                        </div>
                      </div>
                      <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
                        <MonteCarloMetric
                          label="Sucesso"
                          value={formatInvestmentMetric(
                            lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                              .stochastic.success_rate,
                            'percent'
                          )}
                        />
                        <MonteCarloMetric
                          label="Saldo P10"
                          value={formatInvestmentMetric(
                            lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                              .stochastic.percentiles.final_balance_p10,
                            'currency'
                          )}
                        />
                        <MonteCarloMetric
                          label="Saldo P50"
                          value={formatInvestmentMetric(
                            lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                              .stochastic.percentiles.final_balance_p50,
                            'currency'
                          )}
                        />
                        <MonteCarloMetric
                          label="Exaustão mediana"
                          value={
                            lifecycle.withdrawal_plan.monte_carlo_preview.monthly_sequence
                              .stochastic.median_exhaustion_year
                              ? `${formatInvestmentMetric(
                                  lifecycle.withdrawal_plan.monte_carlo_preview
                                    .monthly_sequence.stochastic.median_exhaustion_year,
                                  'number'
                                )} anos`
                              : 'sem exaustão'
                          }
                        />
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      {lifecycle.smart_contributions && lifecycle.smart_contributions.allocations.length > 0 ? (
        <div className="mt-5 rounded-2xl border border-indigo-200 bg-indigo-50/50 p-5 dark:border-indigo-900/40 dark:bg-indigo-950/20">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-indigo-950 dark:text-indigo-100">
                {lifecycle.smart_contributions.title}
              </div>
              <p className="mt-1 text-xs leading-5 text-indigo-900/80 dark:text-indigo-200/80">
                {lifecycle.smart_contributions.description}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-900 dark:bg-indigo-900/60 dark:text-indigo-100">
                Aporte: {formatInvestmentMetric(lifecycle.smart_contributions.contribution_amount, 'currency')}
              </span>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-900 dark:bg-emerald-900/60 dark:text-emerald-100">
                Eficiência: {lifecycle.smart_contributions.efficiency_score_pct.toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-indigo-200/60 text-indigo-950/70 dark:border-indigo-800/60 dark:text-indigo-200/70">
                  <th className="py-2 pr-3 font-medium">Ativo</th>
                  <th className="py-2 px-3 font-medium text-right">Meta</th>
                  <th className="py-2 px-3 font-medium text-right">Peso Atual</th>
                  <th className="py-2 px-3 font-medium text-right">Aporte Sugerido</th>
                  <th className="py-2 px-3 font-medium text-right">Peso Projetado</th>
                  <th className="py-2 pl-3 font-medium text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-indigo-100/60 dark:divide-indigo-900/40">
                {lifecycle.smart_contributions.allocations.map((item) => (
                  <tr key={item.instrument_id} className="text-gray-900 dark:text-gray-100">
                    <td className="py-2.5 pr-3 font-semibold text-indigo-950 dark:text-indigo-100">
                      {item.label}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {item.target_weight_pct.toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-600 dark:text-gray-300">
                      {item.current_weight_pct.toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-3 text-right font-semibold text-indigo-700 dark:text-indigo-300">
                      {item.suggested_contribution > 0
                        ? `${formatInvestmentMetric(item.suggested_contribution, 'currency')} (${item.suggested_contribution_pct.toFixed(0)}%)`
                        : 'R$ 0,00'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-medium">
                      {item.projected_weight_pct.toFixed(1)}%
                    </td>
                    <td className="py-2.5 pl-3 text-center">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${
                          item.rebalance_status === 'underweight_receiving'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200'
                            : item.rebalance_status === 'overweight_hold'
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-200'
                              : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                        }`}
                      >
                        {item.rebalance_status === 'underweight_receiving'
                          ? 'Aportar'
                          : item.rebalance_status === 'overweight_hold'
                            ? 'Aguardar'
                            : 'Equilibrado'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-3 text-[11px] leading-5 text-indigo-900/70 dark:text-indigo-200/70">
            {lifecycle.smart_contributions.methodology}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <TextList title="Premissas" items={lifecycle.assumptions} />
        <TextList title="Próximos refinamentos" items={lifecycle.next_steps} />
      </div>
    </section>
  );
}

function MonteCarloMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-violet-200 bg-white px-3 py-3 dark:border-violet-900/50 dark:bg-gray-950/40">
      <div className="text-[11px] uppercase tracking-[0.12em] text-violet-700/80 dark:text-violet-200/80">
        {label}
      </div>
      <div className="mt-1 font-semibold text-gray-950 dark:text-gray-100">{value}</div>
    </div>
  );
}

function TextList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30">
      <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">{title}</div>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
        {items.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </div>
  );
}
