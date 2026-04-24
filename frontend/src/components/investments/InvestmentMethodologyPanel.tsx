import type { InvestmentMethodologyGuidePayload } from '../../types/api';

interface InvestmentMethodologyPanelProps {
  guide?: InvestmentMethodologyGuidePayload;
}

export default function InvestmentMethodologyPanel({ guide }: InvestmentMethodologyPanelProps) {
  if (!guide) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/30">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-slate-950 dark:text-slate-100">
            {guide.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-700 dark:text-slate-300">
            {guide.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
          {guide.evidence_types.length} tipo(s) de evidência
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        {guide.evidence_types.map((item) => (
          <div
            key={item.kind}
            className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-slate-950 dark:text-slate-100">
                {item.label}
              </div>
              <span className="rounded-full border border-slate-300 px-2 py-1 text-[11px] text-slate-600 dark:border-slate-700 dark:text-slate-300">
                {item.included_count}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {item.description}
            </p>
            <div className="mt-3 rounded-xl bg-slate-50 px-3 py-3 text-xs leading-5 text-slate-500 dark:bg-slate-950/60 dark:text-slate-400">
              {item.limitations}
            </div>
            {item.included_labels.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {item.included_labels.map((label) => (
                  <span
                    key={`${item.kind}-${label}`}
                    className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] text-slate-600 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
          <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
            Premissas principais
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
            {guide.assumption_notes.slice(0, 5).map((note) => (
              <li key={note}>- {note}</li>
            ))}
          </ul>
        </div>

        {guide.decision_profile_notes?.length ? (
          <div className="rounded-2xl border border-sky-200 bg-sky-50/70 p-4 dark:border-sky-900/50 dark:bg-sky-950/20">
            <div className="text-sm font-semibold text-sky-950 dark:text-sky-100">
              Perfil usado na leitura
            </div>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-sky-900/90 dark:text-sky-100/90">
              {guide.decision_profile_notes.map((note) => (
                <li key={note}>- {note}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
          <div className="text-sm font-semibold text-amber-950 dark:text-amber-100">
            Cuidados de leitura
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-900/90 dark:text-amber-100/90">
            {guide.caveats.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      </div>

      {guide.realism_notes?.length ? (
        <div className="mt-5 rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900/60">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Realismo dos dados
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {guide.realism_notes.map((note) => (
              <div
                key={note.dimension}
                className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-950/50"
              >
                <div className="font-semibold text-gray-900 dark:text-gray-100">
                  {note.dimension}
                </div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
                  {note.status}
                </div>
                <p className="mt-2 text-gray-600 dark:text-gray-300">{note.note}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
