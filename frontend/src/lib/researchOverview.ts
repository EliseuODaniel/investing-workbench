import {
  ExperimentRegistryRecord,
  MonteCarloManifest,
  OptimizationManifest,
  WalkForwardManifest,
} from '../types/api';

export interface ResearchTimelineEntry {
  id: string;
  type: 'run' | 'optimization' | 'walkforward' | 'montecarlo' | 'pairs_backtest';
  createdAt: string;
  title: string;
  subtitle: string;
  warnings: string[];
}

export function buildResearchTimeline(
  experimentsOrOptimizations: ExperimentRegistryRecord[] | OptimizationManifest[],
  walkForwardExecutions: WalkForwardManifest[] = [],
  monteCarloExecutions: MonteCarloManifest[] = []
): ResearchTimelineEntry[] {
  return normalizeExperiments(
    experimentsOrOptimizations,
    walkForwardExecutions,
    monteCarloExecutions
  )
    .map((item) => ({
      id: item.experiment_id,
      type: item.experiment_type,
      createdAt: item.created_at,
      title: buildTimelineTitle(item),
      subtitle: buildTimelineSubtitle(item),
      warnings: readWarnings(item),
    }))
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
    .slice(0, 6);
}

export function countResearchWarnings(
  experimentsOrOptimizations: ExperimentRegistryRecord[] | OptimizationManifest[],
  monteCarloExecutions: MonteCarloManifest[] = []
): number {
  const experiments = normalizeExperiments(experimentsOrOptimizations, [], monteCarloExecutions);
  return experiments.reduce((count, item) => count + readWarnings(item).length, 0);
}

export function countExperimentsByType(
  experiments: ExperimentRegistryRecord[],
  experimentType: ExperimentRegistryRecord['experiment_type']
): number {
  return experiments.filter((item) => item.experiment_type === experimentType).length;
}

function buildTimelineTitle(item: ExperimentRegistryRecord): string {
  switch (item.experiment_type) {
    case 'run':
      return `Run · ${item.strategy_names.length} strategies`;
    case 'optimization':
      return `Optimization · ${String(item.summary.objective ?? 'objective')}`;
    case 'walkforward':
      return `Walk-Forward · ${String(item.summary.window_count ?? 0)} windows`;
    case 'montecarlo':
      return `Monte Carlo · ${String(item.summary.simulation_count ?? 0)} sims`;
    case 'pairs_backtest':
      return `Pairs · ${String(item.summary.candidate_pair_count ?? 0)} candidatos`;
  }
}

function buildTimelineSubtitle(item: ExperimentRegistryRecord): string {
  const strategyLabel = item.strategy_names.join(', ');
  switch (item.experiment_type) {
    case 'run':
      return `${strategyLabel} · ${String(item.summary.data_fingerprint ?? 'no fingerprint')}`;
    case 'optimization':
      return `${String(item.summary.completed_trial_count ?? 0)}/${String(item.summary.trial_count ?? 0)} trials · ${strategyLabel}`;
    case 'walkforward':
      return `${String(item.summary.train_window_days ?? 0)}/${String(item.summary.test_window_days ?? 0)}/${String(item.summary.step_days ?? 0)} rows · ${strategyLabel}`;
    case 'montecarlo':
      return `${String(item.summary.method ?? 'unknown')} · ${strategyLabel}`;
    case 'pairs_backtest':
      return `${String(item.summary.scenario_count ?? 0)} cenários · ${String(item.summary.preset_label ?? 'Pairs')}`;
  }
}

function readWarnings(item: ExperimentRegistryRecord): string[] {
  const warnings = item.summary?.warnings;
  return Array.isArray(warnings)
    ? warnings.filter((value): value is string => typeof value === 'string')
    : [];
}

function normalizeExperiments(
  experimentsOrOptimizations: ExperimentRegistryRecord[] | OptimizationManifest[],
  walkForwardExecutions: WalkForwardManifest[],
  monteCarloExecutions: MonteCarloManifest[]
): ExperimentRegistryRecord[] {
  if (
    experimentsOrOptimizations.length === 0 ||
    'experiment_id' in experimentsOrOptimizations[0]
  ) {
    return experimentsOrOptimizations as ExperimentRegistryRecord[];
  }

  const optimizations = experimentsOrOptimizations as OptimizationManifest[];
  return [
    ...optimizations.map((item) => ({
      experiment_id: item.optimization_id,
      experiment_type: 'optimization' as const,
      created_at: item.created_at,
      config_path: item.config_path,
      strategy_names: item.strategy_names,
      artifact_dir: '',
      status: 'completed',
      lineage: {},
      summary: {
        objective: item.objective,
        trial_count: item.trial_count,
        completed_trial_count: item.completed_trial_count,
        warnings: item.warnings,
      },
    })),
    ...walkForwardExecutions.map((item) => ({
      experiment_id: item.walkforward_id,
      experiment_type: 'walkforward' as const,
      created_at: item.created_at,
      config_path: item.config_path,
      strategy_names: item.strategy_names,
      artifact_dir: '',
      status: 'completed',
      lineage: {},
      summary: {
        train_window_days: item.train_window_days,
        test_window_days: item.test_window_days,
        step_days: item.step_days,
        window_count: item.window_count,
        warnings: [],
      },
    })),
    ...monteCarloExecutions.map((item) => ({
      experiment_id: item.montecarlo_id,
      experiment_type: 'montecarlo' as const,
      created_at: item.created_at,
      config_path: item.config_path,
      strategy_names: item.strategy_names,
      artifact_dir: '',
      status: 'completed',
      lineage: { source_run_id: item.source_run_id },
      summary: {
        simulation_count: item.simulation_count,
        method: item.method,
        warnings: item.warnings,
      },
    })),
  ];
}
