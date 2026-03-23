import {
  Database,
  FileStack,
  Fingerprint,
  Loader2,
  RefreshCw,
  Wand2,
} from 'lucide-react';
import { useDatasets } from '../hooks/useDatasets';
import { formatDateTime } from '../lib/utils';

interface DatasetManagerPanelProps {
  currentCachePath?: string;
  onApplyDataset: (dataset: { path: string; name: string }) => void;
  onError: (message: string | null) => void;
}

export default function DatasetManagerPanel({
  currentCachePath,
  onApplyDataset,
  onError,
}: DatasetManagerPanelProps) {
  const {
    datasets,
    selectedDatasetId,
    selectedDataset,
    isLoadingDatasets,
    isLoadingSelectedDataset,
    refreshDatasets,
    loadDataset,
  } = useDatasets(onError);

  return (
    <div className="card mt-6">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center mb-2">
            <Database className="h-4 w-4 mr-2 text-cyan-600 dark:text-cyan-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Dataset Manager
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Inspect local datasets and apply one to the current backtest request.
          </p>
        </div>
        <button
          type="button"
          onClick={refreshDatasets}
          disabled={isLoadingDatasets}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          {isLoadingDatasets ? (
            <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3 inline mr-1" />
          )}
          Refresh
        </button>
      </div>

      <div className="space-y-4">
        <div className="space-y-2 max-h-56 overflow-auto">
          {datasets.map((dataset) => {
            const isActive = dataset.dataset_id === selectedDatasetId;
            const isApplied = currentCachePath === dataset.path;
            return (
              <button
                key={dataset.dataset_id}
                type="button"
                onClick={() => loadDataset(dataset.dataset_id)}
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
                      {dataset.category} · {dataset.format} · {dataset.row_count.toLocaleString('pt-BR')} rows
                    </div>
                  </div>
                  {isApplied && (
                    <span className="rounded-full bg-emerald-100 px-2 py-1 text-[11px] font-medium text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">
                      in use
                    </span>
                  )}
                </div>
                <div className="mt-2 text-[11px] font-mono text-gray-500 dark:text-gray-400">
                  {dataset.path}
                </div>
              </button>
            );
          })}
          {datasets.length === 0 && !isLoadingDatasets && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              No datasets discovered in the local `data/` directory.
            </p>
          )}
        </div>

        {isLoadingSelectedDataset ? (
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-sm text-gray-500 dark:text-gray-400">
            Loading dataset detail...
          </div>
        ) : (
          selectedDataset && (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {selectedDataset.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {selectedDataset.path}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    onApplyDataset({
                      path: selectedDataset.path,
                      name: selectedDataset.name,
                    })
                  }
                  className="inline-flex items-center rounded-lg bg-cyan-600 px-3 py-2 text-xs font-medium text-white hover:bg-cyan-700"
                >
                  <Wand2 className="h-3 w-3 mr-1" />
                  Use in Backtest
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Category</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {selectedDataset.category}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Last Modified</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {formatDateTime(selectedDataset.last_modified)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Range</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {selectedDataset.start_timestamp
                      ? `${new Date(selectedDataset.start_timestamp).toLocaleDateString('pt-BR')} - ${new Date(selectedDataset.end_timestamp || selectedDataset.start_timestamp).toLocaleDateString('pt-BR')}`
                      : 'No datetime index'}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Columns</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {selectedDataset.columns.length}
                  </div>
                </div>
              </div>

              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                  <Fingerprint className="h-3 w-3 mr-1" />
                  Fingerprint
                </div>
                <div className="font-mono text-[11px] break-all text-gray-700 dark:text-gray-300">
                  {selectedDataset.data_fingerprint}
                </div>
              </div>

              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                  <FileStack className="h-3 w-3 mr-1" />
                  Preview
                </div>
                <pre className="text-[11px] whitespace-pre-wrap break-words text-gray-700 dark:text-gray-300">
                  {JSON.stringify(selectedDataset.preview_rows, null, 2)}
                </pre>
              </div>

              {selectedDataset.validation_warnings.length > 0 && (
                <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 px-3 py-3 text-xs text-amber-800 dark:text-amber-200">
                  {selectedDataset.validation_warnings.join(' | ')}
                </div>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
}
