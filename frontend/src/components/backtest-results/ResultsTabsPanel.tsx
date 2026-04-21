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
  latestValidRunId,
  onCopyLink,
  onCopySummary,
  onDownloadCSV,
  onDownloadHTML,
  onDownloadPNG,
  onOpenLatestValidRun,
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

      {backtestResponse.run_quality?.status === 'legacy_invalid' ? (
        <div className="mt-6 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-amber-50">
          <div className="text-sm font-semibold tracking-wide text-amber-200">
            {backtestResponse.run_quality.title}
          </div>
          <p className="mt-2 text-sm leading-6 text-amber-100">
            {backtestResponse.run_quality.message}
          </p>
          <p className="mt-2 text-xs text-amber-200/90">
            Este run permanece acessivel para auditoria, mas nao deve ser usado para comparar
            estrategias atuais.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            {latestValidRunId && onOpenLatestValidRun ? (
              <button
                type="button"
                onClick={onOpenLatestValidRun}
                className="rounded-lg bg-amber-300 px-3 py-2 text-sm font-medium text-slate-950 transition hover:bg-amber-200"
              >
                Abrir ultimo run valido
              </button>
            ) : null}
            <div className="self-center text-xs text-amber-200/90">
              {latestValidRunId
                ? `Run recomendado: ${latestValidRunId}`
                : 'Nenhum run valido mais recente foi encontrado no historico.'}
            </div>
          </div>
        </div>
      ) : null}

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
