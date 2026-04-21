import { GitCompare, Loader2, X } from 'lucide-react';
import { ComparisonRun } from '../types/api';
import { summarizeComparisonRun } from '../lib/runComparison';
import { formatPercent } from '../lib/utils';

interface RunComparisonPanelProps {
  comparisonRuns: ComparisonRun[];
  isLoading: boolean;
  onClear: () => void;
}

export default function RunComparisonPanel({
  comparisonRuns,
  isLoading,
  onClear,
}: RunComparisonPanelProps) {
  if (!isLoading && comparisonRuns.length === 0) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Comparacao de resultados
        </h3>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Selecione pelo menos dois resultados em "Recentes" para comparar retorno,
          drawdown, Sharpe e trades lado a lado.
        </p>
      </div>
    );
  }

  const summarizedRuns = comparisonRuns.map(summarizeComparisonRun);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <GitCompare className="h-4 w-4 mr-2" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Comparacao de resultados
          </h3>
        </div>
        <button
          type="button"
          onClick={onClear}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <X className="h-3 w-3 inline mr-1" />
          Limpar
        </button>
      </div>

      {isLoading ? (
        <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          Carregando resultados selecionados...
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {summarizedRuns.map((run) => (
            <div
              key={run.runId}
              className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800"
            >
              <div className="text-xs font-mono text-gray-500 dark:text-gray-400 mb-2">
                {run.runId}
              </div>
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {run.configPath}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {new Date(run.createdAt).toLocaleString('pt-BR')}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Melhor estrategia</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {run.bestStrategyName}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Estrategias</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {run.strategyCount}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Melhor retorno</div>
                  <div className="font-medium text-emerald-600 dark:text-emerald-400">
                    {formatPercent(run.bestReturn)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Sharpe</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {run.bestSharpe.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Max DD</div>
                  <div className="font-medium text-amber-600 dark:text-amber-400">
                    {formatPercent(run.bestDrawdown)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Trades</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {run.totalTrades}
                  </div>
                </div>
              </div>

              <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                Data: <span className="font-mono">{run.dataFingerprint.slice(0, 12)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
