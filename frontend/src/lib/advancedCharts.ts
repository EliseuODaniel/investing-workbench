import {
  MonteCarloResultsPayload,
  OptimizationResultsPayload,
  PairsBacktestResultsPayload,
  WalkForwardResultsPayload,
} from '../types/api';
import { InteractiveSeriesDefinition } from '../components/charts/InteractiveSeriesChart';

type ChartPoint = Record<string, string | number | null | undefined>;

interface BuiltChart {
  data: ChartPoint[];
  series: InteractiveSeriesDefinition[];
  referenceSeriesId?: string | null;
}

const PALETTE = ['#2563eb', '#f59e0b', '#22c55e', '#8b5cf6', '#ef4444', '#06b6d4'];

function createSeries(
  id: string,
  label: string,
  color: string,
  options?: Partial<InteractiveSeriesDefinition>
): InteractiveSeriesDefinition {
  return {
    id,
    label,
    color,
    ...options,
  };
}

export function buildOptimizationObjectiveChart(
  results: OptimizationResultsPayload | null
): BuiltChart | null {
  if (!results) {
    return null;
  }

  const completed = results.ranked_results.filter(
    (item) => item.status === 'completed' && typeof item.objective_value === 'number'
  );
  if (completed.length === 0) {
    return null;
  }

  const bestByStrategy = new Map<string, typeof completed[number]>();
  completed.forEach((item) => {
    const current = bestByStrategy.get(item.strategy_name);
    if (!current || (item.objective_value ?? 0) > (current.objective_value ?? 0)) {
      bestByStrategy.set(item.strategy_name, item);
    }
  });

  const grouped = Array.from(bestByStrategy.values());

  if (grouped.length > 1) {
    return {
      data: grouped.map((item) => ({
        label: item.strategy_name,
        objective_value: item.objective_value ?? null,
      })),
      series: [createSeries('objective_value', 'Melhor objetivo', '#2563eb', { strokeWidth: 2.5 })],
    };
  }

  return {
    data: completed.slice(0, 8).map((item) => ({
      label: item.trial_id,
      objective_value: item.objective_value ?? null,
    })),
    series: [createSeries('objective_value', 'Objetivo por trial', '#2563eb', { strokeWidth: 2.5 })],
  };
}

export function buildWalkForwardTestChart(
  results: WalkForwardResultsPayload | null
): BuiltChart | null {
  if (!results || results.results.length === 0) {
    return null;
  }

  const windowMap = new Map<string, ChartPoint>();
  const strategyOrder: string[] = [];

  results.results.forEach((item) => {
    if (!windowMap.has(item.window_id)) {
      windowMap.set(item.window_id, { label: item.window_id });
    }
    const row = windowMap.get(item.window_id)!;
    row[item.strategy_name] = item.test_metrics.total_return ?? null;
    if (!strategyOrder.includes(item.strategy_name)) {
      strategyOrder.push(item.strategy_name);
    }
  });

  return {
    data: Array.from(windowMap.values()),
    series: strategyOrder.map((strategyName, index) =>
      createSeries(strategyName, strategyName, PALETTE[index % PALETTE.length])
    ),
  };
}

export function buildMonteCarloReturnChart(
  results: MonteCarloResultsPayload | null
): BuiltChart | null {
  if (!results || results.strategy_summaries.length === 0) {
    return null;
  }

  return {
    data: results.strategy_summaries.map((summary) => ({
      label: summary.strategy_name,
      actual_total_return: summary.actual_total_return,
      median_total_return: summary.median_total_return,
      percentile_05_total_return: summary.percentile_05_total_return,
      percentile_95_total_return: summary.percentile_95_total_return,
    })),
    series: [
      createSeries('actual_total_return', 'Retorno real', '#2563eb', { strokeWidth: 2.5 }),
      createSeries('median_total_return', 'Retorno mediano', '#22c55e'),
      createSeries('percentile_05_total_return', 'Faixa pessimista (5%)', '#ef4444', {
        dashed: true,
      }),
      createSeries('percentile_95_total_return', 'Faixa otimista (95%)', '#8b5cf6', {
        dashed: true,
      }),
    ],
  };
}

export function buildPairsEquityChart(
  results: PairsBacktestResultsPayload | null
): BuiltChart | null {
  if (!results) {
    return null;
  }

  const allSeries: Array<{
    id: string;
    label: string;
    points: Array<Record<string, unknown>>;
    dashed?: boolean;
  }> = [];

  results.scenarios.forEach((scenario) => {
    const curve = Array.isArray(scenario.equity_curve) ? scenario.equity_curve : [];
    if (curve.length === 0) {
      return;
    }
    allSeries.push({
      id: String(scenario.scenario_id),
      label: String(scenario.label),
      points: curve,
      dashed: false,
    });
  });

  results.benchmarks.forEach((benchmark) => {
    if (!Array.isArray(benchmark.equity_curve) || benchmark.equity_curve.length === 0) {
      return;
    }
    allSeries.push({
      id: String(benchmark.benchmark_id),
      label: String(benchmark.label),
      points: benchmark.equity_curve,
      dashed: true,
    });
  });

  if (allSeries.length === 0) {
    return null;
  }

  const rows = new Map<string, ChartPoint>();
  allSeries.forEach((series) => {
    series.points.forEach((point) => {
      const date = typeof point.date === 'string' ? point.date : null;
      const equity = typeof point.equity === 'number' ? point.equity : null;
      if (!date) {
        return;
      }
      if (!rows.has(date)) {
        rows.set(date, { date });
      }
      rows.get(date)![series.id] = equity;
    });
  });

  const benchmarkReference =
    allSeries.find((item) => item.id.includes('selic') || item.label.toLowerCase().includes('selic'))
      ?.id ??
    allSeries.find((item) => item.dashed)?.id ??
    null;

  return {
    data: Array.from(rows.entries())
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([, row]) => row),
    series: allSeries.map((item) =>
      createSeries(
        item.id,
        item.label,
        item.id === benchmarkReference
          ? '#10b981'
          : PALETTE[
              allSeries.findIndex((candidate) => candidate.id === item.id) % PALETTE.length
            ],
        {
          dashed: item.dashed,
          strokeWidth: item.id === benchmarkReference ? 2.5 : undefined,
        }
      )
    ),
    referenceSeriesId: benchmarkReference,
  };
}
