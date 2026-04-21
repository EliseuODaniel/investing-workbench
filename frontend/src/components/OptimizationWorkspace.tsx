import OptimizationFormPanel from './optimization-workspace/OptimizationFormPanel';
import OptimizationJobsPanel from './optimization-workspace/OptimizationJobsPanel';
import OptimizationPlanPreview from './optimization-workspace/OptimizationPlanPreview';
import OptimizationResultsPanel from './optimization-workspace/OptimizationResultsPanel';
import OptimizationWorkspaceHeader from './optimization-workspace/OptimizationWorkspaceHeader';
import { OptimizationWorkspaceProps } from './optimization-workspace/types';
import { useOptimizations } from '../hooks/useOptimizations';

export default function OptimizationWorkspace({
  selectedConfigPath,
  defaultStrategies,
  onError,
}: OptimizationWorkspaceProps) {
  const {
    draft,
    plan,
    latestExecution,
    optimizations,
    selectedOptimizationId,
    selectedManifest,
    selectedResults,
    isPlanning,
    isExecuting,
    isLoadingOptimizations,
    isLoadingSelected,
    canSubmit,
    updateDraft,
    previewPlan,
    runOptimization,
    refreshOptimizations,
    loadOptimizationResults,
  } = useOptimizations(selectedConfigPath, defaultStrategies, onError);

  return (
    <div className="card">
      <OptimizationWorkspaceHeader
        isLoadingOptimizations={isLoadingOptimizations}
        onRefresh={refreshOptimizations}
      />

      {!canSubmit && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          Select a config in the sidebar before building an optimization plan.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <OptimizationFormPanel
          draft={draft}
          canSubmit={canSubmit}
          isPlanning={isPlanning}
          isExecuting={isExecuting}
          onUpdateDraft={updateDraft}
          onPreviewPlan={previewPlan}
          onRunOptimization={runOptimization}
        />

        <div className="space-y-4">
          <OptimizationPlanPreview plan={plan} />
          <OptimizationJobsPanel
            optimizations={optimizations}
            selectedOptimizationId={selectedOptimizationId}
            isLoadingOptimizations={isLoadingOptimizations}
            onLoadOptimization={(optimizationId) => {
              void loadOptimizationResults(optimizationId);
            }}
          />
          <OptimizationResultsPanel
            latestExecution={latestExecution}
            selectedResults={selectedResults}
            selectedManifest={selectedManifest}
            isLoadingSelected={isLoadingSelected}
          />
        </div>
      </div>
    </div>
  );
}
