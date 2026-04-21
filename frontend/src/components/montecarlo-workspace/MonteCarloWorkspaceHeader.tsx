import { Dices, RefreshCw } from 'lucide-react';
import { MonteCarloWorkspaceHeaderProps } from './types';

export default function MonteCarloWorkspaceHeader({
  isLoadingExecutions,
  onRefresh,
}: MonteCarloWorkspaceHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 mb-4">
      <div>
        <div className="flex items-center mb-2">
          <Dices className="h-4 w-4 mr-2 text-rose-600 dark:text-rose-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Monte Carlo Lab
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Re-sample closed trades to inspect tail risk, loss probability, and drawdown stress.
        </p>
      </div>
      <button
        type="button"
        onClick={onRefresh}
        disabled={isLoadingExecutions}
        className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
      >
        <RefreshCw className="h-3 w-3 inline mr-1" />
        Refresh Jobs
      </button>
    </div>
  );
}
