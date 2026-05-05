export interface ConfigInfo {
  name: string;
  path: string;
  display_name: string;
  strategies: string[];
}

export interface SystemArtifactCountsPayload {
  runs: number;
  optimizations: number;
  walkforward: number;
  montecarlo: number;
  pairs_backtests: number;
  research_workspaces: number;
  allocation_workspaces: number;
}

export interface BacktestJobCountsPayload {
  queued: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
}

export interface BacktestJobRuntimePayload {
  execution_mode: 'inline' | 'detached' | string;
  max_workers: number;
  active_futures: number;
}

export interface SystemStatusPayload {
  status: 'ok' | 'degraded';
  api_version: string;
  checked_at: string;
  config_count: number;
  dataset_count: number;
  due_dataset_count: number;
  artifact_counts: SystemArtifactCountsPayload;
  job_counts: BacktestJobCountsPayload;
  job_runtime: BacktestJobRuntimePayload;
  pairs_job_counts: BacktestJobCountsPayload;
  pairs_job_runtime: BacktestJobRuntimePayload;
  latest_run_id?: string | null;
  latest_backtest_job_id?: string | null;
  latest_pairs_backtest_job_id?: string | null;
  latest_pairs_backtest_id?: string | null;
  latest_research_workspace_id?: string | null;
  warnings: string[];
}

export interface InvestmentCategoryPayload {
  category_id: string;
  label: string;
  count: number;
}

export interface InvestmentInstrumentPayload {
  instrument_id: string;
  label: string;
  ticker?: string | null;
  category_id: string;
  category_label: string;
  description: string;
  rationale: string;
  risk_label: string;
  region_label: string;
  source_kind: string;
  listed_on_b3: boolean;
  uses_adjusted_close: boolean;
  available_since?: string | null;
  rebalance_frequency?: string | null;
  implementation_note?: string | null;
  product_profile?: {
    investment_type_label: string;
    liquidity_label: string;
    tax_treatment_label: string;
    income_policy_label: string;
    fee_model_label: string;
    data_quality_label: string;
    investability_label: string;
  };
  components: Array<{ component_id: string; weight: number }>;
  notes: string[];
}

export interface InvestmentPresetPayload {
  preset_id: string;
  label: string;
  description: string;
  asset_ids: string[];
  goal_label: string;
  default_start_date?: string | null;
  default_end_date?: string | null;
  default_initial_capital?: number | null;
  default_monthly_contribution?: number | null;
  default_benchmark_ids?: string[] | null;
  default_fixed_income_study_mode?: string | null;
  default_fixed_income_tax_treatment?: string | null;
  default_fixed_income_window_frequency?: string | null;
}

export interface InvestmentBenchmarkOptionPayload {
  benchmark_id: string;
  label: string;
  description: string;
}

export interface InvestmentPortfolioComponentPayload {
  component_id: string;
  weight: number;
}

export interface InvestmentCustomPortfolioRequestPayload {
  portfolio_id?: string | null;
  label: string;
  description?: string | null;
  rebalance_frequency?: string | null;
  components: InvestmentPortfolioComponentPayload[];
}

export interface SavedInvestmentPortfolioPayload
  extends InvestmentCustomPortfolioRequestPayload {
  portfolio_id: string;
  created_at: string;
  updated_at: string;
}

export interface SavedStrategyRadarItemPayload {
  strategy_id: string;
  label: string;
  family: string;
  direction: string;
  parameter_values?: Record<string, string | number | boolean | null>;
  universe?: string[];
  timeframe?: string | null;
  setup_notes?: string[];
  saved_at?: string | null;
}

export interface StrategySetupPlanPayload {
  plan_id: string;
  strategy_id: string;
  label: string;
  family: string;
  timeframe: string;
  route_hint: string;
  readiness: string;
  run_request: Record<string, unknown>;
  assumptions: string[];
  warnings: string[];
  setup_notes: string[];
  next_actions: string[];
  generated_at: string;
}

export interface SavedStrategySetupRunPayload {
  strategy_id: string;
  run_id?: string | null;
  pairs_backtest_id?: string | null;
  ran_at: string;
  strategy_count: number;
  best_strategy?: string | null;
  total_return?: number | null;
  max_drawdown?: number | null;
  trade_count?: number | null;
  route_hint: string;
  saved_at?: string | null;
}

export interface StrategySetupScorePayload {
  strategy_id: string;
  label: string;
  score: number;
  total_return: number;
  max_drawdown: number;
  trade_count: number;
  run_count: number;
  route_hint: string;
  run_id?: string | null;
  pairs_backtest_id?: string | null;
  return_score: number;
  drawdown_penalty: number;
  execution_score: number;
  robustness_score: number;
  data_validity_score: number;
  ran_at: string;
  methodology: string;
}

export interface InvestmentPortfolioContributionPayload {
  component_id?: string;
  label?: string;
  category_id?: string;
  category_label: string;
  target_weight: number;
  ending_weight: number;
  final_value: number;
}

