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
  data_info: {
    start_date: string;
    end_date: string;
    total_days: number;
    initial_price: number;
    final_price: number;
  };
}