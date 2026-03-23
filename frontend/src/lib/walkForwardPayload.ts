import { WalkForwardRequestPayload } from '../types/api';
import { normalizeStrategyList } from './optimizationPayload';

export interface WalkForwardDraft {
  strategiesText: string;
  trainDaysText: string;
  testDaysText: string;
  stepDaysText: string;
}

export function buildWalkForwardPayload(
  configPath: string,
  fallbackStrategies: string[],
  draft: WalkForwardDraft
): WalkForwardRequestPayload {
  if (!configPath) {
    throw new Error('Select a config before running walk-forward validation');
  }

  const strategies = normalizeStrategyList(draft.strategiesText || fallbackStrategies.join(', '));

  return {
    config_path: configPath,
    strategies: strategies.length > 0 ? strategies : undefined,
    train_window_days: parsePositiveInteger(draft.trainDaysText, 'train window'),
    test_window_days: parsePositiveInteger(draft.testDaysText, 'test window'),
    step_days: parsePositiveInteger(draft.stepDaysText, 'step window'),
  };
}

function parsePositiveInteger(raw: string, label: string): number {
  const normalized = raw.trim();
  const parsed = Number.parseInt(normalized, 10);
  if (!normalized || Number.isNaN(parsed) || parsed <= 0) {
    throw new Error(`Invalid ${label}: expected a positive integer`);
  }
  return parsed;
}
