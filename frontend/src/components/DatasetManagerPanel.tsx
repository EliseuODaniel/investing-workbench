import DatasetCatalogList from './dataset-manager/DatasetCatalogList';
import DatasetDetailPanel from './dataset-manager/DatasetDetailPanel';
import DatasetImportCard from './dataset-manager/DatasetImportCard';
import DatasetManagerHeader from './dataset-manager/DatasetManagerHeader';
import DatasetRefreshQueue from './dataset-manager/DatasetRefreshQueue';
import { DatasetManagerPanelProps } from './dataset-manager/types';
import { useDatasets } from '../hooks/useDatasets';
import { useDatasetManagerPanelState } from '../hooks/useDatasetManagerPanelState';

export default function DatasetManagerPanel({
  currentCachePath,
  onApplyDataset,
  onError,
}: DatasetManagerPanelProps) {
  const datasetsState = useDatasets(onError);
  const panelState = useDatasetManagerPanelState({
    selectedDataset: datasetsState.selectedDataset,
    importDataset: datasetsState.importDataset,
    refreshDataset: datasetsState.refreshDataset,
    updateRefreshPolicy: datasetsState.updateRefreshPolicy,
  });

  return (
    <div className="card mt-6">
      <DatasetManagerHeader
        dueCount={datasetsState.dueDatasets.length}
        isLoadingDatasets={datasetsState.isLoadingDatasets}
        isRefreshingDueDatasets={datasetsState.isRefreshingDueDatasets}
        onRefreshDatasets={datasetsState.refreshDatasets}
        onRefreshDueDatasets={() => {
          void datasetsState.refreshDueDatasets();
        }}
      />

      <div className="space-y-4">
        <DatasetRefreshQueue dueDatasets={datasetsState.dueDatasets} />

        <DatasetImportCard
          sourcePath={panelState.sourcePath}
          datasetName={panelState.datasetName}
          isImportingDataset={datasetsState.isImportingDataset}
          onSourcePathChange={panelState.setSourcePath}
          onDatasetNameChange={panelState.setDatasetName}
          onImport={() => {
            void panelState.handleImport();
          }}
        />

        <DatasetCatalogList
          datasets={datasetsState.datasets}
          selectedDatasetId={datasetsState.selectedDatasetId}
          currentCachePath={currentCachePath}
          isLoadingDatasets={datasetsState.isLoadingDatasets}
          onSelectDataset={(datasetId) => {
            void datasetsState.loadDataset(datasetId);
          }}
        />

        <DatasetDetailPanel
          selectedDataset={datasetsState.selectedDataset}
          isLoadingSelectedDataset={datasetsState.isLoadingSelectedDataset}
          isRefreshingDataset={datasetsState.isRefreshingDataset}
          isUpdatingRefreshPolicy={datasetsState.isUpdatingRefreshPolicy}
          policyEnabled={panelState.policyEnabled}
          policyIntervalDays={panelState.policyIntervalDays}
          policyStartDate={panelState.policyStartDate}
          policyEndDate={panelState.policyEndDate}
          onApplyDataset={onApplyDataset}
          onPolicyEnabledChange={panelState.setPolicyEnabled}
          onPolicyIntervalDaysChange={panelState.setPolicyIntervalDays}
          onPolicyStartDateChange={panelState.handlePolicyStartDateChange}
          onPolicyEndDateChange={panelState.setPolicyEndDate}
          onSavePolicy={() => {
            void panelState.handleSavePolicy();
          }}
          onRefreshNow={() => {
            void panelState.handleRefreshNow();
          }}
        />
      </div>
    </div>
  );
}
