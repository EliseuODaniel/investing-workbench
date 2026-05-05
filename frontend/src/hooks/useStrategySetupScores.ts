import { useMemo } from 'react';
import {
  buildSetupScoreInsights,
  buildSetupScores,
} from '../lib/strategySetupScoring';
import type {
  SavedStrategyRadarItemPayload,
  SavedStrategySetupRunPayload,
  StrategySetupScorePayload,
} from '../types/api';

type UseStrategySetupScoresOptions = {
  savedItems: SavedStrategyRadarItemPayload[];
  setupRunHistory: SavedStrategySetupRunPayload[];
  remoteSetupScores: StrategySetupScorePayload[];
};

export function useStrategySetupScores({
  savedItems,
  setupRunHistory,
  remoteSetupScores,
}: UseStrategySetupScoresOptions) {
  const setupScores = useMemo(
    () =>
      remoteSetupScores.length > 0
        ? remoteSetupScores
        : buildSetupScores(savedItems, setupRunHistory),
    [remoteSetupScores, savedItems, setupRunHistory]
  );
  const setupScoreInsights = useMemo(
    () => buildSetupScoreInsights(setupScores),
    [setupScores]
  );

  return { setupScores, setupScoreInsights };
}
