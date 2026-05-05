import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import AppHeader from './components/app-shell/AppHeader';
import ErrorBanner from './components/app-shell/ErrorBanner';
import HomeSection from './components/app-shell/HomeSection';
import SectionTabs from './components/app-shell/SectionTabs';
import LoadingSpinner from './components/LoadingSpinner';
import { useAppShellState } from './hooks/useAppShellState';
import { useBacktestJobs } from './hooks/useBacktestJobs';
import { useBacktestWorkspace } from './hooks/useBacktestWorkspace';
import { useConfigs } from './hooks/useConfigs';
import { useResearchWorkspaces } from './hooks/useResearchWorkspaces';
import { useRunComparison } from './hooks/useRunComparison';
import { useRunHistory } from './hooks/useRunHistory';
import { useRunPermalink } from './hooks/useRunPermalink';

const AdvancedSection = lazy(() => import('./components/app-shell/AdvancedSection'));
const InvestmentsWorkspace = lazy(() => import('./components/InvestmentsWorkspace'));
const OperateSection = lazy(() => import('./components/app-shell/OperateSection'));
const ResultsSection = lazy(() => import('./components/app-shell/ResultsSection'));

type NavigateAdvancedToolEvent = CustomEvent<{ tool: string }>;

function sectionFallback(message: string) {
  return (
    <div className="card">
      <LoadingSpinner message={message} />
    </div>
  );
}

