import {
  OptimizationDirection,
  OptimizationMode,
  OptimizationRequestPayload,
} from '../types/api';

export interface OptimizationDraft {
  strategiesText: string;
  globalSpaceText: string;
  strategySpaceText: string;
  mode: OptimizationMode;
  objective: string;
  direction: OptimizationDirection;
  maxTrialsText: string;
  seedText: string;
}

export function buildOptimizationPayload(
  configPath: string,
  fallbackStrategies: string[],
  draft: OptimizationDraft
): OptimizationRequestPayload {
  if (!configPath) {
    throw new Error('Select a config before planning an optimization');
  }

  const strategies = normalizeStrategyList(draft.strategiesText || fallbackStrategies.join(', '));
  const parameterSpace = parseJsonObjectInput(draft.globalSpaceText, 'global search space');
  const strategyParameterSpaces = parseJsonObjectInput(
    draft.strategySpaceText,
    'strategy search space'
  ) as Record<string, Record<string, unknown>>;
  const maxTrials = parseOptionalInteger(draft.maxTrialsText, 'max trials');
  const randomSeed = parseRequiredInteger(draft.seedText, 'random seed');

  return {
    config_path: configPath,
    strategies: strategies.length > 0 ? strategies : undefined,
    parameter_space: parameterSpace,
    strategy_parameter_spaces: strategyParameterSpaces,
    mode: draft.mode,
    max_trials: maxTrials,
    random_seed: randomSeed,
    objective: draft.objective.trim() || 'sharpe_ratio',
    direction: draft.direction,
  };
}

export function normalizeStrategyList(raw: string): string[] {
  return raw
    .split(/[\n,]/)
    .map((value) => value.trim())
    .filter(Boolean);
}

export function parseJsonObjectInput(raw: string, label: string): Record<string, unknown> {
  const normalized = raw.trim();
  if (!normalized) {
    return {};
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(normalized);
  } catch {
    throw new Error(`Invalid ${label}: expected valid JSON`);
  }

  if (parsed === null || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error(`Invalid ${label}: expected a JSON object`);
  }

  return parsed as Record<string, unknown>;
}

function parseOptionalInteger(raw: string, label: string): number | undefined {
  const normalized = raw.trim();
  if (!normalized) {
    return undefined;
  }

  const parsed = Number.parseInt(normalized, 10);
  if (Number.isNaN(parsed) || parsed <= 0) {
    throw new Error(`Invalid ${label}: expected a positive integer`);
  }

  return parsed;
}

function parseRequiredInteger(raw: string, label: string): number {
  const parsed = parseOptionalInteger(raw, label);
  if (parsed === undefined) {
    throw new Error(`Invalid ${label}: expected a positive integer`);
  }
  return parsed;
}
