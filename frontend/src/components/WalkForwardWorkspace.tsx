import WalkForwardFormPanel from './walkforward-workspace/WalkForwardFormPanel';
import WalkForwardJobsPanel from './walkforward-workspace/WalkForwardJobsPanel';
import WalkForwardSummaryPanel from './walkforward-workspace/WalkForwardSummaryPanel';
import WalkForwardWorkspaceHeader from './walkforward-workspace/WalkForwardWorkspaceHeader';
import { WalkForwardWorkspaceProps } from './walkforward-workspace/types';
import { useWalkForward } from '../hooks/useWalkForward';

export default function WalkForwardWorkspace({
  selectedConfigPath,
  defaultStrategies,
  onError,
}: WalkForwardWorkspaceProps) {
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
    runWalkForward,
    loadWalkForwardResults,
  } = useWalkForward(selectedConfigPath, defaultStrategies, onError);

  const activeResults = selectedResults ?? latestExecution;

  return (
    <div className="card">
      <WalkForwardWorkspaceHeader
        isLoadingExecutions={isLoadingExecutions}
        onRefresh={refreshExecutions}
      />

      {!canSubmit && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          Select a config in the sidebar before running walk-forward validation.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="space-y-4">
          <WalkForwardFormPanel
            draft={draft}
            canSubmit={canSubmit}
            isExecuting={isExecuting}
            onUpdateDraft={updateDraft}
            onRun={runWalkForward}
          />
          <WalkForwardJobsPanel
            executions={executions}
            selectedExecutionId={selectedExecutionId}
            onLoadExecution={(executionId) => {
              void loadWalkForwardResults(executionId);
            }}
          />
        </div>

        <div className="space-y-4">
          <WalkForwardSummaryPanel
            activeResults={activeResults}
            selectedManifest={selectedManifest}
            isLoadingSelected={isLoadingSelected}
          />
        </div>
      </div>
    </div>
  );
}
