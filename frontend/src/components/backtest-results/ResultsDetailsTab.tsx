import React, { Suspense } from 'react';
import LoadingSpinner from '../LoadingSpinner';
import QuickActions from '../QuickActions';
import ResultsInterpretationPanel from '../ResultsInterpretationPanel';
import RunArtifactsPanel from '../RunArtifactsPanel';
import VisibilityControls from '../VisibilityControls';
import WarningsPanel from '../WarningsPanel';
import { ResultsDetailsTabProps } from './types';

const SelicInfoPanel = React.lazy(() => import('../SelicInfoPanel'));

function lazyPanelFallback(message: string) {
  return (
    <div className="card">
      <LoadingSpinner message={message} />
    </div>
  );
}

export default function ResultsDetailsTab({
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
  visibleBenchmarks,
  visibleStrategies,
  warnings,
}: ResultsDetailsTabProps) {
  return (
    <div className="space-y-6">
      {warnings.length > 0 && (
        <WarningsPanel
          warnings={warnings}
          onDismiss={() => {
            /* read-only warnings for now */
          }}
        />
      )}

      <QuickActions
        strategies={strategyNames}
        onDownloadCSV={onDownloadCSV}
        onDownloadPNG={onDownloadPNG}
        onDownloadHTML={onDownloadHTML}
        onSaveProject={onSaveProject}
        onShareResults={onShareResults}
        onCopySummary={onCopySummary}
        onCopyLink={onCopyLink}
        onCaptureScreenshot={onDownloadPNG}
      />

      <VisibilityControls
        strategies={Object.keys(backtestResponse.results)}
        benchmarks={Object.keys(backtestResponse.benchmarks ?? {})}
        visibleStrategies={visibleStrategies}
        visibleBenchmarks={visibleBenchmarks}
        onStrategyToggle={onToggleStrategyVisibility}
        onBenchmarkToggle={onToggleBenchmarkVisibility}
        onToggleAllStrategies={onToggleAllStrategies}
        onToggleAllBenchmarks={onToggleAllBenchmarks}
      />

      <RunArtifactsPanel
        runId={backtestResponse.run_info?.run_id}
        configSnapshot={runConfigSnapshot}
        dataProfile={runDataProfile}
        isLoading={isLoadingArtifacts}
      />

      <ResultsInterpretationPanel results={backtestResponse.results} />

      {backtestRequest.apply_cash_yield && (
        <Suspense fallback={lazyPanelFallback('Loading SELIC panel...')}>
          <SelicInfoPanel
            useRealSelic={backtestRequest.use_real_selic}
            selicFallbackRate={backtestRequest.selic_fallback_rate}
            selicRatesUsed={Object.values(backtestResponse.results)[0]?.metrics?.selic_rates_used}
            selicRateAnnual={backtestRequest.selic_fallback_rate}
            capital={backtestRequest.initial_capital}
          />
        </Suspense>
      )}
    </div>
  );
}
