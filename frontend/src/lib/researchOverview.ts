import {
  MonteCarloManifest,
  OptimizationManifest,
  WalkForwardManifest,
} from '../types/api';

export interface ResearchTimelineEntry {
  id: string;
  type: 'optimization' | 'walkforward' | 'montecarlo';
  createdAt: string;
  title: string;
  subtitle: string;
  warnings: string[];
}

export function buildResearchTimeline(
  optimizations: OptimizationManifest[],
  walkForwardExecutions: WalkForwardManifest[],
  monteCarloExecutions: MonteCarloManifest[]
): ResearchTimelineEntry[] {
  const timeline: ResearchTimelineEntry[] = [
    ...optimizations.map((item) => ({
      id: item.optimization_id,
      type: 'optimization' as const,
      createdAt: item.created_at,
      title: `Optimization · ${item.objective}`,
      subtitle: `${item.completed_trial_count}/${item.trial_count} trials · ${item.strategy_names.join(', ')}`,
      warnings: item.warnings,
    })),
    ...walkForwardExecutions.map((item) => ({
      id: item.walkforward_id,
      type: 'walkforward' as const,
      createdAt: item.created_at,
      title: `Walk-Forward · ${item.window_count} windows`,
      subtitle: `${item.train_window_days}/${item.test_window_days}/${item.step_days} rows · ${item.strategy_names.join(', ')}`,
      warnings: [],
    })),
    ...monteCarloExecutions.map((item) => ({
      id: item.montecarlo_id,
      type: 'montecarlo' as const,
      createdAt: item.created_at,
      title: `Monte Carlo · ${item.simulation_count} sims`,
      subtitle: `${item.method} · ${item.strategy_names.join(', ')}`,
      warnings: item.warnings,
    })),
  ];

  return timeline
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
    .slice(0, 6);
}

export function countResearchWarnings(
  optimizations: OptimizationManifest[],
  monteCarloExecutions: MonteCarloManifest[]
): number {
  const optimizationWarnings = optimizations.reduce(
    (count, item) => count + item.warnings.length,
    0
  );
  const monteCarloWarnings = monteCarloExecutions.reduce(
    (count, item) => count + item.warnings.length,
    0
  );

  return optimizationWarnings + monteCarloWarnings;
}
