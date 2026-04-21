import { useEffect, useState } from 'react';
import { DatasetDetail } from '../types/api';

interface UseDatasetManagerPanelStateOptions {
  selectedDataset: DatasetDetail | null;
  importDataset: (
    sourcePath: string,
    datasetName?: string,
    overwrite?: boolean,
  ) => Promise<DatasetDetail | null>;
  refreshDataset: (
    datasetId: string,
    startDate: string,
    endDate?: string,
  ) => Promise<DatasetDetail | null>;
  updateRefreshPolicy: (
    datasetId: string,
    enabled: boolean,
    intervalDays: number,
    startDate: string,
    endDate?: string,
  ) => Promise<DatasetDetail | null>;
}

export function useDatasetManagerPanelState({
  selectedDataset,
  importDataset,
  refreshDataset,
  updateRefreshPolicy,
}: UseDatasetManagerPanelStateOptions) {
  const [sourcePath, setSourcePath] = useState('');
  const [datasetName, setDatasetName] = useState('');
  const [refreshStartDate, setRefreshStartDate] = useState('2020-01-01');
  const [policyEnabled, setPolicyEnabled] = useState(false);
  const [policyIntervalDays, setPolicyIntervalDays] = useState('7');
  const [policyStartDate, setPolicyStartDate] = useState('2020-01-01');
  const [policyEndDate, setPolicyEndDate] = useState('');

  useEffect(() => {
    const refreshPolicy = selectedDataset?.provenance?.refresh_policy;
    setPolicyEnabled(refreshPolicy?.enabled ?? false);
    setPolicyIntervalDays(String(refreshPolicy?.interval_days ?? 7));
    setPolicyStartDate(refreshPolicy?.start_date ?? '2020-01-01');
    setRefreshStartDate(refreshPolicy?.start_date ?? '2020-01-01');
    setPolicyEndDate(refreshPolicy?.end_date ?? '');
  }, [selectedDataset]);

  const handleImport = async () => {
    const response = await importDataset(sourcePath, datasetName || undefined, false);
    if (response) {
      setSourcePath('');
      setDatasetName('');
    }
  };

  const handleSavePolicy = async () => {
    if (!selectedDataset) {
      return null;
    }
    return updateRefreshPolicy(
      selectedDataset.dataset_id,
      policyEnabled,
      Number.parseInt(policyIntervalDays || '7', 10),
      policyStartDate,
      policyEndDate || undefined,
    );
  };

  const handleRefreshNow = async () => {
    if (!selectedDataset) {
      return null;
    }
    return refreshDataset(selectedDataset.dataset_id, refreshStartDate);
  };

  return {
    sourcePath,
    datasetName,
    refreshStartDate,
    policyEnabled,
    policyIntervalDays,
    policyStartDate,
    policyEndDate,
    setSourcePath,
    setDatasetName,
    setPolicyEnabled,
    setPolicyIntervalDays,
    setPolicyEndDate,
    handleImport,
    handleSavePolicy,
    handleRefreshNow,
    handlePolicyStartDateChange: (value: string) => {
      setPolicyStartDate(value);
      setRefreshStartDate(value);
    },
  };
}
