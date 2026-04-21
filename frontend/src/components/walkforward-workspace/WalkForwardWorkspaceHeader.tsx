import { CalendarRange, RefreshCw } from 'lucide-react';
import { WalkForwardWorkspaceHeaderProps } from './types';

export default function WalkForwardWorkspaceHeader({
  isLoadingExecutions,
  onRefresh,
}: WalkForwardWorkspaceHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 mb-4">
      <div>
        <div className="flex items-center mb-2">
          <CalendarRange className="h-4 w-4 mr-2 text-sky-600 dark:text-sky-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Walk-Forward Lab
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Stress-test strategies across rolling train and test windows.
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
