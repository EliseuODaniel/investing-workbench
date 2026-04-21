import { BenchmarkResult, StrategyMetrics, StrategyResult } from '../../types/api';
import { TopPerformer } from './types';

type MetricKey = keyof StrategyMetrics;

export function getTopPerformer(
  results: Record<string, StrategyResult>,
  benchmarks: Record<string, BenchmarkResult> | undefined,
  metric: MetricKey,
  higherIsBetter = true,
): TopPerformer | null {
  const allItems: TopPerformer[] = [
    ...Object.entries(results).map(([name, data]) => ({
      name,
      value: data.metrics[metric] as number,
      type: 'strategy' as const,
    })),
    ...(benchmarks
      ? Object.entries(benchmarks).map(([name, data]) => ({
          name,
          value: data.metrics[metric] as number,
          type: 'benchmark' as const,
        }))
      : []),
  ];

  if (allItems.length === 0) {
    return null;
  }

  return allItems.reduce((best, current) => {
    if (current.value === null || current.value === undefined) {
      return best;
    }
    if (best.value === null || best.value === undefined) {
      return current;
    }

    return higherIsBetter
      ? current.value > best.value
        ? current
        : best
      : current.value < best.value
        ? current
        : best;
  });
}

export function getSelicAverageAnnualRate(result: StrategyResult) {
  const rates = result.metrics.selic_rates_used;
  if (!rates || rates.length === 0) {
    return null;
  }

  const grossReturn = rates.reduce((acc, rate) => acc * (1 + rate.rate), 1);
  return grossReturn ** (12 / rates.length) - 1;
}

export function getSelicPeriodLabel(result: StrategyResult) {
  const rates = result.metrics.selic_rates_used;
  if (!rates || rates.length === 0) {
    return null;
  }

  const normalizedPeriods = rates
    .map((rate) => {
      if (rate.period) {
        const [year, month] = rate.period.split('-');
        return {
          year: Number.parseInt(year, 10),
          month: Number.parseInt(month, 10),
        };
      }
      return {
        year: rate.year,
        month: rate.month,
      };
    })
    .filter(
      (value): value is { year: number; month: number } =>
        typeof value.year === 'number' &&
        !Number.isNaN(value.year) &&
        typeof value.month === 'number' &&
        !Number.isNaN(value.month)
    );

  if (normalizedPeriods.length === 0) {
    return null;
  }

  const years = normalizedPeriods.map((rate) => rate.year);
  const months = normalizedPeriods.map((rate) => rate.month);

  return `${Math.min(...years)}/${String(Math.min(...months)).padStart(2, '0')} - ${Math.max(...years)}/${String(Math.max(...months)).padStart(2, '0')}`;
}
