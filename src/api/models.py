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
    fee_rate: Optional[float] = Field(None, description="Percentage fee applied to each trade")
    fixed_fee: Optional[float] = Field(None, description="Fixed fee applied to each trade")
    buy_slippage: Optional[float] = Field(
        None, description="Positive slippage applied to buy executions"
    )
    sell_slippage: Optional[float] = Field(
        None, description="Negative slippage applied to sell executions"
    )
    max_volume_participation: Optional[float] = Field(
        None,
        description="Optional share of bar volume the strategy may consume per bar",
    )
    allow_partial_fills: Optional[bool] = Field(
        None,
        description="Allow partial fills when liquidity is insufficient",
    )
    min_fill_quantity: Optional[float] = Field(
        None,
        description="Minimum executable quantity for a valid partial fill",
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
    cost: Optional[float] = None
    pnl: Optional[float] = None
    layer: Optional[int] = None
    requested_quantity: Optional[float] = None
    fill_ratio: Optional[float] = None


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
    total_fees_paid: float = 0.0
    total_dividends_received: float = 0.0
    selic_rates_used: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="SELIC rates used when real SELIC is enabled",
    )


class ExecutionEvent(BaseModel):
    """Detailed execution event captured during backtest order handling."""

    timestamp: datetime
    event_type: str
    side: str
    requested_quantity: float
    filled_quantity: float
    fill_ratio: float
    requested_price: float
    fill_price: Optional[float] = None
    fees: float = 0.0
    slippage: float = 0.0
    message: str


class ExecutionSummary(BaseModel):
    """Aggregate execution diagnostics for one strategy run."""

    fill_count: int = 0
    partial_fill_count: int = 0
    rejected_buy_count: int = 0
    rejected_sell_count: int = 0
    rejected_order_count: int = 0
    liquidity_constrained: bool = False
    requested_quantity_total: float = 0.0
    filled_quantity_total: float = 0.0


class StrategyResult(BaseModel):
    """Results for a single strategy."""

    strategy_name: str
    equity: List[EquityPoint]
    trades: List[Trade]
    metrics: StrategyMetrics
    start_price: float
    end_price: float
    execution_log: List[ExecutionEvent] = Field(default_factory=list)
    execution_summary: ExecutionSummary = Field(default_factory=ExecutionSummary)
    warnings: List[str] = Field(default_factory=list)


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
    warnings: List[str] = Field(default_factory=list)
    run_quality: Optional[Dict[str, Any]] = Field(
        None,
        description="Quality diagnostics for persisted runs that should not be trusted as-is",
    )


class ConfigInfo(BaseModel):
    """Configuration file information."""

    name: str
    path: str
    display_name: str
    strategies: List[str] = Field(
        default_factory=list,
        description="Available strategies in this config",
    )


class ArtifactCountsModel(BaseModel):
    """Counts of persisted artifact groups available to the local platform."""

    runs: int
    optimizations: int
    walkforward: int
    montecarlo: int
    pairs_backtests: int = 0
    research_workspaces: int
    allocation_workspaces: int


class BacktestJobCountsModel(BaseModel):
    """Counts of persisted async backtest jobs grouped by lifecycle state."""

    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0


class BacktestJobRuntimeModel(BaseModel):
    """Runtime summary for the async backtest execution layer."""

    execution_mode: str = "inline"
    max_workers: int = 0
    active_futures: int = 0


class BacktestJobProgressModel(BaseModel):
    """Progress payload exposed for async backtest jobs."""

    phase: str
    message: str
    percent: float
    updated_at: datetime
    current_step: Optional[int] = None
    total_steps: Optional[int] = None


class BacktestJobEventModel(BaseModel):
    """Lightweight event timeline for async backtest jobs."""

    timestamp: datetime
    level: str = "info"
    phase: str
    message: str
    percent: Optional[float] = None


