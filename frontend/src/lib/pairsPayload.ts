import {
  PairsBacktestRequestPayload,
  PairsBatchRequestPayload,
  PairsScreenRequestPayload,
  PairsScenarioVariantPayload,
  PairsUniverseResolveRequestPayload,
} from '../types/api';

export interface PairsDraft {
  presetId: string;
  tickersText: string;
  startDate: string;
  endDate: string;
  asOfDate: string;
  formationWindowText: string;
  testWindowText: string;
  stepWindowText: string;
  maxPairsText: string;
  topNText: string;
  minPriceText: string;
  minMedianNotionalText: string;
  minReturnCorrText: string;
  minLevelCorrText: string;
  maxCointPvalueText: string;
  minHalfLifeText: string;
  maxHalfLifeText: string;
  minStabilityScoreText: string;
  maxStructuralBreakRiskText: string;
  minBetaAbsText: string;
  maxBetaAbsText: string;
  entryZscoreText: string;
  exitZscoreText: string;
  stopZscoreText: string;
  maxHoldingDaysText: string;
  pairAllocationPctText: string;
  initialCapitalText: string;
  zscoreWindowText: string;
  feeRateText: string;
  slippageText: string;
  shortBorrowRateText: string;
  proxyMinShortScoreText: string;
  borrowSnapshotPathText: string;
  targetPairVolatilityText: string;
  maxGrossExposurePctText: string;
  maxNetExposurePctText: string;
  maxSectorPairsText: string;
  benchmarkIdsText: string;
  researchEntryZscoresText: string;
  researchExitZscoresText: string;
  researchZscoreWindowsText: string;
  researchMaxPairsText: string;
  useProxyShortBorrow: boolean;
  requireCointegration: boolean;
  applyCashYield: boolean;
  useRealSelic: boolean;
  explicitMarginModel: boolean;
  dynamicBeta: boolean;
  researchIncludeDynamicBeta: boolean;
  portfolioConstruction: 'equal_notional' | 'risk_parity';
  regimeFilter: 'none' | 'ma_deviation_and_vol';
}

export interface PairsSetupHandoff {
  source: 'strategy_setup_radar';
  strategy_id: string;
  label: string;
  created_at: string;
  draft: Partial<PairsDraft>;
}

export const PAIRS_SETUP_HANDOFF_STORAGE_KEY =
  'investing-workbench.pairs-setup-handoff.v1';

function parseTickers(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}

function parseList(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseNumberList(value: string): number[] {
  return value
    .split(',')
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isFinite(item));
}

