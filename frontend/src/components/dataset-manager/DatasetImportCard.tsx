import { FileStack, Loader2 } from 'lucide-react';
import { DatasetImportCardProps } from './types';

export default function DatasetImportCard({
  sourcePath,
  datasetName,
  isImportingDataset,
  onSourcePathChange,
  onDatasetNameChange,
  onImport,
}: DatasetImportCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
        Import Local Dataset
      </div>
      <input
        value={sourcePath}
        onChange={(event) => onSourcePathChange(event.target.value)}
        placeholder="/abs/path/to/file.csv"
        className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
      />
      <input
        value={datasetName}
        onChange={(event) => onDatasetNameChange(event.target.value)}
        placeholder="Optional destination name"
        className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
      />
      <button
        type="button"
        onClick={onImport}
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
  );
}