class BacktestJobModel(BaseModel):
    """Persisted async backtest job exposed through the API."""

    job_id: str
    job_type: str = "backtest"
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    attempt_count: int = 1
    cancel_requested: bool = False
    request_payload: Dict[str, Any] = Field(default_factory=dict)
    config_path: Optional[str] = None
    strategy_names: List[str] = Field(default_factory=list)
    progress: BacktestJobProgressModel
    worker_id: Optional[str] = None
    run_id: Optional[str] = None
    result_available: bool = False
    error: Optional[str] = None
    events: List[BacktestJobEventModel] = Field(default_factory=list)


class PairsBacktestJobModel(BaseModel):
    """Persisted async pairs backtest job exposed through the API."""

    job_id: str
    job_type: str = "pairs_backtest"
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    attempt_count: int = 1
    cancel_requested: bool = False
    request_payload: Dict[str, Any] = Field(default_factory=dict)
    batch_mode: bool = False
    preset_id: Optional[str] = None
    requested_tickers: List[str] = Field(default_factory=list)
    progress: BacktestJobProgressModel
    worker_id: Optional[str] = None
    pairs_backtest_id: Optional[str] = None
    result_available: bool = False
    error: Optional[str] = None
    events: List[BacktestJobEventModel] = Field(default_factory=list)


class SystemStatusModel(BaseModel):
    """Operational snapshot for the local API and research workspace."""

    status: str
    api_version: str
    checked_at: datetime
    config_count: int
    dataset_count: int
    due_dataset_count: int = 0
    artifact_counts: ArtifactCountsModel
    job_counts: BacktestJobCountsModel = Field(default_factory=BacktestJobCountsModel)
    job_runtime: BacktestJobRuntimeModel = Field(default_factory=BacktestJobRuntimeModel)
    pairs_job_counts: BacktestJobCountsModel = Field(default_factory=BacktestJobCountsModel)
    pairs_job_runtime: BacktestJobRuntimeModel = Field(default_factory=BacktestJobRuntimeModel)
    latest_run_id: Optional[str] = None
    latest_backtest_job_id: Optional[str] = None
    latest_pairs_backtest_job_id: Optional[str] = None
    latest_pairs_backtest_id: Optional[str] = None
    latest_research_workspace_id: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class PairsUniverseResolveRequestModel(BaseModel):
    """Request model for resolving a B3 pairs-trading universe."""

    preset_id: str = Field(default="ibov_proxy", description="Curated universe preset")
    tickers: List[str] = Field(default_factory=list, description="Optional custom B3 tickers")
    sector_overrides: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional sector/group overrides for custom or known tickers",
    )
    as_of_date: Optional[str] = Field(
        default=None,
        description="Optional logical as-of date used by universe resolution",
    )
    start_date: str = Field(default="2021-01-01", description="Data start date")
    end_date: Optional[str] = Field(default=None, description="Optional data end date")
    force_download: bool = Field(default=False, description="Force data refresh")
    min_price: float = Field(default=5.0, gt=0.0, description="Minimum acceptable price")
    min_median_notional_brl: float = Field(
        default=90000000.0,
        gt=0.0,
        description="Minimum median daily notional in BRL",
    )
    use_proxy_short_borrow: bool = Field(
        default=True,
        description="Use proxy short-borrow heuristics when filtering the universe",
    )
    proxy_borrow_base_rate_annual: float = Field(default=0.03, ge=0.0)
    proxy_borrow_max_rate_annual: float = Field(default=0.12, ge=0.0)
    proxy_min_short_score: float = Field(default=0.35, ge=0.0, le=1.0)
    proxy_borrow_vol_floor: float = Field(default=0.20, ge=0.0)
    proxy_borrow_vol_cap: float = Field(default=0.80, ge=0.0)
    borrow_snapshot_path: Optional[str] = Field(
        default=None,
        description="Optional local CSV with ticker borrow overrides",
    )


