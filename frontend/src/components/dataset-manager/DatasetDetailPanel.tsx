import {
  Clock3,
  Database,
  FileStack,
  Fingerprint,
  Loader2,
  RotateCcw,
  ShieldCheck,
  Wand2,
} from 'lucide-react';
import { formatDateTime } from '../../lib/utils';
import { DatasetDetailPanelProps } from './types';

function formatRange(startTimestamp?: string | null, endTimestamp?: string | null) {
  if (!startTimestamp) {
    return 'No datetime index';
  }

  const start = new Date(startTimestamp).toLocaleDateString('pt-BR');
  const end = new Date(endTimestamp || startTimestamp).toLocaleDateString('pt-BR');
  return `${start} - ${end}`;
}

export default function DatasetDetailPanel({
  selectedDataset,
  isLoadingSelectedDataset,
  isRefreshingDataset,
  isUpdatingRefreshPolicy,
  policyEnabled,
  policyIntervalDays,
  policyStartDate,
  policyEndDate,
  onApplyDataset,
  onPolicyEnabledChange,
  onPolicyIntervalDaysChange,
  onPolicyStartDateChange,
  onPolicyEndDateChange,
  onSavePolicy,
  onRefreshNow,
}: DatasetDetailPanelProps) {
  if (isLoadingSelectedDataset) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-sm text-gray-500 dark:text-gray-400">
        Loading dataset detail...
      </div>
    );
  }

  if (!selectedDataset) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {selectedDataset.name}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">{selectedDataset.path}</div>
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
            {formatRange(selectedDataset.start_timestamp, selectedDataset.end_timestamp)}
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
            <div>Managed: {selectedDataset.provenance.managed ? 'yes' : 'no'}</div>
            <div>Refresh strategy: {selectedDataset.provenance.refresh_strategy ?? 'none'}</div>
            <div>
              Policy: {selectedDataset.provenance.refresh_policy?.enabled ? 'enabled' : 'disabled'}
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
          {selectedDataset.provenance.refresh_policy?.next_refresh_due_at && (
            <div className="mt-2 text-[11px] text-gray-600 dark:text-gray-300">
              Next due:{' '}
              {formatDateTime(selectedDataset.provenance.refresh_policy.next_refresh_due_at)}
              {selectedDataset.provenance.refresh_policy.due_now && ' · due now'}
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
        <div className="rounded-md border border-gray-200 dark:border-gray-700 px-3 py-3 space-y-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Refresh Automation
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              checked={policyEnabled}
              onChange={(event) => onPolicyEnabledChange(event.target.checked)}
            />
            Enable scheduled refresh checks
          </label>
          <div className="grid grid-cols-2 gap-3">
            <input
              value={policyIntervalDays}
              onChange={(event) => onPolicyIntervalDaysChange(event.target.value)}
              placeholder="Interval days"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
            />
            <input
              value={policyStartDate}
              onChange={(event) => onPolicyStartDateChange(event.target.value)}
              placeholder="Start date"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
            />
            <input
              value={policyEndDate}
              onChange={(event) => onPolicyEndDateChange(event.target.value)}
              placeholder="Optional end date"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm col-span-2"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onSavePolicy}
              disabled={isUpdatingRefreshPolicy}
              className="inline-flex items-center rounded-lg bg-slate-700 px-3 py-2 text-xs font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {isUpdatingRefreshPolicy ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <Clock3 className="h-3 w-3 mr-1" />
              )}
              Save Policy
            </button>
            <button
              type="button"
              onClick={onRefreshNow}
              disabled={isRefreshingDataset}
              className="inline-flex items-center rounded-lg bg-cyan-600 px-3 py-2 text-xs font-medium text-white hover:bg-cyan-700 disabled:opacity-50"
            >
              {isRefreshingDataset ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <RotateCcw className="h-3 w-3 mr-1" />
              )}
              Refresh Now
            </button>
          </div>
        </div>
      )}

      {selectedDataset.validation_warnings.length > 0 && (
        <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 px-3 py-3 text-xs text-amber-800 dark:text-amber-200">
          {selectedDataset.validation_warnings.join(' | ')}
        </div>
      )}
    </div>
  );
}