export interface InvestmentCatalogPayload {
  generated_at: string;
  categories: InvestmentCategoryPayload[];
  instruments: InvestmentInstrumentPayload[];
  presets: InvestmentPresetPayload[];
  benchmark_options: InvestmentBenchmarkOptionPayload[];
  market_explorer?: {
    title: string;
    plain_language_summary: string;
    category_lists: Array<{
      list_id: string;
      label: string;
      count: number;
      sample_instrument_ids: string[];
      sample_labels: string[];
    }>;
    curated_lists?: Array<{
      list_id: string;
      label: string;
      description: string;
      count: number;
      instrument_ids: string[];
      sample_labels: string[];
      risk_labels: string[];
    }>;
    product_type_facets: Array<{
      source_kind: string;
      label: string;
      count: number;
    }>;
    risk_facets: Array<{ facet_id: string; label: string; count: number }>;
    region_facets: Array<{ facet_id: string; label: string; count: number }>;
    product_data_filters?: Array<{
      filter_id: string;
      label: string;
      source_id: string;
      status: string;
      options: Array<{ value: string; label: string; count: number }>;
    }>;
    product_data_screeners?: Array<{
      screener_id: string;
      label: string;
      source_id: string;
      status: string;
      methodology: string;
      rows: Array<{
        instrument_id: string;
        label: string;
        ticker?: string | null;
        segment?: string | null;
        listing_status?: string | null;
        yield_12m_pct?: number | null;
        liquidity_label?: string | null;
        income_focus?: string | null;
        data_quality_score?: number | null;
      }>;
    }>;
    product_data_rankings?: Array<{
      ranking_id: string;
      label: string;
      source_id: string;
      status: string;
      methodology: string;
      rows: Array<{
        rank: number;
        instrument_id: string;
        label: string;
        score: number;
        reason: string;
      }>;
    }>;
    ranking_backlog: Array<{ ranking_id: string; label: string; status: string }>;
  };
  investor_easy_parity?: {
    title: string;
    source_url: string;
    plain_language_summary: string;
    observed_at: string;
    calculator_count: number;
    available_calculator_count: number;
    feature_coverage: Array<{
      feature_id: string;
      label: string;
      site_offer: string;
      local_status: string;
      local_surface: string;
    }>;
    calculator_suite: Array<{
      calculator_id: string;
      label: string;
      tier: string;
      formula_family: string;
      status: string;
      local_surface: string;
    }>;
    plan_equivalence: Array<{
      plan_label: string;
      site_limit: string;
      local_equivalent: string;
    }>;
    remaining_gaps: string[];
  };
  product_data_plan?: {
    title: string;
    plain_language_summary: string;
    status: string;
    source_count: number;
    connected_source_count: number;
    partial_source_count: number;
    roadmap_step_count?: number;
    roadmap_completed_step_count?: number;
    roadmap_completion_pct?: number;
    sources: Array<{
      source_id: string;
      label: string;
      url: string;
      coverage: string;
      freshness_policy: string;
      integration_status: string;
      connector_status?: string;
      cache_key?: string;
      families: string[];
      expected_fields?: string[];
    }>;
    family_coverage: Array<{
      family_id: string;
      label: string;
      instrument_count: number;
      product_profile_count: number;
      coverage_score: number;
      external_data_status: string;
    }>;
    source_manifest?: {
      title: string;
      plain_language_summary: string;
      cache_root: string;
      checked_at: string;
      source_count: number;
      warm_source_count: number;
      stale_source_count: number;
      sources: Array<{
        source_id: string;
        cache_key: string;
        cache_dir: string;
        exists: boolean;
        file_count: number;
        total_size_bytes: number;
        latest_file_name?: string | null;
        latest_file_at?: string | null;
        age_days?: number | null;
        freshness_status: string;
        freshness_label: string;
        connector_status: string;
        expected_fields: string[];
        row_count?: number | null;
        schema_version?: string | null;
        source_url?: string | null;
        checksum_sha256?: string | null;
        collection_mode?: string | null;
        refresh_history?: Array<{
          ran_at: string;
          started_at?: string;
          finished_at?: string;
          duration_ms?: number;
          source_attempted_url?: string;
          source_id: string;
          status: string;
          status_label: string;
          message: string;
          row_count?: number | null;
          schema_version?: string | null;
          checksum_sha256?: string | null;
          collection_mode?: string | null;
          fetch_error?: string | null;
        }>;
      }>;
      takeaways: string[];
    };
    catalog_enrichment?: Array<{
      family_id: string;
      source_id: string;
      matched_instrument_count: number;
      cached_row_count: number;
      status: string;
      sample: Array<{
        instrument_id: string;
        ticker?: string | null;
        segment?: string | null;
        listing_status?: string | null;
      }>;
      next_action: string;
    }>;
    identity_map?: Array<{
      ticker?: string | null;
      name?: string | null;
      segment?: string | null;
      listing_status?: string | null;
      source_id: string;
      identity_status: string;
    }>;
    fii_cvm_bridge?: {
      source_id: string;
      status: string;
      mapped_instrument_count: number;
      matched_cvm_cache_count: number;
      coverage_ratio: number;
      methodology: string;
      rows: Array<{
        instrument_id: string;
        ticker: string;
        label: string;
        cnpj_fundo: string;
        bridge_status: string;
        latest_date?: string | null;
        net_worth?: number | null;
        quota?: number | null;
        shareholders?: number | null;
        source_note: string;
      }>;
    };
    cvm_fund_profile?: {
      source_id: string;
      status: string;
      row_count: number;
      latest_date?: string | null;
      total_net_worth: number;
      total_shareholders: number;
      net_flow: number;
      methodology: string;
      sample_largest_funds: Array<{
        cnpj_fundo?: string | null;
        net_worth: number;
        quota: number;
        shareholders: number;
      }>;
    };
    cvm_fund_rankings?: Array<{
      ranking_id: string;
      label: string;
      source_id: string;
      status: string;
      latest_date?: string | null;
      methodology: string;
      rows: Array<{
        rank: number;
        cnpj_fundo?: string | null;
        score: number;
        score_label: string;
        net_worth: number;
        quota: number;
        shareholders: number;
        net_flow: number;
      }>;
    }>;
    etf_bdr_profile?: {
      source_id: string;
      status: string;
      row_count: number;
      average_fee_pct?: number | null;
      methodology: string;
      product_type_counts: Array<{ product_type: string; count: number }>;
      sample_low_fee_products: Array<{
        ticker?: string | null;
        name?: string | null;
        product_type?: string | null;
        reference_index?: string | null;
        admin_fee_pct?: number | null;
        exposure?: string | null;
        tracking_note?: string | null;
        data_quality_score: number;
      }>;
    };
    etf_bdr_rankings?: Array<{
      ranking_id: string;
      label: string;
      source_id: string;
      status: string;
      methodology: string;
      rows: Array<{
        rank: number;
        ticker?: string | null;
        name?: string | null;
        product_type?: string | null;
        reference_index?: string | null;
        admin_fee_pct?: number | null;
        exposure?: string | null;
        tracking_note?: string | null;
        data_quality_score: number;
        score: number;
        score_label: string;
      }>;
    }>;
    methodology_readiness_ranking?: {
      ranking_id: string;
      label: string;
      status: string;
      methodology: string;
      rows: Array<{
        rank: number;
        instrument_id: string;
        ticker: string;
        label: string;
        product_family: string;
        score: number;
        score_components: Record<string, number>;
        source_ids: string[];
        caveat: string;
      }>;
    };
    implementation_steps: string[];
    roadmap_steps?: Array<{
      step_id: string;
      label: string;
      status: string;
      release_ids: string[];
    }>;
    next_release_candidates: Array<{
      release_id: string;
      label: string;
      source_ids: string[];
      user_value: string;
      screeners_enabled?: string[];
      ranking_candidates?: string[];
      status?: string;
    }>;
    market_filter_backlog?: Array<{
      filter_id: string;
      label: string;
      families: string[];
      status: string;
    }>;
    validation_plan?: Array<{
      gate_id: string;
      label: string;
      checks: string[];
    }>;
    quality_gate: string[];
  };
  notes: string[];
  sources: Array<{ label: string; url: string }>;
}

export interface InvestmentProductDataRefreshRequestPayload {
  source_id: string;
  force?: boolean;
}

export interface InvestmentProductDataRefreshResponsePayload {
  source_id: string;
  status: string;
  status_label: string;
  message: string;
  manifest?: {
    source_id: string;
    source_url?: string;
    schema_version?: string;
    collected_at?: string;
    row_count?: number;
    file_name?: string;
    checksum_sha256?: string;
    fields?: string[];
    collection_mode?: string;
    caveat?: string;
  } | null;
  history?: Array<{
    ran_at: string;
    started_at?: string;
    finished_at?: string;
    duration_ms?: number;
    source_attempted_url?: string;
    source_id: string;
    status: string;
    status_label: string;
    message: string;
    row_count?: number | null;
    schema_version?: string | null;
    checksum_sha256?: string | null;
    collection_mode?: string | null;
    fetch_error?: string | null;
  }>;
}

export interface InvestmentCompareRequestPayload {
  asset_ids: string[];
  custom_portfolios?: InvestmentCustomPortfolioRequestPayload[];
  start_date?: string;
  end_date?: string | null;
  initial_capital?: number;
  monthly_contribution?: number;
  benchmark_ids?: string[];
  fixed_income_study_mode?: string;
  fixed_income_tax_treatment?: string;
  fixed_income_window_frequency?: string;
  decision_profile?: InvestmentDecisionProfilePayload;
  force_download?: boolean;
}

export interface InvestmentDecisionProfilePayload {
  objective: string;
  objective_label?: string;
  horizon_years: number;
  liquidity_need: string;
  liquidity_need_label?: string;
  mark_to_market_tolerance: string;
  mark_to_market_tolerance_label?: string;
  tax_view: string;
  tax_view_label?: string;
  monthly_income_target: number;
}

export interface InvestmentComparisonResultPayload {
  instrument_id: string;
  label: string;
  ticker?: string | null;
  category_id: string;
  category_label: string;
  description: string;
  rationale: string;
  risk_label: string;
  region_label: string;
  source_kind: string;
  invested_total: number;
  final_value: number;
  net_profit: number;
  total_return_on_invested: number;
  time_weighted_return: number;
  cagr: number;
  annual_volatility: number;
  max_drawdown: number;
  availability_start: string;
  availability_end: string;
  taxes_paid_total?: number;
  realized_taxes_paid?: number;
  estimated_exit_taxes?: number;
  strategy_metadata?: Record<string, unknown>;
  invested_total_real: number;
  final_value_real: number;
  net_profit_real: number;
  real_total_return_on_invested: number;
  real_time_weighted_return: number;
  real_cagr: number;
  final_value_net: number;
  net_profit_net: number;
  cagr_net: number;
  final_value_real_net: number;
  net_profit_real_net: number;
  real_cagr_net: number;
  component_breakdown: InvestmentPortfolioContributionPayload[];
  category_breakdown: InvestmentPortfolioContributionPayload[];
}

