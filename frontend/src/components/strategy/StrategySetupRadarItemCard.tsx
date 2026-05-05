import { ClipboardList, Pencil, Trash2 } from 'lucide-react';
import type {
  BacktestResponse,
  PairsBacktestResultsPayload,
  StrategySetupScorePayload,
  StrategySetupPlanPayload,
} from '../../types/api';
import type { SavedStrategyRadarItem } from '../../hooks/useSavedStrategyRadar';
import type { StrategySetupRunHistoryItem } from '../../lib/strategySetupHistory';
import {
  StrategySetupEditForm,
  type StrategySetupDraft,
} from './StrategySetupEditForm';
import { StrategySetupPlanCard } from './StrategySetupPlanCard';

type StrategySetupRadarItemCardProps = {
  item: SavedStrategyRadarItem;
  isEditing: boolean;
  draft: StrategySetupDraft | null;
  history: StrategySetupRunHistoryItem[];
  setupScore?: StrategySetupScorePayload;
  plan?: StrategySetupPlanPayload;
  isPlanning: boolean;
  isRunning: boolean;
  handoffMessage?: string;
  runError?: string;
  runResult?: BacktestResponse;
  pairsRunResult?: PairsBacktestResultsPayload;
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

export function StrategySetupRadarItemCard({
  item,
  isEditing,
  draft,
  history,
  setupScore,
  plan,
  isPlanning,
  isRunning,
  handoffMessage,
  runError,
  runResult,
  pairsRunResult,
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
}: StrategySetupRadarItemCardProps) {
  const latestHistory = history[0];

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-semibold text-gray-900 dark:text-gray-100">{item.label}</div>
          <div className="mt-1 text-gray-500 dark:text-gray-400">
            {item.family} · {item.direction}
          </div>
          <div className="mt-1 text-gray-500 dark:text-gray-400">
            {item.timeframe || 'daily'} ·{' '}
            {(item.universe || []).slice(0, 4).join(', ') || 'universo a definir'}
          </div>
          {item.parameter_values && Object.keys(item.parameter_values).length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(item.parameter_values)
                .slice(0, 4)
                .map(([key, value]) => (
                  <span
                    key={key}
                    className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-600 dark:bg-gray-800 dark:text-gray-300"
                  >
                    {key}: {String(value)}
                  </span>
                ))}
            </div>
          ) : null}
          {latestHistory ? (
            <div className="mt-2 flex flex-wrap gap-1">
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200">
                {history.length} execucao(oes)
              </span>
              {typeof latestHistory.total_return === 'number' ? (
                <span className="rounded-full border border-gray-200 bg-gray-50 px-2 py-0.5 text-[11px] text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300">
                  retorno {formatPercent(latestHistory.total_return)}
                </span>
              ) : null}
              {typeof latestHistory.max_drawdown === 'number' ? (
                <span className="rounded-full border border-gray-200 bg-gray-50 px-2 py-0.5 text-[11px] text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300">
                  DD {formatPercent(latestHistory.max_drawdown)}
                </span>
              ) : null}
              {setupScore ? (
                <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-[11px] text-indigo-700 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-indigo-200">
                  score {setupScore.score.toFixed(1)}
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            className="rounded-full border border-gray-300 p-1.5 text-gray-500 transition hover:border-blue-300 hover:text-blue-600 dark:border-gray-700 dark:text-gray-400 dark:hover:border-blue-800 dark:hover:text-blue-300"
            onClick={() => onEdit(item)}
            aria-label={`Editar setup ${item.label}`}
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            className="rounded-full border border-gray-300 p-1.5 text-gray-500 transition hover:border-emerald-300 hover:text-emerald-600 dark:border-gray-700 dark:text-gray-400 dark:hover:border-emerald-800 dark:hover:text-emerald-300"
            onClick={() => onPrepare(item)}
            aria-label={`Preparar execucao ${item.label}`}
          >
            <ClipboardList className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            className="rounded-full border border-gray-300 p-1.5 text-gray-500 transition hover:border-red-300 hover:text-red-600 dark:border-gray-700 dark:text-gray-400 dark:hover:border-red-800 dark:hover:text-red-300"
            onClick={() => onRemove(item.strategy_id)}
            aria-label={`Remover ${item.label} do radar`}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
      {isEditing && draft ? (
        <StrategySetupEditForm
          draft={draft}
          onChange={onDraftChange}
          onCancel={onCancelEdit}
          onSave={() => onSaveEdit(item)}
        />
      ) : null}
      <StrategySetupPlanCard
        plan={plan}
        isPlanning={isPlanning}
        isRunning={isRunning}
        handoffMessage={handoffMessage}
        runError={runError}
        runResult={runResult}
        pairsRunResult={pairsRunResult}
        history={history}
        loadedRunResponses={loadedRunResponses}
        loadedPairsBacktestResults={loadedPairsBacktestResults}
        loadingRunId={loadingRunId}
        loadingPairsBacktestId={loadingPairsBacktestId}
        onRun={onRun}
        onPairsHandoff={onPairsHandoff}
        onLoadRunResponse={onLoadRunResponse}
        onLoadPairsBacktestResults={onLoadPairsBacktestResults}
      />
    </div>
  );
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}
