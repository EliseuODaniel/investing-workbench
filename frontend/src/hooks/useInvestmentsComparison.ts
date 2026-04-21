import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  InvestmentCatalogPayload,
  InvestmentCompareRequestPayload,
  InvestmentComparisonResponsePayload,
} from '../types/api';

const DEFAULT_REQUEST: InvestmentCompareRequestPayload = {
  asset_ids: [],
  start_date: '2021-01-01',
  end_date: '',
  initial_capital: 10000,
  monthly_contribution: 500,
  benchmark_ids: ['selic_cash', 'bova11'],
  force_download: false,
};

export function useInvestmentsComparison(onError: (message: string | null) => void) {
  const [catalog, setCatalog] = useState<InvestmentCatalogPayload | null>(null);
  const [request, setRequest] = useState<InvestmentCompareRequestPayload>(DEFAULT_REQUEST);
  const [comparison, setComparison] = useState<InvestmentComparisonResponsePayload | null>(null);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('balanced_b3');
  const [isLoadingCatalog, setIsLoadingCatalog] = useState(false);
  const [isComparing, setIsComparing] = useState(false);

  const selectedPreset = useMemo(
    () => catalog?.presets.find((preset) => preset.preset_id === selectedPresetId) ?? null,
    [catalog, selectedPresetId]
  );

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
      setRequest((current) => ({ ...current, asset_ids: preset.asset_ids }));
    },
    [catalog]
  );

  const loadCatalog = useCallback(async () => {
    setIsLoadingCatalog(true);
    try {
      const response = await apiClient.getInvestmentCatalog();
      setCatalog(response);
      const defaultPreset =
        response.presets.find((preset) => preset.preset_id === 'balanced_b3') ??
        response.presets[0] ??
        null;
      if (defaultPreset) {
        setSelectedPresetId(defaultPreset.preset_id);
        setRequest((current) => ({ ...current, asset_ids: defaultPreset.asset_ids }));
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

  const compare = async () => {
    setIsComparing(true);
    onError(null);
    try {
      const payload: InvestmentCompareRequestPayload = {
        ...request,
        end_date: request.end_date || null,
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
    applyPreset,
    updateRequest,
    toggleAsset,
    toggleBenchmark,
    compare,
    reloadCatalog: loadCatalog,
  };
}
