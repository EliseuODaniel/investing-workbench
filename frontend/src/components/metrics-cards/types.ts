import { ReactNode } from 'react';
import { BenchmarkResult, StrategyResult } from '../../types/api';

export interface MetricsCardsProps {
  results: Record<string, StrategyResult>;
  benchmarks?: Record<string, BenchmarkResult>;
}

export interface TopPerformer {
  name: string;
  value: number;
  type: 'strategy' | 'benchmark';
}

export interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: ReactNode;
  isTopPerformer?: boolean;
  topPerformerLabel?: string;
}

export interface TopPerformersSummaryProps {
  topReturn: TopPerformer | null;
  topSharpe: TopPerformer | null;
  topHitRate: TopPerformer | null;
  lowestDrawdown: TopPerformer | null;
}

export interface StrategyMetricsSectionProps {
  results: Record<string, StrategyResult>;
  topReturn: TopPerformer | null;
  topSharpe: TopPerformer | null;
  topHitRate: TopPerformer | null;
  lowestDrawdown: TopPerformer | null;
}

export interface BenchmarkMetricsSectionProps {
  benchmarks?: Record<string, BenchmarkResult>;
}