export interface InvestmentComparisonBenchmarkPayload
  extends InvestmentComparisonResultPayload {
  benchmark_id: string;
  equity_curve: Array<{ date: string; equity: number }>;
}

export interface InvestmentComparisonChartPayload {
  reference_series_id?: string | null;
  series: Array<{ id: string; label: string; color: string; dashed?: boolean }>;
  points: Array<Record<string, string | number | null>>;
}

export interface InvestmentMethodologyEvidencePayload {
  kind: string;
  label: string;
  description: string;
  limitations: string;
  included_count: number;
  included_labels: string[];
}

export interface InvestmentMethodologyGuidePayload {
  title: string;
  plain_language_summary: string;
  evidence_types: InvestmentMethodologyEvidencePayload[];
  assumption_notes: string[];
  caveats: string[];
  decision_profile_notes?: string[];
  realism_notes?: Array<{
    dimension: string;
    status: string;
    note: string;
  }>;
}

export interface InvestmentProductRealismDimensionPayload {
  dimension_id: string;
  label: string;
  status: 'modeled' | 'partial' | 'not_modeled' | string;
  status_label: string;
  summary: string;
  current_scope: string[];
  limitations: string;
  next_step: string;
}

export interface InvestmentProductRealismPayload {
  title: string;
  plain_language_summary: string;
  product_types: Array<{
    source_kind: string;
    label: string;
    count: number;
  }>;
  coverage: InvestmentProductRealismDimensionPayload[];
  income_policy_examples?: Array<{
    policy_id: string;
    label: string;
    cashflow_treatment: string;
    tax_treatment: string;
    reinvestment_assumption: string;
    user_decision: string;
  }>;
  next_methodology_steps: string[];
}

export interface InvestmentRetailFixedIncomeEquivalenceRowPayload {
  holding_days: number;
  holding_years: number;
  tax_exempt_product: string;
  tax_exempt_pct_cdi: number;
  tax_exempt_annual_rate: number;
  ir_rate: number;
  iof_rate: number;
  net_gain_retention: number;
  equivalent_cdb_pct_cdi: number;
  equivalent_cdb_annual_rate: number;
  interpretation: string;
}

export interface InvestmentRetailFixedIncomeTaxableProductExamplePayload {
  product_id: string;
  label: string;
  holding_days: number;
  gross_pct_cdi: number;
  annual_fee_rate: number;
  gross_annual_rate: number;
  ir_rate: number;
  iof_rate: number;
  net_annual_rate: number;
  net_pct_cdi: number;
  liquidity: string;
  credit_note: string;
  interpretation: string;
}

export interface InvestmentRetailFixedIncomeEquivalencePayload {
  title: string;
  plain_language_summary: string;
  reference_cdi_annual_rate: number;
  profile_horizon_days: number;
  profile_horizon_label: string;
  uses_fixed_income_backtest: boolean;
  rows: InvestmentRetailFixedIncomeEquivalenceRowPayload[];
  taxable_product_examples?: InvestmentRetailFixedIncomeTaxableProductExamplePayload[];
  assumptions: string[];
  next_steps: string[];
}

export interface InvestmentResultStoryPayload {
  story_id: string;
  label: string;
  question: string;
  winner_id?: string | null;
  winner_label?: string | null;
  metric_label: string;
  metric_value: number;
  metric_kind: string;
  interpretation: string;
  caveat: string;
}

export interface InvestmentResultRankingPayload {
  ranking_id: string;
  label: string;
  metric_label: string;
  metric_kind: string;
  rows: Array<{
    rank: number;
    instrument_id: string;
    label: string;
    category_label: string;
    value: number;
  }>;
}

export interface InvestmentResultStoriesPayload {
  title: string;
  plain_language_summary: string;
  stories: InvestmentResultStoryPayload[];
  rankings: InvestmentResultRankingPayload[];
  next_questions: string[];
}

export interface InvestmentMarketRankingPayload {
  ranking_id: string;
  label: string;
  metric_label: string;
  metric_kind: string;
  methodology: string;
  weights?: Record<string, number>;
  rows: Array<{
    rank: number;
    instrument_id: string;
    label: string;
    category_label: string;
    source_kind: string;
    risk_label: string;
    value: number;
    secondary_value: number;
  }>;
}

export interface InvestmentMarketRankingsPayload {
  title: string;
  plain_language_summary: string;
  universe_label: string;
  as_of_date?: string | null;
  source_label: string;
  benchmark_context: Array<{
    benchmark_id: string;
    label: string;
    metric_label: string;
    metric_kind: string;
    value: number;
    total: number;
    interpretation: string;
  }>;
  rankings: InvestmentMarketRankingPayload[];
  export_columns: string[];
  methodology_notes: string[];
  generated_at: string;
}

export interface InvestmentMarketScreenersPayload {
  title: string;
  plain_language_summary: string;
  universe_count: number;
  presets: Array<{
    preset_id: string;
    label: string;
    rule_summary: string;
    matched_count: number;
    universe_count: number;
    sort_key: string;
    rows: Array<{
      rank: number;
      instrument_id: string;
      label: string;
      category_label: string;
      real_cagr: number;
      max_drawdown: number;
      annual_volatility: number;
      net_profit: number;
    }>;
  }>;
  methodology_notes: string[];
}

export interface InvestmentCacheStatusPayload {
  title: string;
  plain_language_summary: string;
  status: string;
  status_label: string;
  checked_at: string;
  caches: Array<{
    cache_id: string;
    label: string;
    path: string;
    patterns?: string[];
    exists: boolean;
    file_count: number;
    total_size_bytes: number;
    latest_file_name?: string | null;
    latest_file_at?: string | null;
    age_days?: number | null;
    freshness_status?: string;
    freshness_label?: string;
    status: string;
    status_label: string;
    cold_start_note: string;
    refresh_hint?: string;
    used_in_current_result?: boolean;
  }>;
  takeaways: string[];
}

export interface InvestmentDecisionCardPayload {
  decision_id: string;
  label: string;
  when_it_fits: string;
  watch_out: string;
  best_match_id?: string | null;
  best_match_label?: string | null;
  metric_label?: string | null;
  metric_value?: number | null;
  metric_kind?: string | null;
  fit_score?: number | null;
  fit_label?: string | null;
  profile_reason?: string | null;
}

export interface InvestmentFixedIncomeDecisionGuidePayload {
  title: string;
  plain_language_summary: string;
  study_label?: string | null;
  tax_treatment?: string | null;
  window_frequency?: string | null;
  decision_profile?: InvestmentDecisionProfilePayload;
  profile_summary?: string;
  decision_cards: InvestmentDecisionCardPayload[];
  next_questions: string[];
}

export interface InvestmentPortfolioObjectivePayload {
  objective_id: string;
  label: string;
  question: string;
  best_match_id?: string | null;
  best_match_label?: string | null;
  reason: string;
  tradeoff: string;
  metric_label?: string | null;
  metric_value?: number | null;
  metric_kind?: string | null;
  fit_score?: number | null;
  fit_label?: string | null;
  profile_reason?: string | null;
}

export interface InvestmentPortfolioObjectiveSummaryPayload {
  title: string;
  plain_language_summary: string;
  objectives: InvestmentPortfolioObjectivePayload[];
  portfolio_rows: Array<{
    instrument_id?: string | null;
    label?: string | null;
    source_kind?: string | null;
    final_value: number;
    real_cagr: number;
    max_drawdown: number;
    component_count: number;
    top_components: Array<{
      label?: string | null;
      target_weight: number;
      ending_weight: number;
      final_value: number;
    }>;
    category_breakdown: Array<{
      label?: string | null;
      target_weight: number;
      ending_weight: number;
      final_value: number;
    }>;
  }>;
  fixed_income_study_available?: boolean;
  decision_profile?: InvestmentDecisionProfilePayload;
  scenario_cards?: Array<{
    scenario_id: string;
    label: string;
    description: string;
    best_match_id?: string | null;
    best_match_label?: string | null;
    metric_label: string;
    metric_value: number;
    metric_kind: string;
    target_value?: number | null;
    target_met?: boolean | null;
  }>;
  profile_summary?: string;
  next_steps: string[];
}