class PairsScreenRequestModel(PairsUniverseResolveRequestModel):
    """Request model for screening candidate B3 pairs."""

    formation_window: int = Field(default=252, ge=30)
    test_window: int = Field(default=21, ge=1)
    max_pairs: int = Field(default=3, ge=1)
    top_n: int = Field(default=20, ge=1, le=100)
    min_return_corr: float = Field(default=0.25, ge=-1.0, le=1.0)
    min_level_corr: float = Field(default=0.10, ge=-1.0, le=1.0)
    max_coint_pvalue: float = Field(default=0.10, ge=0.0, le=1.0)
    min_half_life: float = Field(default=2.0, gt=0.0)
    max_half_life: float = Field(default=60.0, gt=0.0)
    min_stability_score: float = Field(default=0.35, ge=0.0, le=1.0)
    max_structural_break_risk: float = Field(default=0.75, ge=0.0, le=1.0)
    min_beta_abs: float = Field(default=0.10, ge=0.0)
    max_beta_abs: float = Field(default=3.0, gt=0.0)
    require_cointegration: bool = Field(default=True)


class PairsScenarioVariantModel(BaseModel):
    """Custom scenario variant for one pairs backtest batch."""

    scenario_id: str
    label: str
    require_cointegration: bool = True
    overrides: Dict[str, Any] = Field(default_factory=dict)


class PairsBacktestRequestModel(PairsScreenRequestModel):
    """Request model for executing a B3 pairs-trading backtest."""

    step_window: int = Field(default=21, ge=1)
    entry_zscore: float = Field(default=2.0, gt=0.0)
    exit_zscore: float = Field(default=0.5, ge=0.0)
    stop_zscore: float = Field(default=4.0, gt=0.0)
    max_holding_days: int = Field(default=30, ge=1)
    pair_allocation_pct: float = Field(default=0.30, gt=0.0, le=1.0)
    initial_capital: float = Field(default=100000.0, gt=0.0)
    zscore_window: int = Field(default=60, ge=10)
    fee_rate: float = Field(default=0.0003, ge=0.0)
    slippage: float = Field(default=0.0005, ge=0.0)
    short_borrow_rate_annual: float = Field(default=0.05, ge=0.0)
    apply_cash_yield: bool = Field(default=False)
    use_real_selic: bool = Field(default=False)
    selic_path: str = Field(default="data/selic_daily.csv")
    selic_fallback_rate: float = Field(default=0.13, ge=0.0)
    cash_collateral_ratio: float = Field(default=1.0, ge=0.0)
    explicit_margin_model: bool = Field(default=False)
    short_margin_haircut: float = Field(default=0.50, ge=0.0)
    dynamic_beta: bool = Field(default=False)
    rolling_beta_window: int = Field(default=60, ge=10)
    regime_filter: str = Field(default="none")
    regime_ma_window: int = Field(default=63, ge=5)
    regime_max_deviation: float = Field(default=0.08, ge=0.0)
    regime_vol_window: int = Field(default=21, ge=5)
    regime_vol_lookback: int = Field(default=252, ge=21)
    regime_vol_quantile: float = Field(default=0.75, ge=0.0, le=1.0)
    portfolio_construction: str = Field(default="equal_notional")
    target_pair_volatility_annual: float = Field(default=0.18, ge=0.0)
    max_gross_exposure_pct: float = Field(default=1.50, gt=0.0)
    max_net_exposure_pct: float = Field(default=0.20, ge=0.0)
    max_sector_pairs: int = Field(default=1, ge=1)
    benchmark_ids: List[str] = Field(default_factory=list)
    scenario_label: str = Field(default="Realistic cointegration")
    scenario_id: str = Field(default="realistic_cointegration")


class PairsBatchRequestModel(PairsBacktestRequestModel):
    """Request model for running a multi-scenario pairs-trading batch."""

    scenario_variants: List[PairsScenarioVariantModel] = Field(default_factory=list)


class PairsIbovBackfillRequestModel(BaseModel):
    """Request model for backfilling official IBOV snapshots."""

    start_date: str = Field(description="Inclusive start date for snapshot backfill")
    end_date: str = Field(description="Inclusive end date for snapshot backfill")
    force_refresh: bool = Field(default=False, description="Refresh cached snapshots")


