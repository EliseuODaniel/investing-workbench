import { lazy, Suspense } from 'react';
import LoadingSpinner from '../LoadingSpinner';
import RunHistoryPanel from '../RunHistoryPanel';
import SavedResearchWorkspacesPanel from '../SavedResearchWorkspacesPanel';
import SectionTabs from './SectionTabs';
import { ComparisonRun, ResearchWorkspacePayload, RunSummary } from '../../types/api';
import { ResultsTab } from '../../hooks/useAppShellState';

const RunComparisonPanel = lazy(() => import('../RunComparisonPanel'));

interface ResultsSectionProps {
  resultsTab: ResultsTab;
  resultsTabs: Array<{ id: ResultsTab; label: string; badge?: string | number }>;
  onResultsTabChange: (tab: ResultsTab) => void;
  runs: RunSummary[];
  isLoadingRuns: boolean;
  onRefreshRuns: () => void;
  onLoadRun: (runId: string) => Promise<void> | void;
  selectedRunIds: string[];
  onToggleCompare: (runId: string) => void;
  comparisonRuns: ComparisonRun[];
  isLoadingComparison: boolean;
  onClearComparison: () => void;
  savedResearchWorkspaces: ResearchWorkspacePayload[];
  isLoadingResearchWorkspaces: boolean;
  onRefreshResearchWorkspaces: () => void;
  onOpenWorkspace: (workspace: ResearchWorkspacePayload) => void;
  onError: (message: string | null) => void;
}

export default function ResultsSection({
  resultsTab,
  resultsTabs,
  onResultsTabChange,
  runs,
  isLoadingRuns,
  onRefreshRuns,
  onLoadRun,
  selectedRunIds,
  onToggleCompare,
  comparisonRuns,
  isLoadingComparison,
  onClearComparison,
  savedResearchWorkspaces,
  isLoadingResearchWorkspaces,
  onRefreshResearchWorkspaces,
  onOpenWorkspace,
  onError,
}: ResultsSectionProps) {
  return (
    <div className="space-y-6">
      <div className="card">
        <div className="max-w-3xl">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Resultados e historico
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Tudo que ja foi executado fica aqui. Primeiro leia o que aconteceu, depois
            compare runs ou reabra estudos salvos quando precisar.
          </p>
        </div>
        <div className="mt-4">
          <SectionTabs
            tabs={resultsTabs}
            activeTab={resultsTab}
            onChange={onResultsTabChange}
          />
        </div>
      </div>

      {resultsTab === 'history' && (
        <RunHistoryPanel
          runs={runs}
          isLoading={isLoadingRuns}
          onRefresh={onRefreshRuns}
          onLoadRun={onLoadRun}
          selectedRunIds={selectedRunIds}
          onToggleCompare={onToggleCompare}
        />
      )}

      {resultsTab === 'compare' && (
        <Suspense
          fallback={
            <div className="card">
              <LoadingSpinner message="Carregando comparacao..." />
            </div>
          }
        >
          <RunComparisonPanel
            comparisonRuns={comparisonRuns}
            isLoading={isLoadingComparison}
            onClear={onClearComparison}
          />
        </Suspense>
      )}

      {resultsTab === 'workspaces' && (
        <SavedResearchWorkspacesPanel
          workspaces={savedResearchWorkspaces}
          isLoading={isLoadingResearchWorkspaces}
          onRefresh={onRefreshResearchWorkspaces}
          onOpenWorkspace={onOpenWorkspace}
          onLoadRun={onLoadRun}
          onError={onError}
        />
      )}
    </div>
  );
}
