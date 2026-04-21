import { useMemo } from 'react';
import { Loader2 } from 'lucide-react';
import InteractiveSeriesChart from '../charts/InteractiveSeriesChart';
import { buildOptimizationObjectiveChart } from '../../lib/advancedCharts';
import { formatPercent } from '../../lib/utils';
import { OptimizationResultsPanelProps } from './types';

export default function OptimizationResultsPanel({
  latestExecution,
  selectedResults,
  selectedManifest,
  isLoadingSelected,
}: OptimizationResultsPanelProps) {
  const results = selectedResults ?? latestExecution;
  const optimizationChart = useMemo(() => buildOptimizationObjectiveChart(results), [results]);
  const objectiveFormatter = useMemo(() => {
    const objective = results?.objective ?? '';
    return objective.includes('return') || objective.includes('drawdown')
      ? (value: number) => formatPercent(value)
      : (value: number) => value.toFixed(4);
  }, [results?.objective]);

  if (!results && !selectedManifest) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Optimization Results
        </h4>
        {isLoadingSelected && (
          <Loader2 className="h-4 w-4 animate-spin text-gray-500 dark:text-gray-400" />
        )}
      </div>

      {selectedManifest && (
        <div className="mb-3 text-xs text-gray-500 dark:text-gray-400">
          {selectedManifest.optimization_id} | {selectedManifest.direction}{' '}
          {selectedManifest.objective}
        </div>
      )}

      {results && (
        <div className="space-y-4">
          {optimizationChart && (
            <InteractiveSeriesChart
              title="Leitura visual dos melhores trials"
              description="Resumo grafico dos melhores resultados da optimization. Clique na legenda para destacar uma série."
              data={optimizationChart.data}
              xKey="label"
              series={optimizationChart.series}
              yTickFormatter={objectiveFormatter}
              tooltipValueFormatter={(value) => objectiveFormatter(value)}
              emptyText="Sem trials completos para gerar o gráfico da optimization."
              heightClassName="h-[18rem]"
            />
          )}

          {results.ranked_results.slice(0, 5).map((result) => (
            <div key={result.trial_id} className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                    {result.trial_id}
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {result.strategy_name}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {result.objective}
                  </div>
                  <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                    {result.objective.includes('drawdown')
                      ? formatPercent(result.objective_value ?? 0)
                      : (result.objective_value ?? 0).toFixed(4)}
                  </div>
                </div>
              </div>
              {result.run_id && (
                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  Run: <span className="font-mono">{result.run_id}</span>
                </div>
              )}
              <pre className="mt-2 text-xs text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                {JSON.stringify(result.parameters, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