class PairsIbovSnapshotModel(BaseModel):
    """Cached official IBOV snapshot payload."""

    index_id: str
    snapshot_id: str
    as_of_date: str
    source_kind: str
    source_url: str
    validity_label: Optional[str] = None
    ticker_count: int
    tickers: List[str] = Field(default_factory=list)
    constituents: List[Dict[str, Any]] = Field(default_factory=list)
    imported_at: str


class PairsIbovBackfillResponseModel(BaseModel):
    """Summary of one IBOV snapshot backfill operation."""

    index_id: str
    start_date: str
    end_date: str
    snapshot_count: int
    snapshots: List[Dict[str, Any]] = Field(default_factory=list)


class PairsUniversePayloadModel(BaseModel):
    """Resolved pairs universe payload."""

    preset: Optional[Dict[str, Any]] = None
    requested_tickers: List[str] = Field(default_factory=list)
    as_of_date: Optional[str] = None
    resolved_as_of_date: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    common_index_start: Optional[str] = None
    common_index_end: Optional[str] = None
    common_index_days: int = 0
    quality_report: Dict[str, Any] = Field(default_factory=dict)
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    eligible_assets: List[Dict[str, Any]] = Field(default_factory=list)
    unavailable_tickers: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class PairsScreenPayloadModel(BaseModel):
    """Pairs screener response payload."""

    preset: Optional[Dict[str, Any]] = None
    requested_tickers: List[str] = Field(default_factory=list)
    resolved_as_of_date: Optional[str] = None
    screening_window: Dict[str, Any] = Field(default_factory=dict)
    criteria: Dict[str, Any] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)
    quality_report: Dict[str, Any] = Field(default_factory=dict)
    selected_pairs: List[Dict[str, Any]] = Field(default_factory=list)
    candidate_pairs: List[Dict[str, Any]] = Field(default_factory=list)
    rejected_pairs: List[Dict[str, Any]] = Field(default_factory=list)
    rejection_summary: Dict[str, int] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class PairsBacktestManifestModel(BaseModel):
    """Persisted summary for one pairs-trading execution."""

    pairs_backtest_id: str
    created_at: str
    preset_id: str
    preset_label: str
    universe_as_of_date: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    requested_tickers: List[str] = Field(default_factory=list)
    available_tickers: List[str] = Field(default_factory=list)
    eligible_tickers: List[str] = Field(default_factory=list)
    scenario_count: int
    batch_mode: bool = False
    benchmark_ids: List[str] = Field(default_factory=list)
    candidate_pair_count: int = 0
    reconstitution_segment_count: int = 0
    warnings: List[str] = Field(default_factory=list)


class PairsBacktestResultsModel(BaseModel):
    """Detailed result payload for one pairs-trading execution."""

    pairs_backtest_id: str
    created_at: str
    manifest: Dict[str, Any] = Field(default_factory=dict)
    preset: Optional[Dict[str, Any]] = None
    universe: Dict[str, Any] = Field(default_factory=dict)
    candidate_pairs: List[Dict[str, Any]] = Field(default_factory=list)
    benchmarks: List[Dict[str, Any]] = Field(default_factory=list)
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    robustness_report: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class Wege3RegraARunRequestModel(BaseModel):
    """Request model for the dedicated WEGE3 Regra A scenario."""

    start_date: str = Field(default="2021-01-01")
    end_date: Optional[str] = Field(default=None)
    force_download: bool = Field(default=False)


class Wege3RegraATradeModel(BaseModel):
    """Trade-level audit row for the WEGE3 Regra A scenario."""

    timestamp: str
    action: str
    price: float
    notional: float
    quantity: float
    cash_after: float
    position_after: float
    reference_after: float


class Wege3RegraAArtifactsModel(BaseModel):
    """Generated artifact locations for the WEGE3 Regra A scenario."""

    summary_output_path: str
    trades_output_path: str
    comparison_output_path: Optional[str] = None
    comparison_trades_output_path: Optional[str] = None
    search_output_path: Optional[str] = None


