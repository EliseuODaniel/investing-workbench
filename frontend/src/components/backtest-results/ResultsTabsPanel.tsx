import SectionTabs from '../app-shell/SectionTabs';
import ResultsDetailsTab from './ResultsDetailsTab';
import ResultsOverviewTab from './ResultsOverviewTab';
import ResultsSummaryHero from './ResultsSummaryHero';
import TradingHistoryTab from './TradingHistoryTab';
import { ResultsTabsPanelProps } from './types';

export default function ResultsTabsPanel({
  activeTab,
  backtestRequest,
  backtestResponse,
  isLoadingArtifacts,
  onCopyLink,
  onCopySummary,
  onDownloadCSV,
  onDownloadHTML,
  onDownloadPNG,
  onSaveProject,
  onShareResults,
  onToggleAllBenchmarks,
  onToggleAllStrategies,
  onToggleBenchmarkVisibility,
  onToggleStrategyVisibility,
  runConfigSnapshot,
  runDataProfile,
  strategyNames,
  totalTradesCount,
  visibleStrategies,
  visibleBenchmarks,
  warnings,
  onSetActiveTab,
}: ResultsTabsPanelProps) {
  const tabs = [
    { id: 'charts' as const, label: 'Graficos' },
    { id: 'summary' as const, label: 'Resumo' },
    {
      id: 'trades' as const,
      label: 'Trades',
      badge: totalTradesCount > 0 ? totalTradesCount : undefined,
    },
    {
      id: 'details' as const,
      label: 'Detalhes',
      badge: backtestResponse.run_info?.run_id ? 'Run' : undefined,
    },
  ];

  return (
    <div className="card">
      <div className="flex flex-col gap-3 border-b border-gray-200 pb-4 dark:border-gray-700">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Workspace do Resultado
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Comece pelos graficos. Resumo, trades e detalhes ficam um passo abaixo quando voce
            quiser aprofundar.
          </p>
        </div>
        <SectionTabs tabs={tabs} activeTab={activeTab} onChange={onSetActiveTab} />
      </div>

      <div className="mt-6">
        {activeTab === 'summary' && (
          <div className="space-y-6">
            <ResultsSummaryHero
              backtestRequest={backtestRequest}
              backtestResponse={backtestResponse}
              totalTradesCount={totalTradesCount}
            />
            <ResultsOverviewTab
              backtestResponse={backtestResponse}
              visibleStrategies={visibleStrategies}
              visibleBenchmarks={visibleBenchmarks}
              mode="summary"
            />
          </div>
        )}
        {activeTab === 'charts' && (
          <ResultsOverviewTab
            backtestResponse={backtestResponse}
            visibleStrategies={visibleStrategies}
            visibleBenchmarks={visibleBenchmarks}
            mode="charts"
          />
        )}
        {activeTab === 'trades' && (
          <TradingHistoryTab
            backtestResponse={backtestResponse}
            totalTradesCount={totalTradesCount}
          />
        )}
        {activeTab === 'details' && (
          <ResultsDetailsTab
            backtestRequest={backtestRequest}
            backtestResponse={backtestResponse}
            isLoadingArtifacts={isLoadingArtifacts}
            onCopyLink={onCopyLink}
            onCopySummary={onCopySummary}
            onDownloadCSV={onDownloadCSV}
            onDownloadHTML={onDownloadHTML}
            onDownloadPNG={onDownloadPNG}
            onSaveProject={onSaveProject}
            onShareResults={onShareResults}
            onToggleAllBenchmarks={onToggleAllBenchmarks}
            onToggleAllStrategies={onToggleAllStrategies}
            onToggleBenchmarkVisibility={onToggleBenchmarkVisibility}
            onToggleStrategyVisibility={onToggleStrategyVisibility}
            runConfigSnapshot={runConfigSnapshot}
            runDataProfile={runDataProfile}
            strategyNames={strategyNames}
            visibleBenchmarks={visibleBenchmarks}
            visibleStrategies={visibleStrategies}
            warnings={warnings}
          />
        )}
      </div>
    </div>
  );
}
