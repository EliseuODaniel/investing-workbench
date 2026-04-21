import MonteCarloFormPanel from './montecarlo-workspace/MonteCarloFormPanel';
import MonteCarloJobsPanel from './montecarlo-workspace/MonteCarloJobsPanel';
import MonteCarloSummaryPanel from './montecarlo-workspace/MonteCarloSummaryPanel';
import MonteCarloWorkspaceHeader from './montecarlo-workspace/MonteCarloWorkspaceHeader';
import { MonteCarloWorkspaceProps } from './montecarlo-workspace/types';
import { useMonteCarlo } from '../hooks/useMonteCarlo';

export default function MonteCarloWorkspace({
  selectedConfigPath,
  currentRunId,
  defaultStrategies,
  onError,
}: MonteCarloWorkspaceProps) {
  const {
    draft,
    latestExecution,
    executions,
    selectedExecutionId,
    selectedManifest,
    selectedResults,
    isExecuting,
    isLoadingExecutions,
    isLoadingSelected,
    canSubmit,
    updateDraft,
    refreshExecutions,
    runMonteCarlo,
    loadMonteCarloResults,
  } = useMonteCarlo(selectedConfigPath, currentRunId, defaultStrategies, onError);

  const activeResults = selectedResults ?? latestExecution;

  return (
    <div className="card">
      <MonteCarloWorkspaceHeader
        isLoadingExecutions={isLoadingExecutions}
        onRefresh={refreshExecutions}
      />

      {!canSubmit && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          Load a persisted run or select a config before running Monte Carlo analysis.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="space-y-4">
          <MonteCarloFormPanel
            draft={draft}
            currentRunId={currentRunId}
            selectedConfigPath={selectedConfigPath}
            canSubmit={canSubmit}
            isExecuting={isExecuting}
            onUpdateDraft={updateDraft}
            onRun={runMonteCarlo}
          />
          <MonteCarloJobsPanel
            executions={executions}
            selectedExecutionId={selectedExecutionId}
            onLoadExecution={(executionId) => {
              void loadMonteCarloResults(executionId);
            }}
          />
        </div>

        <div className="space-y-4">
          <MonteCarloSummaryPanel
            activeResults={activeResults}
            selectedManifest={selectedManifest}
            isLoadingSelected={isLoadingSelected}
          />
        </div>
      </div>
    </div>
  );
}