class Wege3RegraAScenarioResponseModel(BaseModel):
    """Detailed WEGE3 Regra A scenario payload exposed through the API."""

    scenario_id: str
    scenario_label: str
    generated_at: datetime
    request: Dict[str, Any] = Field(default_factory=dict)
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    dataset: Dict[str, Any] = Field(default_factory=dict)
    result: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    benchmarks: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    audit: Dict[str, Any] = Field(default_factory=dict)
    comparison_variants: List[Dict[str, Any]] = Field(default_factory=list)
    best_strategy: Dict[str, Any] = Field(default_factory=dict)
    parameter_search: Dict[str, Any] = Field(default_factory=dict)
    strategy_context: Dict[str, Any] = Field(default_factory=dict)
    comparison_chart: Dict[str, Any] = Field(default_factory=dict)
    trades: List[Wege3RegraATradeModel] = Field(default_factory=list)
    artifacts: Wege3RegraAArtifactsModel
    reproduction_command: str


class InvestmentCatalogRequestModel(BaseModel):
    """Optional catalog query parameters for the investment comparison workspace."""

    include_presets: bool = Field(default=True)


class InvestmentPortfolioComponentRequestModel(BaseModel):
    """One weighted sleeve inside a custom portfolio request."""

    component_id: str = Field(min_length=1)
    weight: float = Field(gt=0.0)


class InvestmentCustomPortfolioRequestModel(BaseModel):
    """User-defined portfolio to compare against guided presets and single assets."""

    portfolio_id: Optional[str] = None
    label: str = Field(min_length=1)
    description: Optional[str] = None
    rebalance_frequency: str = Field(default="monthly")
    components: List[InvestmentPortfolioComponentRequestModel] = Field(
        default_factory=list,
        min_length=1,
    )


class InvestmentDecisionProfileRequestModel(BaseModel):
    """Optional investor profile used to rank didactic decision guidance."""

    objective: str = Field(default="balanced")
    horizon_years: int = Field(default=5, ge=1, le=40)
    liquidity_need: str = Field(default="monthly")
    mark_to_market_tolerance: str = Field(default="medium")
    tax_view: str = Field(default="gross")
    monthly_income_target: float = Field(default=0.0, ge=0.0)


class InvestmentCompareRequestModel(BaseModel):
    """Request model for comparing historical B3 investment alternatives."""

    asset_ids: List[str] = Field(default_factory=list)
    custom_portfolios: List[InvestmentCustomPortfolioRequestModel] = Field(default_factory=list)
    start_date: str = Field(default="2021-01-01")
    end_date: Optional[str] = Field(default=None)
    initial_capital: float = Field(default=10000.0, gt=0.0)
    monthly_contribution: float = Field(default=0.0, ge=0.0)
    benchmark_ids: List[str] = Field(default_factory=list)
    fixed_income_study_mode: str = Field(default="auto")
    fixed_income_tax_treatment: str = Field(default="gross")
    fixed_income_window_frequency: str = Field(default="monthly")
    decision_profile: InvestmentDecisionProfileRequestModel = Field(
        default_factory=InvestmentDecisionProfileRequestModel
    )
    force_download: bool = Field(default=False)


class InvestmentMarketRankingsRequestModel(BaseModel):
    """Request model for a market-rankings snapshot over a preset or custom universe."""

    preset_id: str = Field(default="first_steps")
    asset_ids: List[str] = Field(default_factory=list)
    start_date: str = Field(default="2021-01-01")
    end_date: Optional[str] = Field(default=None)
    initial_capital: float = Field(default=10000.0, gt=0.0)
    monthly_contribution: float = Field(default=0.0, ge=0.0)
    benchmark_ids: List[str] = Field(default_factory=lambda: ["selic_cash"])
    decision_profile: InvestmentDecisionProfileRequestModel = Field(
        default_factory=InvestmentDecisionProfileRequestModel
    )
    force_download: bool = Field(default=False)


class InvestmentProductDataRefreshRequestModel(BaseModel):
    """Request model for refreshing one product-data source."""

    source_id: str = Field(default="b3_fii_listed")
    force: bool = Field(default=False)


class InvestmentProductDataRefreshResponseModel(BaseModel):
    """Response payload for one product-data source refresh."""

    source_id: str
    status: str
    status_label: str
    message: str
    manifest: Optional[Dict[str, Any]] = Field(default=None)
    history: List[Dict[str, Any]] = Field(default_factory=list)


