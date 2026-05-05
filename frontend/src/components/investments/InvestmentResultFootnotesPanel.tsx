import type { InvestmentCatalogPayload } from '../../types/api';

interface InvestmentResultFootnotesPanelProps {
  warnings: string[];
  sources?: InvestmentCatalogPayload['sources'];
}

export default function InvestmentResultFootnotesPanel({
  warnings,
  sources = [],
}: InvestmentResultFootnotesPanelProps) {
  return (
    <>
      {warnings.length > 0 ? (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">
          <div className="font-semibold">Atencoes sobre o recorte</div>
          <ul className="mt-2 space-y-1">
            {warnings.map((warning) => (
              <li key={warning}>- {warning}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-4 text-sm text-gray-600 dark:border-gray-800 dark:bg-gray-900/50 dark:text-gray-300">
        <div className="font-semibold text-gray-900 dark:text-gray-100">Fontes e cobertura</div>
        <div className="mt-2 space-y-1">
          {sources.map((source) => (
            <div key={source.url}>
              <a
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-700 hover:underline dark:text-blue-300"
              >
                {source.label}
              </a>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