export interface InvestmentPortfolioLifecyclePayload {
  title: string;
  plain_language_summary: string;
  uses_portfolio_rows: boolean;
  portfolio_count: number;
  scenario_cards: Array<{
    scenario_id: string;
    label: string;
    description: string;
    best_match_id?: string | null;
    best_match_label?: string | null;
    metric_label: string;
    metric_value: number;
    metric_kind: string;
    comparison_label?: string | null;
    target_value?: number | null;
    target_met?: boolean | null;
  }>;
  withdrawal_plan?: {
    title: string;
    withdrawal_rate: number;
    monthly_income_target?: number | null;
    best_candidate_id?: string | null;
    best_candidate_label?: string | null;
    target_met_count: number;
    candidate_count: number;
    feasibility_label: string;
    candidates: Array<{
      instrument_id: string;
      label: string;
      source_kind?: string | null;
      final_value_real_net: number;
      monthly_withdrawal: number;
      income_gap?: number | null;
      target_met?: boolean | null;
      max_drawdown: number;
      real_cagr: number;
      annual_volatility: number;
    }>;
    stress_tests?: Array<{
      scenario_id: string;
      label: string;
      description: string;
      withdrawal_multiplier: number;
      drawdown_buffer: number;
      stressed_monthly_withdrawal: number;
      income_gap?: number | null;
      target_met?: boolean | null;
      interpretation: string;
    }>;
    stress_summary?: string;
    monte_carlo_preview?: {
      title: string;
      methodology: string;
      instrument_id: string;
      label: string;
      real_cagr: number;
      annual_volatility: number;
      years_of_income_at_target?: number | null;
      coverage_score: number;
      target_met_count: number;
      scenario_count: number;
      scenarios: Array<{
        scenario_id: string;
        label: string;
        description: string;
        monthly_withdrawal: number;
        income_gap?: number | null;
        target_met?: boolean | null;
      }>;
      monthly_sequence?: {
        title: string;
        horizon_years: number;
        monthly_withdrawal: number;
        monthly_base_return: number;
        monthly_volatility: number;
        success_count: number;
        path_count: number;
        success_rate: number;
        methodology: string;
        paths: Array<{
          path_id: string;
          label: string;
          monthly_return: number;
          early_shock: number;
          final_balance: number;
          lowest_balance: number;
          exhaustion_month?: number | null;
          exhaustion_year?: number | null;
          survived_horizon: boolean;
          checkpoints: Array<{
            month: number;
            year: number;
            balance: number;
          }>;
        }>;
        stochastic?: {
          title: string;
          simulation_count: number;
          seed: number;
          success_count: number;
          success_rate: number;
          percentiles: {
            final_balance_p10: number;
            final_balance_p50: number;
            final_balance_p90: number;
          };
          median_exhaustion_month?: number | null;
          median_exhaustion_year?: number | null;
          sample_paths: Array<{
            path_index: number;
            final_balance: number;
            lowest_balance: number;
            exhaustion_month?: number | null;
            survived_horizon: boolean;
          }>;
          methodology: string;
        };
      };
      caveat: string;
    };
  };
  assumptions: string[];
  next_steps: string[];
}

export interface InvestmentStudyQualityPayload {
  title: string;
  status: string;
  status_label: string;
  readiness_score: number;
  completed_checks: number;
  total_checks: number;
  summary: string;
  remaining_work: string[];
  checks: Array<{
    check_id: string;
    label: string;
    status: string;
    status_label: string;
    detail: string;
    severity: string;
  }>;
}

export interface InvestmentComparisonRequestSnapshotPayload {
  asset_ids: string[];
  custom_portfolios: InvestmentCustomPortfolioRequestPayload[];
  start_date: string;
  end_date?: string | null;
  initial_capital: number;
  monthly_contribution: number;
  benchmark_ids: string[];
  fixed_income_study_mode: string;
  fixed_income_tax_treatment: string;
  fixed_income_window_frequency: string;
  decision_profile: InvestmentDecisionProfilePayload;
  force_download: boolean;
}

export interface InvestmentMarketRankingsRequestPayload {
  preset_id?: string;
  asset_ids?: string[];
  start_date?: string;
  end_date?: string | null;
  initial_capital?: number;
  monthly_contribution?: number;
  benchmark_ids?: string[];
  decision_profile?: Partial<InvestmentDecisionProfilePayload>;
  force_download?: boolean;
}

export interface InvestmentMarketRankingsSnapshotPayload {
  generated_at: string;
  request: Record<string, unknown>;
  market_rankings: InvestmentMarketRankingsPayload;
  market_screeners: InvestmentMarketScreenersPayload;
  cache_status: InvestmentCacheStatusPayload;
  warnings: string[];
}

export interface InvestmentFixedIncomeResultPayload
  extends InvestmentComparisonResultPayload {
  family_id: string;
  family_label: string;
  duration_years?: number | null;
  title_type?: string;
  selection_rule?: string;
  source_method_label?: string;
  display_value: number;
  display_profit: number;
  display_cagr: number;
  display_value_real: number;
  display_profit_real: number;
  display_real_cagr: number;
  comparison_metric_label: string;
  relative_gap_vs_benchmark: number;
  value_gap_vs_benchmark: number;
  relative_gap_vs_benchmark_real: number;
  value_gap_vs_benchmark_real: number;
  is_benchmark: boolean;
}

export interface InvestmentFixedIncomeWindowPayload {
  study_id: string;
  instrument_id: string;
  label: string;
  source_kind: string;
  family_id: string;
  family_label: string;
  duration_years?: number | null;
  window_years: number;
  window_frequency: string;
  window_frequency_requested?: string;
  windows_count: number;
  win_rate: number;
  average_excess_return: number;
  median_excess_return: number;
  best_excess_return: number;
  worst_excess_return: number;
  best_window_start?: string | null;
  best_window_end?: string | null;
  worst_window_start?: string | null;
  worst_window_end?: string | null;
}

export interface InvestmentFixedIncomeStudyPayload {
  study_id: string;
  study_label: string;
  methodology: {
    study_id: string;
    study_label: string;
    benchmark_instrument_id: string;
    benchmark_label: string;
    series_source_label: string;
    series_source_url?: string;
    index_methodology_label: string;
    study_scope_label?: string;
    what_it_measures?: string;
    what_it_does_not_measure?: string;
    rolling_window_note: string;
    full_period_note: string;
    comparison_metric_label?: string;
    tax_treatment?: string;
    window_frequency_requested?: string;
    window_frequency_effective?: string;
    selected_fixed_income_ids: string[];
    video_reference_match: boolean;
    cache?: Record<string, unknown>;
    benchmark_cache?: Record<string, unknown>;
  };
  full_period: {
    start_date: string;
    end_date: string;
    initial_capital: number;
    monthly_contribution: number;
    benchmark: InvestmentFixedIncomeResultPayload;
    results: InvestmentFixedIncomeResultPayload[];
    leaders: {
      overall?: InvestmentFixedIncomeResultPayload;
      best_real_cagr?: InvestmentFixedIncomeResultPayload;
      post_fixed?: InvestmentFixedIncomeResultPayload;
      prefixado?: InvestmentFixedIncomeResultPayload;
      ipca_plus?: InvestmentFixedIncomeResultPayload;
      most_consistent?: InvestmentFixedIncomeWindowPayload;
    };
  };
  rolling_windows: InvestmentFixedIncomeWindowPayload[];
  takeaways: string[];
}

