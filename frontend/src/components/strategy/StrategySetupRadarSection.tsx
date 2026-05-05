import { Radar } from 'lucide-react';
import type {
  BacktestResponse,
  PairsBacktestResultsPayload,
  StrategySetupScorePayload,
  StrategySetupPlanPayload,
} from '../../types/api';
import type { SavedStrategyRadarItem } from '../../hooks/useSavedStrategyRadar';
import type { StrategySetupRunHistoryItem } from '../../lib/strategySetupHistory';
import type { SetupScoreInsight } from '../../lib/strategySetupScoring';
import type { StrategySetupDraft } from './StrategySetupEditForm';
import { StrategySetupRadarItemCard } from './StrategySetupRadarItemCard';
import { StrategySetupRankingPanel } from './StrategySetupRankingPanel';

type StrategySetupRadarSectionProps = {
  radarPlan: string[];
  savedItems: SavedStrategyRadarItem[];
  setupScores: StrategySetupScorePayload[];
  setupScoreInsights: SetupScoreInsight[];
  editingStrategyId: string | null;
  setupDraft: StrategySetupDraft | null;
  setupRunHistory: StrategySetupRunHistoryItem[];
  setupPlans: Record<string, StrategySetupPlanPayload>;
  planningStrategyId: string | null;
  runningStrategyId: string | null;
  handoffMessages: Record<string, string>;
  setupRunErrors: Record<string, string>;
  setupRunResults: Record<string, BacktestResponse>;
  pairsRunResults: Record<string, PairsBacktestResultsPayload>;
  loadedRunResponses: Record<string, BacktestResponse>;
  loadedPairsBacktestResults: Record<string, PairsBacktestResultsPayload>;
  loadingRunId: string | null;
  loadingPairsBacktestId: string | null;
  onEdit: (item: SavedStrategyRadarItem) => void;
  onRemove: (strategyId: string) => void;
  onPrepare: (item: SavedStrategyRadarItem) => void;
  onDraftChange: (field: keyof StrategySetupDraft, value: string) => void;
  onCancelEdit: () => void;
  onSaveEdit: (item: SavedStrategyRadarItem) => void;
  onRun: (plan: StrategySetupPlanPayload) => void;
  onPairsHandoff: (plan: StrategySetupPlanPayload) => void;
  onLoadRunResponse: (runId: string) => void;
  onLoadPairsBacktestResults: (pairsBacktestId: string) => void;
};

export function StrategySetupRadarSection({
  radarPlan,
  savedItems,
  setupScores,
  setupScoreInsights,
  editingStrategyId,
  setupDraft,
  setupRunHistory,
  setupPlans,
  planningStrategyId,
  runningStrategyId,
  handoffMessages,
  setupRunErrors,
  setupRunResults,
  pairsRunResults,
  loadedRunResponses,
  loadedPairsBacktestResults,
  loadingRunId,
  loadingPairsBacktestId,
  onEdit,
  onRemove,
  onPrepare,
  onDraftChange,
  onCancelEdit,
  onSaveEdit,
  onRun,
  onPairsHandoff,
  onLoadRunResponse,
  onLoadPairsBacktestResults,
}: StrategySetupRadarSectionProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50/70 p-3 dark:border-gray-800 dark:bg-gray-950/30">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
          <Radar className="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
          Radar de setups
        </div>
        <span className="rounded-full border border-gray-300 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300">
          {savedItems.length} favorito(s)
        </span>
      </div>
      <ul className="mt-3 space-y-1 text-xs leading-5 text-gray-600 dark:text-gray-300">
        {radarPlan.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
      <StrategySetupRankingPanel scores={setupScores} insights={setupScoreInsights} />
      {savedItems.length > 0 ? (
        <div className="mt-3 space-y-2">
          {savedItems.map((item) => {
            const itemHistory = setupRunHistory.filter(
              (historyItem) => historyItem.strategy_id === item.strategy_id
            );
            const setupScore = setupScores.find(
              (score) => score.strategy_id === item.strategy_id
            );
            return (
              <StrategySetupRadarItemCard
                key={item.strategy_id}
                item={item}
                isEditing={editingStrategyId === item.strategy_id}
                draft={setupDraft}
                history={itemHistory}
                setupScore={setupScore}
                plan={setupPlans[item.strategy_id]}
                isPlanning={planningStrategyId === item.strategy_id}
                isRunning={runningStrategyId === item.strategy_id}
                handoffMessage={handoffMessages[item.strategy_id]}
                runError={setupRunErrors[item.strategy_id]}
                runResult={setupRunResults[item.strategy_id]}
                pairsRunResult={pairsRunResults[item.strategy_id]}
                loadedRunResponses={loadedRunResponses}
                loadedPairsBacktestResults={loadedPairsBacktestResults}
                loadingRunId={loadingRunId}
                loadingPairsBacktestId={loadingPairsBacktestId}
                onEdit={onEdit}
                onRemove={onRemove}
                onPrepare={onPrepare}
                onDraftChange={onDraftChange}
                onCancelEdit={onCancelEdit}
                onSaveEdit={onSaveEdit}
                onRun={onRun}
                onPairsHandoff={onPairsHandoff}
                onLoadRunResponse={onLoadRunResponse}
                onLoadPairsBacktestResults={onLoadPairsBacktestResults}
              />
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