function App() {
  const [error, setError] = useState<string | null>(null);
  const [researchWorkspaceRefreshToken, setResearchWorkspaceRefreshToken] = useState(0);
  const {
    configs,
    selectedConfig,
    backtestRequest,
    handleConfigChange,
    handleRequestChange,
  } = useConfigs(setError);
  const { runs, isLoadingRuns, refreshRuns, loadRunResponse, loadRunArtifacts } =
    useRunHistory(setError);
  const {
    selectedRunIds,
    comparisonRuns,
    isLoadingComparison,
    toggleRunSelection,
    clearComparison,
  } = useRunComparison(runs, setError);
  const {
    workspaces: savedResearchWorkspaces,
    isLoading: isLoadingResearchWorkspaces,
    refresh: refreshResearchWorkspaces,
  } = useResearchWorkspaces(setError, researchWorkspaceRefreshToken);
  const appShell = useAppShellState({
    runsCount: runs.length,
    selectedRunCount: selectedRunIds.length,
    workspaceCount: savedResearchWorkspaces.length,
  });

  const loadRunFromPermalinkRef = useRef<(runId: string) => Promise<void>>(async () => undefined);

  const { updatePermalink, copyRunUrl, shareRunUrl } = useRunPermalink({
    isReady: !isLoadingRuns,
    onLoadRun: async (runId) => {
      await loadRunFromPermalinkRef.current(runId);
    },
    onError: setError,
  });
  const workspace = useBacktestWorkspace({
    backtestRequest,
    selectedConfig,
    refreshRuns,
    loadRunResponse,
    loadRunArtifacts,
    updatePermalink,
    copyRunUrl,
    shareRunUrl,
    onError: setError,
  });
  const backtestJobs = useBacktestJobs({
    backtestRequest,
    selectedConfig,
    onLoadCompletedRun: workspace.handleLoadRun,
    refreshRuns,
    onError: setError,
  });

  useEffect(() => {
    loadRunFromPermalinkRef.current = workspace.handleLoadRun;
  }, [workspace.handleLoadRun]);

  useEffect(() => {
    function handleNavigateAdvancedTool(event: Event) {
      const detail = (event as NavigateAdvancedToolEvent).detail;
      if (detail?.tool === 'pairs') {
        appShell.setPrimarySection('advanced');
        appShell.setAdvancedTool('pairs');
      }
    }
    window.addEventListener(
      'investing-workbench:navigate-advanced-tool',
      handleNavigateAdvancedTool
    );
    return () => {
      window.removeEventListener(
        'investing-workbench:navigate-advanced-tool',
        handleNavigateAdvancedTool
      );
    };
  }, [appShell]);
  const defaultStrategies = backtestRequest.strategies ?? selectedConfig?.strategies ?? [];
  const latestValidRunId =
    runs.find((run) => run.run_quality?.status !== 'legacy_invalid')?.run_id ?? null;
  const isBacktestBusy =
    workspace.appState === 'loading' ||
    backtestJobs.isSubmittingJob ||
    backtestJobs.isActiveJobRunning;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <AppHeader />

        <div className="card mb-6">
          <SectionTabs
            tabs={appShell.primaryTabs}
            activeTab={appShell.primarySection}
            onChange={appShell.setPrimarySection}
          />
        </div>

        {appShell.primarySection !== 'simulate' && error ? (
          <ErrorBanner error={error} dimmed />
        ) : null}

        {appShell.primarySection === 'home' && (
          <HomeSection
            runsCount={runs.length}
            workspaceCount={savedResearchWorkspaces.length}
            comparisonCount={selectedRunIds.length}
            onOpenInvestments={() => appShell.setPrimarySection('investments')}
            onStartSimulation={() => appShell.setPrimarySection('simulate')}
            onOpenResults={() => appShell.setPrimarySection('results')}
            onOpenPlanner={() => {
              appShell.setPrimarySection('advanced');
              appShell.setAdvancedTool('allocation');
            }}
            onOpenAdvanced={() => appShell.setPrimarySection('advanced')}
          />
        )}

        {appShell.primarySection === 'investments' && (
          <Suspense fallback={sectionFallback('Carregando area de investimentos...')}>
            <InvestmentsWorkspace onError={setError} />
          </Suspense>
        )}

        {appShell.primarySection === 'simulate' && (
          <Suspense fallback={sectionFallback('Carregando simulador...')}>
            <OperateSection
              simulateTabs={appShell.simulateTabs}
              simulateTab={appShell.simulateTab}
              onSimulateTabChange={(tab) =>
                appShell.setSimulateTab(tab as typeof appShell.simulateTab)
              }
              backtestFormProps={{
                configs,
                selectedConfig,
                backtestRequest,
                onConfigChange: handleConfigChange,
                onRequestChange: handleRequestChange,
                onRunBacktest: backtestJobs.startJob,
                isLoading: isBacktestBusy,
              }}
              datasetManagerProps={{
                currentCachePath: backtestRequest.cache_path,
                onApplyDataset: (dataset) => {
                  handleRequestChange({
                    cache_path: dataset.path,
                    data_source: dataset.name,
                  });
                  setError(null);
                },
                onError: setError,
              }}
              jobsPanelProps={{
                jobs: backtestJobs.jobs,
                activeJob: backtestJobs.activeJob,
                isLoadingJobs: backtestJobs.isLoadingJobs,
                isCancellingJob: backtestJobs.isCancellingJob,
                onOpenJob: backtestJobs.openJob,
                onResumeJob: backtestJobs.resumeJob,
                onCancelActiveJob: backtestJobs.cancelActiveJob,
                onRefreshJobs: backtestJobs.refreshJobs,
              }}
              resultsWorkspaceProps={
                workspace.backtestResponse
                  ? {
                      activeTab: workspace.activeTab,
                      backtestRequest,
                      backtestResponse: workspace.backtestResponse,
                      exportContainerRef: workspace.exportContainerRef,
                      isLoadingArtifacts: workspace.isLoadingArtifacts,
                      latestValidRunId,
                      onCopyLink: workspace.actions.copyRunLink,
                      onCopySummary: workspace.actions.copySummary,
                      onDownloadCSV: workspace.actions.downloadCSV,
                      onDownloadHTML: workspace.actions.downloadHTML,
                      onDownloadPNG: workspace.actions.downloadPNG,
                      onOpenLatestValidRun: latestValidRunId
                        ? () => workspace.handleLoadRun(latestValidRunId)
                        : undefined,
                      onSaveProject: workspace.actions.saveProjectBundle,
                      onSetActiveTab: workspace.setActiveTab,
                      onShareResults: workspace.actions.shareResults,
                      onToggleAllBenchmarks: workspace.visibility.toggleAllBenchmarks,
                      onToggleAllStrategies: workspace.visibility.toggleAllStrategies,
                      onToggleBenchmarkVisibility: workspace.visibility.toggleBenchmarkVisibility,
                      onToggleStrategyVisibility: workspace.visibility.toggleStrategyVisibility,
                      runConfigSnapshot: workspace.runConfigSnapshot,
                      runDataProfile: workspace.runDataProfile,
                      strategyNames: workspace.strategyNames,
                      totalTradesCount: workspace.totalTradesCount,
                      visibleBenchmarks: workspace.visibleBenchmarks,
                      visibleStrategies: workspace.visibleStrategies,
                      warnings: workspace.warnings,
                    }
                  : null
              }
              isBacktestBusy={isBacktestBusy}
              loadingMessage={
                backtestJobs.activeJob?.progress.message || 'Running backtest analysis...'
              }
              workspaceState={workspace.appState}
              error={error}
            />
          </Suspense>
        )}

        {appShell.primarySection === 'results' && (
          <Suspense fallback={sectionFallback('Carregando resultados...')}>
            <ResultsSection
              resultsTab={appShell.resultsTab}
              resultsTabs={appShell.resultsTabs}
              onResultsTabChange={appShell.setResultsTab}
              runs={runs}
              isLoadingRuns={isLoadingRuns}
              onRefreshRuns={refreshRuns}
              onLoadRun={workspace.handleLoadRun}
              selectedRunIds={selectedRunIds}
              onToggleCompare={toggleRunSelection}
              comparisonRuns={comparisonRuns}
              isLoadingComparison={isLoadingComparison}
              onClearComparison={clearComparison}
              savedResearchWorkspaces={savedResearchWorkspaces}
              isLoadingResearchWorkspaces={isLoadingResearchWorkspaces}
              onRefreshResearchWorkspaces={refreshResearchWorkspaces}
              onOpenWorkspace={appShell.openWorkspaceInResearch}
              onError={setError}
            />
          </Suspense>
        )}

        {appShell.primarySection === 'advanced' && (
          <Suspense fallback={sectionFallback('Carregando area avancada...')}>
            <AdvancedSection
              advancedTool={appShell.advancedTool}
              advancedTools={appShell.advancedTools}
              onAdvancedToolChange={appShell.setAdvancedTool}
              selectedConfigPath={selectedConfig?.path}
              defaultStrategies={defaultStrategies}
              currentRunId={workspace.backtestResponse?.run_info?.run_id}
              onError={setError}
              onLoadRun={workspace.handleLoadRun}
              workspaceToOpen={appShell.workspaceToOpen}
              onWorkspaceOpened={appShell.clearWorkspaceToOpen}
              onWorkspaceSaved={() =>
                setResearchWorkspaceRefreshToken((current) => current + 1)
              }
            />
          </Suspense>
        )}
      </div>
    </div>
  );
}

export default App;
