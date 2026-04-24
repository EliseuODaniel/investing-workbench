import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  InvestmentCatalogPayload,
  InvestmentCompareRequestPayload,
  InvestmentComparisonResponsePayload,
  InvestmentCustomPortfolioRequestPayload,
} from '../types/api';

const DEFAULT_REQUEST: InvestmentCompareRequestPayload = {
  asset_ids: [],
  custom_portfolios: [],
  start_date: '2021-01-01',
  end_date: '',
  initial_capital: 10000,
  monthly_contribution: 500,
  benchmark_ids: ['selic_cash', 'bova11'],
  fixed_income_study_mode: 'auto',
  fixed_income_tax_treatment: 'gross',
  fixed_income_window_frequency: 'monthly',
  decision_profile: {
    objective: 'balanced',
    horizon_years: 5,
    liquidity_need: 'monthly',
    mark_to_market_tolerance: 'medium',
    tax_view: 'gross',
    monthly_income_target: 0,
  },
  force_download: false,
};

export function useInvestmentsComparison(onError: (message: string | null) => void) {
  const [catalog, setCatalog] = useState<InvestmentCatalogPayload | null>(null);
  const [request, setRequest] = useState<InvestmentCompareRequestPayload>(DEFAULT_REQUEST);
  const [comparison, setComparison] = useState<InvestmentComparisonResponsePayload | null>(null);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('sardinha_40_plus');
  const [isLoadingCatalog, setIsLoadingCatalog] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [isCustomPortfolioEnabled, setIsCustomPortfolioEnabled] = useState(false);
  const [customPortfolioName, setCustomPortfolioName] = useState('Minha carteira');
  const [customPortfolioDescription, setCustomPortfolioDescription] = useState(
    'Carteira personalizada para comparar a alocacao contra ativos e carteiras guiadas.'
  );
  const [customPortfolioWeights, setCustomPortfolioWeights] = useState<Record<string, number>>({});

  const selectedPreset = useMemo(
    () => catalog?.presets.find((preset) => preset.preset_id === selectedPresetId) ?? null,
    [catalog, selectedPresetId]
  );

  const customPortfolioAssets = useMemo(() => {
    if (!catalog) {
      return [];
    }
    const selectedIds = new Set(request.asset_ids ?? []);
    return catalog.instruments.filter(
      (instrument) =>
        selectedIds.has(instrument.instrument_id) &&
        instrument.source_kind !== 'model_portfolio' &&
        instrument.source_kind !== 'custom_portfolio'
    );
  }, [catalog, request.asset_ids]);

  const applyPreset = useCallback(
    (presetId: string) => {
      if (!catalog) {
        return;
      }
      const preset = catalog.presets.find((item) => item.preset_id === presetId);
      if (!preset) {
        return;
      }
      setSelectedPresetId(presetId);
      setRequest((current) => ({
        ...current,
        asset_ids: preset.asset_ids,
        custom_portfolios: [],
        start_date: preset.default_start_date ?? current.start_date,
        end_date: preset.default_end_date ?? '',
        initial_capital: preset.default_initial_capital ?? current.initial_capital,
        monthly_contribution:
          preset.default_monthly_contribution ?? current.monthly_contribution,
        benchmark_ids:
          preset.default_benchmark_ids !== undefined && preset.default_benchmark_ids !== null
            ? preset.default_benchmark_ids
            : current.benchmark_ids,
        fixed_income_study_mode:
          preset.default_fixed_income_study_mode ?? current.fixed_income_study_mode,
        fixed_income_tax_treatment:
          preset.default_fixed_income_tax_treatment ?? current.fixed_income_tax_treatment,
        fixed_income_window_frequency:
          preset.default_fixed_income_window_frequency ?? current.fixed_income_window_frequency,
      }));
    },
    [catalog]
  );

  const loadCatalog = useCallback(async () => {
    setIsLoadingCatalog(true);
    try {
      const response = await apiClient.getInvestmentCatalog();
      setCatalog(response);
      const defaultPreset =
        response.presets.find((preset) => preset.preset_id === 'sardinha_40_plus') ??
        response.presets.find((preset) => preset.preset_id === 'balanced_b3') ??
        response.presets[0] ??
        null;
      if (defaultPreset) {
        setSelectedPresetId(defaultPreset.preset_id);
        setRequest((current) => ({
          ...current,
          asset_ids: defaultPreset.asset_ids,
          custom_portfolios: [],
          start_date: defaultPreset.default_start_date ?? current.start_date,
          end_date: defaultPreset.default_end_date ?? '',
          initial_capital: defaultPreset.default_initial_capital ?? current.initial_capital,
          monthly_contribution:
            defaultPreset.default_monthly_contribution ?? current.monthly_contribution,
          benchmark_ids:
            defaultPreset.default_benchmark_ids !== undefined &&
            defaultPreset.default_benchmark_ids !== null
              ? defaultPreset.default_benchmark_ids
              : current.benchmark_ids,
          fixed_income_study_mode:
            defaultPreset.default_fixed_income_study_mode ?? current.fixed_income_study_mode,
          fixed_income_tax_treatment:
            defaultPreset.default_fixed_income_tax_treatment ??
            current.fixed_income_tax_treatment,
          fixed_income_window_frequency:
            defaultPreset.default_fixed_income_window_frequency ??
            current.fixed_income_window_frequency,
        }));
      }
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load investment catalog');
    } finally {
      setIsLoadingCatalog(false);
    }
  }, [onError]);

  const updateRequest = <K extends keyof InvestmentCompareRequestPayload>(
    key: K,
    value: InvestmentCompareRequestPayload[K]
  ) => {
    setRequest((current) => ({ ...current, [key]: value }));
  };

  const toggleAsset = (instrumentId: string) => {
    setRequest((current) => {
      const currentIds = current.asset_ids ?? [];
      const alreadySelected = currentIds.includes(instrumentId);
      return {
        ...current,
        custom_portfolios: [],
        asset_ids: alreadySelected
          ? currentIds.filter((item) => item !== instrumentId)
          : [...currentIds, instrumentId],
      };
    });
  };

  const toggleBenchmark = (benchmarkId: string) => {
    setRequest((current) => {
      const currentIds = current.benchmark_ids ?? [];
      const alreadySelected = currentIds.includes(benchmarkId);
      return {
        ...current,
        benchmark_ids: alreadySelected
          ? currentIds.filter((item) => item !== benchmarkId)
          : [...currentIds, benchmarkId],
      };
    });
  };

  useEffect(() => {
    setCustomPortfolioWeights((current) => {
      const next: Record<string, number> = {};
      for (const instrument of customPortfolioAssets) {
        next[instrument.instrument_id] =
          current[instrument.instrument_id] ?? Math.max(1, 100 / customPortfolioAssets.length);
      }
      return next;
    });
  }, [customPortfolioAssets]);

  const buildCustomPortfolios = useCallback((): InvestmentCustomPortfolioRequestPayload[] => {
    if (!isCustomPortfolioEnabled) {
      return [];
    }
    const components = customPortfolioAssets
      .map((instrument) => ({
        component_id: instrument.instrument_id,
        weight: Math.max(0, customPortfolioWeights[instrument.instrument_id] ?? 0),
      }))
      .filter((component) => component.weight > 0);
    if (components.length < 2) {
      return [];
    }
    return [
      {
        portfolio_id: 'CUSTOM_PORTFOLIO_MINHA_CARTEIRA',
        label: customPortfolioName.trim() || 'Minha carteira',
        description:
          customPortfolioDescription.trim() ||
          'Carteira personalizada para comparar alocacoes no mesmo fluxo de aportes.',
        rebalance_frequency: 'monthly',
        components,
      },
    ];
  }, [
    customPortfolioAssets,
    customPortfolioDescription,
    customPortfolioName,
    customPortfolioWeights,
    isCustomPortfolioEnabled,
  ]);

  const updateCustomPortfolioWeight = (instrumentId: string, value: number) => {
    setCustomPortfolioWeights((current) => ({
      ...current,
      [instrumentId]: Math.max(0, value),
    }));
  };

  const compare = async () => {
    setIsComparing(true);
    onError(null);
    try {
      const customPortfolios = buildCustomPortfolios();
      const payload: InvestmentCompareRequestPayload = {
        ...request,
        end_date: request.end_date || null,
        custom_portfolios: customPortfolios,
      };
      const response = await apiClient.compareInvestments(payload);
      setComparison(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to compare investments');
    } finally {
      setIsComparing(false);
    }
  };

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  return {
    catalog,
    comparison,
    request,
    selectedPreset,
    selectedPresetId,
    isLoadingCatalog,
    isComparing,
    isCustomPortfolioEnabled,
    customPortfolioName,
    customPortfolioDescription,
    customPortfolioWeights,
    customPortfolioAssets,
    applyPreset,
    updateRequest,
    toggleAsset,
    toggleBenchmark,
    setIsCustomPortfolioEnabled,
    setCustomPortfolioName,
    setCustomPortfolioDescription,
    updateCustomPortfolioWeight,
    compare,
    reloadCatalog: loadCatalog,
  };
}
