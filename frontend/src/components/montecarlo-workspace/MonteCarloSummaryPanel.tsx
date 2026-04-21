import { AlertTriangle, ShieldAlert } from 'lucide-react';
import { formatCurrency, formatPercent } from '../../lib/utils';
import { MonteCarloSummaryPanelProps } from './types';

export default function MonteCarloSummaryPanel({
  activeResults,
  selectedManifest,
  isLoadingSelected,
}: MonteCarloSummaryPanelProps) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center mb-3">
        <ShieldAlert className="h-4 w-4 mr-2 text-rose-600 dark:text-rose-400" />
        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Robustness Summary
        </h4>
      </div>

      {!activeResults ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Run or select a Monte Carlo job to inspect tail scenarios.
        </p>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-gray-500 dark:text-gray-400">Simulations</div>
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {activeResults.simulation_count}
              </div>
            </div>
            <div>
              <div className="text-gray-500 dark:text-gray-400">Method</div>
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {activeResults.method}
              </div>
            </div>
          </div>

          <div className="text-xs text-gray-500 dark:text-gray-400 font-mono">
            Source run: {activeResults.source_run_id}
          </div>

          {selectedManifest && selectedManifest.warnings.length > 0 && (
            <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-xs text-amber-800 dark:text-amber-200">
              {selectedManifest.warnings.join(' | ')}
            </div>
          )}

          {isLoadingSelected && (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Loading persisted Monte Carlo results...
            </div>
          )}

          <div className="space-y-3">
            {activeResults.strategy_summaries.map((summary) => (
              <div
                key={summary.strategy_name}
                className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {summary.strategy_name}
                  </div>
                  {summary.warnings.length > 0 && (
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                  )}
                </div>
                <div className="mt-2 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-gray-300">
                  <div>Loss Prob: {formatPercent(summary.loss_probability)}</div>
                  <div>Ruin Prob: {formatPercent(summary.ruin_probability)}</div>
                  <div>Median Return: {formatPercent(summary.median_total_return)}</div>
                  <div>95% DD Tail: {formatPercent(summary.percentile_95_max_drawdown)}</div>
                  <div>Worst Equity: {formatCurrency(summary.worst_final_equity)}</div>
                  <div>Best Equity: {formatCurrency(summary.best_final_equity)}</div>
                </div>
                {summary.warnings.length > 0 && (
                  <div className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                    {summary.warnings.join(' | ')}
                  </div>
                )}
              </div>
            ))}
          </div>

          {activeResults.results[0] && (
            <div className="space-y-2">
              {activeResults.results[0].simulations.slice(0, 3).map((simulation) => (
                <div
                  key={simulation.simulation_number}
                  className="rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2"
                >
                  <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    Simulation #{simulation.simulation_number}
                  </div>
                  <div className="mt-1 text-xs text-gray-600 dark:text-gray-300">
                    Final {formatCurrency(simulation.final_equity)} · Return{' '}
                    {formatPercent(simulation.total_return)} · Drawdown{' '}
                    {formatPercent(simulation.max_drawdown)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
