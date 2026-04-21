import { usePairsTrading } from '../hooks/usePairsTrading';
import { PairsBatchSummaryPanel } from './pairs/PairsBatchSummaryPanel';
import { PairsControlsCard } from './pairs/PairsControlsCard';
import { PairsHistoryCard } from './pairs/PairsHistoryCard';
import { PairsScreenerPanel } from './pairs/PairsScreenerPanel';
import { PairsUniversePanel } from './pairs/PairsUniversePanel';

interface PairsTradingWorkspaceProps {
  onError: (message: string | null) => void;
}

export default function PairsTradingWorkspace({ onError }: PairsTradingWorkspaceProps) {
  const {
    draft,
    presets,
    universe,
    screening,
    latestBacktest,
    backtests,
    selectedBacktestId,
    selectedBacktest,
    isLoadingPresets,
    isResolving,
    isScreening,
    isRunning,
    isLoadingBacktests,
    isLoadingSelected,
    updateDraft,
    refreshBacktests,
    resolveUniverse,
    runScreen,
    runBacktest,
    runBatch,
    runResearchBatch,
    loadBacktestResults,
  } = usePairsTrading(onError);

  const activeBacktest = selectedBacktest ?? latestBacktest;
  const selectedPreset = presets.find((preset) => preset.preset_id === draft.presetId) ?? null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <PairsControlsCard
          draft={draft}
          presets={presets}
          selectedPreset={selectedPreset}
          isResolving={isResolving}
          isScreening={isScreening}
          isRunning={isRunning}
          updateDraft={updateDraft}
          onResolveUniverse={() => void resolveUniverse()}
          onRunScreen={() => void runScreen()}
          onRunBacktest={() => void runBacktest()}
          onRunBatch={() => void runBatch()}
          onRunResearchBatch={() => void runResearchBatch()}
        />

        <PairsHistoryCard
          backtests={backtests}
          selectedBacktestId={selectedBacktestId}
          isLoadingBacktests={isLoadingBacktests}
          onRefreshBacktests={() => void refreshBacktests()}
          onLoadBacktestResults={(backtestId) => void loadBacktestResults(backtestId)}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <PairsUniversePanel
          universe={universe}
          isResolving={isResolving}
          isLoadingPresets={isLoadingPresets}
        />
        <PairsScreenerPanel
          screening={screening}
          eligibleAssetCount={universe?.eligible_assets.length ?? 0}
          isScreening={isScreening}
        />
      </div>

      <PairsBatchSummaryPanel
        activeBacktest={activeBacktest}
        isRunning={isRunning}
        isLoadingSelected={isLoadingSelected}
      />
    </div>
  );
}