export interface InvestmentFixedIncomeBacktestPayload {
  requested_study_mode?: string;
  tax_treatment?: string;
  window_frequency?: string;
  selected_study_id?: string;
  selected_study_label?: string;
  study_count?: number;
  studies?: InvestmentFixedIncomeStudyPayload[];
  summary?: {
    available_study_ids: string[];
    takeaways: string[];
  };
  methodology: {
    benchmark_instrument_id: string;
    benchmark_label: string;
    series_source_label: string;
    series_source_url?: string;
    index_methodology_label: string;
    study_id?: string;
    study_label?: string;
    study_scope_label?: string;
    what_it_measures?: string;
    what_it_does_not_measure?: string;
    rolling_window_note: string;
    full_period_note: string;
    comparison_metric_label?: string;
    tax_treatment?: string;
    window_frequency_requested?: string;
    window_frequency_effective?: string;
    selected_fixed_income_ids: string[];
    video_reference_match: boolean;
    cache?: Record<string, unknown>;
    benchmark_cache?: Record<string, unknown>;
  };
  full_period: {
    start_date: string;
    end_date: string;
    initial_capital: number;
    monthly_contribution: number;
    benchmark: InvestmentFixedIncomeResultPayload;
    results: InvestmentFixedIncomeResultPayload[];
    leaders: {
      overall?: InvestmentFixedIncomeResultPayload;
      best_real_cagr?: InvestmentFixedIncomeResultPayload;
      post_fixed?: InvestmentFixedIncomeResultPayload;
      prefixado?: InvestmentFixedIncomeResultPayload;
      ipca_plus?: InvestmentFixedIncomeResultPayload;
      most_consistent?: InvestmentFixedIncomeWindowPayload;
    };
  };
  rolling_windows: InvestmentFixedIncomeWindowPayload[];
  takeaways: string[];
}

export interface InvestmentComparisonResponsePayload {
  generated_at: string;
  request: InvestmentComparisonRequestSnapshotPayload;
  catalog_snapshot: Record<string, unknown>;
  assumptions: string[];
  results: InvestmentComparisonResultPayload[];
  benchmarks: InvestmentComparisonBenchmarkPayload[];
  chart: InvestmentComparisonChartPayload;
  real_chart: InvestmentComparisonChartPayload;
  inflation: {
    label: string;
    accumulated_rate: number;
    purchasing_power_loss: number;
    availability_start: string;
    availability_end: string;
    source_label: string;
  };
  class_summary: Array<{
    category_label: string;
    asset_count: number;
    average_final_value: number;
    average_cagr: number;
    average_real_cagr: number;
    average_max_drawdown: number;
    leader_label: string;
  }>;
  highlights: {
    best_final_value?: InvestmentComparisonResultPayload;
    best_real_cagr?: InvestmentComparisonResultPayload;
    most_defensive?: InvestmentComparisonResultPayload;
    beats_selic_count?: number | null;
    beats_bova11_count?: number | null;
    beats_inflation_count?: number | null;
    insights?: string[];
  };
  fixed_income_backtest?: InvestmentFixedIncomeBacktestPayload | null;
  methodology_guide?: InvestmentMethodologyGuidePayload;
  product_realism?: InvestmentProductRealismPayload;
  retail_fixed_income_equivalence?: InvestmentRetailFixedIncomeEquivalencePayload;
  result_stories?: InvestmentResultStoriesPayload;
  market_rankings?: InvestmentMarketRankingsPayload;
  market_screeners?: InvestmentMarketScreenersPayload;
  cache_status?: InvestmentCacheStatusPayload;
  fixed_income_decision_guide?: InvestmentFixedIncomeDecisionGuidePayload | null;
  portfolio_objective_summary?: InvestmentPortfolioObjectiveSummaryPayload;
  portfolio_lifecycle?: InvestmentPortfolioLifecyclePayload;
  study_quality?: InvestmentStudyQualityPayload;
  warnings: string[];
}

export interface PairsUniversePresetPayload {
  preset_id: string;
  label: string;
  description: string;
  universe_kind: string;
  history_mode: string;
  benchmark_tickers: string[];
  tickers: string[];
  ticker_count: number;
}

export interface PairsUniverseResolveRequestPayload {
  preset_id?: string;
  tickers?: string[];
  sector_overrides?: Record<string, string>;
  as_of_date?: string | null;
  start_date?: string;
  end_date?: string | null;
  force_download?: boolean;
  min_price?: number;
  min_median_notional_brl?: number;
  use_proxy_short_borrow?: boolean;
  proxy_borrow_base_rate_annual?: number;
  proxy_borrow_max_rate_annual?: number;
  proxy_min_short_score?: number;
  proxy_borrow_vol_floor?: number;
  proxy_borrow_vol_cap?: number;
  borrow_snapshot_path?: string | null;
}

export interface PairsScreenRequestPayload extends PairsUniverseResolveRequestPayload {
  formation_window?: number;
  test_window?: number;
  max_pairs?: number;
  top_n?: number;
  min_return_corr?: number;
  min_level_corr?: number;
  max_coint_pvalue?: number;
  min_half_life?: number;
  max_half_life?: number;
  min_stability_score?: number;
  max_structural_break_risk?: number;
  min_beta_abs?: number;
  max_beta_abs?: number;
  require_cointegration?: boolean;
}

export interface PairsScenarioVariantPayload {
  scenario_id: string;
  label: string;
  require_cointegration?: boolean;
  overrides?: Record<string, unknown>;
}

export interface PairsBacktestRequestPayload extends PairsScreenRequestPayload {
  step_window?: number;
  entry_zscore?: number;
  exit_zscore?: number;
  stop_zscore?: number;
  max_holding_days?: number;
  pair_allocation_pct?: number;
  initial_capital?: number;
  zscore_window?: number;
  fee_rate?: number;
  slippage?: number;
  short_borrow_rate_annual?: number;
  apply_cash_yield?: boolean;
  use_real_selic?: boolean;
  selic_path?: string;
  selic_fallback_rate?: number;
  cash_collateral_ratio?: number;
  explicit_margin_model?: boolean;
  short_margin_haircut?: number;
  dynamic_beta?: boolean;
  rolling_beta_window?: number;
  regime_filter?: string;
  regime_ma_window?: number;
  regime_max_deviation?: number;
  regime_vol_window?: number;
  regime_vol_lookback?: number;
  regime_vol_quantile?: number;
  portfolio_construction?: string;
  target_pair_volatility_annual?: number;
  max_gross_exposure_pct?: number;
  max_net_exposure_pct?: number;
  max_sector_pairs?: number;
  benchmark_ids?: string[];
  scenario_label?: string;
  scenario_id?: string;
}

export interface PairsBatchRequestPayload extends PairsBacktestRequestPayload {
  scenario_variants?: PairsScenarioVariantPayload[];
}

export interface PairsUniverseResolvedPresetPayload {
  preset_id?: string;
  label?: string;
  description?: string;
  source_kind?: string;
  source_url?: string;
  validity_label?: string;
  cache_status?: string;
  requested_as_of_date?: string;
  resolved_as_of_date?: string;
  ticker_count?: number;
  [key: string]: unknown;
}

export interface PairsQualityReportPayload {
  requested_ticker_count?: number;
  loaded_ticker_count?: number;
  eligible_ticker_count?: number;
  unavailable_ticker_count?: number;
  common_index_days?: number;
  borrow_override_count?: number;
  borrow_snapshot_path?: string | null;
  borrow_snapshot_managed_path?: string | null;
  borrow_snapshot_dataset_id?: string | null;
  issue_counts?: Record<string, number>;
  unavailable_tickers?: Record<string, string>;
  coverage_quality_score?: number;
  [key: string]: unknown;
}

