import { Download } from 'lucide-react';
import { downloadCSV, formatCurrency, formatPercent, formatNumber } from '../../lib/utils';
import type {
  InvestmentMarketRankingPayload,
  InvestmentMarketRankingsPayload,
} from '../../types/api';

interface InvestmentMarketRankingsPanelProps {
  rankings?: InvestmentMarketRankingsPayload;
}

export default function InvestmentMarketRankingsPanel({
  rankings,
}: InvestmentMarketRankingsPanelProps) {
  if (!rankings || rankings.rankings.length === 0) {
    return null;
  }

  const visibleRankings = rankings.rankings.slice(0, 8);

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {rankings.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {rankings.plain_language_summary}
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span>{rankings.universe_label}</span>
            {rankings.as_of_date ? <span>Base ate {rankings.as_of_date}</span> : null}
            <span>{rankings.source_label}</span>
          </div>
        </div>
        <button
          type="button"
          className="btn-secondary inline-flex items-center gap-2"
          onClick={() => downloadCSV(toRankingsCsv(rankings), 'investment_market_rankings.csv')}
        >
          <Download className="h-4 w-4" />
          CSV
        </button>
      </div>

      {rankings.benchmark_context.length > 0 ? (
        <div className="mt-5 grid gap-3 lg:grid-cols-2">
          {rankings.benchmark_context.map((item) => (
            <div
              key={item.benchmark_id}
              className="rounded-2xl border border-blue-200 bg-blue-50/70 p-4 text-sm text-blue-950 dark:border-blue-900/50 dark:bg-blue-950/20 dark:text-blue-100"
            >
              <div className="font-semibold">{item.label}</div>
              <p className="mt-1 text-xs leading-5 text-blue-900/80 dark:text-blue-100/80">
                {item.interpretation}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {visibleRankings.map((ranking) => (
          <RankingTable key={ranking.ranking_id} ranking={ranking} />
        ))}
      </div>

      <div className="mt-5 rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30">
        <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
          Metodo e limites
        </div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          {rankings.methodology_notes.map((note) => (
            <li key={note}>- {note}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function RankingTable({ ranking }: { ranking: InvestmentMarketRankingPayload }) {
  return (
    <article className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-800 dark:bg-gray-950/50">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              {ranking.label}
            </div>
            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {ranking.metric_label}
            </div>
          </div>
          {ranking.weights ? (
            <span className="rounded-full border border-gray-300 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300">
              fatorial
            </span>
          ) : null}
        </div>
        <p className="mt-2 text-xs leading-5 text-gray-500 dark:text-gray-400">
          {ranking.methodology}
        </p>
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-800">
        {ranking.rows.slice(0, 6).map((row) => (
          <div
            key={`${ranking.ranking_id}-${row.instrument_id}`}
            className="grid grid-cols-[auto_1fr_auto] items-center gap-3 px-4 py-3 text-sm"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-200">
              {row.rank}
            </div>
            <div>
              <div className="font-semibold text-gray-900 dark:text-gray-100">{row.label}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {row.category_label} · {row.risk_label}
              </div>
            </div>
            <div className="text-right font-semibold text-gray-900 dark:text-gray-100">
              {formatRankingValue(row.value, ranking.metric_kind)}
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function formatRankingValue(value: number, kind: string) {
  if (kind === 'currency') {
    return formatCurrency(value);
  }
  if (kind === 'percent') {
    return formatPercent(value);
  }
  if (kind === 'count') {
    return formatNumber(value, 0);
  }
  return formatNumber(value, 2);
}

function toRankingsCsv(rankings: InvestmentMarketRankingsPayload) {
  const header = rankings.export_columns.join(',');
  const rows = rankings.rankings.flatMap((ranking) =>
    ranking.rows.map((row) =>
      [
        ranking.ranking_id,
        ranking.label,
        row.rank,
        row.instrument_id,
        row.label,
        row.category_label,
        row.source_kind,
        row.risk_label,
        row.value,
        row.secondary_value,
      ]
        .map(csvCell)
        .join(',')
    )
  );
  return [header, ...rows].join('\n');
}

function csvCell(value: string | number) {
  const text = String(value);
  if (text.includes(',') || text.includes('"') || text.includes('\n')) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}
