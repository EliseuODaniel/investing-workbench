import type { ComponentProps } from 'react';
import BacktestForm from '../BacktestForm';
import BacktestJobsPanel from '../BacktestJobsPanel';
import BacktestResultsWorkspace from '../BacktestResultsWorkspace';
import DatasetManagerPanel from '../DatasetManagerPanel';
import InitialWorkspaceState from '../InitialWorkspaceState';
import LoadingSpinner from '../LoadingSpinner';
import SectionTabs from './SectionTabs';
import ErrorBanner from './ErrorBanner';

interface OperateSectionProps {
  simulateTabs: ComponentProps<typeof SectionTabs>['tabs'];
  simulateTab: string;
  onSimulateTabChange: (tab: string) => void;
  backtestFormProps: ComponentProps<typeof BacktestForm>;
  datasetManagerProps: ComponentProps<typeof DatasetManagerPanel>;
  jobsPanelProps: ComponentProps<typeof BacktestJobsPanel>;
  resultsWorkspaceProps: ComponentProps<typeof BacktestResultsWorkspace> | null;
  isBacktestBusy: boolean;
  loadingMessage: string;
  workspaceState: 'idle' | 'loading' | 'success' | 'error';
  error: string | null;
}

export default function OperateSection({
  simulateTabs,
  simulateTab,
  onSimulateTabChange,
  backtestFormProps,
  datasetManagerProps,
  jobsPanelProps,
  resultsWorkspaceProps,
  isBacktestBusy,
  loadingMessage,
  workspaceState,
  error,
}: OperateSectionProps) {
  const showJobsPanel =
    jobsPanelProps.jobs.some((job) => job.status !== 'completed') ||
    (jobsPanelProps.activeJob !== null && jobsPanelProps.activeJob.status !== 'completed');

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-1">
        <div className="card">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Simular</h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Primeiro escolha a configuracao do estudo. Se precisar, troque a base de
              dados sem sair do fluxo principal.
            </p>
          </div>
          <SectionTabs
            tabs={simulateTabs}
            activeTab={simulateTab}
            onChange={onSimulateTabChange}
          />
        </div>

        {simulateTab === 'configure' ? (
          <BacktestForm {...backtestFormProps} />
        ) : (
          <DatasetManagerPanel {...datasetManagerProps} />
        )}
      </div>

      <div className="lg:col-span-2">
        {showJobsPanel ? <BacktestJobsPanel {...jobsPanelProps} /> : null}

        {workspaceState === 'error' && error ? <ErrorBanner error={error} /> : null}

        {isBacktestBusy ? <LoadingSpinner message={loadingMessage} /> : null}

        {!isBacktestBusy && workspaceState === 'success' && resultsWorkspaceProps ? (
          <BacktestResultsWorkspace {...resultsWorkspaceProps} />
        ) : null}

        {!isBacktestBusy && workspaceState === 'idle' ? <InitialWorkspaceState /> : null}
      </div>
    </div>
  );
}
