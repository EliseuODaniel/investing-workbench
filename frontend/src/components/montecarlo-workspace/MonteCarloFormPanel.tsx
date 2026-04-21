import { Activity, Loader2 } from 'lucide-react';
import { MonteCarloFormPanelProps } from './types';

export default function MonteCarloFormPanel({
  draft,
  currentRunId,
  selectedConfigPath,
  canSubmit,
  isExecuting,
  onUpdateDraft,
  onRun,
}: MonteCarloFormPanelProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => onUpdateDraft('sourceMode', 'current-run')}
          className={`rounded-lg border px-3 py-2 text-sm ${
            draft.sourceMode === 'current-run'
              ? 'border-rose-500 bg-rose-50 text-rose-700 dark:border-rose-400 dark:bg-rose-950/30 dark:text-rose-200'
              : 'border-gray-200 text-gray-600 dark:border-gray-700 dark:text-gray-300'
          }`}
        >
          Current Run
        </button>
        <button
          type="button"
          onClick={() => onUpdateDraft('sourceMode', 'config')}
          className={`rounded-lg border px-3 py-2 text-sm ${
            draft.sourceMode === 'config'
              ? 'border-rose-500 bg-rose-50 text-rose-700 dark:border-rose-400 dark:bg-rose-950/30 dark:text-rose-200'
              : 'border-gray-200 text-gray-600 dark:border-gray-700 dark:text-gray-300'
          }`}
        >
          Fresh Config Run
        </button>
      </div>

      <div className="rounded-lg bg-gray-50 dark:bg-gray-800 px-3 py-3 text-xs text-gray-600 dark:text-gray-300">
        {draft.sourceMode === 'current-run' ? (
          <span>
            Source run: <span className="font-mono">{currentRunId ?? 'none loaded'}</span>
          </span>
        ) : (
          <span>
            Source config:{' '}
            <span className="font-mono">{selectedConfigPath ?? 'none selected'}</span>
          </span>
        )}
      </div>

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
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Simulations
          </label>
          <input
            value={draft.simulationsText}
            onChange={(event) => onUpdateDraft('simulationsText', event.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          />
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
            Method
          </label>
          <select
            value={draft.method}
            onChange={(event) =>
              onUpdateDraft('method', event.target.value as 'bootstrap' | 'shuffle')
            }
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          >
            <option value="bootstrap">Bootstrap</option>
            <option value="shuffle">Shuffle</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Ruin Threshold
          </label>
          <input
            value={draft.ruinThresholdText}
            onChange={(event) => onUpdateDraft('ruinThresholdText', event.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={onRun}
        disabled={!canSubmit || isExecuting}
        className="inline-flex items-center px-4 py-2 rounded-lg bg-rose-600 text-white text-sm font-medium hover:bg-rose-700 disabled:opacity-50"
      >
        {isExecuting ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Activity className="h-4 w-4 mr-2" />
        )}
        Run Monte Carlo
      </button>
    </div>
  );
}
