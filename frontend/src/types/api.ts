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
  data_source?: string;
  cache_path?: string;
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

export interface DatasetSummary {
  dataset_id: string;
  name: string;
  path: string;
  format: string;
  category: string;
  row_count: number;
  start_timestamp?: string | null;
  end_timestamp?: string | null;
  columns: string[];
  file_size_bytes: number;
  last_modified: string;
  data_fingerprint: string;
}

export interface DatasetDetail extends DatasetSummary {
  preview_rows: Array<Record<string, unknown>>;
  validation_warnings: string[];
}

export interface WalkForwardRequestPayload {
  config_path: string;
  strategies?: string[];
  train_window_days: number;
  test_window_days: number;
  step_days: number;
}

export interface WalkForwardStrategySummary {
  strategy_name: string;
  window_count: number;
  avg_train_total_return: number;
  avg_test_total_return: number;
  avg_test_sharpe_ratio: number;
  worst_test_drawdown: number;
}

export interface WalkForwardWindowResult {
  window_id: string;
  strategy_name: string;
  train_start: string;
  train_end: string;
  test_start: string;
  test_end: string;
  train_metrics: Record<string, number>;
  test_metrics: Record<string, number>;
}

export interface WalkForwardManifest {
  walkforward_id: string;
  created_at: string;
  config_path: string;
  strategy_names: string[];
  train_window_days: number;
  test_window_days: number;
  step_days: number;
  window_count: number;
  strategy_summaries: WalkForwardStrategySummary[];
}

export interface WalkForwardResultsPayload {
  walkforward_id: string;
  config_path: string;
  strategy_names: string[];
  train_window_days: number;
  test_window_days: number;
  step_days: number;
  window_count: number;
  strategy_summaries: WalkForwardStrategySummary[];
  results: WalkForwardWindowResult[];
}

export type MonteCarloMethod = 'bootstrap' | 'shuffle';

export interface MonteCarloRequestPayload {
  config_path?: string;
  run_id?: string;
  strategies?: string[];
  simulation_count: number;
  random_seed: number;
  method: MonteCarloMethod;
  ruin_threshold_pct: number;
}

export interface MonteCarloStrategySummary {
  strategy_name: string;
  trade_count: number;
  simulation_count: number;
  method: MonteCarloMethod;
  actual_final_equity: number;
  actual_total_return: number;
  actual_max_drawdown: number;
  loss_probability: number;
  ruin_probability: number;
  percentile_05_final_equity: number;
  median_final_equity: number;
  percentile_95_final_equity: number;
  percentile_05_total_return: number;
  median_total_return: number;
  percentile_95_total_return: number;
  percentile_05_max_drawdown: number;
  median_max_drawdown: number;
  percentile_95_max_drawdown: number;
  worst_final_equity: number;
  best_final_equity: number;
  warnings: string[];
}

export interface MonteCarloSimulationSummary {
  simulation_number: number;
  final_equity: number;
  total_return: number;
  max_drawdown: number;
  min_equity: number;
}

export interface MonteCarloStrategyResult extends MonteCarloStrategySummary {
  simulations: MonteCarloSimulationSummary[];
}

export interface MonteCarloManifest {
  montecarlo_id: string;
  created_at: string;
  config_path?: string | null;
  source_run_id: string;
  strategy_names: string[];
  simulation_count: number;
  random_seed: number;
  method: MonteCarloMethod;
  ruin_threshold_pct: number;
  warnings: string[];
  strategy_summaries: MonteCarloStrategySummary[];
}

export interface MonteCarloResultsPayload {
  montecarlo_id: string;
  config_path?: string | null;
  source_run_id: string;
  strategy_names: string[];
  simulation_count: number;
  random_seed: number;
  method: MonteCarloMethod;
  ruin_threshold_pct: number;
  warnings: string[];
  strategy_summaries: MonteCarloStrategySummary[];
  results: MonteCarloStrategyResult[];
}
