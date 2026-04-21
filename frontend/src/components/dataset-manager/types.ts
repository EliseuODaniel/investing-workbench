import { DatasetDetail, DatasetSummary } from '../../types/api';

export interface DatasetManagerPanelProps {
  currentCachePath?: string;
  onApplyDataset: (dataset: { path: string; name: string }) => void;
  onError: (message: string | null) => void;
}

export interface DatasetManagerHeaderProps {
  dueCount: number;
  isLoadingDatasets: boolean;
  isRefreshingDueDatasets: boolean;
  onRefreshDatasets: () => void;
  onRefreshDueDatasets: () => void;
}

export interface DatasetRefreshQueueProps {
  dueDatasets: DatasetSummary[];
}

export interface DatasetImportCardProps {
  sourcePath: string;
  datasetName: string;
  isImportingDataset: boolean;
  onSourcePathChange: (value: string) => void;
  onDatasetNameChange: (value: string) => void;
  onImport: () => void;
}

export interface DatasetCatalogListProps {
  datasets: DatasetSummary[];
  selectedDatasetId: string | null;
  currentCachePath?: string;
  isLoadingDatasets: boolean;
  onSelectDataset: (datasetId: string) => void;
}

export interface DatasetDetailPanelProps {
  selectedDataset: DatasetDetail | null;
  isLoadingSelectedDataset: boolean;
  isRefreshingDataset: boolean;
  isUpdatingRefreshPolicy: boolean;
  policyEnabled: boolean;
  policyIntervalDays: string;
  policyStartDate: string;
  policyEndDate: string;
  onApplyDataset: (dataset: { path: string; name: string }) => void;
  onPolicyEnabledChange: (value: boolean) => void;
  onPolicyIntervalDaysChange: (value: string) => void;
  onPolicyStartDateChange: (value: string) => void;
  onPolicyEndDateChange: (value: string) => void;
  onSavePolicy: () => void;
  onRefreshNow: () => void;
}
