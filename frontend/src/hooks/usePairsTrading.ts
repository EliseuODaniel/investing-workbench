import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  buildPairsBacktestPayload,
  buildPairsBatchPayload,
  buildPairsResearchBatchPayload,
  buildPairsScreenPayload,
  PairsDraft,
} from '../lib/pairsPayload';
import {
  PairsBacktestManifestPayload,
  PairsBacktestResultsPayload,
  PairsScreenPayload,
  PairsUniversePayload,
  PairsUniversePresetPayload,
} from '../types/api';

const DEFAULT_DRAFT: PairsDraft = {
  presetId: 'ibov_proxy',
  tickersText: '',
  startDate: '2021-01-01',
  endDate: '',
  asOfDate: '',
  formationWindowText: '252',
  testWindowText: '21',
  stepWindowText: '21',
  maxPairsText: '3',
  topNText: '20',
  minPriceText: '5',
  minMedianNotionalText: '90000000',
  minReturnCorrText: '0.25',
  minLevelCorrText: '0.10',
  maxCointPvalueText: '0.10',
  minHalfLifeText: '2',
  maxHalfLifeText: '60',
  minStabilityScoreText: '0.35',
  maxStructuralBreakRiskText: '0.75',
  minBetaAbsText: '0.10',
  maxBetaAbsText: '3.00',
  entryZscoreText: '2.0',
  exitZscoreText: '0.5',
  stopZscoreText: '4.0',
  maxHoldingDaysText: '30',
  pairAllocationPctText: '0.30',
  initialCapitalText: '100000',
  zscoreWindowText: '60',
  feeRateText: '0.0003',
  slippageText: '0.0005',
  shortBorrowRateText: '0.05',
  proxyMinShortScoreText: '0.35',
  borrowSnapshotPathText: '',
  targetPairVolatilityText: '0.18',
  maxGrossExposurePctText: '1.50',
  maxNetExposurePctText: '0.20',
  maxSectorPairsText: '1',
  benchmarkIdsText: 'BOVA11.SA, ^BVSP, equal_weight, selic_cash',
  researchEntryZscoresText: '1.5, 2.0, 2.5',
  researchExitZscoresText: '0.25, 0.5',
  researchZscoreWindowsText: '40, 60, 90',
  researchMaxPairsText: '2, 3, 5',
  useProxyShortBorrow: true,
  requireCointegration: true,
  applyCashYield: false,
  useRealSelic: false,
  explicitMarginModel: false,
  dynamicBeta: false,
  researchIncludeDynamicBeta: true,
  portfolioConstruction: 'equal_notional',
  regimeFilter: 'none',
};

export function usePairsTrading(onError: (message: string | null) => void) {
  const [draft, setDraft] = useState<PairsDraft>(DEFAULT_DRAFT);
  const [presets, setPresets] = useState<PairsUniversePresetPayload[]>([]);
  const [universe, setUniverse] = useState<PairsUniversePayload | null>(null);
  const [screening, setScreening] = useState<PairsScreenPayload | null>(null);
  const [latestBacktest, setLatestBacktest] = useState<PairsBacktestResultsPayload | null>(null);
  const [backtests, setBacktests] = useState<PairsBacktestManifestPayload[]>([]);
  const [selectedBacktestId, setSelectedBacktestId] = useState<string | null>(null);
  const [selectedBacktest, setSelectedBacktest] = useState<PairsBacktestResultsPayload | null>(
    null
  );
  const [isLoadingPresets, setIsLoadingPresets] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [isScreening, setIsScreening] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoadingBacktests, setIsLoadingBacktests] = useState(false);
  const [isLoadingSelected, setIsLoadingSelected] = useState(false);

  const updateDraft = <K extends keyof PairsDraft>(key: K, value: PairsDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const refreshPresets = useCallback(async () => {
    setIsLoadingPresets(true);
    try {
      const response = await apiClient.listPairsUniverses();
      setPresets(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load pairs universe presets');
    } finally {
      setIsLoadingPresets(false);
    }
  }, [onError]);

  const refreshBacktests = useCallback(async () => {
    setIsLoadingBacktests(true);
    try {
      const response = await apiClient.listPairsBacktests();
      setBacktests(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load persisted pairs backtests');
    } finally {
      setIsLoadingBacktests(false);
    }
  }, [onError]);

  const resolveUniverse = async () => {
    setIsResolving(true);
    onError(null);
    try {
      const response = await apiClient.resolvePairsUniverse(buildPairsScreenPayload(draft));
      setUniverse(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to resolve pairs universe');
    } finally {
      setIsResolving(false);
    }
  };

  const runScreen = async () => {
    setIsScreening(true);
    onError(null);
    try {
      const response = await apiClient.screenPairs(buildPairsScreenPayload(draft));
      setScreening(response);
      if (!universe) {
        setUniverse({
          preset: response.preset,
          requested_tickers: response.requested_tickers,
          resolved_as_of_date: response.resolved_as_of_date ?? null,
          start_date: draft.startDate,
          end_date: draft.endDate || null,
          common_index_days: Number(response.screening_window.formation_days || 0),
          quality_report: response.quality_report,
          assets: [],
          eligible_assets: [],
          unavailable_tickers: {},
          warnings: response.warnings,
        });
      }
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to run pairs screener');
    } finally {
      setIsScreening(false);
    }
  };

  const runBacktest = async () => {
    setIsRunning(true);
    onError(null);
    try {
      const response = await apiClient.runPairsBacktest(buildPairsBacktestPayload(draft));
      setLatestBacktest(response);
      setSelectedBacktestId(response.pairs_backtest_id);
      setSelectedBacktest(response);
      await refreshBacktests();
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to execute pairs backtest');
    } finally {
      setIsRunning(false);
    }
  };

  const runBatch = async () => {
    setIsRunning(true);
    onError(null);
    try {
      const response = await apiClient.runPairsBatchBacktest(buildPairsBatchPayload(draft));
      setLatestBacktest(response);
      setSelectedBacktestId(response.pairs_backtest_id);
      setSelectedBacktest(response);
      await refreshBacktests();
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to execute pairs batch backtest');
    } finally {
      setIsRunning(false);
    }
  };

  const runResearchBatch = async () => {
    setIsRunning(true);
    onError(null);
    try {
      const response = await apiClient.runPairsBatchBacktest(buildPairsResearchBatchPayload(draft));
      setLatestBacktest(response);
      setSelectedBacktestId(response.pairs_backtest_id);
      setSelectedBacktest(response);
      await refreshBacktests();
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to execute pairs research batch');
    } finally {
      setIsRunning(false);
    }
  };

  const loadBacktestResults = async (backtestId: string) => {
    setSelectedBacktestId(backtestId);
    setIsLoadingSelected(true);
    onError(null);
    try {
      const response = await apiClient.getPairsBacktestResults(backtestId);
      setSelectedBacktest(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load persisted pairs backtest');
    } finally {
      setIsLoadingSelected(false);
    }
  };

  useEffect(() => {
    void refreshPresets();
    void refreshBacktests();
  }, [refreshBacktests, refreshPresets]);

  return {
    draft,
    presets,
    universe,
    screening,
    latestBacktest,
    backtests,
    selectedBacktestId,
    selectedBacktest,
    isLoadingPresets,
    isResolving,
    isScreening,
    isRunning,
    isLoadingBacktests,
    isLoadingSelected,
    updateDraft,
    refreshPresets,
    refreshBacktests,
    resolveUniverse,
    runScreen,
    runBacktest,
    runBatch,
    runResearchBatch,
    loadBacktestResults,
  };
}
