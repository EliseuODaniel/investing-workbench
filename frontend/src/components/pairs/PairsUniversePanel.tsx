import { PairsUniversePayload } from '../../types/api';
import { formatNumber } from './pairsFormat';

interface PairsUniversePanelProps {
  universe: PairsUniversePayload | null;
  isResolving: boolean;
  isLoadingPresets: boolean;
}

export function PairsUniversePanel({
  universe,
  isResolving,
  isLoadingPresets,
}: PairsUniversePanelProps) {
  const universePreset = universe?.preset ?? null;
  const resolvedUniverseDate = universe?.resolved_as_of_date ?? null;
  const universeValidityLabel =
    typeof universePreset?.validity_label === 'string' ? universePreset.validity_label : null;
  const universeAssets = universe?.assets ?? [];
  const borrowSnapshotPath =
    typeof universe?.quality_report.borrow_snapshot_path === 'string'
      ? universe.quality_report.borrow_snapshot_path
      : null;
  const borrowSnapshotManagedPath =
    typeof universe?.quality_report.borrow_snapshot_managed_path === 'string'
      ? universe.quality_report.borrow_snapshot_managed_path
      : null;
  const issueCounts =
    universe?.quality_report.issue_counts && typeof universe.quality_report.issue_counts === 'object'
      ? Object.entries(universe.quality_report.issue_counts)
      : [];
  const eligibleAssets = universeAssets.filter((asset) => asset.eligibility_status === 'eligible');
  const ineligibleAssets = universeAssets.filter((asset) => asset.eligibility_status !== 'eligible');

  return (
    <div className="card">
      <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
        Qualidade do universo
      </h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Diagnóstico de cobertura, liquidez e elegibilidade para short.
      </p>
      {universe ? (
        <div className="mt-4 space-y-4">
          {universePreset && (
            <div className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-200">
              <div className="font-medium">
                {String(universePreset.label ?? 'Preset')}
                {resolvedUniverseDate ? ` · snapshot ${resolvedUniverseDate}` : ''}
              </div>
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {String(universePreset.description ?? '')}
              </div>
              {universeValidityLabel && (
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Vigência B3: {universeValidityLabel}
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Solicitados</div>
              <div className="mt-1 text-lg font-semibold">
                {String(universe.quality_report.requested_ticker_count ?? 'n/a')}
              </div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Carregados</div>
              <div className="mt-1 text-lg font-semibold">
                {String(universe.quality_report.loaded_ticker_count ?? 'n/a')}
              </div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Elegíveis</div>
              <div className="mt-1 text-lg font-semibold">
                {String(universe.quality_report.eligible_ticker_count ?? 'n/a')}
              </div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Dias comuns</div>
              <div className="mt-1 text-lg font-semibold">{universe.common_index_days}</div>
            </div>
          </div>

          {universe.quality_report.borrow_override_count ? (
            <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-800 dark:border-sky-900/60 dark:bg-sky-950/30 dark:text-sky-200">
              Borrow snapshot carregado de {borrowSnapshotPath ?? 'arquivo local'} com{' '}
              {String(universe.quality_report.borrow_override_count)} override(s) de aluguel.
              {borrowSnapshotManagedPath ? (
                <div className="mt-1 text-xs text-sky-700/80 dark:text-sky-200/80">
                  Copia governada: {borrowSnapshotManagedPath}
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left dark:border-gray-800">
                  <th className="pb-2 pr-4 font-medium">Ticker</th>
                  <th className="pb-2 pr-4 font-medium">Setor</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium">Notional mediano</th>
                  <th className="pb-2 pr-4 font-medium">Short score</th>
                  <th className="pb-2 pr-4 font-medium">Razões</th>
                </tr>
              </thead>
              <tbody>
                {eligibleAssets.slice(0, 8).map((asset) => (
                  <tr
                    key={String(asset.ticker)}
                    className="border-b border-gray-100 dark:border-gray-900"
                  >
                    <td className="py-2 pr-4 font-medium">{String(asset.ticker)}</td>
                    <td className="py-2 pr-4">{String(asset.sector_group)}</td>
                    <td className="py-2 pr-4">{String(asset.eligibility_status)}</td>
                    <td className="py-2 pr-4">
                      {formatNumber(Number(asset.median_notional_brl || 0), 0)}
                    </td>
                    <td className="py-2 pr-4">{formatNumber(Number(asset.short_score || 0), 2)}</td>
                    <td className="py-2 pr-4 text-xs text-gray-500 dark:text-gray-400">
                      {(asset.eligibility_reasons || []).join(', ') || 'ok'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {issueCounts.length > 0 && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 dark:border-rose-900/60 dark:bg-rose-950/30">
              <div className="text-sm font-medium text-rose-900 dark:text-rose-100">
                Principais motivos de rejeição
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-rose-800 dark:text-rose-200">
                {issueCounts.map(([issue, count]) => (
                  <span
                    key={issue}
                    className="rounded-full bg-white/70 px-2 py-1 dark:bg-rose-900/30"
                  >
                    {issue}: {String(count)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {ineligibleAssets.length > 0 && (
            <div className="overflow-x-auto">
              <div className="mb-2 text-sm font-medium text-gray-800 dark:text-gray-100">
                Ativos rejeitados pelo universo
              </div>
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left dark:border-gray-800">
                    <th className="pb-2 pr-4 font-medium">Ticker</th>
                    <th className="pb-2 pr-4 font-medium">Setor</th>
                    <th className="pb-2 pr-4 font-medium">Notional</th>
                    <th className="pb-2 pr-4 font-medium">Short score</th>
                    <th className="pb-2 pr-4 font-medium">Razões</th>
                  </tr>
                </thead>
                <tbody>
                  {ineligibleAssets.map((asset) => (
                    <tr
                      key={String(asset.ticker)}
                      className="border-b border-gray-100 dark:border-gray-900"
                    >
                      <td className="py-2 pr-4 font-medium">{String(asset.ticker)}</td>
                      <td className="py-2 pr-4">{String(asset.sector_group || 'n/a')}</td>
                      <td className="py-2 pr-4">
                        {formatNumber(Number(asset.median_notional_brl || 0), 0)}
                      </td>
                      <td className="py-2 pr-4">
                        {formatNumber(Number(asset.short_score || 0), 2)}
                      </td>
                      <td className="py-2 pr-4 text-xs text-gray-500 dark:text-gray-400">
                        {(asset.eligibility_reasons || []).join(', ') || 'n/a'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {universe.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
              {universe.warnings.join(' ')}
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
          {isResolving || isLoadingPresets
            ? 'Carregando universo...'
            : 'Resolva um universo para abrir o dashboard de qualidade.'}
        </div>
      )}
    </div>
  );
}
