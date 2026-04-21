import ResultsTabsPanel from './backtest-results/ResultsTabsPanel';
import { BacktestResultsWorkspaceProps } from './backtest-results/types';

export default function BacktestResultsWorkspace({
  activeTab,
  backtestRequest,
  backtestResponse,
  exportContainerRef,
  isLoadingArtifacts,
  latestValidRunId,
  onCopyLink,
  onCopySummary,
  onDownloadCSV,
  onDownloadHTML,
  onDownloadPNG,
  onOpenLatestValidRun,
  onSaveProject,
  onSetActiveTab,
  onShareResults,
  onToggleAllBenchmarks,
  onToggleAllStrategies,
  onToggleBenchmarkVisibility,
  onToggleStrategyVisibility,
  runConfigSnapshot,
  runDataProfile,
  strategyNames,
  totalTradesCount,
  visibleBenchmarks,
  visibleStrategies,
  warnings,
}: BacktestResultsWorkspaceProps) {
  return (
    <div ref={exportContainerRef} className="space-y-6">
      <ResultsTabsPanel
        activeTab={activeTab}
        backtestRequest={backtestRequest}
        backtestResponse={backtestResponse}
        isLoadingArtifacts={isLoadingArtifacts}
        latestValidRunId={latestValidRunId}
        onCopyLink={onCopyLink}
        onCopySummary={onCopySummary}
        onDownloadCSV={onDownloadCSV}
        onDownloadHTML={onDownloadHTML}
        onDownloadPNG={onDownloadPNG}
        onOpenLatestValidRun={onOpenLatestValidRun}
        onSaveProject={onSaveProject}
        onShareResults={onShareResults}
        onToggleAllBenchmarks={onToggleAllBenchmarks}
        onToggleAllStrategies={onToggleAllStrategies}
        onToggleBenchmarkVisibility={onToggleBenchmarkVisibility}
        onToggleStrategyVisibility={onToggleStrategyVisibility}
        runConfigSnapshot={runConfigSnapshot}
        runDataProfile={runDataProfile}
        strategyNames={strategyNames}
        totalTradesCount={totalTradesCount}
        visibleStrategies={visibleStrategies}
        visibleBenchmarks={visibleBenchmarks}
        warnings={warnings}
        onSetActiveTab={onSetActiveTab}
      />
    </div>
  );
}
