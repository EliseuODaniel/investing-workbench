"""Pydantic models for API request/response."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """Request model for backtest endpoint."""

    config_path: Optional[str] = Field(None, description="Path to config file")
    strategies: Optional[List[str]] = Field(None, description="Strategy names to run")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    initial_capital: Optional[float] = Field(None, description="Initial capital")
    base_bet: Optional[float] = Field(None, description="Base bet size")
    multiplier: Optional[float] = Field(None, description="Bet multiplier")
    drop_step: Optional[float] = Field(None, description="Price drop step")
    take_profit: Optional[float] = Field(None, description="Take profit percentage")
    max_layers: Optional[int] = Field(None, description="Maximum number of layers")
    data_source: Optional[str] = Field(None, description="Logical data source name")
    cache_path: Optional[str] = Field(None, description="Local dataset cache path to use")
    force_download: Optional[bool] = Field(False, description="Force data download")
    apply_cash_yield: Optional[bool] = Field(
        None, description="Enable cash yield based on SELIC rate"
    )
    selic_rate_annual: Optional[float] = Field(
        None, description="Annual SELIC rate (e.g., 0.13 for 13%)"
    )
    use_real_selic: Optional[bool] = Field(
        None, description="Use real monthly SELIC rates from file/download"
    )
    selic_path: Optional[str] = Field(None, description="Path to SELIC data file")
    selic_fallback_rate: Optional[float] = Field(
        None, description="Annual fallback rate when real data unavailable"
    )

    # Benchmark fields
    benchmarks: Optional[List[str]] = Field(
        None,
        description="Benchmark tickers to include (e.g., ['^BVSP', 'SPY'])",
    )
    include_selic_benchmark: Optional[bool] = Field(
        None, description="Include SELIC as a benchmark"
    )
    include_buy_hold_benchmark: Optional[bool] = Field(
        True, description="Include BTC Buy & Hold benchmark"
    )


class Trade(BaseModel):
    """Trade information."""

    timestamp: datetime
    action: str
    price: float
    quantity: float
    pnl: Optional[float] = None
    layer: Optional[int] = None


class EquityPoint(BaseModel):
    """Equity data point."""

    timestamp: datetime
    equity: float
    cash: float


class StrategyMetrics(BaseModel):
    """Strategy performance metrics."""

    total_return: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    hit_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_pnl: float
    volatility: float
    total_interest_earned: float = 0.0
    selic_rates_used: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="SELIC rates used when real SELIC is enabled",
    )


class StrategyResult(BaseModel):
    """Results for a single strategy."""

    strategy_name: str
    equity: List[EquityPoint]
    trades: List[Trade]
    metrics: StrategyMetrics
    start_price: float
    end_price: float


class BenchmarkResult(BaseModel):
    """Results for a benchmark."""

    name: str = Field(description="Benchmark display name")
    ticker: str = Field(description="Benchmark ticker symbol")
    equity: List[EquityPoint] = Field(description="Equity curve for the benchmark")
    metrics: StrategyMetrics = Field(description="Performance metrics for the benchmark")


class BacktestResponse(BaseModel):
    """Response model for backtest endpoint."""

    results: Dict[str, StrategyResult]
    buy_hold_equity: List[EquityPoint]
    benchmarks: Optional[Dict[str, BenchmarkResult]] = Field(
        None,
        description="Benchmark results",
    )
    run_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Information about the persisted run artifacts",
    )
    data_info: Dict[str, Any] = Field(description="Information about the data used")


class ConfigInfo(BaseModel):
    """Configuration file information."""

    name: str
    path: str
    display_name: str
    strategies: List[str] = Field(
        default_factory=list,
        description="Available strategies in this config",
    )


class DatasetSummaryModel(BaseModel):
    """Summary of a discovered local dataset."""

    dataset_id: str
    name: str
    path: str
    format: str
    category: str
    row_count: int
    start_timestamp: Optional[str]
    end_timestamp: Optional[str]
    columns: List[str]
    file_size_bytes: int
    last_modified: str
    data_fingerprint: str


class DatasetDetailModel(DatasetSummaryModel):
    """Detailed inspection payload for one local dataset."""

    preview_rows: List[Dict[str, Any]]
    validation_warnings: List[str]


class RunSummary(BaseModel):
    """Summary of a persisted run."""

    run_id: str
    created_at: str
    config_path: str
    artifact_dir: str
    strategy_names: List[str]
    benchmark_names: List[str]
    request_payload: Dict[str, Any]
    data_info: Dict[str, Any]
    config_snapshot_path: str
    data_profile_path: str
    data_fingerprint: str


class OptimizationPlanRequest(BaseModel):
    """Request model for optimization planning and execution."""

    config_path: str = Field(description="Path to config file")
    strategies: Optional[List[str]] = Field(
        None,
        description="Strategy names to include in the optimization job",
    )
    parameter_space: Dict[str, Any] = Field(
        default_factory=dict,
        description="Global search-space definition",
    )
    strategy_parameter_spaces: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-strategy search-space overrides",
    )
    mode: str = Field(default="grid", description="Optimization mode: grid or random")
    max_trials: Optional[int] = Field(None, description="Optional cap on generated trials")
    random_seed: int = Field(default=42, description="Random seed for deterministic planning")
    objective: str = Field(default="sharpe_ratio", description="Metric used for ranking")
    direction: str = Field(default="maximize", description="maximize or minimize")


class WalkForwardRequestModel(BaseModel):
    """Request model for walk-forward and out-of-sample validation."""

    config_path: str = Field(description="Path to config file")
    strategies: Optional[List[str]] = Field(
        None,
        description="Strategy names to include in validation",
    )
    train_window_days: int = Field(default=90, description="Rows per training window")
    test_window_days: int = Field(default=30, description="Rows per test window")
    step_days: int = Field(default=30, description="Rows to advance between windows")


class MonteCarloRequestModel(BaseModel):
    """Request model for Monte Carlo robustness analysis."""

    config_path: Optional[str] = Field(None, description="Path to config file")
    run_id: Optional[str] = Field(None, description="Existing persisted run to analyze")
    strategies: Optional[List[str]] = Field(
        None,
        description="Strategy names to include in the analysis",
    )
    simulation_count: int = Field(default=500, description="Number of Monte Carlo simulations")
    random_seed: int = Field(default=42, description="Random seed for deterministic sampling")
    method: str = Field(
        default="bootstrap",
        description="Monte Carlo sampling method: bootstrap or shuffle",
    )
    ruin_threshold_pct: float = Field(
        default=0.30,
        description="Drawdown threshold used to flag ruin probability",
    )