class InvestmentCatalogResponseModel(BaseModel):
    """Catalog payload for the didactic B3 investment comparison experience."""

    generated_at: datetime
    categories: List[Dict[str, Any]] = Field(default_factory=list)
    instruments: List[Dict[str, Any]] = Field(default_factory=list)
    presets: List[Dict[str, Any]] = Field(default_factory=list)
    benchmark_options: List[Dict[str, Any]] = Field(default_factory=list)
    market_explorer: Dict[str, Any] = Field(default_factory=dict)
    investor_easy_parity: Dict[str, Any] = Field(default_factory=dict)
    product_data_plan: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)
    sources: List[Dict[str, str]] = Field(default_factory=list)


class InvestmentCompareResponseModel(BaseModel):
    """Result payload for one cross-asset B3 comparison run."""

    generated_at: datetime
    request: Dict[str, Any] = Field(default_factory=dict)
    catalog_snapshot: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)
    benchmarks: List[Dict[str, Any]] = Field(default_factory=list)
    chart: Dict[str, Any] = Field(default_factory=dict)
    real_chart: Dict[str, Any] = Field(default_factory=dict)
    inflation: Dict[str, Any] = Field(default_factory=dict)
    class_summary: List[Dict[str, Any]] = Field(default_factory=list)
    highlights: Dict[str, Any] = Field(default_factory=dict)
    fixed_income_backtest: Optional[Dict[str, Any]] = Field(default=None)
    methodology_guide: Dict[str, Any] = Field(default_factory=dict)
    product_realism: Dict[str, Any] = Field(default_factory=dict)
    retail_fixed_income_equivalence: Dict[str, Any] = Field(default_factory=dict)
    result_stories: Dict[str, Any] = Field(default_factory=dict)
    market_rankings: Dict[str, Any] = Field(default_factory=dict)
    market_screeners: Dict[str, Any] = Field(default_factory=dict)
    cache_status: Dict[str, Any] = Field(default_factory=dict)
    fixed_income_decision_guide: Optional[Dict[str, Any]] = Field(default=None)
    portfolio_objective_summary: Dict[str, Any] = Field(default_factory=dict)
    portfolio_lifecycle: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class InvestmentMarketRankingsResponseModel(BaseModel):
    """Compact market explorer ranking payload."""

    generated_at: datetime
    request: Dict[str, Any] = Field(default_factory=dict)
    market_rankings: Dict[str, Any] = Field(default_factory=dict)
    market_screeners: Dict[str, Any] = Field(default_factory=dict)
    cache_status: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class SavedInvestmentPortfolioModel(BaseModel):
    """Reusable custom portfolio saved by the investments workspace."""

    portfolio_id: Optional[str] = Field(default=None)
    label: str
    description: Optional[str] = Field(default=None)
    rebalance_frequency: Optional[str] = Field(default="monthly")
    components: List[InvestmentPortfolioComponentRequestModel] = Field(default_factory=list)
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)


class SavedPairsRadarItemModel(BaseModel):
    """Saved pairs-trading radar favorite."""

    pairs_backtest_id: str
    label: str
    preset_label: str
    created_at: str
    saved_at: Optional[str] = Field(default=None)
    scenario_count: int = Field(default=0, ge=0)
    candidate_pair_count: int = Field(default=0, ge=0)
    benchmark_ids: List[str] = Field(default_factory=list)


class SavedStrategyRadarItemModel(BaseModel):
    """Saved strategy radar favorite."""

    strategy_id: str
    label: str
    family: str
    direction: str
    parameter_values: Dict[str, Any] = Field(default_factory=dict)
    universe: List[str] = Field(default_factory=list)
    timeframe: Optional[str] = Field(default=None)
    setup_notes: List[str] = Field(default_factory=list)
    saved_at: Optional[str] = Field(default=None)


