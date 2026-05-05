import { Play } from 'lucide-react';
import type {
  BacktestResponse,
  PairsBacktestResultsPayload,
  StrategySetupPlanPayload,
} from '../../types/api';
import type { StrategySetupRunHistoryItem } from '../../lib/strategySetupHistory';

type StrategySetupPlanCardProps = {
  plan?: StrategySetupPlanPayload;
  isPlanning: boolean;
  isRunning: boolean;
  handoffMessage?: string;
  runError?: string;
  runResult?: BacktestResponse;
  pairsRunResult?: PairsBacktestResultsPayload;
  history: StrategySetupRunHistoryItem[];
  loadedRunResponses: Record<string, BacktestResponse>;
  loadedPairsBacktestResults: Record<string, PairsBacktestResultsPayload>;
  loadingRunId: string | null;
  loadingPairsBacktestId: string | null;
  onRun: (plan: StrategySetupPlanPayload) => void;
  onPairsHandoff: (plan: StrategySetupPlanPayload) => void;
  onLoadRunResponse: (runId: string) => void;
  onLoadPairsBacktestResults: (pairsBacktestId: string) => void;
};

export function StrategySetupPlanCard({
  plan,
  isPlanning,
  isRunning,
  handoffMessage,
  runError,
  runResult,
  pairsRunResult,
  history,
  loadedRunResponses,
  loadedPairsBacktestResults,
  loadingRunId,
  loadingPairsBacktestId,
  onRun,
  onPairsHandoff,
  onLoadRunResponse,
  onLoadPairsBacktestResults,
}: StrategySetupPlanCardProps) {
  if (!plan) {
    return isPlanning ? (
      <div className="mt-3 text-[11px] text-gray-500 dark:text-gray-400">
        Preparando plano...
      </div>
    ) : null;
  }

  const canRun = ['/backtest', '/pairs/backtests'].includes(plan.route_hint);

  return (
    <div className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50/70 p-3 text-xs dark:border-emerald-900/50 dark:bg-emerald-950/20">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="font-semibold text-emerald-950 dark:text-emerald-100">
          Plano preparado
        </div>
        <span className="rounded-full border border-emerald-300 px-2 py-0.5 text-[11px] text-emerald-700 dark:border-emerald-800 dark:text-emerald-200">
          {plan.route_hint} · {plan.readiness}
        </span>
      </div>
      <pre className="mt-2 max-h-32 overflow-auto rounded-lg bg-white p-2 text-[11px] leading-5 text-gray-700 dark:bg-gray-950 dark:text-gray-200">
        {JSON.stringify(plan.run_request, null, 2)}
      </pre>
      {plan.warnings.length > 0 ? (
        <ul className="mt-2 space-y-1 text-[11px] leading-5 text-amber-800 dark:text-amber-200">
          {plan.warnings.map((warning) => (
            <li key={warning}>- {warning}</li>
          ))}
        </ul>
      ) : null}
      <div className="mt-2 text-[11px] leading-5 text-emerald-900 dark:text-emerald-100">
        {plan.next_actions[0]}
      </div>
      <div className="mt-3 flex flex-wrap justify-end gap-2">
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded-lg border border-emerald-300 bg-white px-2 py-1.5 text-xs font-medium text-emerald-700 hover:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60 dark:border-emerald-800 dark:bg-gray-950 dark:text-emerald-200"
          onClick={() => onRun(plan)}
          disabled={isRunning || !canRun}
        >
          <Play className="h-3.5 w-3.5" />
          {isRunning
            ? 'Rodando...'
            : plan.route_hint === '/pairs/backtests'
              ? 'Rodar Pairs'
              : 'Rodar backtest'}
        </button>
        {plan.route_hint === '/pairs/backtests' ? (
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-lg border border-blue-300 bg-white px-2 py-1.5 text-xs font-medium text-blue-700 hover:border-blue-500 dark:border-blue-800 dark:bg-gray-950 dark:text-blue-200"
            onClick={() => onPairsHandoff(plan)}
          >
            Enviar para Pairs
          </button>
        ) : null}
      </div>
      {handoffMessage ? (
        <div className="mt-2 rounded-lg border border-blue-200 bg-blue-50 px-2 py-1.5 text-[11px] text-blue-800 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-100">
          {handoffMessage}
        </div>
      ) : null}
      {runError ? (
        <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-2 py-1.5 text-[11px] text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-100">
          {runError}
        </div>
      ) : null}
      {runResult ? (
        <div className="mt-2 rounded-lg border border-emerald-200 bg-white px-2 py-1.5 text-[11px] leading-5 text-emerald-900 dark:border-emerald-900/60 dark:bg-gray-950 dark:text-emerald-100">
          Execucao concluida: {Object.keys(runResult.results).length} estrategia(s)
          {runResult.run_info?.run_id ? ` · run ${runResult.run_info?.run_id}` : ''}
        </div>
      ) : null}
      <StrategySetupHistoryList
        history={history}
        loadedRunResponses={loadedRunResponses}
        loadedPairsBacktestResults={loadedPairsBacktestResults}
        loadingRunId={loadingRunId}
        loadingPairsBacktestId={loadingPairsBacktestId}
        onLoadRunResponse={onLoadRunResponse}
        onLoadPairsBacktestResults={onLoadPairsBacktestResults}
      />
      {pairsRunResult ? (
        <div className="mt-2 rounded-lg border border-blue-200 bg-white px-2 py-1.5 text-[11px] leading-5 text-blue-900 dark:border-blue-900/60 dark:bg-gray-950 dark:text-blue-100">
          Pairs concluido: {pairsRunResult.scenarios.length} cenario(s) ·{' '}
          {pairsRunResult.candidate_pairs.length} par(es) candidato(s) · id{' '}
          {pairsRunResult.pairs_backtest_id}
        </div>
      ) : null}
    </div>
  );
}

