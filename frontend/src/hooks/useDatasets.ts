import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import { DatasetDetail, DatasetSummary } from '../types/api';

export function useDatasets(onError: (message: string | null) => void) {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<DatasetDetail | null>(null);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
  const [isLoadingSelectedDataset, setIsLoadingSelectedDataset] = useState(false);
  const [isImportingDataset, setIsImportingDataset] = useState(false);
  const [isRefreshingDataset, setIsRefreshingDataset] = useState(false);

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

  const importDataset = useCallback(
    async (sourcePath: string, datasetName?: string, overwrite?: boolean) => {
      setIsImportingDataset(true);
      try {
        const response = await apiClient.importDataset({
          source_path: sourcePath,
          dataset_name: datasetName || undefined,
          overwrite: overwrite || false,
        });
        await refreshDatasets();
        setSelectedDatasetId(response.dataset_id);
        setSelectedDataset(response);
        return response;
      } catch (error: any) {
        onError(error.response?.data?.detail || 'Failed to import dataset');
        return null;
      } finally {
        setIsImportingDataset(false);
      }
    },
    [onError, refreshDatasets]
  );

  const refreshDataset = useCallback(
    async (datasetId: string, startDate: string, endDate?: string) => {
      setIsRefreshingDataset(true);
      try {
        const response = await apiClient.refreshDataset(datasetId, {
          start_date: startDate,
          end_date: endDate || undefined,
        });
        await refreshDatasets();
        setSelectedDataset(response);
        return response;
      } catch (error: any) {
        onError(error.response?.data?.detail || 'Failed to refresh dataset');
        return null;
      } finally {
        setIsRefreshingDataset(false);
      }
    },
    [onError, refreshDatasets]
  );

  return {
    datasets,
    selectedDatasetId,
    selectedDataset,
    selectedSummary,
    isLoadingDatasets,
    isLoadingSelectedDataset,
    isImportingDataset,
    isRefreshingDataset,
    refreshDatasets,
    loadDataset,
    importDataset,
    refreshDataset,
  };
}