export interface PairsUniverseAssetPayload {
  ticker: string;
  sector_group?: string;
  eligibility_status?: string;
  eligibility_reasons?: string[];
  median_notional_brl?: number;
  borrow_source?: string | null;
  borrow_proxy_rate_annual?: number | null;
  margin_haircut?: number | null;
  short_eligible?: boolean | null;
  [key: string]: unknown;
}

export interface PairsScreeningWindowPayload {
  formation_start?: string;
  formation_end?: string;
  trade_start?: string;
  trade_end?: string;
  formation_days?: number;
  test_days?: number;
  [key: string]: unknown;
}

export interface PairsScreenCriteriaPayload {
  require_cointegration?: boolean;
  top_n?: number;
  max_pairs?: number;
  max_coint_pvalue?: number;
  min_return_corr?: number;
  min_half_life?: number;
  max_half_life?: number;
  [key: string]: unknown;
}

export interface PairsScreenSummaryPayload {
  requested_ticker_count?: number;
  loaded_ticker_count?: number;
  eligible_ticker_count?: number;
  candidate_pair_count?: number;
  selected_pair_count?: number;
  rejected_pair_count?: number;
  [key: string]: unknown;
}

export interface PairsCandidatePairStabilityPayload {
  window_count?: number;
  pass_count?: number;
  pass_rate?: number;
  mean_coint_pvalue?: number | null;
  beta_dispersion?: number | null;
  half_life_dispersion?: number | null;
  return_corr_dispersion?: number | null;
  structural_break_risk?: number;
  stability_score?: number;
  stability_band?: string;
  [key: string]: unknown;
}

export interface PairsCandidateRankingComponentsPayload {
  coint_score?: number;
  return_corr_score?: number;
  level_corr_score?: number;
  stability_score?: number;
  beta_quality?: number;
  structural_break_penalty?: number;
  ranking_score?: number;
  [key: string]: unknown;
}

export interface PairsCandidatePairPayload {
  pair_label: string;
  y_ticker?: string;
  x_ticker?: string;
  sector_group?: string;
  coint_pvalue?: number;
  adf_pvalue?: number;
  half_life?: number;
  return_corr?: number;
  level_corr?: number;
  beta?: number;
  ranking_score?: number;
  segment_id?: string;
  segment_start_date?: string;
  segment_end_date?: string;
  resolved_as_of_date?: string;
  stability?: PairsCandidatePairStabilityPayload;
  ranking_components?: PairsCandidateRankingComponentsPayload;
  rejection_reasons?: string[];
  [key: string]: unknown;
}

export interface PairsBenchmarkCurvePointPayload {
  date: string;
  equity: number;
  [key: string]: unknown;
}

export interface PairsBenchmarkPayload {
  benchmark_id: string;
  label: string;
  equity_curve: PairsBenchmarkCurvePointPayload[];
  [key: string]: unknown;
}

export interface PairsScenarioMetricsPayload {
  return_total?: number;
  cagr?: number;
  volatility?: number;
  sharpe?: number;
  sortino?: number;
  max_drawdown?: number;
  final_equity?: number;
  trade_count?: number;
  win_rate?: number;
  profit_factor?: number;
  avg_trade_pnl?: number;
  avg_gross_exposure_pct?: number;
  turnover?: number;
  short_borrow_cost_total?: number;
  fees_total?: number;
  slippage_total?: number;
  [key: string]: unknown;
}

export interface PairsScenarioQualitySummaryPayload {
  regime_blocked_entries?: number;
  portfolio_cap_blocked_entries?: number;
  sector_cap_blocked_entries?: number;
  cash_yield_total?: number;
  first_trade_date?: string;
  selected_pair_count?: number;
  trade_count?: number;
  reconstitution_segment_count?: number;
  [key: string]: unknown;
}

export interface PairsBorrowSourceMixPayload {
  short_borrow_source?: string;
  trade_count?: number;
  [key: string]: unknown;
}

export interface PairsSectorMixPayload {
  sector_group?: string;
  selection_count?: number;
  [key: string]: unknown;
}

export interface PairsScenarioPortfolioSummaryPayload {
  construction?: string;
  target_pair_volatility_annual?: number;
  max_sector_pairs?: number;
  max_gross_exposure_pct?: number;
  max_net_exposure_pct?: number;
  gross_exposure_peak?: number;
  gross_exposure_average?: number;
  net_exposure_abs_average?: number;
  open_positions_peak?: number;
  unique_pairs_traded?: number;
  unique_assets_used?: number;
  allocation_pct_average?: number;
  allocation_pct_max?: number;
  top_pair_concentration_pct?: number;
  sector_mix?: PairsSectorMixPayload[];
  borrow_source_mix?: PairsBorrowSourceMixPayload[];
  [key: string]: unknown;
}

export interface PairsScenarioTradeAuditPayload {
  pair_label?: string;
  long_ticker?: string;
  short_ticker?: string;
  entry_date?: string;
  exit_date?: string;
  exit_reason?: string;
  beta?: number;
  z_entry?: number;
  z_exit?: number;
  long_notional?: number;
  short_notional?: number;
  gross_pnl?: number;
  net_pnl?: number;
  short_borrow_cost?: number;
  fees_paid?: number;
  slippage_cost?: number;
  holding_days?: number;
  short_borrow_source?: string;
  [key: string]: unknown;
}

export interface PairsScenarioSelectionPayload {
  pair_label?: string;
  y_ticker?: string;
  x_ticker?: string;
  sector_group?: string;
  trade_start?: string;
  trade_end?: string;
  return_corr?: number;
  level_corr?: number;
  coint_pvalue?: number;
  adf_pvalue?: number;
  beta?: number;
  half_life?: number;
  stability_score?: number;
  structural_break_risk?: number;
  ranking_score?: number;
  [key: string]: unknown;
}

export interface PairsPairPnlPayload {
  pair_label?: string;
  net_pnl?: number;
  [key: string]: unknown;
}

export interface PairsPairSummaryPayload {
  pair_label?: string;
  selection_count?: number;
  avg_return_corr?: number;
  avg_coint_pvalue?: number;
  avg_beta?: number;
  avg_half_life?: number;
  rationale?: string;
  [key: string]: unknown;
}

export interface PairsScenarioAlphaBenchmarkPayload {
  benchmark_id: string;
  label: string;
  final_equity: number;
  equity_gap: number;
  return_total: number;
  excess_return_total: number;
}

export interface PairsScenarioAlphaDecompositionPayload {
  initial_capital?: number;
  final_equity?: number;
  total_pnl?: number;
  trade_gross_pnl_total?: number;
  trade_net_pnl_total?: number;
  dividend_pnl_total?: number;
  cash_yield_total?: number;
  short_borrow_cost_total?: number;
  fees_total?: number;
  slippage_total?: number;
  explained_pnl_total?: number;
  residual_pnl_total?: number;
  trade_return_total?: number;
  cash_return_total?: number;
  trade_share_of_total_pnl?: number;
  cash_share_of_total_pnl?: number;
  primary_benchmark_id?: string | null;
  primary_benchmark_equity_gap?: number | null;
  primary_benchmark_excess_return?: number | null;
  benchmark_comparison?: PairsScenarioAlphaBenchmarkPayload[];
  [key: string]: unknown;
}

export interface PairsScenarioPayload {
  scenario_id: string;
  label: string;
  require_cointegration?: boolean;
  metrics: PairsScenarioMetricsPayload;
  alpha_decomposition?: PairsScenarioAlphaDecompositionPayload;
  portfolio_summary: PairsScenarioPortfolioSummaryPayload;
  quality_summary: PairsScenarioQualitySummaryPayload;
  equity_curve?: Record<string, unknown>[];
  trades?: PairsScenarioTradeAuditPayload[];
  selected_pairs?: PairsScenarioSelectionPayload[];
  pair_summary?: PairsPairSummaryPayload[];
  pair_pnl?: PairsPairPnlPayload[];
  top_candidate_pairs?: PairsCandidatePairPayload[];
  segments?: Record<string, unknown>[];
  reconstitution_enabled?: boolean;
  [key: string]: unknown;
}

