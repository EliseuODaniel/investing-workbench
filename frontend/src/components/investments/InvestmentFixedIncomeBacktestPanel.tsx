import { formatCurrency, formatDate, formatNumber, formatPercent } from '../../lib/utils';
import type {
  InvestmentFixedIncomeBacktestPayload,
  InvestmentFixedIncomeResultPayload,
  InvestmentFixedIncomeStudyPayload,
  InvestmentFixedIncomeWindowPayload,
} from '../../types/api';

interface InvestmentFixedIncomeBacktestPanelProps {
  backtest?: InvestmentFixedIncomeBacktestPayload | null;
}

interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  tone: 'blue' | 'amber' | 'emerald' | 'cyan';
}

const metricCardTones: Record<MetricCardProps['tone'], string> = {
  blue: 'border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/20 dark:text-blue-100',
  amber:
    'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100',
  emerald:
    'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-100',
  cyan: 'border-cyan-200 bg-cyan-50 text-cyan-900 dark:border-cyan-900/50 dark:bg-cyan-950/20 dark:text-cyan-100',
};

const metricLabelTones: Record<MetricCardProps['tone'], string> = {
  blue: 'text-blue-700 dark:text-blue-300',
  amber: 'text-amber-700 dark:text-amber-300',
  emerald: 'text-emerald-700 dark:text-emerald-300',
  cyan: 'text-cyan-700 dark:text-cyan-300',
};

function groupRollingWindows(rows: InvestmentFixedIncomeWindowPayload[]) {
  const grouped = new Map<number, InvestmentFixedIncomeWindowPayload[]>();
  for (const row of rows) {
    const current = grouped.get(row.window_years) ?? [];
    current.push(row);
    grouped.set(row.window_years, current);
  }
  return Array.from(grouped.entries())
    .sort(([left], [right]) => left - right)
    .map(([windowYears, groupedRows]) => ({
      windowYears,
      rows: [...groupedRows].sort((left, right) => right.win_rate - left.win_rate),
    }));
}

function MetricCard({ label, value, detail, tone }: MetricCardProps) {
  return (
    <div className={`rounded-2xl border p-4 ${metricCardTones[tone]}`}>
      <div className={`text-xs font-semibold uppercase tracking-[0.18em] ${metricLabelTones[tone]}`}>
        {label}
      </div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
      <div className="mt-1 text-sm opacity-85">{detail}</div>
    </div>
  );
}