class StrategySetupPlanModel(BaseModel):
    """Prepared execution plan for a saved strategy setup draft."""

    plan_id: str
    strategy_id: str
    label: str
    family: str
    timeframe: str
    route_hint: str
    readiness: str
    run_request: Dict[str, Any]
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    setup_notes: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    generated_at: str


class SavedStrategySetupRunModel(BaseModel):
    """Persisted execution summary for a strategy setup."""

    strategy_id: str
    run_id: Optional[str] = Field(default=None)
    pairs_backtest_id: Optional[str] = Field(default=None)
    ran_at: str
    strategy_count: int = Field(default=0, ge=0)
    best_strategy: Optional[str] = Field(default=None)
    total_return: Optional[float] = Field(default=None)
    max_drawdown: Optional[float] = Field(default=None)
    trade_count: Optional[int] = Field(default=None, ge=0)
    route_hint: str = Field(default="/backtest")
    saved_at: Optional[str] = Field(default=None)


class StrategySetupScoreModel(BaseModel):
    """Explainable score for a strategy setup based on latest execution."""

    strategy_id: str
    label: str
    score: float
    total_return: float
    max_drawdown: float
    trade_count: int = Field(default=0, ge=0)
    run_count: int = Field(default=0, ge=0)
    route_hint: str
    run_id: Optional[str] = Field(default=None)
    pairs_backtest_id: Optional[str] = Field(default=None)
    return_score: float
    drawdown_penalty: float
    execution_score: float
    robustness_score: float
    data_validity_score: float
    ran_at: str
    methodology: str


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
    refresh_due: bool = False
    next_refresh_due_at: Optional[str] = None


class DatasetDetailModel(DatasetSummaryModel):
    """Detailed inspection payload for one local dataset."""

    preview_rows: List[Dict[str, Any]]
    validation_warnings: List[str]
    validation: Optional[Dict[str, Any]]
    provenance: Optional[Dict[str, Any]]


class DatasetImportRequest(BaseModel):
    """Request model for importing a local dataset into the data catalog."""

    source_path: str = Field(description="Absolute or relative path to the source file")
    dataset_name: Optional[str] = Field(
        None,
        description="Optional destination filename or stem inside data/",
    )
    overwrite: bool = Field(default=False, description="Overwrite existing dataset if present")


class DatasetRefreshRequest(BaseModel):
    """Request model for refreshing a supported dataset."""

    start_date: str = Field(default="2020-01-01", description="Refresh start date")
    end_date: Optional[str] = Field(None, description="Refresh end date")


class DatasetRefreshPolicyRequest(BaseModel):
    """Request model for a persisted dataset refresh policy."""

    enabled: bool = Field(description="Whether scheduled refresh checks are enabled")
    interval_days: int = Field(default=7, ge=1, description="Days between refreshes")
    start_date: str = Field(default="2020-01-01", description="Refresh start date")
    end_date: Optional[str] = Field(None, description="Optional refresh end date")


class DatasetRefreshDueRequest(BaseModel):
    """Request model for refreshing due datasets in batch."""

    limit: Optional[int] = Field(
        None,
        ge=1,
        description="Optional cap on the number of due datasets to refresh",
    )


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
    run_quality: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional quality issue detected for this persisted run",
    )


class AllocationHoldingModel(BaseModel):
    """Current holding used for allocation planning."""

    asset: str = Field(description="Asset identifier, such as BTC-BRL or SPY")
    quantity: float = Field(ge=0.0, description="Current quantity held")


class AllocationTargetModel(BaseModel):
    """Target portfolio weight for one asset."""

    asset: str = Field(description="Asset identifier, such as BTC-BRL or SPY")
    target_weight: float = Field(ge=0.0, le=1.0, description="Desired portfolio weight")


