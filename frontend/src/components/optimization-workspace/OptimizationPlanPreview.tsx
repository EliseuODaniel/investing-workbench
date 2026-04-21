import { Target } from 'lucide-react';
import { OptimizationPlanPreviewProps } from './types';

export default function OptimizationPlanPreview({ plan }: OptimizationPlanPreviewProps) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center mb-3">
        <Target className="h-4 w-4 mr-2 text-indigo-600 dark:text-indigo-400" />
        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Plan Preview</h4>
      </div>

      {!plan ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Preview a plan to inspect the generated trial space before execution.
        </p>
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-gray-500 dark:text-gray-400">Trials</div>
              <div className="font-medium text-gray-900 dark:text-gray-100">{plan.trial_count}</div>
            </div>
            <div>
              <div className="text-gray-500 dark:text-gray-400">Mode</div>
              <div className="font-medium text-gray-900 dark:text-gray-100">{plan.mode}</div>
            </div>
          </div>
          {plan.warnings.length > 0 && (
            <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-xs text-amber-800 dark:text-amber-200">
              {plan.warnings.join(' | ')}
            </div>
          )}
          <div className="space-y-2">
            {plan.trials.slice(0, 4).map((trial) => (
              <div key={trial.trial_id} className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-2">
                <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                  {trial.trial_id}
                </div>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {trial.strategy_name}
                </div>
                <pre className="mt-2 text-xs text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                  {JSON.stringify(trial.parameters, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