export interface PairsRobustnessRankingPayload {
  scenario_id?: string;
  label?: string;
  return_total?: number;
  sharpe?: number;
  max_drawdown?: number;
  trade_count?: number;
  [key: string]: unknown;
}

export interface PairsRobustnessDispersionPayload {
  return_total_range?: number;
  sharpe_range?: number;
  max_drawdown_range?: number;
  [key: string]: unknown;
}

export interface PairsRobustnessReportPayload {
  rankings: PairsRobustnessRankingPayload[];
  dispersion: PairsRobustnessDispersionPayload;
  [key: string]: unknown;
}

export interface PairsReconstitutionSegmentPayload {
  segment_id: string;
  start_date: string;
  end_date: string;
  requested_as_of_date?: string;
  resolved_as_of_date?: string;
  requested_tickers?: string[];
  eligible_tickers?: string[];
  quality_report?: PairsQualityReportPayload;
  [key: string]: unknown;
}

export interface PairsResultUniversePayload {
  reconstitution_plan?: PairsReconstitutionSegmentPayload[];
  quality_report?: PairsQualityReportPayload;
  [key: string]: unknown;
}

export interface PairsUniversePayload {
  preset?: PairsUniverseResolvedPresetPayload | null;
  requested_tickers: string[];
  as_of_date?: string | null;
  resolved_as_of_date?: string | null;
  start_date: string;
  end_date?: string | null;
  common_index_start?: string | null;
  common_index_end?: string | null;
  common_index_days: number;
  quality_report: PairsQualityReportPayload;
  assets: PairsUniverseAssetPayload[];
  eligible_assets: PairsUniverseAssetPayload[];
  unavailable_tickers: Record<string, string>;
  warnings: string[];
}

export interface PairsScreenPayload {
  preset?: PairsUniverseResolvedPresetPayload | null;
  requested_tickers: string[];
  resolved_as_of_date?: string | null;
  screening_window: PairsScreeningWindowPayload;
  criteria: PairsScreenCriteriaPayload;
  summary: PairsScreenSummaryPayload;
  quality_report: PairsQualityReportPayload;
  selected_pairs: PairsCandidatePairPayload[];
  candidate_pairs: PairsCandidatePairPayload[];
  rejected_pairs: PairsCandidatePairPayload[];
  rejection_summary: Record<string, number>;
  warnings: string[];
}

export interface PairsBacktestManifestPayload {
  pairs_backtest_id: string;
  created_at: string;
  preset_id: string;
  preset_label: string;
  universe_as_of_date?: string | null;
  start_date: string;
  end_date?: string | null;
  requested_tickers: string[];
  available_tickers: string[];
  eligible_tickers: string[];
  scenario_count: number;
  batch_mode: boolean;
  benchmark_ids: string[];
  candidate_pair_count: number;
  reconstitution_segment_count: number;
  warnings: string[];
}

export interface SavedPairsRadarItemPayload {
  pairs_backtest_id: string;
  label: string;
  preset_label: string;
  created_at: string;
  saved_at: string;
  scenario_count: number;
  candidate_pair_count: number;
  benchmark_ids: string[];
}

export interface PairsBacktestResultsPayload {
  pairs_backtest_id: string;
  created_at: string;
  manifest: PairsBacktestManifestPayload | Record<string, unknown>;
  preset?: PairsUniverseResolvedPresetPayload | null;
  universe: PairsResultUniversePayload;
  candidate_pairs: PairsCandidatePairPayload[];
  benchmarks: PairsBenchmarkPayload[];
  scenarios: PairsScenarioPayload[];
  robustness_report: PairsRobustnessReportPayload;
  warnings: string[];
}

export interface PairsBacktestJobPayload {
  job_id: string;
  job_type: 'pairs_backtest';
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | string;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  attempt_count: number;
  cancel_requested: boolean;
  request_payload: Record<string, unknown>;
  batch_mode: boolean;
  preset_id?: string | null;
  requested_tickers: string[];
  progress: BacktestJobProgressPayload;
  worker_id?: string | null;
  pairs_backtest_id?: string | null;
  result_available: boolean;
  error?: string | null;
  events: BacktestJobEventPayload[];
}

export interface BacktestJobProgressPayload {
  phase: string;
  message: string;
  percent: number;
  updated_at: string;
  current_step?: number | null;
  total_steps?: number | null;
}

export interface BacktestJobEventPayload {
  timestamp: string;
  level: string;
  phase: string;
  message: string;
  percent?: number | null;
}

export interface BacktestJobPayload {
  job_id: string;
  job_type: 'backtest';
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  attempt_count: number;
  cancel_requested: boolean;
  request_payload: Record<string, unknown>;
  config_path?: string | null;
  strategy_names: string[];
  progress: BacktestJobProgressPayload;
  worker_id?: string | null;
  run_id?: string | null;
  result_available: boolean;
  error?: string | null;
  events: BacktestJobEventPayload[];
}

export interface Trade {
  timestamp: string;
  action: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  cost?: number | null;
  pnl?: number | null;
  layer?: number | null;
  requested_quantity?: number | null;
  fill_ratio?: number | null;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  cash: number;
}

export interface SelicRateUsage {
  period?: string;
  year?: number;
  month?: number;
  rate: number;
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
  total_fees_paid?: number;
  total_dividends_received?: number;
  selic_rates_used?: SelicRateUsage[];
}

export interface ExecutionEvent {
  timestamp: string;
  event_type: string;
  side: string;
  requested_quantity: number;
  filled_quantity: number;
  fill_ratio: number;
  requested_price: number;
  fill_price?: number | null;
  fees: number;
  slippage: number;
  message: string;
}

export interface ExecutionSummary {
  fill_count: number;
  partial_fill_count: number;
  rejected_buy_count: number;
  rejected_sell_count: number;
  rejected_order_count: number;
  liquidity_constrained: boolean;
  requested_quantity_total: number;
  filled_quantity_total: number;
}

export interface StrategyResult {
  strategy_name: string;
  equity: EquityPoint[];
  trades: Trade[];
  metrics: StrategyMetrics;
  start_price: number;
  end_price: number;
  execution_log?: ExecutionEvent[];
  execution_summary?: ExecutionSummary;
  warnings?: string[];
}

export interface BenchmarkResult {
  name: string;
  ticker: string;
  equity: EquityPoint[];
  metrics: StrategyMetrics;
}

export interface RunQualityIssue {
  status: 'legacy_invalid' | string;
  code: string;
  title: string;
  message: string;
  details?: Record<string, unknown>;
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
  fee_rate?: number;
  fixed_fee?: number;
  buy_slippage?: number;
  sell_slippage?: number;
  max_volume_participation?: number;
  allow_partial_fills?: boolean;
  min_fill_quantity?: number;
  // Benchmark fields
  benchmarks?: string[];
  include_selic_benchmark?: boolean;
  include_buy_hold_benchmark?: boolean;
}

export interface Wege3RegraARunRequestPayload {
  start_date?: string;
  end_date?: string | null;
  force_download?: boolean;
}

export interface Wege3RegraATradePayload {
  timestamp: string;
  action: string;
  price: number;
  notional: number;
  quantity: number;
  cash_after: number;
  position_after: number;
  reference_after: number;
}

export interface Wege3RegraAArtifactsPayload {
  summary_output_path: string;
  trades_output_path: string;
  comparison_output_path?: string | null;
  comparison_trades_output_path?: string | null;
  search_output_path?: string | null;
}

