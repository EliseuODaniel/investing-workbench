import { Beaker, Loader2, PlayCircle } from 'lucide-react';
import { OptimizationFormPanelProps } from './types';

export default function OptimizationFormPanel({
  draft,
  canSubmit,
  isPlanning,
  isExecuting,
  onUpdateDraft,
  onPreviewPlan,
  onRunOptimization,
}: OptimizationFormPanelProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
          Strategies
        </label>
        <input
          value={draft.strategiesText}
          onChange={(event) => onUpdateDraft('strategiesText', event.target.value)}
          placeholder="Simple Martingale, Buy & Hold"
          className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
        />
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Comma or line-separated. Defaults to the strategies selected in the current form.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Objective
          </label>
          <select
            value={draft.objective}
            onChange={(event) => onUpdateDraft('objective', event.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          >
            <option value="sharpe_ratio">Sharpe Ratio</option>
            <option value="total_return">Total Return</option>
            <option value="cagr">CAGR</option>
            <option value="max_drawdown">Max Drawdown</option>
            <option value="volatility">Volatility</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Direction
          </label>
          <select
            value={draft.direction}
            onChange={(event) =>
              onUpdateDraft('direction', event.target.value as 'maximize' | 'minimize')
            }
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          >
            <option value="maximize">Maximize</option>
            <option value="minimize">Minimize</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Mode
          </label>
          <select
            value={draft.mode}
            onChange={(event) => onUpdateDraft('mode', event.target.value as 'grid' | 'random')}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          >
            <option value="grid">Grid</option>
            <option value="random">Random</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Max Trials
          </label>
          <input
            value={draft.maxTrialsText}
            onChange={(event) => onUpdateDraft('maxTrialsText', event.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
          Random Seed
        </label>
        <input
          value={draft.seedText}
          onChange={(event) => onUpdateDraft('seedText', event.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
          Global Search Space JSON
        </label>
        <textarea
          value={draft.globalSpaceText}
          onChange={(event) => onUpdateDraft('globalSpaceText', event.target.value)}
          rows={10}
          className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs font-mono"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
          Strategy Overrides JSON
        </label>
        <textarea
          value={draft.strategySpaceText}
          onChange={(event) => onUpdateDraft('strategySpaceText', event.target.value)}
          rows={10}
          className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs font-mono"
        />
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onPreviewPlan}
          disabled={!canSubmit || isPlanning}
          className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {isPlanning ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Beaker className="h-4 w-4 mr-2" />
          )}
          Preview Plan
        </button>
        <button
          type="button"
          onClick={onRunOptimization}
          disabled={!canSubmit || isExecuting}
          className="inline-flex items-center px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
        >
          {isExecuting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <PlayCircle className="h-4 w-4 mr-2" />
          )}
          Run Optimization
        </button>
      </div>
    </div>
  );
}
