import {
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
