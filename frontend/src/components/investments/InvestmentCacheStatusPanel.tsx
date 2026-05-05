import type { InvestmentCacheStatusPayload } from '../../types/api';
import { formatNumber } from '../../lib/utils';

interface InvestmentCacheStatusPanelProps {
  status?: InvestmentCacheStatusPayload;
}

export default function InvestmentCacheStatusPanel({ status }: InvestmentCacheStatusPanelProps) {
  if (!status) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/30">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-slate-950 dark:text-slate-100">
            {status.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-700 dark:text-slate-300">
            {status.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
          {status.status_label}
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        {status.caches.map((cache) => (
          <article
            key={cache.cache_id}
            className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-slate-950 dark:text-slate-100">
                {cache.label}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {cache.freshness_label ? (
                  <span className="rounded-full border border-slate-300 bg-slate-50 px-2 py-1 text-[11px] font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-200">
                    {cache.freshness_label}
                  </span>
                ) : null}
                {cache.used_in_current_result ? (
                  <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-[11px] font-medium text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
                    usado agora
                  </span>
                ) : null}
              </div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-xl bg-slate-50 px-3 py-3 dark:bg-slate-950/60">
                <div className="text-xs text-slate-500 dark:text-slate-400">Arquivos</div>
                <div className="mt-1 font-semibold text-slate-950 dark:text-slate-100">
                  {formatNumber(cache.file_count, 0)}
                </div>
              </div>
              <div className="rounded-xl bg-slate-50 px-3 py-3 dark:bg-slate-950/60">
                <div className="text-xs text-slate-500 dark:text-slate-400">Tamanho</div>
                <div className="mt-1 font-semibold text-slate-950 dark:text-slate-100">
                  {formatNumber(cache.total_size_bytes / 1024 / 1024, 1)} MB
                </div>
              </div>
              <div className="rounded-xl bg-slate-50 px-3 py-3 dark:bg-slate-950/60">
                <div className="text-xs text-slate-500 dark:text-slate-400">Idade</div>
                <div className="mt-1 font-semibold text-slate-950 dark:text-slate-100">
                  {formatCacheAge(cache.age_days)}
                </div>
              </div>
              <div className="rounded-xl bg-slate-50 px-3 py-3 dark:bg-slate-950/60">
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  Último arquivo
                </div>
                <div className="mt-1 truncate font-semibold text-slate-950 dark:text-slate-100">
                  {cache.latest_file_name ?? 'sem arquivo'}
                </div>
              </div>
            </div>
            <div className="mt-3 rounded-xl bg-slate-50 px-3 py-3 text-xs leading-5 text-slate-500 dark:bg-slate-950/60 dark:text-slate-400">
              {cache.status_label}. {cache.cold_start_note}
              {cache.refresh_hint ? (
                <span className="mt-2 block text-slate-600 dark:text-slate-300">
                  {cache.refresh_hint}
                </span>
              ) : null}
            </div>
          </article>
        ))}
      </div>

      <div className="mt-5 rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
        <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
          Leitura rápida
        </div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
          {status.takeaways.map((item) => (
            <li key={item}>- {item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function formatCacheAge(ageDays?: number | null) {
  if (ageDays === null || ageDays === undefined) {
    return 'sem histórico';
  }
  if (ageDays <= 0) {
    return 'hoje';
  }
  if (ageDays === 1) {
    return '1 dia';
  }
  return `${formatNumber(ageDays, 0)} dias`;
}
