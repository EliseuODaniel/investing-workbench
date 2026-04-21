import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  BrainCircuit,
  ChevronRight,
  CalendarRange,
  Dices,
  GitBranch,
  Link2,
  Loader2,
  Save,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { useExperimentContextDrilldown } from '../hooks/useExperimentContextDrilldown';
import { useResearchOverview } from '../hooks/useResearchOverview';
import {
  buildResearchTimeline,
  countExperimentsByType,
  countResearchWarnings,
} from '../lib/researchOverview';
import { summarizeResearchAlignment } from '../lib/researchDrilldown';
import { formatPercent } from '../lib/utils';
import { apiClient } from '../lib/api';
import {
  ExperimentDetailPayload,
  ExperimentRegistryRecord,
  ResearchWorkspacePayload,
} from '../types/api';

interface ResearchOverviewPanelProps {
  onError: (message: string | null) => void;
  onLoadRun: (runId: string) => Promise<void> | void;
  workspaceToOpen?: ResearchWorkspacePayload | null;
  onWorkspaceOpened?: () => void;
  onWorkspaceSaved?: () => void;
}

export default function ResearchOverviewPanel({
  onError,
  onLoadRun,
  workspaceToOpen = null,
  onWorkspaceOpened,
  onWorkspaceSaved,
}: ResearchOverviewPanelProps) {
  const {
    experiments,
    optimizations,
    walkForwardExecutions,
    monteCarloExecutions,
    isLoading,
    refresh,
  } = useResearchOverview(onError);

  const latestOptimization = optimizations[0] ?? null;
  const latestWalkForward = walkForwardExecutions[0] ?? null;
  const latestMonteCarlo = monteCarloExecutions[0] ?? null;
  const [selectedExperiment, setSelectedExperiment] = useState<ExperimentRegistryRecord | null>(
    null
  );
  const [selectedDetail, setSelectedDetail] = useState<ExperimentDetailPayload | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isOpeningRun, setIsOpeningRun] = useState(false);
  const [isSavingWorkspace, setIsSavingWorkspace] = useState(false);
  const [contextOverrides, setContextOverrides] = useState({
    optimizationId: 'auto',
    walkforwardId: 'auto',
    montecarloId: 'auto',
  });
  const [pendingWorkspaceSelection, setPendingWorkspaceSelection] = useState<{
    optimizationId: string;
    walkforwardId: string;
    montecarloId: string;
  } | null>(null);
  const [timelineFilter, setTimelineFilter] = useState<
    'all' | 'run' | 'optimization' | 'walkforward' | 'montecarlo' | 'pairs_backtest'
  >('all');
  const timeline = buildResearchTimeline(
    timelineFilter === 'all'
      ? experiments
      : experiments.filter((item) => item.experiment_type === timelineFilter)
  );
  const warningCount = countResearchWarnings(experiments);
  const optimizationCount = countExperimentsByType(experiments, 'optimization');
  const walkForwardCount = countExperimentsByType(experiments, 'walkforward');
  const monteCarloCount = countExperimentsByType(experiments, 'montecarlo');
  const {
    candidates: contextCandidates = {
      optimization: [],
      walkforward: [],
      montecarlo: [],
    },
    targets: contextTargets,
    optimizationResults,
    walkForwardResults,
    monteCarloResults,
    isLoading: isLoadingContext,
  } = useExperimentContextDrilldown(
    selectedDetail,
    experiments,
    {
      optimizationId:
        contextOverrides.optimizationId === 'auto'
          ? null
          : contextOverrides.optimizationId,
      walkforwardId:
        contextOverrides.walkforwardId === 'auto'
          ? null
          : contextOverrides.walkforwardId,
      montecarloId:
        contextOverrides.montecarloId === 'auto'
          ? null
          : contextOverrides.montecarloId,
    },
    onError
  );
  const alignment = summarizeResearchAlignment(
    optimizationResults,
    walkForwardResults,
    monteCarloResults
  );

  useEffect(() => {
    if (timeline.length === 0) {
      setSelectedExperiment(null);
      setSelectedDetail(null);
      return;
    }

    setSelectedExperiment((current) => {
      if (current && timeline.some((item) => item.id === current.experiment_id)) {
        return current;
      }
      const next = experiments.find((item) => item.experiment_id === timeline[0]?.id);
      return next ?? null;
    });
  }, [experiments, timeline]);

  useEffect(() => {
    if (!selectedExperiment) {
      setSelectedDetail(null);
      return;
    }

    let isCancelled = false;
    setDetailLoading(true);
    apiClient
      .getExperiment(selectedExperiment.experiment_type, selectedExperiment.experiment_id)
      .then((payload) => {
        if (!isCancelled) {
          setSelectedDetail(payload);
        }
      })
      .catch((error: any) => {
        if (!isCancelled) {
          onError(error.response?.data?.detail || 'Failed to load experiment detail');
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setDetailLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [onError, selectedExperiment]);

  useEffect(() => {
    if (pendingWorkspaceSelection) {
      setContextOverrides(pendingWorkspaceSelection);
      setPendingWorkspaceSelection(null);
      return;
    }

    setContextOverrides({
      optimizationId: 'auto',
      walkforwardId: 'auto',
      montecarloId: 'auto',
    });
  }, [
    pendingWorkspaceSelection,
    selectedDetail?.record.experiment_id,
    selectedDetail?.record.experiment_type,
  ]);

  const openExperiment = useCallback(
    (record: ExperimentRegistryRecord) => {
      const knownRecord = experiments.find(
        (item) =>
          item.experiment_id === record.experiment_id &&
          item.experiment_type === record.experiment_type
      );
      setSelectedExperiment(knownRecord ?? record);
    },
    [experiments]
  );

  const loadWorkspace = useCallback(
    (workspace: ResearchWorkspacePayload) => {
      const selectedRecord =
        experiments.find(
          (item) =>
            item.experiment_type === workspace.selected_experiment.experiment_type &&
            item.experiment_id === workspace.selected_experiment.experiment_id
        ) ??
        workspace.records.selected;

      setPendingWorkspaceSelection({
        optimizationId: workspace.selection.optimization_id ?? 'auto',
        walkforwardId: workspace.selection.walkforward_id ?? 'auto',
        montecarloId: workspace.selection.montecarlo_id ?? 'auto',
      });
      openExperiment(selectedRecord);
    },
    [experiments, openExperiment]
  );

  useEffect(() => {
    if (!workspaceToOpen) {
      return;
    }

    loadWorkspace(workspaceToOpen);
    onWorkspaceOpened?.();
  }, [loadWorkspace, onWorkspaceOpened, workspaceToOpen]);

  function relationshipLabel(relationship: string): string {
    switch (relationship) {
      case 'best_run':
        return 'Best run';
      case 'source_run':
        return 'Source run';
      case 'parent_optimization':
        return 'Parent optimization';
      case 'best_run_for_optimization':
        return 'Best run for optimization';
      case 'source_run_for_montecarlo':
        return 'Source run for Monte Carlo';
      case 'child_of_optimization':
        return 'Child of optimization';
      default:
        return relationship;
    }
  }

  async function openAnchorRun() {
    if (!contextTargets.anchorRunId) {
      return;
    }

    setIsOpeningRun(true);
    try {
      await onLoadRun(contextTargets.anchorRunId);
    } catch (error: any) {
      onError(error?.message || 'Failed to load anchor run');
    } finally {
      setIsOpeningRun(false);
    }
  }

  async function saveWorkspace() {
    if (!selectedExperiment) {
      return;
    }

    setIsSavingWorkspace(true);
    try {
      await apiClient.saveResearchWorkspace({
        name: `${selectedExperiment.experiment_type} · ${selectedExperiment.experiment_id}`,
        selected_experiment_type: selectedExperiment.experiment_type,
        selected_experiment_id: selectedExperiment.experiment_id,
        optimization_id: contextTargets.optimization?.experiment_id ?? null,
        walkforward_id: contextTargets.walkforward?.experiment_id ?? null,
        montecarlo_id: contextTargets.montecarlo?.experiment_id ?? null,
        anchor_run_id: contextTargets.anchorRunId ?? null,
      });
      await refresh();
      onWorkspaceSaved?.();
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to save research workspace');
    } finally {
      setIsSavingWorkspace(false);
    }
  }

  return (
    <div className="card bg-gradient-to-br from-amber-50 via-white to-rose-50 dark:from-amber-950/20 dark:via-gray-800 dark:to-rose-950/20">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center mb-2">
            <Sparkles className="h-4 w-4 mr-2 text-amber-600 dark:text-amber-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Research Overview
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Unified view of persisted optimization, walk-forward, and Monte Carlo work.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={isLoading}
          className="text-xs px-2 py-1 rounded bg-white/80 dark:bg-gray-700 hover:bg-white dark:hover:bg-gray-600 transition-colors"
        >
          {isLoading ? (
            <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3 inline mr-1" />
          )}
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
        <div className="rounded-lg border border-indigo-200 dark:border-indigo-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400 mb-2">
            <BrainCircuit className="h-3 w-3 mr-1" />
            Optimizations
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {optimizationCount}
          </div>
          {latestOptimization && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Latest best: {latestOptimization.best_objective_value?.toFixed(3) ?? 'n/a'}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-sky-200 dark:border-sky-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-400 mb-2">
            <CalendarRange className="h-3 w-3 mr-1" />
            Walk-Forward
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {walkForwardCount}
          </div>
          {latestWalkForward && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Latest windows: {latestWalkForward.window_count}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-rose-200 dark:border-rose-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-rose-600 dark:text-rose-400 mb-2">
            <Dices className="h-3 w-3 mr-1" />
            Monte Carlo
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {monteCarloCount}
          </div>
          {latestMonteCarlo && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Latest sims: {latestMonteCarlo.simulation_count}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-amber-200 dark:border-amber-900 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-400 mb-2">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Warnings
          </div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {warningCount}
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Persisted research warnings across latest jobs
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Latest Signals
          </h4>
          <div className="space-y-3 text-sm">
            <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="text-xs uppercase tracking-wide text-indigo-500 mb-1">
                Optimization
              </div>
              {latestOptimization ? (
                <div className="text-gray-700 dark:text-gray-200">
                  Best objective for <span className="font-medium">{latestOptimization.objective}</span>:{' '}
                  <span className="font-semibold">
                    {latestOptimization.best_objective_value?.toFixed(3) ?? 'n/a'}
                  </span>
                </div>
              ) : (
                <div className="text-gray-500 dark:text-gray-400">No persisted optimization yet.</div>
              )}
            </div>

            <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="text-xs uppercase tracking-wide text-sky-500 mb-1">
                Walk-Forward
              </div>
              {latestWalkForward?.strategy_summaries[0] ? (
                <div className="text-gray-700 dark:text-gray-200">
                  Avg test return for{' '}
                  <span className="font-medium">
                    {latestWalkForward.strategy_summaries[0].strategy_name}
                  </span>
                  :{' '}
                  <span className="font-semibold">
                    {formatPercent(
                      latestWalkForward.strategy_summaries[0].avg_test_total_return
                    )}
                  </span>
                </div>
              ) : (
                <div className="text-gray-500 dark:text-gray-400">No persisted walk-forward yet.</div>
              )}
            </div>

            <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
              <div className="text-xs uppercase tracking-wide text-rose-500 mb-1">
                Monte Carlo
              </div>
              {latestMonteCarlo?.strategy_summaries[0] ? (
                <div className="text-gray-700 dark:text-gray-200">
                  Loss probability for{' '}
                  <span className="font-medium">
                    {latestMonteCarlo.strategy_summaries[0].strategy_name}
                  </span>
                  :{' '}
                  <span className="font-semibold">
                    {formatPercent(
                      latestMonteCarlo.strategy_summaries[0].loss_probability
                    )}
                  </span>
                </div>
              ) : (
                <div className="text-gray-500 dark:text-gray-400">No persisted Monte Carlo yet.</div>
              )}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Recent Research Timeline
            </h4>
            <select
              value={timelineFilter}
              onChange={(event) =>
                setTimelineFilter(
                  event.target.value as
                    | 'all'
                    | 'run'
                    | 'optimization'
                    | 'walkforward'
                    | 'montecarlo'
                    | 'pairs_backtest'
                )
              }
              className="rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1 text-xs"
            >
              <option value="all">All</option>
              <option value="run">Runs</option>
              <option value="optimization">Optimizations</option>
              <option value="walkforward">Walk-Forward</option>
              <option value="montecarlo">Monte Carlo</option>
              <option value="pairs_backtest">Pairs</option>
            </select>
          </div>
          <div className="space-y-3">
            {timeline.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Run research jobs to build a persisted timeline here.
              </p>
            )}
            {timeline.map((entry) => (
              <button
                key={`${entry.type}-${entry.id}`}
                type="button"
                onClick={() => {
                  const next = experiments.find((item) => item.experiment_id === entry.id);
                  if (next) {
                    openExperiment(next);
                  }
                }}
                className={`w-full text-left rounded-md border px-3 py-3 transition-colors ${
                  selectedExperiment?.experiment_id === entry.id
                    ? 'border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/20'
                    : 'border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {entry.title}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>{new Date(entry.createdAt).toLocaleString('pt-BR')}</span>
                    <ChevronRight className="h-3 w-3" />
                  </div>
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 font-mono">
                  {entry.id}
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  {entry.subtitle}
                </div>
                {entry.warnings.length > 0 && (
                  <div className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                    {entry.warnings.join(' | ')}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/40">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Experiment Detail
          </h4>
          {!selectedExperiment && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Select a timeline item to inspect its persisted manifest.
            </p>
          )}
          {detailLoading && (
            <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Loading detail...
            </div>
          )}
          {selectedDetail && !detailLoading && (
            <div className="space-y-3 text-sm">
              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">
                  Record
                </div>
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  {selectedDetail.record.experiment_type} · {selectedDetail.record.experiment_id}
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {selectedDetail.record.strategy_names.join(', ') || 'No strategies'}
                </div>
              </div>
              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="flex items-center text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                  <GitBranch className="h-3 w-3 mr-1" />
                  Related Experiments
                </div>
                {selectedDetail.related_experiments.length === 0 ? (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    No linked experiments yet.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedDetail.related_experiments.map((relation) => (
                      <button
                        key={`${relation.relationship}-${relation.record.experiment_type}-${relation.record.experiment_id}`}
                        type="button"
                        onClick={() => openExperiment(relation.record)}
                        className="w-full rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2 text-left hover:border-amber-300 dark:hover:border-amber-700 transition-colors"
                      >
                        <div className="text-xs uppercase tracking-wide text-amber-600 dark:text-amber-400">
                          {relationshipLabel(relation.relationship)}
                        </div>
                        <div className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">
                          {relation.record.experiment_type} · {relation.record.experiment_id}
                        </div>
                        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          {relation.record.strategy_names.join(', ') || 'No strategies'}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="flex items-center text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                  <Link2 className="h-3 w-3 mr-1" />
                  Context Comparison
                </div>
                {isLoadingContext ? (
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                    <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                    Loading linked artifacts...
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <label className="space-y-1">
                        <span className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Optimization Source
                        </span>
                        <select
                          value={contextOverrides.optimizationId}
                          onChange={(event) =>
                            setContextOverrides((current) => ({
                              ...current,
                              optimizationId: event.target.value,
                            }))
                          }
                          className="w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-2"
                        >
                          <option value="auto">Auto</option>
                          {contextCandidates.optimization.map((candidate) => (
                            <option key={candidate.experiment_id} value={candidate.experiment_id}>
                              {candidate.experiment_id}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="space-y-1">
                        <span className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Walk-Forward Source
                        </span>
                        <select
                          value={contextOverrides.walkforwardId}
                          onChange={(event) =>
                            setContextOverrides((current) => ({
                              ...current,
                              walkforwardId: event.target.value,
                            }))
                          }
                          className="w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-2"
                        >
                          <option value="auto">Auto</option>
                          {contextCandidates.walkforward.map((candidate) => (
                            <option key={candidate.experiment_id} value={candidate.experiment_id}>
                              {candidate.experiment_id}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="space-y-1">
                        <span className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Monte Carlo Source
                        </span>
                        <select
                          value={contextOverrides.montecarloId}
                          onChange={(event) =>
                            setContextOverrides((current) => ({
                              ...current,
                              montecarloId: event.target.value,
                            }))
                          }
                          className="w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-2"
                        >
                          <option value="auto">Auto</option>
                          {contextCandidates.montecarlo.map((candidate) => (
                            <option key={candidate.experiment_id} value={candidate.experiment_id}>
                              {candidate.experiment_id}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div className="rounded-md border border-dashed border-gray-200 dark:border-gray-700 px-2 py-2">
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Mode
                        </div>
                        <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                          Explicit compare
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Save this curated comparison as a reusable research workspace.
                      </div>
                      <button
                        type="button"
                        onClick={saveWorkspace}
                        disabled={isSavingWorkspace || !selectedExperiment}
                        className="rounded bg-indigo-100 px-3 py-2 text-xs font-medium text-indigo-800 transition-colors hover:bg-indigo-200 disabled:opacity-50 dark:bg-indigo-900/40 dark:text-indigo-200 dark:hover:bg-indigo-900/60"
                      >
                        <Save className="mr-1 inline h-3 w-3" />
                        {isSavingWorkspace ? 'Saving...' : 'Save Workspace'}
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <button
                        type="button"
                        disabled={!contextTargets.optimization}
                        onClick={() => contextTargets.optimization && openExperiment(contextTargets.optimization)}
                        className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2 text-left disabled:opacity-50"
                      >
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Optimization
                        </div>
                        <div className="mt-1 font-mono text-gray-700 dark:text-gray-200">
                          {contextTargets.optimization?.experiment_id ?? 'n/a'}
                        </div>
                      </button>
                      <button
                        type="button"
                        disabled={!contextTargets.walkforward}
                        onClick={() => contextTargets.walkforward && openExperiment(contextTargets.walkforward)}
                        className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2 text-left disabled:opacity-50"
                      >
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Walk-Forward
                        </div>
                        <div className="mt-1 font-mono text-gray-700 dark:text-gray-200">
                          {contextTargets.walkforward?.experiment_id ?? 'n/a'}
                        </div>
                      </button>
                      <button
                        type="button"
                        disabled={!contextTargets.montecarlo}
                        onClick={() => contextTargets.montecarlo && openExperiment(contextTargets.montecarlo)}
                        className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2 text-left disabled:opacity-50"
                      >
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Monte Carlo
                        </div>
                        <div className="mt-1 font-mono text-gray-700 dark:text-gray-200">
                          {contextTargets.montecarlo?.experiment_id ?? 'n/a'}
                        </div>
                      </button>
                      <div className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2">
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Anchor Run
                        </div>
                        <div className="mt-1 font-mono text-gray-700 dark:text-gray-200">
                          {contextTargets.anchorRunId ?? 'n/a'}
                        </div>
                        {contextTargets.anchorRunId && (
                          <button
                            type="button"
                            onClick={openAnchorRun}
                            disabled={isOpeningRun}
                            className="mt-2 rounded bg-amber-100 px-2 py-1 text-[11px] font-medium text-amber-800 transition-colors hover:bg-amber-200 disabled:opacity-50 dark:bg-amber-900/40 dark:text-amber-200 dark:hover:bg-amber-900/60"
                          >
                            {isOpeningRun ? 'Opening...' : 'Open Run'}
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2">
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Objective
                        </div>
                        <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                          {alignment.optimizationObjectiveValue !== null
                            ? alignment.optimizationObjectiveValue.toFixed(3)
                            : 'n/a'}
                        </div>
                      </div>
                      <div className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2">
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          OOS Avg Return
                        </div>
                        <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                          {alignment.walkForwardAvgTestReturn !== null
                            ? formatPercent(alignment.walkForwardAvgTestReturn)
                            : 'n/a'}
                        </div>
                      </div>
                      <div className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2">
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Loss Prob
                        </div>
                        <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                          {alignment.monteCarloLossProbability !== null
                            ? formatPercent(alignment.monteCarloLossProbability)
                            : 'n/a'}
                        </div>
                      </div>
                      <div className="rounded-md border border-gray-200 dark:border-gray-700 px-2 py-2">
                        <div className="uppercase tracking-wide text-gray-500 dark:text-gray-400">
                          Run Link
                        </div>
                        <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                          {alignment.runLinkAligned ? 'Aligned' : 'Unaligned'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">
                  Manifest Preview
                </div>
                <pre className="max-h-80 overflow-auto text-xs text-gray-700 dark:text-gray-200 whitespace-pre-wrap break-all">
                  {JSON.stringify(selectedDetail.manifest, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