function parseOptionalString(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function parseNumber(value: string): number {
  return Number(value);
}

function buildCommonPayload(draft: PairsDraft): PairsUniverseResolveRequestPayload {
  const tickers = parseTickers(draft.tickersText);
  return {
    preset_id: draft.presetId,
    tickers: tickers.length > 0 ? tickers : undefined,
    as_of_date: parseOptionalString(draft.asOfDate),
    start_date: draft.startDate,
    end_date: parseOptionalString(draft.endDate),
    min_price: parseNumber(draft.minPriceText),
    min_median_notional_brl: parseNumber(draft.minMedianNotionalText),
    use_proxy_short_borrow: draft.useProxyShortBorrow,
    proxy_min_short_score: parseNumber(draft.proxyMinShortScoreText),
    borrow_snapshot_path: parseOptionalString(draft.borrowSnapshotPathText),
  };
}

export function buildPairsScreenPayload(draft: PairsDraft): PairsScreenRequestPayload {
  return {
    ...buildCommonPayload(draft),
    formation_window: parseNumber(draft.formationWindowText),
    test_window: parseNumber(draft.testWindowText),
    max_pairs: parseNumber(draft.maxPairsText),
    top_n: parseNumber(draft.topNText),
    min_return_corr: parseNumber(draft.minReturnCorrText),
    min_level_corr: parseNumber(draft.minLevelCorrText),
    max_coint_pvalue: parseNumber(draft.maxCointPvalueText),
    min_half_life: parseNumber(draft.minHalfLifeText),
    max_half_life: parseNumber(draft.maxHalfLifeText),
    min_stability_score: parseNumber(draft.minStabilityScoreText),
    max_structural_break_risk: parseNumber(draft.maxStructuralBreakRiskText),
    min_beta_abs: parseNumber(draft.minBetaAbsText),
    max_beta_abs: parseNumber(draft.maxBetaAbsText),
    require_cointegration: draft.requireCointegration,
  };
}

export function buildPairsBacktestPayload(draft: PairsDraft): PairsBacktestRequestPayload {
  return {
    ...buildPairsScreenPayload(draft),
    step_window: parseNumber(draft.stepWindowText),
    entry_zscore: parseNumber(draft.entryZscoreText),
    exit_zscore: parseNumber(draft.exitZscoreText),
    stop_zscore: parseNumber(draft.stopZscoreText),
    max_holding_days: parseNumber(draft.maxHoldingDaysText),
    pair_allocation_pct: parseNumber(draft.pairAllocationPctText),
    initial_capital: parseNumber(draft.initialCapitalText),
    zscore_window: parseNumber(draft.zscoreWindowText),
    fee_rate: parseNumber(draft.feeRateText),
    slippage: parseNumber(draft.slippageText),
    short_borrow_rate_annual: parseNumber(draft.shortBorrowRateText),
    portfolio_construction: draft.portfolioConstruction,
    target_pair_volatility_annual: parseNumber(draft.targetPairVolatilityText),
    max_gross_exposure_pct: parseNumber(draft.maxGrossExposurePctText),
    max_net_exposure_pct: parseNumber(draft.maxNetExposurePctText),
    max_sector_pairs: parseNumber(draft.maxSectorPairsText),
    benchmark_ids: parseList(draft.benchmarkIdsText),
    apply_cash_yield: draft.applyCashYield,
    use_real_selic: draft.useRealSelic,
    explicit_margin_model: draft.explicitMarginModel,
    dynamic_beta: draft.dynamicBeta,
    regime_filter: draft.regimeFilter,
  };
}

export function buildPairsBatchPayload(draft: PairsDraft): PairsBatchRequestPayload {
  return buildPairsBacktestPayload(draft);
}

function scenarioIdSuffix(value: number): string {
  return String(value).replace('.', '_').replace('-', 'neg_');
}

export function buildPairsResearchBatchPayload(draft: PairsDraft): PairsBatchRequestPayload {
  const basePayload = buildPairsBacktestPayload(draft);
  const baseEntry = parseNumber(draft.entryZscoreText);
  const baseExit = parseNumber(draft.exitZscoreText);
  const baseWindow = parseNumber(draft.zscoreWindowText);
  const baseMaxPairs = parseNumber(draft.maxPairsText);

  const scenarioVariants: PairsScenarioVariantPayload[] = [
    {
      scenario_id: 'realistic_cointegration',
      label: 'Realistic cointegration',
      require_cointegration: true,
      overrides: {},
    },
  ];

  for (const value of parseNumberList(draft.researchEntryZscoresText)) {
    if (value === baseEntry) {
      continue;
    }
    scenarioVariants.push({
      scenario_id: `entry_z_${scenarioIdSuffix(value)}`,
      label: `Entry z ${value.toFixed(2)}`,
      require_cointegration: draft.requireCointegration,
      overrides: { entry_zscore: value },
    });
  }

  for (const value of parseNumberList(draft.researchExitZscoresText)) {
    if (value === baseExit) {
      continue;
    }
    scenarioVariants.push({
      scenario_id: `exit_z_${scenarioIdSuffix(value)}`,
      label: `Exit z ${value.toFixed(2)}`,
      require_cointegration: draft.requireCointegration,
      overrides: { exit_zscore: value },
    });
  }

  for (const value of parseNumberList(draft.researchZscoreWindowsText)) {
    if (value === baseWindow) {
      continue;
    }
    scenarioVariants.push({
      scenario_id: `z_window_${scenarioIdSuffix(value)}`,
      label: `Z window ${value}`,
      require_cointegration: draft.requireCointegration,
      overrides: { zscore_window: value },
    });
  }

  for (const value of parseNumberList(draft.researchMaxPairsText)) {
    if (value === baseMaxPairs) {
      continue;
    }
    scenarioVariants.push({
      scenario_id: `max_pairs_${scenarioIdSuffix(value)}`,
      label: `Max pairs ${value}`,
      require_cointegration: draft.requireCointegration,
      overrides: { max_pairs: value },
    });
  }

  if (draft.researchIncludeDynamicBeta && !draft.dynamicBeta) {
    scenarioVariants.push({
      scenario_id: 'dynamic_beta',
      label: 'Dynamic beta',
      require_cointegration: draft.requireCointegration,
      overrides: { dynamic_beta: true },
    });
  }

  scenarioVariants.push(
    {
      scenario_id: 'frictionless_cointegration',
      label: 'Frictionless cointegration',
      require_cointegration: true,
      overrides: {
        fee_rate: 0.0,
        slippage: 0.0,
        short_borrow_rate_annual: 0.0,
        use_proxy_short_borrow: false,
      },
    },
    {
      scenario_id: 'no_cointegration_filter',
      label: 'No cointegration filter',
      require_cointegration: false,
      overrides: {},
    }
  );

  return {
    ...basePayload,
    scenario_variants: scenarioVariants,
  };
}

export function readPairsSetupHandoff(): PairsSetupHandoff | null {
  if (typeof window === 'undefined') {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(PAIRS_SETUP_HANDOFF_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!isPairsSetupHandoff(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function isPairsSetupHandoff(value: unknown): value is PairsSetupHandoff {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as Partial<PairsSetupHandoff>;
  return (
    candidate.source === 'strategy_setup_radar' &&
    typeof candidate.strategy_id === 'string' &&
    typeof candidate.label === 'string' &&
    typeof candidate.created_at === 'string' &&
    typeof candidate.draft === 'object'
  );
}
