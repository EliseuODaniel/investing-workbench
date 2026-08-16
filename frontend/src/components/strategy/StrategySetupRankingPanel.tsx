import {
  buildSetupDiversificationSummary,
  buildSetupScoresCsv,
  buildStrategyCorrelationMatrix,
  type SetupScoreInsight,
} from '../../lib/strategySetupScoring';
import { downloadCSV } from '../../lib/utils';
import type { StrategySetupScorePayload } from '../../types/api';

type StrategySetupRankingPanelProps = {
  scores: StrategySetupScorePayload[];
  insights: SetupScoreInsight[];
};

export function StrategySetupRankingPanel({
  scores,
  insights,
}: StrategySetupRankingPanelProps) {
  if (scores.length === 0) {
    return null;
  }

  const diversification = buildSetupDiversificationSummary(scores);
  const correlation = buildStrategyCorrelationMatrix(scores);

  return (
    <div className="mt-3 rounded-lg border border-indigo-200 bg-indigo-50/70 p-3 text-xs dark:border-indigo-900/50 dark:bg-indigo-950/20">
      <div className="font-semibold text-indigo-950 dark:text-indigo-100">
        Ranking dos setups executados
      </div>
      <div className="mt-2 flex justify-end">
        <button
          type="button"
          className="rounded-lg border border-indigo-200 bg-white px-2 py-1 text-[11px] font-medium text-indigo-700 hover:border-indigo-400 dark:border-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-100"
          onClick={() => exportSetupScoresCsv(scores)}
        >
          Exportar CSV
        </button>
      </div>
      <div className="mt-2 grid gap-1">
        {scores.slice(0, 3).map((score, index) => (
          <div
            key={score.strategy_id}
            className="rounded-lg border border-indigo-100 bg-white/70 p-2 text-[11px] text-indigo-900 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-indigo-100"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span>
                {index + 1}. {score.label}
              </span>
              <span>
                score {score.score.toFixed(1)} · retorno {formatPercent(score.total_return)} · DD{' '}
                {formatPercent(score.max_drawdown)} · trades {score.trade_count ?? 0} · runs{' '}
                {score.run_count ?? 0}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              <span className="rounded-full bg-indigo-100 px-2 py-0.5 dark:bg-indigo-900/60">
                retorno +{score.return_score.toFixed(1)}
              </span>
              <span className="rounded-full bg-indigo-100 px-2 py-0.5 dark:bg-indigo-900/60">
                drawdown -{score.drawdown_penalty.toFixed(1)}
              </span>
              <span className="rounded-full bg-indigo-100 px-2 py-0.5 dark:bg-indigo-900/60">
                execucao +{score.execution_score.toFixed(1)}
              </span>
              <span className="rounded-full bg-indigo-100 px-2 py-0.5 dark:bg-indigo-900/60">
                robustez +{score.robustness_score.toFixed(1)}
              </span>
              <span className="rounded-full bg-indigo-100 px-2 py-0.5 dark:bg-indigo-900/60">
                dados +{score.data_validity_score.toFixed(1)}
              </span>
            </div>
            <div className="mt-1 text-[10px] leading-4 text-indigo-800/80 dark:text-indigo-100/80">
              {score.methodology}
            </div>
          </div>
        ))}
      </div>
      {insights.length > 0 ? (
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {insights.map((insight) => (
            <div
              key={insight.insight_id}
              className="rounded-lg border border-indigo-100 bg-white/70 p-2 text-[11px] text-indigo-900 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-indigo-100"
            >
              <div className="font-semibold">{insight.label}</div>
              <div className="mt-1">
                {insight.setup_label} · {insight.value_label}
              </div>
              <div className="mt-1 text-[10px] leading-4 text-indigo-800/80 dark:text-indigo-100/80">
                {insight.interpretation}
              </div>
            </div>
          ))}
        </div>
      ) : null}
      {diversification ? (
        <div className="mt-3 rounded-lg border border-indigo-100 bg-white/80 p-2.5 text-[11px] text-indigo-950 dark:border-indigo-900/50 dark:bg-indigo-950/40 dark:text-indigo-100">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-semibold">Diversificação de estratégias combinadas</span>
            <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-200">
              score {diversification.diversificationScore}/100
            </span>
          </div>
          <div className="mt-1 text-[10px] leading-4 text-indigo-900/80 dark:text-indigo-200/80">
            {diversification.interpretation}
          </div>
        </div>
      ) : null}
      {correlation ? (
        <div className="mt-3 rounded-lg border border-indigo-100 bg-white/80 p-2.5 text-[11px] text-indigo-950 dark:border-indigo-900/50 dark:bg-indigo-950/40 dark:text-indigo-100">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-semibold">Matriz de correlação entre setups</span>
            <span className="text-[10px] text-indigo-700 dark:text-indigo-300">
              correlação média: {correlation.averageCorrelation.toFixed(2)}
            </span>
          </div>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-center text-[10px]">
              <thead>
                <tr>
                  <th className="py-1 text-left font-medium text-gray-500">Setup</th>
                  {correlation.strategies.map((s, idx) => (
                    <th key={s.strategy_id} className="py-1 px-1.5 font-medium text-gray-600 dark:text-gray-300">
                      S{idx + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {correlation.strategies.map((s1, i) => (
                  <tr key={s1.strategy_id} className="border-t border-indigo-50 dark:border-indigo-950/30">
                    <td className="py-1 text-left font-medium text-indigo-900 dark:text-indigo-200 truncate max-w-[120px]">
                      S{i + 1}. {s1.label}
                    </td>
                    {correlation.matrix[i].map((val, j) => (
                      <td
                        key={`${i}-${j}`}
                        className={`py-1 px-1.5 font-semibold ${
                          i === j
                            ? 'bg-indigo-100/50 text-indigo-950 dark:bg-indigo-900/40 dark:text-indigo-100'
                            : val < 0.3
                              ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200'
                              : val > 0.7
                                ? 'bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200'
                                : 'text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {val.toFixed(2)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function exportSetupScoresCsv(scores: StrategySetupScorePayload[]) {
  const csv = buildSetupScoresCsv(scores);
  downloadCSV(csv, `strategy_setup_scores_${new Date().toISOString().slice(0, 10)}.csv`);
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}
