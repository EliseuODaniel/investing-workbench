import { LucideIcon } from 'lucide-react';
import { BenchmarkResult, EquityPoint, StrategyResult } from '../../types/api';

export type ChartTabId = 'equity' | 'drawdown' | 'cash' | 'trades';

export interface ChartsTabbedProps {
  results: Record<string, StrategyResult>;
  buyHoldEquity: EquityPoint[];
  visibleStrategies: string[];
  visibleBenchmarks: string[];
  benchmarks?: Record<string, BenchmarkResult>;
}

export interface ChartTabDefinition {
  id: ChartTabId;
  name: string;
  icon: LucideIcon;
  description: string;
}

export interface EquityChartPoint extends Record<string, string | number | null> {
  timestamp: string;
  date: string;
}

export interface DrawdownChartPoint extends Record<string, string | number> {
  timestamp: string;
  date: string;
}

export interface TradeScatterPoint {
  timestamp: Date;
  price: number;
  action: 'BUY' | 'SELL';
  strategy: string;
  pnl: number;
  layer: number;
  equity: number;
  color: string;
}

export interface ChartTabsNavProps {
  tabs: ChartTabDefinition[];
  activeTab: ChartTabId;
  onSelectTab: (tab: ChartTabId) => void;
}

export interface EquityChartPanelProps {
  results: Record<string, StrategyResult>;
  benchmarks?: Record<string, BenchmarkResult>;
  visibleStrategies: string[];
  visibleBenchmarks: string[];
  equityData: EquityChartPoint[];
  getStrategyColor: (strategyName: string) => string;
}

export interface DrawdownChartPanelProps {
  results: Record<string, StrategyResult>;
  visibleStrategies: string[];
  drawdownData: DrawdownChartPoint[];
}

export interface CashChartPanelProps {
  results: Record<string, StrategyResult>;
  visibleStrategies: string[];
  equityData: EquityChartPoint[];
  getStrategyColor: (strategyName: string) => string;
}

export interface TradesChartPanelProps {
  results: Record<string, StrategyResult>;
  visibleStrategies: string[];
  tradesData: TradeScatterPoint[];
  getStrategyColor: (strategyName: string) => string;
}

export interface ChartControlsFooterProps {
  description: string;
}