function StrategySetupHistoryList({
  history,
  loadedRunResponses,
  loadedPairsBacktestResults,
  loadingRunId,
  loadingPairsBacktestId,
  onLoadRunResponse,
  onLoadPairsBacktestResults,
}: Pick<
  StrategySetupPlanCardProps,
  | 'history'
  | 'loadedRunResponses'
  | 'loadedPairsBacktestResults'
  | 'loadingRunId'
  | 'loadingPairsBacktestId'
  | 'onLoadRunResponse'
  | 'onLoadPairsBacktestResults'
>) {
  if (history.length === 0) {
    return null;
  }

  return (
    <div className="mt-2 rounded-lg border border-gray-200 bg-white p-2 text-[11px] leading-5 text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300">
      <div className="font-semibold text-gray-800 dark:text-gray-100">
        Historico do setup
      </div>
      <div className="mt-1 grid gap-1">
        {history.slice(0, 3).map((historyItem) => (
          <div
            key={`${historyItem.strategy_id}-${historyItem.ran_at}-${
              historyItem.run_id || historyItem.pairs_backtest_id || 'local'
            }`}
            className="rounded-md border border-gray-100 p-2 dark:border-gray-800"
          >
            <div className="flex flex-wrap justify-between gap-2">
              <span>
                {formatDateTime(historyItem.ran_at)}
                {historyItem.run_id
                  ? ` · ${historyItem.run_id}`
                  : historyItem.pairs_backtest_id
                    ? ` · ${historyItem.pairs_backtest_id}`
                    : ''}
              </span>
              <span>
                {historyItem.best_strategy || 'setup'} ·{' '}
                {typeof historyItem.total_return === 'number'
                  ? formatPercent(historyItem.total_return)
                  : 'sem retorno'}
              </span>
            </div>
            {historyItem.run_id ? (
              <button
                type="button"
                className="mt-2 rounded-lg border border-gray-300 px-2 py-1 text-[11px] font-medium text-gray-600 hover:border-blue-300 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:text-gray-300 dark:hover:border-blue-800 dark:hover:text-blue-200"
                onClick={() => onLoadRunResponse(historyItem.run_id || '')}
                disabled={loadingRunId === historyItem.run_id}
              >
                {loadingRunId === historyItem.run_id ? 'Carregando...' : 'Ver resultado'}
              </button>
            ) : null}
            {historyItem.pairs_backtest_id ? (
              <button
                type="button"
                className="mt-2 rounded-lg border border-gray-300 px-2 py-1 text-[11px] font-medium text-gray-600 hover:border-blue-300 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:text-gray-300 dark:hover:border-blue-800 dark:hover:text-blue-200"
                onClick={() => onLoadPairsBacktestResults(historyItem.pairs_backtest_id || '')}
                disabled={loadingPairsBacktestId === historyItem.pairs_backtest_id}
              >
                {loadingPairsBacktestId === historyItem.pairs_backtest_id
                  ? 'Carregando...'
                  : 'Ver Pairs'}
              </button>
            ) : null}
            {historyItem.run_id && loadedRunResponses[historyItem.run_id] ? (
              <div className="mt-2 grid gap-1">
                {Object.values(loadedRunResponses[historyItem.run_id].results).map((result) => (
                  <div
                    key={result.strategy_name}
                    className="rounded-lg bg-gray-50 px-2 py-1.5 dark:bg-gray-900"
                  >
                    <div className="font-semibold text-gray-800 dark:text-gray-100">
                      {result.strategy_name}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2 text-[11px]">
                      <span>retorno {formatPercent(result.metrics.total_return)}</span>
                      <span>DD {formatPercent(result.metrics.max_drawdown)}</span>
                      <span>trades {result.metrics.total_trades}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
            {historyItem.pairs_backtest_id &&
            loadedPairsBacktestResults[historyItem.pairs_backtest_id] ? (
              <div className="mt-2 grid gap-1">
                {loadedPairsBacktestResults[historyItem.pairs_backtest_id].scenarios.map(
                  (scenario) => (
                    <div
                      key={scenario.scenario_id}
                      className="rounded-lg bg-gray-50 px-2 py-1.5 dark:bg-gray-900"
                    >
                      <div className="font-semibold text-gray-800 dark:text-gray-100">
                        {scenario.label}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-2 text-[11px]">
                        <span>
                          retorno {formatPercent(scenario.metrics.return_total ?? 0)}
                        </span>
                        <span>DD {formatPercent(scenario.metrics.max_drawdown ?? 0)}</span>
                        <span>trades {scenario.metrics.trade_count ?? 0}</span>
                      </div>
                    </div>
                  )
                )}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}
