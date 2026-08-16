import { BookOpen } from 'lucide-react';
import { useSavedStrategyRadar } from '../hooks/useSavedStrategyRadar';
import { useStrategyCatalogData } from '../hooks/useStrategyCatalogData';
import { useStrategySetupDraftEditor } from '../hooks/useStrategySetupDraftEditor';
import { useStrategySetupExecution } from '../hooks/useStrategySetupExecution';
import { useStrategySetupScores } from '../hooks/useStrategySetupScores';
import { StrategyCatalogList } from './strategy/StrategyCatalogList';
import { StrategySetupRadarSection } from './strategy/StrategySetupRadarSection';
import { StrategyScoreDimensionsPanel } from './strategy/StrategyScoreDimensionsPanel';

export default function StrategyCatalogPanel() {
  const {
    savedItems,
    savedStrategyIds,
    saveStrategy,
    removeStrategy,
    updateStrategySetup,
  } = useSavedStrategyRadar();
  const {
    editingStrategyId,
    setupDraft,
    startEditingSetup,
    cancelEditingSetup,
    saveEditedSetup,
    updateDraftField,
  } = useStrategySetupDraftEditor({ updateStrategySetup });
  const {
    setupPlans,
    setupRunResults,
    loadedRunResponses,
    loadedPairsBacktestResults,
    pairsRunResults,
    setupRunErrors,
    handoffMessages,
    loadingRunId,
    loadingPairsBacktestId,
    setupRunHistory,
    remoteSetupScores,
    planningStrategyId,
    runningStrategyId,
    hydrateSetupRuns,
    prepareSetupPlan,
    runPreparedSetup,
    runAllPreparedSetups,
    loadRunResponse,
    loadPairsBacktestResults,
    sendPairsHandoff,
  } = useStrategySetupExecution();
  const { catalog, error, familyCount } = useStrategyCatalogData({ hydrateSetupRuns });
  const { setupScores, setupScoreInsights } = useStrategySetupScores({
    savedItems,
    setupRunHistory,
    remoteSetupScores,
  });

  if (error) {
    return (
      <section className="card border-amber-200 bg-amber-50/80 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100">
        {error}
      </section>
    );
  }

  if (!catalog) {
    return (
      <section className="card text-sm text-gray-500 dark:text-gray-400">
        Carregando catalogo de estrategias...
      </section>
    );
  }

  return (
    <section className="card space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            <BookOpen className="h-4 w-4 text-blue-600 dark:text-blue-300" />
            {catalog.title}
          </div>
          <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
            {catalog.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-gray-300 bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200">
          {catalog.strategies.length} estrategias · {familyCount} familias
        </div>
      </div>

      <StrategyCatalogList
        strategies={catalog.strategies}
        savedStrategyIds={savedStrategyIds}
        onSaveStrategy={saveStrategy}
        onRemoveStrategy={removeStrategy}
      />

      <StrategyScoreDimensionsPanel dimensions={catalog.score_dimensions} />

      <StrategySetupRadarSection
        radarPlan={catalog.radar_plan}
        savedItems={savedItems}
        setupScores={setupScores}
        setupScoreInsights={setupScoreInsights}
        editingStrategyId={editingStrategyId}
        setupDraft={setupDraft}
        setupRunHistory={setupRunHistory}
        setupPlans={setupPlans}
        planningStrategyId={planningStrategyId}
        runningStrategyId={runningStrategyId}
        handoffMessages={handoffMessages}
        setupRunErrors={setupRunErrors}
        setupRunResults={setupRunResults}
        pairsRunResults={pairsRunResults}
        loadedRunResponses={loadedRunResponses}
        loadedPairsBacktestResults={loadedPairsBacktestResults}
        loadingRunId={loadingRunId}
        loadingPairsBacktestId={loadingPairsBacktestId}
        onEdit={startEditingSetup}
        onRemove={removeStrategy}
        onPrepare={(strategy) => void prepareSetupPlan(strategy)}
        onDraftChange={updateDraftField}
        onCancelEdit={cancelEditingSetup}
        onSaveEdit={saveEditedSetup}
        onRun={(plan) => void runPreparedSetup(plan)}
        onRunAll={(plans) => void runAllPreparedSetups(plans)}
        onPairsHandoff={sendPairsHandoff}
        onLoadRunResponse={(runId) => void loadRunResponse(runId)}
        onLoadPairsBacktestResults={(pairsBacktestId) =>
          void loadPairsBacktestResults(pairsBacktestId)
        }
      />
    </section>
  );
}
