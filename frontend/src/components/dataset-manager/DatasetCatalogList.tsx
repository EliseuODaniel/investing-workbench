import { formatDateTime } from '../../lib/utils';
import { DatasetCatalogListProps } from './types';

export default function DatasetCatalogList({
  datasets,
  selectedDatasetId,
  currentCachePath,
  isLoadingDatasets,
  onSelectDataset,
}: DatasetCatalogListProps) {
  return (
    <div className="space-y-2 max-h-56 overflow-auto">
      {datasets.map((dataset) => {
        const isActive = dataset.dataset_id === selectedDatasetId;
        const isApplied = currentCachePath === dataset.path;

        return (
          <button
            key={dataset.dataset_id}
            type="button"
            onClick={() => onSelectDataset(dataset.dataset_id)}
            className={`w-full text-left rounded-lg border px-3 py-3 transition-colors ${
              isActive
                ? 'border-cyan-500 bg-cyan-50 dark:border-cyan-400 dark:bg-cyan-950/30'
                : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800'
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {dataset.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {dataset.category} · {dataset.format} ·{' '}
                  {dataset.row_count.toLocaleString('pt-BR')} rows
                </div>
              </div>
              <div className="flex items-center gap-2">
                {dataset.refresh_due && (
                  <span className="rounded-full bg-amber-100 px-2 py-1 text-[11px] font-medium text-amber-700 dark:bg-amber-900 dark:text-amber-200">
                    due
                  </span>
                )}
                {isApplied && (
                  <span className="rounded-full bg-emerald-100 px-2 py-1 text-[11px] font-medium text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">
                    in use
                  </span>
                )}
              </div>
            </div>
            <div className="mt-2 text-[11px] font-mono text-gray-500 dark:text-gray-400">
              {dataset.path}
            </div>
            {dataset.next_refresh_due_at && (
              <div className="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
                Next due: {formatDateTime(dataset.next_refresh_due_at)}
              </div>
            )}
          </button>
        );
      })}

      {datasets.length === 0 && !isLoadingDatasets && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No datasets discovered in the local `data/` directory.
        </p>
      )}
    </div>
  );
}
