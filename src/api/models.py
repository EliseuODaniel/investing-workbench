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
