import { useEffect, useState } from 'react';
import {
  ArrowUpDown,
  Download,
  FolderOpen,
  Link2,
  Loader2,
  RefreshCw,
  Save,
  ScrollText,
  Upload,
} from 'lucide-react';
import { apiClient } from '../lib/api';
import {
  filterAndSortResearchWorkspaces,
  type ResearchWorkspaceSort,
} from '../lib/researchWorkspaceList';
import {
  buildResearchWorkspaceNarrative,
  buildResearchWorkspaceNarrativeFromReport,
  type ResearchWorkspaceNarrative,
} from '../lib/researchWorkspaceNarrative';
import {
  downloadHTMLDocument,
  downloadJSON,
  downloadText,
  formatDateTime,
} from '../lib/utils';
import { ResearchWorkspacePayload } from '../types/api';
import ResearchWorkspaceReportView from './research-workspaces/ResearchWorkspaceReportView';

interface SavedResearchWorkspacesPanelProps {
  workspaces: ResearchWorkspacePayload[];
  isLoading: boolean;
  onRefresh: () => Promise<void> | void;
  onOpenWorkspace: (workspace: ResearchWorkspacePayload) => void;
  onLoadRun: (runId: string) => Promise<void> | void;
  onError: (message: string | null) => void;
}

export default function SavedResearchWorkspacesPanel({
  workspaces,
  isLoading,
  onRefresh,
  onOpenWorkspace,
  onLoadRun,
  onError,
}: SavedResearchWorkspacesPanelProps) {
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'workspace' | 'report'>('workspace');
  const [isOpeningRun, setIsOpeningRun] = useState(false);
  const [isSavingMetadata, setIsSavingMetadata] = useState(false);
  const [isImportingWorkspace, setIsImportingWorkspace] = useState(false);
  const [isExportingNarrative, setIsExportingNarrative] = useState(false);
  const [isLoadingServerNarrative, setIsLoadingServerNarrative] = useState(false);
  const [serverNarrative, setServerNarrative] = useState<ResearchWorkspaceNarrative | null>(null);
  const [editableName, setEditableName] = useState('');
  const [editableNotes, setEditableNotes] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<ResearchWorkspaceSort>('created_desc');

  const visibleWorkspaces = filterAndSortResearchWorkspaces(workspaces, {
    query: searchQuery,
    sort: sortOrder,
  });

  useEffect(() => {
    if (visibleWorkspaces.length === 0) {
      setSelectedWorkspaceId(null);
      return;
    }

    setSelectedWorkspaceId((current) => {
      if (
        current &&
        visibleWorkspaces.some((workspace) => workspace.workspace_id === current)
      ) {
        return current;
      }
      return visibleWorkspaces[0]?.workspace_id ?? null;
    });
  }, [visibleWorkspaces]);

  const selectedWorkspace =
    visibleWorkspaces.find((workspace) => workspace.workspace_id === selectedWorkspaceId) ??
    null;
  const selectedNarrative = selectedWorkspace
    ? buildResearchWorkspaceNarrative(selectedWorkspace)
    : null;
  const effectiveNarrative = serverNarrative ?? selectedNarrative;
  const reportNarrative = selectedWorkspace ? effectiveNarrative ?? selectedNarrative : null;

  useEffect(() => {
    if (!selectedWorkspace) {
      setViewMode('workspace');
    }
  }, [selectedWorkspace]);

  useEffect(() => {
    if (!selectedWorkspace || viewMode !== 'report') {
      setServerNarrative(null);
      setIsLoadingServerNarrative(false);
      return;
    }

    let isActive = true;
    setServerNarrative(null);
    setIsLoadingServerNarrative(true);

    apiClient
      .getResearchWorkspaceReport(selectedWorkspace.workspace_id)
      .then((response) => {
        if (!isActive) {
          return;
        }
        setServerNarrative(buildResearchWorkspaceNarrativeFromReport(response.report));
      })
      .catch((error: any) => {
        if (!isActive) {
          return;
        }
        onError(error.response?.data?.detail || 'Failed to load research workspace report');
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingServerNarrative(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [onError, selectedWorkspace, viewMode]);

  useEffect(() => {
    setEditableName(selectedWorkspace?.name ?? '');
    setEditableNotes(selectedWorkspace?.notes ?? '');
  }, [selectedWorkspace?.name, selectedWorkspace?.notes, selectedWorkspace?.workspace_id]);

  async function openAnchorRun() {
    const runId = selectedWorkspace?.selection.anchor_run_id;
    if (!runId) {
      return;
    }

    setIsOpeningRun(true);
    try {
      await onLoadRun(runId);
    } catch (error: any) {
      onError(error?.message || 'Failed to load research workspace anchor run');
    } finally {
      setIsOpeningRun(false);
    }
  }

  function exportWorkspace() {
    if (!selectedWorkspace) {
      return;
    }
    downloadJSON(selectedWorkspace, `${selectedWorkspace.workspace_id}.json`);
  }

  async function exportNarrative() {
    if (!selectedWorkspace || !effectiveNarrative) {
      return;
    }

    setIsExportingNarrative(true);
    try {
      const markdown = await apiClient.exportResearchWorkspaceReport(
        selectedWorkspace.workspace_id,
        'markdown'
      );
      downloadText(markdown, `${selectedWorkspace.workspace_id}_brief.md`);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to export research workspace brief');
    } finally {
      setIsExportingNarrative(false);
    }
  }

  async function exportNarrativeHtml() {
    if (!selectedWorkspace || !effectiveNarrative) {
      return;
    }

    setIsExportingNarrative(true);
    try {
      const html = await apiClient.exportResearchWorkspaceReport(
        selectedWorkspace.workspace_id,
        'html'
      );
      downloadHTMLDocument(html, `${selectedWorkspace.workspace_id}_brief.html`);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to export research workspace HTML brief');
    } finally {
      setIsExportingNarrative(false);
    }
  }

  async function saveMetadata() {
    if (!selectedWorkspace) {
      return;
    }

    setIsSavingMetadata(true);
    try {
      await apiClient.updateResearchWorkspace(selectedWorkspace.workspace_id, {
        name: editableName,
        notes: editableNotes,
      });
      await onRefresh();
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to update research workspace');
    } finally {
      setIsSavingMetadata(false);
    }
  }

  async function importWorkspace(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsImportingWorkspace(true);
    try {
      const text = await file.text();
      const payload = JSON.parse(text);
      const imported = await apiClient.importResearchWorkspace({ payload });
      await onRefresh();
      setSelectedWorkspaceId(imported.workspace_id);
    } catch (error: any) {
      onError(error?.message || 'Failed to import research workspace JSON');
    } finally {
      event.target.value = '';
      setIsImportingWorkspace(false);
    }
  }

  async function copyNarrative() {
    if (!selectedWorkspace) {
      return;
    }

    setIsExportingNarrative(true);
    try {
      const markdown = await apiClient.exportResearchWorkspaceReport(
        selectedWorkspace.workspace_id,
        'markdown'
      );
      await navigator.clipboard.writeText(markdown);
    } catch (error: any) {
      onError(error.response?.data?.detail || error?.message || 'Failed to copy research workspace brief');
    } finally {
      setIsExportingNarrative(false);
    }
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center mb-2">
            <FolderOpen className="h-4 w-4 mr-2 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Saved Research Workspaces
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Reopen curated experiment comparisons, export them, or jump to the anchor run.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          {isLoading ? (
            <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3 inline mr-1" />
          )}
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="space-y-2">
          <div className="grid grid-cols-1 gap-3 rounded-lg border border-gray-200 dark:border-gray-700 p-3 bg-white/80 dark:bg-gray-900/40">
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  Total
                </div>
                <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {workspaces.length}
                </div>
              </div>
              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  With Notes
                </div>
                <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {workspaces.filter((workspace) => Boolean(workspace.notes?.trim())).length}
                </div>
              </div>
              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  With Anchor
                </div>
                <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {workspaces.filter((workspace) => Boolean(workspace.selection.anchor_run_id)).length}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3">
              <label className="text-xs text-gray-500 dark:text-gray-400">
                Search
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Name, note, workspace id, run..."
                  className="mt-1 w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100"
                />
              </label>
              <label className="text-xs text-gray-500 dark:text-gray-400">
                Sort
                <div className="relative mt-1">
                  <ArrowUpDown className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                  <select
                    value={sortOrder}
                    onChange={(event) =>
                      setSortOrder(event.target.value as ResearchWorkspaceSort)
                    }
                    className="w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 py-2 pl-9 pr-3 text-sm text-gray-900 dark:text-gray-100"
                  >
                    <option value="created_desc">Newest first</option>
                    <option value="created_asc">Oldest first</option>
                    <option value="name_asc">Name A-Z</option>
                    <option value="name_desc">Name Z-A</option>
                  </select>
                </div>
              </label>
            </div>
          </div>

          {visibleWorkspaces.length === 0 && (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {workspaces.length === 0
                ? 'No saved research workspace yet.'
                : 'No workspace matches the current filters.'}
            </div>
          )}
          {visibleWorkspaces.map((workspace) => (
            <button
              key={workspace.workspace_id}
              type="button"
              onClick={() => setSelectedWorkspaceId(workspace.workspace_id)}
              className={`w-full rounded-lg border px-3 py-3 text-left transition-colors ${
                selectedWorkspaceId === workspace.workspace_id
                  ? 'border-indigo-300 bg-indigo-50 dark:border-indigo-700 dark:bg-indigo-950/20'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {workspace.name}
              </div>
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {formatDateTime(workspace.created_at)}
              </div>
              <div className="mt-1 text-xs font-mono text-gray-500 dark:text-gray-400">
                {workspace.workspace_id}
              </div>
            </button>
          ))}
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          {!selectedWorkspace ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Select a saved workspace to inspect or reopen it.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {selectedWorkspace.name}
                  </div>
                  <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Created at {formatDateTime(selectedWorkspace.created_at)}
                  </div>
                </div>
                <div className="inline-flex rounded-lg border border-gray-200 dark:border-gray-700 p-1 bg-gray-50 dark:bg-gray-800">
                  <button
                    type="button"
                    onClick={() => setViewMode('workspace')}
                    className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                      viewMode === 'workspace'
                        ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    Workspace View
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('report')}
                    className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                      viewMode === 'report'
                        ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    Report View
                  </button>
                </div>
              </div>

              {viewMode === 'report' && reportNarrative ? (
                <ResearchWorkspaceReportView
                  workspace={selectedWorkspace}
                  narrative={reportNarrative}
                  onExportBrief={exportNarrative}
                  onExportHtml={exportNarrativeHtml}
                  onCopyBrief={copyNarrative}
                  isExporting={isExportingNarrative}
                  isLoading={isLoadingServerNarrative}
                />
              ) : (
                <>
                  <div className="grid grid-cols-1 gap-3">
                    <label className="text-xs text-gray-500 dark:text-gray-400">
                      Workspace Name
                      <input
                        value={editableName}
                        onChange={(event) => setEditableName(event.target.value)}
                        className="mt-1 w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100"
                      />
                    </label>
                    <label className="text-xs text-gray-500 dark:text-gray-400">
                      Notes
                      <textarea
                        value={editableNotes}
                        onChange={(event) => setEditableNotes(event.target.value)}
                        rows={3}
                        className="mt-1 w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100"
                      />
                    </label>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                      <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Selected
                      </div>
                      <div className="mt-1 font-mono text-gray-900 dark:text-gray-100">
                        {selectedWorkspace.selected_experiment.experiment_id}
                      </div>
                    </div>
                    <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                      <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Anchor Run
                      </div>
                      <div className="mt-1 font-mono text-gray-900 dark:text-gray-100">
                        {selectedWorkspace.selection.anchor_run_id ?? 'n/a'}
                      </div>
                    </div>
                    <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                      <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Optimization
                      </div>
                      <div className="mt-1 font-mono text-gray-900 dark:text-gray-100">
                        {selectedWorkspace.selection.optimization_id ?? 'n/a'}
                      </div>
                    </div>
                    <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                      <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Walk-Forward
                      </div>
                      <div className="mt-1 font-mono text-gray-900 dark:text-gray-100">
                        {selectedWorkspace.selection.walkforward_id ?? 'n/a'}
                      </div>
                    </div>
                    <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                      <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Monte Carlo
                      </div>
                      <div className="mt-1 font-mono text-gray-900 dark:text-gray-100">
                        {selectedWorkspace.selection.montecarlo_id ?? 'n/a'}
                      </div>
                    </div>
                    <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                      <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Primary Type
                      </div>
                      <div className="mt-1 text-gray-900 dark:text-gray-100">
                        {selectedWorkspace.selected_experiment.experiment_type}
                      </div>
                    </div>
                  </div>

                  {selectedNarrative && (
                    <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800/60">
                      <div className="flex items-center mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        <ScrollText className="h-3 w-3 mr-1" />
                        Executive Snapshot
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-200">
                        {selectedNarrative.executiveSummary}
                      </p>
                      <div className="mt-3">
                        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">
                          Highlights
                        </div>
                        <div className="space-y-1 text-sm text-gray-700 dark:text-gray-200">
                          {selectedNarrative.highlights.map((item) => (
                            <div key={item}>- {item}</div>
                          ))}
                        </div>
                      </div>
                      <div className="mt-3">
                        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">
                          Risks
                        </div>
                        <div className="space-y-1 text-sm text-gray-700 dark:text-gray-200">
                          {(selectedNarrative.risks.length > 0
                            ? selectedNarrative.risks
                            : ['No explicit risks or warnings were detected in this workspace.']
                          ).map((item) => (
                            <div key={item}>- {item}</div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onOpenWorkspace(selectedWorkspace)}
                      className="rounded bg-indigo-100 px-3 py-2 text-xs font-medium text-indigo-800 transition-colors hover:bg-indigo-200 dark:bg-indigo-900/40 dark:text-indigo-200 dark:hover:bg-indigo-900/60"
                    >
                      <Link2 className="mr-1 inline h-3 w-3" />
                      Open In Research Overview
                    </button>
                    <button
                      type="button"
                      onClick={saveMetadata}
                      disabled={isSavingMetadata}
                      className="rounded bg-emerald-100 px-3 py-2 text-xs font-medium text-emerald-800 transition-colors hover:bg-emerald-200 disabled:opacity-50 dark:bg-emerald-900/40 dark:text-emerald-200 dark:hover:bg-emerald-900/60"
                    >
                      <Save className="mr-1 inline h-3 w-3" />
                      {isSavingMetadata ? 'Saving...' : 'Save Notes'}
                    </button>
                    <button
                      type="button"
                      onClick={openAnchorRun}
                      disabled={!selectedWorkspace.selection.anchor_run_id || isOpeningRun}
                      className="rounded bg-amber-100 px-3 py-2 text-xs font-medium text-amber-800 transition-colors hover:bg-amber-200 disabled:opacity-50 dark:bg-amber-900/40 dark:text-amber-200 dark:hover:bg-amber-900/60"
                    >
                      {isOpeningRun ? 'Opening...' : 'Open Anchor Run'}
                    </button>
                    <button
                      type="button"
                      onClick={exportWorkspace}
                      className="rounded bg-gray-100 px-3 py-2 text-xs font-medium text-gray-800 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
                    >
                      <Download className="mr-1 inline h-3 w-3" />
                      Export JSON
                    </button>
                    <button
                      type="button"
                      onClick={exportNarrative}
                      disabled={!selectedNarrative}
                      className="rounded bg-gray-100 px-3 py-2 text-xs font-medium text-gray-800 transition-colors hover:bg-gray-200 disabled:opacity-50 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
                    >
                      <ScrollText className="mr-1 inline h-3 w-3" />
                      Export Brief
                    </button>
                    <label className="rounded bg-gray-100 px-3 py-2 text-xs font-medium text-gray-800 transition-colors hover:bg-gray-200 cursor-pointer dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600">
                      <Upload className="mr-1 inline h-3 w-3" />
                      {isImportingWorkspace ? 'Importing...' : 'Import JSON'}
                      <input
                        type="file"
                        accept="application/json"
                        onChange={importWorkspace}
                        className="hidden"
                        disabled={isImportingWorkspace}
                      />
                    </label>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
