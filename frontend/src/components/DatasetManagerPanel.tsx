import {
  Database,
  FileStack,
  Fingerprint,
  Loader2,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Wand2,
} from 'lucide-react';
import { useState } from 'react';
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
  const [sourcePath, setSourcePath] = useState('');
  const [datasetName, setDatasetName] = useState('');
  const [refreshStartDate, setRefreshStartDate] = useState('2020-01-01');
  const {
    datasets,
    selectedDatasetId,
    selectedDataset,
    isLoadingDatasets,
    isLoadingSelectedDataset,
    isImportingDataset,
    isRefreshingDataset,
    refreshDatasets,
    loadDataset,
    importDataset,
    refreshDataset,
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
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Import Local Dataset
          </div>
          <input
            value={sourcePath}
            onChange={(event) => setSourcePath(event.target.value)}
            placeholder="/abs/path/to/file.csv"
            className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
          />
          <input
            value={datasetName}
            onChange={(event) => setDatasetName(event.target.value)}
            placeholder="Optional destination name"
            className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={() => {
              importDataset(sourcePath, datasetName || undefined, false).then((response) => {
                if (response) {
                  setSourcePath('');
                  setDatasetName('');
                }
              });
            }}
            disabled={!sourcePath.trim() || isImportingDataset}
            className="inline-flex items-center rounded-lg bg-cyan-600 px-3 py-2 text-xs font-medium text-white hover:bg-cyan-700 disabled:opacity-50"
          >
            {isImportingDataset ? (
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            ) : (
              <FileStack className="h-3 w-3 mr-1" />
            )}
            Import into data/
          </button>
        </div>

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

              {selectedDataset.validation && (
                <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                  <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                    <ShieldCheck className="h-3 w-3 mr-1" />
                    Validation
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs text-gray-700 dark:text-gray-300">
                    <div>Missing values: {selectedDataset.validation.missing_value_count}</div>
                    <div>Duplicate rows: {selectedDataset.validation.duplicate_index_count}</div>
                    <div>Date gaps: {selectedDataset.validation.date_gap_count}</div>
                    <div>Price anomalies: {selectedDataset.validation.price_anomaly_count}</div>
                    <div>
                      Missing OHLC cols:{' '}
                      {selectedDataset.validation.missing_required_columns.length > 0
                        ? selectedDataset.validation.missing_required_columns.join(', ')
                        : 'none'}
                    </div>
                    <div>
                      Refresh:{' '}
                      {selectedDataset.validation.supported_refresh ? 'supported' : 'static only'}
                    </div>
                  </div>
                </div>
              )}

              {selectedDataset.provenance && (
                <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                  <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                    <Database className="h-3 w-3 mr-1" />
                    Provenance
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs text-gray-700 dark:text-gray-300">
                    <div>Source kind: {selectedDataset.provenance.source_kind}</div>
                    <div>
                      Managed: {selectedDataset.provenance.managed ? 'yes' : 'no'}
                    </div>
                    <div>
                      Refresh strategy:{' '}
                      {selectedDataset.provenance.refresh_strategy ?? 'none'}
                    </div>
                    <div>
                      Imported at:{' '}
                      {selectedDataset.provenance.imported_at
                        ? formatDateTime(selectedDataset.provenance.imported_at)
                        : 'n/a'}
                    </div>
                  </div>
                  {selectedDataset.provenance.source_path && (
                    <div className="mt-2 text-[11px] font-mono break-all text-gray-600 dark:text-gray-300">
                      {selectedDataset.provenance.source_path}
                    </div>
                  )}
                  {selectedDataset.provenance.history.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {selectedDataset.provenance.history
                        .slice()
                        .reverse()
                        .slice(0, 4)
                        .map((entry) => (
                          <div
                            key={`${entry.event_type}-${entry.occurred_at}`}
                            className="rounded border border-gray-200 dark:border-gray-700 px-2 py-2"
                          >
                            <div className="text-[11px] font-semibold text-gray-700 dark:text-gray-200">
                              {entry.event_type}
                            </div>
                            <div className="text-[11px] text-gray-500 dark:text-gray-400">
                              {formatDateTime(entry.occurred_at)}
                            </div>
                            {Object.keys(entry.details).length > 0 && (
                              <pre className="mt-1 text-[10px] whitespace-pre-wrap break-words text-gray-600 dark:text-gray-300">
                                {JSON.stringify(entry.details, null, 2)}
                              </pre>
                            )}
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              )}

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

              {selectedDataset.validation?.supported_refresh && (
                <div className="rounded-md border border-gray-200 dark:border-gray-700 px-3 py-3 space-y-3">
                  <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Refresh Dataset
                  </div>
                  <input
                    value={refreshStartDate}
                    onChange={(event) => setRefreshStartDate(event.target.value)}
                    className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => refreshDataset(selectedDataset.dataset_id, refreshStartDate)}
                    disabled={isRefreshingDataset}
                    className="inline-flex items-center rounded-lg bg-slate-700 px-3 py-2 text-xs font-medium text-white hover:bg-slate-800 disabled:opacity-50"
                  >
                    {isRefreshingDataset ? (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <RotateCcw className="h-3 w-3 mr-1" />
                    )}
                    Refresh Cache
                  </button>
                </div>
              )}

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
