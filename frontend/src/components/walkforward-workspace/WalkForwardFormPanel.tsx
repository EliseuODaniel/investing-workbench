import { Activity, Loader2 } from 'lucide-react';
import { WalkForwardFormPanelProps } from './types';

export default function WalkForwardFormPanel({
  draft,
  canSubmit,
  isExecuting,
  onUpdateDraft,
  onRun,
}: WalkForwardFormPanelProps) {
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
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Train Rows
          </label>
          <input
            value={draft.trainDaysText}
            onChange={(event) => onUpdateDraft('trainDaysText', event.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Test Rows
          </label>
          <input
            value={draft.testDaysText}
            onChange={(event) => onUpdateDraft('testDaysText', event.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">
            Step Rows
          </label>
          <input
            value={draft.stepDaysText}
            onChange={(event) => onUpdateDraft('stepDaysText', event.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={onRun}
        disabled={!canSubmit || isExecuting}
        className="inline-flex items-center px-4 py-2 rounded-lg bg-sky-600 text-white text-sm font-medium hover:bg-sky-700 disabled:opacity-50"
      >
        {isExecuting ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Activity className="h-4 w-4 mr-2" />
        )}
        Run Walk-Forward
      </button>
    </div>
  );
}
