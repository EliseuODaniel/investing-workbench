import { Copy, Download, FileCode2, ScrollText } from 'lucide-react';
import { ResearchWorkspaceNarrative } from '../../lib/researchWorkspaceNarrative';
import { formatDateTime } from '../../lib/utils';
import { ResearchWorkspacePayload } from '../../types/api';

interface ResearchWorkspaceReportViewProps {
  workspace: ResearchWorkspacePayload;
  narrative: ResearchWorkspaceNarrative;
  onExportBrief: () => void;
  onExportHtml: () => void;
  onCopyBrief: () => void | Promise<void>;
  isExporting?: boolean;
  isLoading?: boolean;
}

export default function ResearchWorkspaceReportView({
  workspace,
  narrative,
  onExportBrief,
  onExportHtml,
  onCopyBrief,
  isExporting = false,
  isLoading = false,
}: ResearchWorkspaceReportViewProps) {
  const selectionItems = [
    {
      label: 'Primary Experiment',
      value: `${workspace.selected_experiment.experiment_type}:${workspace.selected_experiment.experiment_id}`,
    },
    {
      label: 'Anchor Run',
      value: workspace.selection.anchor_run_id ?? 'n/a',
    },
    {
      label: 'Optimization',
      value: workspace.selection.optimization_id ?? 'n/a',
    },
    {
      label: 'Walk-Forward',
      value: workspace.selection.walkforward_id ?? 'n/a',
    },
    {
      label: 'Monte Carlo',
      value: workspace.selection.montecarlo_id ?? 'n/a',
    },
  ];

  const risks =
    narrative.risks.length > 0
      ? narrative.risks
      : ['No explicit risks or warnings were detected in this workspace.'];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
            <ScrollText className="h-3 w-3 mr-1" />
            Report View
          </div>
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {workspace.name}
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Created at {formatDateTime(workspace.created_at)}
          </div>
          <div className="mt-1 text-xs font-mono text-gray-500 dark:text-gray-400">
            {workspace.workspace_id}
          </div>
          {isLoading && (
            <div className="mt-2 text-xs text-sky-600 dark:text-sky-300">
              Syncing report from API...
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onCopyBrief}
            disabled={isExporting}
            className="rounded bg-gray-100 px-3 py-2 text-xs font-medium text-gray-800 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
          >
            <Copy className="mr-1 inline h-3 w-3" />
            {isExporting ? 'Working...' : 'Copy Brief'}
          </button>
          <button
            type="button"
            onClick={onExportBrief}
            disabled={isExporting}
            className="rounded bg-gray-100 px-3 py-2 text-xs font-medium text-gray-800 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
          >
            <Download className="mr-1 inline h-3 w-3" />
            {isExporting ? 'Working...' : 'Export Brief'}
          </button>
          <button
            type="button"
            onClick={onExportHtml}
            disabled={isExporting}
            className="rounded bg-gray-100 px-3 py-2 text-xs font-medium text-gray-800 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
          >
            <FileCode2 className="mr-1 inline h-3 w-3" />
            {isExporting ? 'Working...' : 'Export HTML'}
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800/60">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          Executive Summary
        </div>
        <p className="mt-2 text-sm text-gray-700 dark:text-gray-200">
          {narrative.executiveSummary}
        </p>
      </div>

      {workspace.notes && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Notes
          </div>
          <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-200">
            {workspace.notes}
          </p>
        </div>
      )}

      {narrative.keyMetrics.length > 0 && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">
            Key Metrics
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {narrative.keyMetrics.map((item) => (
              <div key={item.label} className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  {item.label}
                </div>
                <div className="mt-1 font-semibold text-gray-900 dark:text-gray-100 break-all">
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
            Highlights
          </div>
          <div className="space-y-2 text-sm text-gray-700 dark:text-gray-200">
            {narrative.highlights.map((item) => (
              <div key={item}>- {item}</div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
            Risks
          </div>
          <div className="space-y-2 text-sm text-gray-700 dark:text-gray-200">
            {risks.map((item) => (
              <div key={item}>- {item}</div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">
          Attached Artifacts
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {selectionItems.map((item) => (
            <div key={item.label} className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                {item.label}
              </div>
              <div className="mt-1 font-mono text-gray-900 dark:text-gray-100 break-all">
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
          Markdown Preview
        </div>
        <pre className="overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-gray-700 dark:text-gray-200">
          {narrative.markdown}
        </pre>
      </div>
    </div>
  );
}
