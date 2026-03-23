export interface ConfigInfo {
  name: string;
  path: string;
  display_name: string;
  strategies: string[];
}

export interface Trade {
  timestamp: string;
  action: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  pnl?: number | null;
  layer: number;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  cash: number;
}

export interface StrategyMetrics {
  total_return: number;
  cagr: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  hit_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_trade_pnl: number;
  volatility: number;
  total_interest_earned: number;
  selic_rates_used?: Array<{
    year: number;
    month: number;
    rate: number;
  }>;
}

export interface StrategyResult {
  strategy_name: string;
  equity: EquityPoint[];
  trades: Trade[];
  metrics: StrategyMetrics;
  start_price: number;
  end_price: number;
}

export interface BenchmarkResult {
  name: string;
  ticker: string;
  equity: EquityPoint[];
  metrics: StrategyMetrics;
}

export interface BacktestRequest {
  config_path?: string;
  strategies?: string[];
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  base_bet?: number;
  multiplier?: number;
  drop_step?: number;
  take_profit?: number;
  max_layers?: number;
  force_download?: boolean;
  apply_cash_yield?: boolean;
  selic_rate_annual?: number;
  use_real_selic?: boolean;
  selic_path?: string;
  selic_fallback_rate?: number;
  // Benchmark fields
  benchmarks?: string[];
  include_selic_benchmark?: boolean;
  include_buy_hold_benchmark?: boolean;
}

export interface BacktestResponse {
  results: Record<string, StrategyResult>;
  buy_hold_equity: EquityPoint[];
  benchmarks?: Record<string, BenchmarkResult>;
  run_info?: {
    run_id: string;
    artifact_dir: string;
    data_fingerprint?: string;
    manifest_path?: string;
    response_path?: string;
    config_snapshot_path?: string;
    data_profile_path?: string;
  };
  data_info: {
    start_date: string;
    end_date: string;
    total_days: number;
    initial_price: number;
    final_price: number;
  };
}

export interface BenchmarkConfigSnapshot {
  ticker: string;
  name: string;
  enabled: boolean;
}

export interface StrategyConfigSnapshot {
  name: string;
  class_path: string;
  parameters: Record<string, unknown>;
}

export interface RunConfigSnapshot {
  backtest: {
    initial_capital: number;
    start_date: string;
    end_date?: string | null;
    data_source: string;
    cache_path: string;
    output_dir: string;
    apply_cash_yield?: boolean;
    benchmarks?: BenchmarkConfigSnapshot[] | null;
    include_selic_benchmark?: boolean;
    include_buy_hold_benchmark?: boolean;
  };
  strategies: StrategyConfigSnapshot[];
  plotting?: Record<string, unknown> | null;
}

export interface RunDataProfile {
  asset: string;
  cache_path: string;
  row_count: number;
  columns: string[];
  index_name?: string | null;
  start_timestamp: string;
  end_timestamp: string;
  data_fingerprint: string;
}

export interface RunSummary {
  run_id: string;
  created_at: string;
  config_path: string;
  artifact_dir: string;
  strategy_names: string[];
  benchmark_names: string[];
  request_payload: Record<string, unknown>;
  data_info: Record<string, unknown>;
  config_snapshot_path: string;
  data_profile_path: string;
  data_fingerprint: string;
}

export interface ComparisonRun {
  summary: RunSummary;
  response: BacktestResponse;
}

export interface ComparisonRunOverview {
  runId: string;
  createdAt: string;
  configPath: string;
  strategyCount: number;
  totalTrades: number;
  bestStrategyName: string;
  bestReturn: number;
  bestSharpe: number;
  bestDrawdown: number;
  dataFingerprint: string;
}

export type OptimizationMode = 'grid' | 'random';
export type OptimizationDirection = 'maximize' | 'minimize';

export interface OptimizationRequestPayload {
  config_path: string;
  strategies?: string[];
  parameter_space: Record<string, unknown>;
  strategy_parameter_spaces: Record<string, Record<string, unknown>>;
  mode: OptimizationMode;
  max_trials?: number;
  random_seed: number;
  objective: string;
  direction: OptimizationDirection;
}

export interface OptimizationTrialCandidate {
  trial_id: string;
  strategy_name: string;
  parameters: Record<string, unknown>;
}

export interface OptimizationPlan {
  config_path: string;
  objective: string;
  direction: OptimizationDirection;
  mode: OptimizationMode;
  random_seed: number;
  strategy_names: string[];
  trial_count: number;
  truncated: boolean;
  warnings: string[];
  trials: OptimizationTrialCandidate[];
}

export interface OptimizationManifest {
  optimization_id: string;
  created_at: string;
  config_path: string;
  objective: string;
  direction: OptimizationDirection;
  mode: OptimizationMode;
  random_seed: number;
  strategy_names: string[];
  trial_count: number;
  completed_trial_count: number;
  truncated: boolean;
  warnings: string[];
  best_trial_id?: string | null;
  best_run_id?: string | null;
  best_objective_value?: number | null;
}

export interface OptimizationTrialResult {
  trial_id: string;
  strategy_name: string;
  parameters: Record<string, unknown>;
  run_id?: string | null;
  objective: string;
  objective_value?: number | null;
  metrics: Record<string, number | string | null | undefined>;
  status: 'completed' | 'failed';
  error?: string | null;
}

export interface OptimizationResultsPayload {
  optimization_id: string;
  objective: string;
  direction: OptimizationDirection;
  mode: OptimizationMode;
  random_seed: number;
  strategy_names: string[];
  trial_count: number;
  completed_trial_count: number;
  truncated: boolean;
  warnings: string[];
  ranked_results: OptimizationTrialResult[];
  results: OptimizationTrialResult[];
}
