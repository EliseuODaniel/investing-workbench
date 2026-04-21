import {
  ExperimentDetailPayload,
  ExperimentRegistryRecord,
  MonteCarloResultsPayload,
  OptimizationResultsPayload,
  WalkForwardResultsPayload,
} from '../types/api';

export interface ResearchAlignmentSummary {
  bestRunId: string | null;
  monteCarloSourceRunId: string | null;
  runLinkAligned: boolean;
  optimizationObjectiveValue: number | null;
  walkForwardAvgTestReturn: number | null;
  monteCarloLossProbability: number | null;
  monteCarloRuinProbability: number | null;
}

export interface ExperimentContextTargets {
  anchorRunId: string | null;
  optimization: ExperimentRegistryRecord | null;
  walkforward: ExperimentRegistryRecord | null;
  montecarlo: ExperimentRegistryRecord | null;
}

export interface ExperimentContextCandidates {
  optimization: ExperimentRegistryRecord[];
  walkforward: ExperimentRegistryRecord[];
  montecarlo: ExperimentRegistryRecord[];
}

export interface ExperimentContextOverrides {
  optimizationId?: string | null;
  walkforwardId?: string | null;
  montecarloId?: string | null;
}

export function summarizeResearchAlignment(
  optimizationResults: OptimizationResultsPayload | null,
  walkForwardResults: WalkForwardResultsPayload | null,
  monteCarloResults: MonteCarloResultsPayload | null
): ResearchAlignmentSummary {
  const bestTrial = optimizationResults?.ranked_results?.[0] ?? null;
  const walkForwardSummary = walkForwardResults?.strategy_summaries?.[0] ?? null;
  const monteCarloSummary = monteCarloResults?.strategy_summaries?.[0] ?? null;
  const bestRunId = bestTrial?.run_id ?? null;
  const monteCarloSourceRunId = monteCarloResults?.source_run_id ?? null;

  return {
    bestRunId,
    monteCarloSourceRunId,
    runLinkAligned:
      Boolean(bestRunId) &&
      Boolean(monteCarloSourceRunId) &&
      bestRunId === monteCarloSourceRunId,
    optimizationObjectiveValue:
      typeof bestTrial?.objective_value === 'number' ? bestTrial.objective_value : null,
    walkForwardAvgTestReturn:
      typeof walkForwardSummary?.avg_test_total_return === 'number'
        ? walkForwardSummary.avg_test_total_return
        : null,
    monteCarloLossProbability:
      typeof monteCarloSummary?.loss_probability === 'number'
        ? monteCarloSummary.loss_probability
        : null,
    monteCarloRuinProbability:
      typeof monteCarloSummary?.ruin_probability === 'number'
        ? monteCarloSummary.ruin_probability
        : null,
  };
}

export function inferExperimentContext(
  detail: ExperimentDetailPayload,
  experiments: ExperimentRegistryRecord[]
): ExperimentContextTargets {
  const selected = detail.record;

  const optimization =
    selected.experiment_type === 'optimization'
      ? selected
      : findRelatedExperiment(detail, ['best_run_for_optimization', 'parent_optimization']);
  const montecarlo =
    selected.experiment_type === 'montecarlo'
      ? selected
      : findRelatedExperiment(detail, ['source_run_for_montecarlo']);
  const anchorRunId =
    (selected.experiment_type === 'run' ? selected.experiment_id : null) ??
    selected.lineage.best_run_id ??
    selected.lineage.source_run_id ??
    (findRelatedExperiment(detail, ['best_run', 'source_run'])?.experiment_id ?? null);

  const walkforward =
    selected.experiment_type === 'walkforward'
      ? selected
      : findMatchingWalkForward(selected, experiments);

  return {
    anchorRunId,
    optimization,
    walkforward,
    montecarlo,
  };
}

export function listExperimentContextCandidates(
  detail: ExperimentDetailPayload,
  experiments: ExperimentRegistryRecord[]
): ExperimentContextCandidates {
  const selected = detail.record;

  return {
    optimization: buildCandidateList(detail, experiments, selected, 'optimization'),
    walkforward: buildCandidateList(detail, experiments, selected, 'walkforward'),
    montecarlo: buildCandidateList(detail, experiments, selected, 'montecarlo'),
  };
}

export function applyExperimentContextOverrides(
  inferred: ExperimentContextTargets,
  candidates: ExperimentContextCandidates,
  overrides: ExperimentContextOverrides
): ExperimentContextTargets {
  return {
    anchorRunId: inferred.anchorRunId,
    optimization:
      resolveCandidate(candidates.optimization, overrides.optimizationId) ??
      inferred.optimization,
    walkforward:
      resolveCandidate(candidates.walkforward, overrides.walkforwardId) ??
      inferred.walkforward,
    montecarlo:
      resolveCandidate(candidates.montecarlo, overrides.montecarloId) ??
      inferred.montecarlo,
  };
}

function findRelatedExperiment(
  detail: ExperimentDetailPayload,
  relationships: string[]
): ExperimentRegistryRecord | null {
  const match = detail.related_experiments.find((relation) =>
    relationships.includes(relation.relationship)
  );
  return match?.record ?? null;
}

function findMatchingWalkForward(
  selected: ExperimentRegistryRecord,
  experiments: ExperimentRegistryRecord[]
): ExperimentRegistryRecord | null {
  return experiments
    .filter((candidate) => candidate.experiment_type === 'walkforward')
    .filter(
      (candidate) =>
        candidate.config_path === selected.config_path &&
        candidate.strategy_names.some((strategy) => selected.strategy_names.includes(strategy))
    )
    .sort((left, right) => right.created_at.localeCompare(left.created_at))[0] ?? null;
}

function buildCandidateList(
  detail: ExperimentDetailPayload,
  experiments: ExperimentRegistryRecord[],
  selected: ExperimentRegistryRecord,
  experimentType: ExperimentRegistryRecord['experiment_type']
): ExperimentRegistryRecord[] {
  const relatedMatches = detail.related_experiments
    .map((relation) => relation.record)
    .filter((record) => record.experiment_type === experimentType);
  const contextualMatches = experiments
    .filter((candidate) => candidate.experiment_type === experimentType)
    .filter(
      (candidate) =>
        candidate.config_path === selected.config_path &&
        candidate.strategy_names.some((strategy) => selected.strategy_names.includes(strategy))
    );

  const selectedMatch =
    selected.experiment_type === experimentType ? [selected] : [];

  return dedupeRecords([...selectedMatch, ...relatedMatches, ...contextualMatches]).sort((left, right) =>
    right.created_at.localeCompare(left.created_at)
  );
}

function dedupeRecords(records: ExperimentRegistryRecord[]): ExperimentRegistryRecord[] {
  const seen = new Set<string>();
  return records.filter((record) => {
    const key = `${record.experiment_type}:${record.experiment_id}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function resolveCandidate(
  candidates: ExperimentRegistryRecord[],
  experimentId: string | null | undefined
): ExperimentRegistryRecord | null {
  if (!experimentId) {
    return null;
  }
  return candidates.find((candidate) => candidate.experiment_id === experimentId) ?? null;
}
