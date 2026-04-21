import { PairsScreenPayload } from '../../types/api';
import { formatNumber, formatPercent } from './pairsFormat';

interface PairsScreenerPanelProps {
  screening: PairsScreenPayload | null;
  eligibleAssetCount: number;
  isScreening: boolean;
}

export function PairsScreenerPanel({
  screening,
  eligibleAssetCount,
  isScreening,
}: PairsScreenerPanelProps) {
  const candidatePairs = screening?.candidate_pairs ?? [];
  const rejectedPairs = screening?.rejected_pairs ?? [];
  const rejectionSummary = screening?.rejection_summary ?? {};

  return (
    <div className="card">
      <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
        Screener de pares
      </h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Ranking por p-value, correlação e estabilidade em sub-janelas.
      </p>
      {screening ? (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Candidatos</div>
              <div className="mt-1 text-lg font-semibold">
                {String(screening.summary.candidate_pair_count ?? '0')}
              </div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Selecionados</div>
              <div className="mt-1 text-lg font-semibold">
                {String(screening.summary.selected_pair_count ?? '0')}
              </div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Rejeitados</div>
              <div className="mt-1 text-lg font-semibold">
                {String(screening.summary.rejected_pair_count ?? '0')}
              </div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Elegíveis</div>
              <div className="mt-1 text-lg font-semibold">{eligibleAssetCount}</div>
            </div>
            <div className="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">Janela</div>
              <div className="mt-1 text-lg font-semibold">
                {String(screening.screening_window.formation_days ?? 'n/a')}
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left dark:border-gray-800">
                  <th className="pb-2 pr-4 font-medium">Par</th>
                  <th className="pb-2 pr-4 font-medium">p-value</th>
                  <th className="pb-2 pr-4 font-medium">Half-life</th>
                  <th className="pb-2 pr-4 font-medium">Beta</th>
                  <th className="pb-2 pr-4 font-medium">Score</th>
                  <th className="pb-2 pr-4 font-medium">Estabilidade</th>
                  <th className="pb-2 pr-4 font-medium">Break risk</th>
                </tr>
              </thead>
              <tbody>
                {candidatePairs.slice(0, 10).map((pair) => (
                  <tr
                    key={String(pair.pair_label)}
                    className="border-b border-gray-100 dark:border-gray-900"
                  >
                    <td className="py-2 pr-4 font-medium">{String(pair.pair_label)}</td>
                    <td className="py-2 pr-4">{formatNumber(Number(pair.coint_pvalue || 0), 3)}</td>
                    <td className="py-2 pr-4">{formatNumber(Number(pair.half_life || 0), 1)}</td>
                    <td className="py-2 pr-4">{formatNumber(Number(pair.beta || 0), 2)}</td>
                    <td className="py-2 pr-4">{formatNumber(Number(pair.ranking_score || 0), 3)}</td>
                    <td className="py-2 pr-4">
                      {formatPercent(Number(pair.stability?.stability_score || 0))}
                    </td>
                    <td className="py-2 pr-4">
                      {formatPercent(Number(pair.stability?.structural_break_risk || 0))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {Object.keys(rejectionSummary).length > 0 && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 dark:border-rose-900/60 dark:bg-rose-950/30">
              <div className="text-sm font-medium text-rose-900 dark:text-rose-100">
                Motivos de rejeição no screener
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-rose-800 dark:text-rose-200">
                {Object.entries(rejectionSummary)
                  .sort((left, right) => right[1] - left[1])
                  .map(([reason, count]) => (
                    <span
                      key={reason}
                      className="rounded-full bg-white/70 px-2 py-1 dark:bg-rose-900/30"
                    >
                      {reason}: {String(count)}
                    </span>
                  ))}
              </div>
            </div>
          )}

          {rejectedPairs.length > 0 && (
            <div className="overflow-x-auto">
              <div className="mb-2 text-sm font-medium text-gray-800 dark:text-gray-100">
                Melhores pares rejeitados
              </div>
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left dark:border-gray-800">
                    <th className="pb-2 pr-4 font-medium">Par</th>
                    <th className="pb-2 pr-4 font-medium">p-value</th>
                    <th className="pb-2 pr-4 font-medium">Score</th>
                    <th className="pb-2 pr-4 font-medium">Razões</th>
                  </tr>
                </thead>
                <tbody>
                  {rejectedPairs.slice(0, 8).map((pair) => (
                    <tr
                      key={String(pair.pair_label)}
                      className="border-b border-gray-100 dark:border-gray-900"
                    >
                      <td className="py-2 pr-4 font-medium">{String(pair.pair_label)}</td>
                      <td className="py-2 pr-4">
                        {formatNumber(Number(pair.coint_pvalue || 0), 3)}
                      </td>
                      <td className="py-2 pr-4">
                        {formatNumber(Number(pair.ranking_score || 0), 3)}
                      </td>
                      <td className="py-2 pr-4 text-xs text-gray-500 dark:text-gray-400">
                        {(pair.rejection_reasons || []).join(', ') || 'n/a'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
          {isScreening ? 'Rodando screener...' : 'Rode o screener para ver o ranking de pares.'}
        </div>
      )}
    </div>
  );
}
