import { MonteCarloMethod, MonteCarloRequestPayload } from '../types/api';
import { normalizeStrategyList } from './optimizationPayload';

export type MonteCarloSourceMode = 'current-run' | 'config';

export interface MonteCarloDraft {
  sourceMode: MonteCarloSourceMode;
  strategiesText: string;
  simulationsText: string;
  seedText: string;
  ruinThresholdText: string;
  method: MonteCarloMethod;
}

export function buildMonteCarloPayload(
  configPath: string | undefined,
  runId: string | undefined,
  fallbackStrategies: string[],
  draft: MonteCarloDraft
): MonteCarloRequestPayload {
  const strategies = normalizeStrategyList(draft.strategiesText || fallbackStrategies.join(', '));
  const simulationCount = parsePositiveInteger(draft.simulationsText, 'simulation count');
  const randomSeed = parsePositiveInteger(draft.seedText, 'random seed');
  const ruinThresholdPct = parseProbability(draft.ruinThresholdText, 'ruin threshold');

  if (draft.sourceMode === 'current-run') {
    if (!runId) {
      throw new Error('Load or run a persisted backtest before using current-run Monte Carlo');
    }

    return {
      run_id: runId,
      strategies: strategies.length > 0 ? strategies : undefined,
      simulation_count: simulationCount,
      random_seed: randomSeed,
      method: draft.method,
      ruin_threshold_pct: ruinThresholdPct,
    };
  }

  if (!configPath) {
    throw new Error('Select a config before running Monte Carlo from config');
  }

  return {
    config_path: configPath,
    strategies: strategies.length > 0 ? strategies : undefined,
    simulation_count: simulationCount,
    random_seed: randomSeed,
    method: draft.method,
    ruin_threshold_pct: ruinThresholdPct,
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

function parseProbability(raw: string, label: string): number {
  const normalized = raw.trim();
  const parsed = Number.parseFloat(normalized);
  if (!normalized || Number.isNaN(parsed) || parsed < 0 || parsed >= 1) {
    throw new Error(`Invalid ${label}: expected a decimal between 0 and 1`);
  }
  return parsed;
}