export interface Wege3RegraAScenarioPayload {
  scenario_id: string;
  scenario_label: string;
  generated_at: string;
  request: Record<string, unknown>;
  assumptions: Record<string, unknown>;
  dataset: Record<string, unknown>;
  result: Record<string, unknown>;
  statistics: Record<string, unknown>;
  benchmarks: Record<string, Record<string, unknown>>;
  audit: Record<string, unknown>;
  comparison_variants: Array<Record<string, unknown>>;
  best_strategy: Record<string, unknown>;
  parameter_search: Record<string, unknown>;
  strategy_context: Record<string, unknown>;
  comparison_chart: Record<string, unknown>;
  trades: Wege3RegraATradePayload[];
  artifacts: Wege3RegraAArtifactsPayload;
  reproduction_command: string;
}

export interface BacktestStrategyCatalogPayload {
  title: string;
  plain_language_summary: string;
  generated_at: string;
  strategies: Array<{
    strategy_id: string;
    label: string;
    family: string;
    direction: string;
    required_inputs: string[];
    parameter_defaults?: Record<string, string | number | boolean | null>;
    universe_defaults?: string[];
    supported_timeframes: string[];
    execution_notes?: string[];
    risk_notes: string[];
  }>;
  score_dimensions: Array<{
    dimension_id: string;
    label: string;
    description: string;
  }>;
  radar_plan: string[];
}

export interface BacktestResponse {
  results: Record<string, StrategyResult>;
  buy_hold_equity: EquityPoint[];
  benchmarks?: Record<string, BenchmarkResult>;
  run_quality?: RunQualityIssue | null;
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
  warnings?: string[];
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
  run_quality?: RunQualityIssue | null;
}

export interface ExperimentLineagePayload {
  source_run_id?: string;
  best_run_id?: string;
  parent_optimization_id?: string;
}

export interface ExperimentRegistryRecord {
  experiment_id: string;
  experiment_type: 'run' | 'optimization' | 'walkforward' | 'montecarlo' | 'pairs_backtest';
  created_at: string;
  config_path?: string | null;
  strategy_names: string[];
  artifact_dir: string;
  status: string;
  lineage: ExperimentLineagePayload;
  summary: Record<string, unknown>;
}

export interface ExperimentDetailPayload {
  record: ExperimentRegistryRecord;
  manifest: Record<string, unknown>;
  related_experiments: ExperimentRelationPayload[];
}

export interface ExperimentRelationPayload {
  relationship:
    | 'best_run'
    | 'source_run'
    | 'parent_optimization'
    | 'best_run_for_optimization'
    | 'source_run_for_montecarlo'
    | 'child_of_optimization';
  record: ExperimentRegistryRecord;
}

export interface ResearchWorkspaceSelectionPayload {
  optimization_id?: string | null;
  walkforward_id?: string | null;
  montecarlo_id?: string | null;
  anchor_run_id?: string | null;
}

export interface ResearchWorkspacePayload {
  workspace_id: string;
  created_at: string;
  name: string;
  notes?: string | null;
  selected_experiment: {
    experiment_type: ExperimentRegistryRecord['experiment_type'];
    experiment_id: string;
  };
  selection: ResearchWorkspaceSelectionPayload;
  records: {
    selected: ExperimentRegistryRecord;
    optimization?: ExperimentRegistryRecord | null;
    walkforward?: ExperimentRegistryRecord | null;
    montecarlo?: ExperimentRegistryRecord | null;
    anchor_run?: ExperimentRegistryRecord | null;
  };
}

export interface ResearchWorkspaceReportPayload {
  title: string;
  executive_summary: string;
  highlights: string[];
  risks: string[];
  key_metrics: Array<{
    label: string;
    value: string;
  }>;
  markdown: string;
  html: string;
}

export interface ResearchWorkspaceReportEnvelope {
  workspace: ResearchWorkspacePayload;
  report: ResearchWorkspaceReportPayload;
}

export interface ResearchWorkspaceCreatePayload {
  name?: string;
  notes?: string;
  selected_experiment_type: ExperimentRegistryRecord['experiment_type'];
  selected_experiment_id: string;
  optimization_id?: string | null;
  walkforward_id?: string | null;
  montecarlo_id?: string | null;
  anchor_run_id?: string | null;
}

export interface ResearchWorkspaceUpdatePayload {
  name?: string;
  notes?: string;
}

export interface ResearchWorkspaceImportPayload {
  payload: ResearchWorkspacePayload;
}

export interface AllocationHoldingPayload {
  asset: string;
  quantity: number;
}

export interface AllocationTargetPayload {
  asset: string;
  target_weight: number;
}

export interface AllocationPlanRequestPayload {
  cash: number;
  holdings: AllocationHoldingPayload[];
  prices: Record<string, number>;
  targets: AllocationTargetPayload[];
  weight_tolerance?: number;
  min_trade_notional?: number;
  reserve_cash?: number;
}

export interface AllocationActionPayload {
  asset: string;
  action: "buy" | "sell" | "hold";
  price: number;
  current_quantity: number;
  current_value: number;
  current_weight: number;
  target_quantity: number;
  target_value: number;
  target_weight: number;
  quantity_delta: number;
  notional_delta: number;
  drift_weight: number;
  projected_quantity: number;
  reason: string;
}

export interface AllocationPlanResponsePayload {
  total_equity: number;
  current_cash: number;
  target_cash: number;
  projected_cash: number;
  current_cash_weight: number;
  target_cash_weight: number;
  turnover_notional: number;
  turnover_ratio: number;
  cash_gap_to_target: number;
  max_abs_drift_weight: number;
  needs_rebalance: boolean;
  actions: AllocationActionPayload[];
  warnings: string[];
}

export interface AllocationWorkspaceSummaryPayload {
  asset_count: number;
  assets: string[];
  buy_count: number;
  sell_count: number;
  hold_count: number;
  needs_rebalance: boolean;
  turnover_ratio: number;
  turnover_notional: number;
  total_equity: number;
  current_cash_weight: number;
  target_cash_weight: number;
  projected_cash: number;
  reserve_cash: number;
  max_abs_drift_weight: number;
}

export interface AllocationWorkspacePayload {
  workspace_id: string;
  created_at: string;
  name: string;
  notes?: string | null;
  request: AllocationPlanRequestPayload;
  plan: AllocationPlanResponsePayload;
  summary: AllocationWorkspaceSummaryPayload;
}

export interface AllocationWorkspaceCreatePayload {
  name?: string;
  notes?: string;
  request: AllocationPlanRequestPayload;
}

export interface AllocationWorkspaceUpdatePayload {
  name?: string;
  notes?: string;
}

export interface AllocationWorkspaceImportPayload {
  payload: AllocationWorkspacePayload;
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
  refresh_due: boolean;
  next_refresh_due_at?: string | null;
}

export interface DatasetRefreshPolicy {
  enabled: boolean;
  interval_days: number;
  start_date: string;
  end_date?: string | null;
  next_refresh_due_at?: string | null;
  due_now: boolean;
}

export interface DatasetDetail extends DatasetSummary {
  preview_rows: Array<Record<string, unknown>>;
  validation_warnings: string[];
  validation?: {
    datetime_index_detected: boolean;
    duplicate_index_count: number;
    missing_value_count: number;
    date_gap_count: number;
    missing_required_columns: string[];
    price_anomaly_count: number;
    supported_refresh: boolean;
  } | null;
  provenance?: {
    managed: boolean;
    source_kind: string;
    source_path?: string | null;
    refresh_strategy?: string | null;
    imported_at?: string | null;
    last_refreshed_at?: string | null;
    refresh_policy?: DatasetRefreshPolicy | null;
    history: Array<{
      event_type: string;
      occurred_at: string;
      details: Record<string, unknown>;
    }>;
  } | null;
}

export interface DatasetImportRequestPayload {
  source_path: string;
  dataset_name?: string;
  overwrite?: boolean;
}

export interface DatasetRefreshRequestPayload {
  start_date: string;
  end_date?: string;
}

export interface DatasetRefreshPolicyRequestPayload {
  enabled: boolean;
  interval_days: number;
  start_date: string;
  end_date?: string;
}

export interface DatasetRefreshDueRequestPayload {
  limit?: number;
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
