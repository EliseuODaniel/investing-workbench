import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import { DatasetDetail, DatasetSummary } from '../types/api';

export function useDatasets(onError: (message: string | null) => void) {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<DatasetDetail | null>(null);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
  const [isLoadingSelectedDataset, setIsLoadingSelectedDataset] = useState(false);

  const selectedSummary = useMemo(
    () =>
      selectedDatasetId
        ? datasets.find((dataset) => dataset.dataset_id === selectedDatasetId) ?? null
        : null,
    [datasets, selectedDatasetId]
  );

  const refreshDatasets = useCallback(async () => {
    setIsLoadingDatasets(true);
    try {
      const response = await apiClient.listDatasets();
      setDatasets(response);
      if (!selectedDatasetId && response.length > 0) {
        setSelectedDatasetId(response[0].dataset_id);
      }
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load dataset catalog');
    } finally {
      setIsLoadingDatasets(false);
    }
  }, [onError, selectedDatasetId]);

  const loadDataset = useCallback(
    async (datasetId: string) => {
      setSelectedDatasetId(datasetId);
      setIsLoadingSelectedDataset(true);
      try {
        const response = await apiClient.getDataset(datasetId);
        setSelectedDataset(response);
      } catch (error: any) {
        onError(error.response?.data?.detail || 'Failed to load dataset details');
      } finally {
        setIsLoadingSelectedDataset(false);
      }
    },
    [onError]
  );

  useEffect(() => {
    refreshDatasets();
  }, [refreshDatasets]);

  useEffect(() => {
    if (selectedDatasetId) {
      loadDataset(selectedDatasetId);
    }
  }, [loadDataset, selectedDatasetId]);

  return {
    datasets,
    selectedDatasetId,
    selectedDataset,
    selectedSummary,
    isLoadingDatasets,
    isLoadingSelectedDataset,
    refreshDatasets,
    loadDataset,
  };
}
