import { Clock3 } from 'lucide-react';
import { formatDateTime } from '../../lib/utils';
import { DatasetRefreshQueueProps } from './types';

export default function DatasetRefreshQueue({ dueDatasets }: DatasetRefreshQueueProps) {
  if (dueDatasets.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/30">
      <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-200">
        <Clock3 className="h-3 w-3 mr-1" />
        Refresh Queue
      </div>
      <div className="mt-2 text-xs text-amber-900 dark:text-amber-100">
        {dueDatasets.length} dataset{dueDatasets.length > 1 ? 's are' : ' is'} due for refresh.
      </div>
      <div className="mt-2 space-y-1 text-[11px] text-amber-800 dark:text-amber-200">
        {dueDatasets.slice(0, 4).map((dataset) => (
          <div key={dataset.dataset_id}>
            {dataset.name}
            {dataset.next_refresh_due_at && ` · due ${formatDateTime(dataset.next_refresh_due_at)}`}
          </div>
        ))}
      </div>
    </div>
  );
}