class AllocationPlanRequestModel(BaseModel):
    """Request model for portfolio rebalance planning."""

    cash: float = Field(ge=0.0, description="Current available cash")
    holdings: List[AllocationHoldingModel] = Field(
        default_factory=list,
        description="Current holdings and quantities",
    )
    prices: Dict[str, float] = Field(
        default_factory=dict,
        description="Latest asset prices keyed by symbol",
    )
    targets: List[AllocationTargetModel] = Field(
        default_factory=list,
        description="Target asset weights that should sum to at most 1.0",
    )
    weight_tolerance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Skip trades when the drift is within this absolute weight tolerance",
    )
    min_trade_notional: float = Field(
        default=0.0,
        ge=0.0,
        description="Skip trades smaller than this notional amount",
    )
    reserve_cash: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum cash that must remain after the rebalance",
    )


class AllocationActionModel(BaseModel):
    """One asset-level rebalance recommendation."""

    asset: str
    action: str
    price: float
    current_quantity: float
    current_value: float
    current_weight: float
    target_quantity: float
    target_value: float
    target_weight: float
    quantity_delta: float
    notional_delta: float
    drift_weight: float
    projected_quantity: float
    reason: str


class AllocationPlanResponseModel(BaseModel):
    """Response model for a rebalance plan."""

    total_equity: float
    current_cash: float
    target_cash: float
    projected_cash: float
    current_cash_weight: float
    target_cash_weight: float
    turnover_notional: float
    turnover_ratio: float
    cash_gap_to_target: float
    max_abs_drift_weight: float
    needs_rebalance: bool
    actions: List[AllocationActionModel]
    warnings: List[str] = Field(default_factory=list)


class AllocationWorkspaceSummaryModel(BaseModel):
    """Summary fields exposed for a saved allocation workspace."""

    asset_count: int
    assets: List[str] = Field(default_factory=list)
    buy_count: int
    sell_count: int
    hold_count: int
    needs_rebalance: bool
    turnover_ratio: float
    turnover_notional: float
    total_equity: float
    current_cash_weight: float
    target_cash_weight: float
    projected_cash: float
    reserve_cash: float
    max_abs_drift_weight: float


class AllocationWorkspaceModel(BaseModel):
    """Saved allocation workspace payload."""

    workspace_id: str
    created_at: str
    name: str
    notes: Optional[str] = None
    request: AllocationPlanRequestModel
    plan: AllocationPlanResponseModel
    summary: AllocationWorkspaceSummaryModel


class AllocationWorkspaceCreateRequestModel(BaseModel):
    """Request model for saving an allocation workspace."""

    name: Optional[str] = Field(None, description="Optional workspace label")
    notes: Optional[str] = Field(None, description="Optional user notes")
    request: AllocationPlanRequestModel = Field(description="Rebalance planning request payload")


class AllocationWorkspaceUpdateRequestModel(BaseModel):
    """Request model for editable allocation workspace metadata."""

    name: Optional[str] = Field(None, description="Updated workspace label")
    notes: Optional[str] = Field(None, description="Updated workspace notes")


class AllocationWorkspaceImportRequestModel(BaseModel):
    """Request model for importing an exported allocation workspace JSON."""

    payload: Dict[str, Any] = Field(description="Previously exported allocation workspace payload")


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


class ResearchWorkspaceCreateRequestModel(BaseModel):
    """Request model for saving a research workspace selection."""

    name: Optional[str] = Field(None, description="Optional workspace label")
    notes: Optional[str] = Field(None, description="Optional user notes")
    selected_experiment_type: str = Field(description="Primary experiment type")
    selected_experiment_id: str = Field(description="Primary experiment identifier")
    optimization_id: Optional[str] = Field(None, description="Chosen optimization experiment id")
    walkforward_id: Optional[str] = Field(None, description="Chosen walk-forward experiment id")
    montecarlo_id: Optional[str] = Field(None, description="Chosen Monte Carlo experiment id")
    anchor_run_id: Optional[str] = Field(None, description="Chosen anchor run id")


class ResearchWorkspaceUpdateRequestModel(BaseModel):
    """Request model for editable saved workspace metadata."""

    name: Optional[str] = Field(None, description="Updated workspace label")
    notes: Optional[str] = Field(None, description="Updated workspace notes")


class ResearchWorkspaceImportRequestModel(BaseModel):
    """Request model for importing an exported research workspace JSON."""

    payload: Dict[str, Any] = Field(description="Previously exported workspace payload")