function StudyResultTable({ study }: { study: InvestmentFixedIncomeStudyPayload }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr className="text-left text-xs uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
              <th className="px-4 py-3">Instrumento</th>
              <th className="px-4 py-3">Família</th>
              <th className="px-4 py-3">Valor final</th>
              <th className="px-4 py-3">Valor real</th>
              <th className="px-4 py-3">Vs benchmark</th>
              <th className="px-4 py-3">CAGR</th>
              <th className="px-4 py-3">DD máx</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
            {study.full_period.results.map((row) => (
              <tr key={`${study.study_id}-${row.instrument_id}`}>
                <td className="px-4 py-4 align-top">
                  <div className="font-semibold text-gray-900 dark:text-gray-100">{row.label}</div>
                  <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {row.duration_years
                      ? `duration alvo de ${formatNumber(row.duration_years, 1)} anos`
                      : 'referência pós-fixada'}
                  </div>
                  <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {row.source_method_label}
                  </div>
                </td>
                <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                  {row.family_label}
                </td>
                <td className="px-4 py-4 text-gray-900 dark:text-gray-100">
                  <div className="font-semibold">{formatCurrency(row.display_value)}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    lucro {formatCurrency(row.display_profit)}
                  </div>
                  {Math.abs(row.final_value_net - row.final_value) > 0.01 ? (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      bruto {formatCurrency(row.final_value)} | líquido{' '}
                      {formatCurrency(row.final_value_net)}
                    </div>
                  ) : null}
                </td>
                <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                  <div>{formatCurrency(row.display_value_real)}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    CAGR real {formatPercent(row.display_real_cagr)}
                  </div>
                </td>
                <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                  <div>{formatPercent(row.relative_gap_vs_benchmark)}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {formatCurrency(row.value_gap_vs_benchmark)}
                  </div>
                </td>
                <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                  <div>{formatPercent(row.display_cagr)}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    real {formatPercent(row.display_real_cagr)}
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
  );
}

function StudyMethodologyCards({ study }: { study: InvestmentFixedIncomeStudyPayload }) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">Isso mede</div>
        <div className="mt-3 rounded-xl bg-gray-50 px-3 py-3 text-sm text-gray-600 dark:bg-gray-900/60 dark:text-gray-300">
          {study.methodology.what_it_measures ?? study.methodology.index_methodology_label}
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">Isso não mede</div>
        <div className="mt-3 rounded-xl bg-gray-50 px-3 py-3 text-sm text-gray-600 dark:bg-gray-900/60 dark:text-gray-300">
          {study.methodology.what_it_does_not_measure ?? study.methodology.full_period_note}
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Leitura do estudo
        </div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          {study.takeaways.map((item) => (
            <li key={item}>- {item}</li>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Fontes e método
        </div>
        <div className="mt-3 space-y-3 text-sm text-gray-600 dark:text-gray-300">
          <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
            {study.methodology.index_methodology_label}
          </div>
          <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
            {study.methodology.series_source_label}
          </div>
          <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
            {study.methodology.rolling_window_note}
          </div>
        </div>
      </div>
    </div>
  );
}

function RollingWindowCards({ study }: { study: InvestmentFixedIncomeStudyPayload }) {
  const groupedWindows = groupRollingWindows(study.rolling_windows);

  return (
    <div className="mt-5 grid gap-4 xl:grid-cols-4">
      {groupedWindows.map((group) => (
        <div
          key={`${study.study_id}-${group.windowYears}`}
          className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800"
        >
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Janelas de {group.windowYears} {group.windowYears === 1 ? 'ano' : 'anos'}
          </div>
          <div className="mt-3 space-y-3">
            {group.rows.map((row) => (
              <div
                key={`${study.study_id}-${row.instrument_id}-${group.windowYears}`}
                className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-900/60"
              >
                <div className="font-semibold text-gray-900 dark:text-gray-100">{row.label}</div>
                <div className="mt-1 text-gray-600 dark:text-gray-300">
                  venceu o benchmark em {formatPercent(row.win_rate)}
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  {formatNumber(row.windows_count, 0)} janelas
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  excesso médio {formatPercent(row.average_excess_return)}
                </div>
                {row.best_window_start && row.best_window_end ? (
                  <div className="text-gray-500 dark:text-gray-400">
                    melhor janela {formatDate(row.best_window_start)} até{' '}
                    {formatDate(row.best_window_end)}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function formatLeaderValue(leader?: InvestmentFixedIncomeResultPayload) {
  return leader ? formatCurrency(leader.display_value) : 'n/a';
}

function FixedIncomeStudyCard({ study }: { study: InvestmentFixedIncomeStudyPayload }) {
  const leaders = study.full_period.leaders;
  const overallLeader = leaders.overall;
  const prefixadoLeader = leaders.prefixado;
  const ipcaLeader = leaders.ipca_plus;
  const consistentLeader = leaders.most_consistent;

  return (
    <div className="rounded-2xl border border-gray-200 p-5 dark:border-gray-800">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {study.study_label}
          </div>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            {study.methodology.study_scope_label ?? study.methodology.index_methodology_label}
          </p>
        </div>
        <div className="rounded-xl bg-gray-50 px-3 py-2 text-xs text-gray-600 dark:bg-gray-900/60 dark:text-gray-300">
          Métrica principal: {study.methodology.comparison_metric_label ?? 'valor final'}
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-4">
        <MetricCard
          label="Líder geral"
          value={overallLeader?.label ?? 'n/a'}
          detail={formatLeaderValue(overallLeader)}
          tone="blue"
        />
        <MetricCard
          label="Melhor prefixado"
          value={prefixadoLeader?.label ?? 'n/a'}
          detail={formatLeaderValue(prefixadoLeader)}
          tone="amber"
        />
        <MetricCard
          label="Melhor IPCA+"
          value={ipcaLeader?.label ?? 'n/a'}
          detail={formatLeaderValue(ipcaLeader)}
          tone="emerald"
        />
        <MetricCard
          label="Mais consistente"
          value={consistentLeader?.label ?? 'n/a'}
          detail={consistentLeader ? `${formatPercent(consistentLeader.win_rate)} em 5 anos` : 'n/a'}
          tone="cyan"
        />
      </div>

      <div className="mt-5 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <StudyResultTable study={study} />
        <StudyMethodologyCards study={study} />
      </div>

      <RollingWindowCards study={study} />
    </div>
  );
}

export default function InvestmentFixedIncomeBacktestPanel({
  backtest,
}: InvestmentFixedIncomeBacktestPanelProps) {
  if (!backtest) {
    return null;
  }

  const studies = backtest.studies ?? [];

  return (
    <section className="space-y-5 rounded-2xl border border-gray-200 p-5 dark:border-gray-800">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Backtests de renda fixa
          </div>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Esta área separa o que é índice teórico de duration constante do que é experiência real
            de Tesouro Direto com preços oficiais e visão líquida.
          </p>
        </div>
        {backtest.methodology.video_reference_match ? (
          <div className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-200">
            Recorte alinhado ao vídeo
          </div>
        ) : null}
      </div>

      {backtest.summary?.takeaways?.length ? (
        <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
          <div className="text-sm font-semibold text-blue-900 dark:text-blue-100">
            O que muda quando trocamos a metodologia
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
            {backtest.summary.takeaways.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {studies.map((study) => (
        <FixedIncomeStudyCard key={study.study_id} study={study} />
      ))}
    </section>
  );
}
