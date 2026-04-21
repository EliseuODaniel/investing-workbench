import axios from 'axios';
import {
  AllocationPlanRequestPayload,
  AllocationPlanResponsePayload,
  AllocationWorkspaceCreatePayload,
  AllocationWorkspaceImportPayload,
  AllocationWorkspacePayload,
  AllocationWorkspaceUpdatePayload,
  BacktestJobPayload,
  BacktestRequest,
  BacktestResponse,
  ConfigInfo,
  DatasetDetail,
  DatasetImportRequestPayload,
  DatasetRefreshDueRequestPayload,
  DatasetRefreshPolicyRequestPayload,
  DatasetRefreshRequestPayload,
  DatasetSummary,
  ExperimentDetailPayload,
  ExperimentRegistryRecord,
  InvestmentCatalogPayload,
  InvestmentCompareRequestPayload,
  InvestmentComparisonResponsePayload,
  MonteCarloManifest,
  MonteCarloRequestPayload,
  MonteCarloResultsPayload,
  OptimizationManifest,
  OptimizationPlan,
  OptimizationRequestPayload,
  OptimizationResultsPayload,
  PairsBacktestManifestPayload,
  PairsBacktestJobPayload,
  PairsBacktestRequestPayload,
  PairsBacktestResultsPayload,
  PairsBatchRequestPayload,
  PairsScreenPayload,
  PairsScreenRequestPayload,
  PairsUniversePayload,
  PairsUniversePresetPayload,
  PairsUniverseResolveRequestPayload,
  ResearchWorkspaceCreatePayload,
  ResearchWorkspaceImportPayload,
  ResearchWorkspacePayload,
  ResearchWorkspaceReportEnvelope,
  ResearchWorkspaceUpdatePayload,
  RunConfigSnapshot,
  RunDataProfile,
  RunSummary,
  WalkForwardManifest,
  WalkForwardRequestPayload,
  WalkForwardResultsPayload,
  SystemStatusPayload,
  Wege3RegraARunRequestPayload,
  Wege3RegraAScenarioPayload,
} from '../types/api';

const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
});

export const apiClient = {
  getConfigs: async (): Promise<ConfigInfo[]> => {
    const response = await api.get('/configs');
    return response.data;
  },

  getSystemStatus: async (): Promise<SystemStatusPayload> => {
    const response = await api.get('/system/status');
    return response.data;
  },

  getInvestmentCatalog: async (): Promise<InvestmentCatalogPayload> => {
    const response = await api.get('/investments/catalog');
    return response.data;
  },

  compareInvestments: async (
    request: InvestmentCompareRequestPayload
  ): Promise<InvestmentComparisonResponsePayload> => {
    const response = await api.post('/investments/compare', request);
    return response.data;
  },

  listPairsUniverses: async (): Promise<PairsUniversePresetPayload[]> => {
    const response = await api.get('/pairs/universes');
    return response.data;
  },

  resolvePairsUniverse: async (
    request: PairsUniverseResolveRequestPayload
  ): Promise<PairsUniversePayload> => {
    const response = await api.post('/pairs/universe/resolve', request);
    return response.data;
  },

  screenPairs: async (request: PairsScreenRequestPayload): Promise<PairsScreenPayload> => {
    const response = await api.post('/pairs/screener', request);
    return response.data;
  },

  runPairsBacktest: async (
    request: PairsBacktestRequestPayload
  ): Promise<PairsBacktestResultsPayload> => {
    const response = await api.post('/pairs/backtests', request);
    return response.data;
  },

  runPairsBatchBacktest: async (
    request: PairsBatchRequestPayload
  ): Promise<PairsBacktestResultsPayload> => {
    const response = await api.post('/pairs/backtests/batch', request);
    return response.data;
  },

  listPairsBacktests: async (): Promise<PairsBacktestManifestPayload[]> => {
    const response = await api.get('/pairs/backtests');
    return response.data;
  },

  getPairsBacktestManifest: async (
    backtestId: string
  ): Promise<PairsBacktestManifestPayload> => {
    const response = await api.get(`/pairs/backtests/${backtestId}`);
    return response.data;
  },

  getPairsBacktestResults: async (
    backtestId: string
  ): Promise<PairsBacktestResultsPayload> => {
    const response = await api.get(`/pairs/backtests/${backtestId}/results`);
    return response.data;
  },

  createPairsBacktestJob: async (
    request: PairsBacktestRequestPayload
  ): Promise<PairsBacktestJobPayload> => {
    const response = await api.post('/pairs/backtests/jobs', request);
    return response.data;
  },

  createPairsBatchBacktestJob: async (
    request: PairsBatchRequestPayload
  ): Promise<PairsBacktestJobPayload> => {
    const response = await api.post('/pairs/backtests/jobs/batch', request);
    return response.data;
  },

  listPairsBacktestJobs: async (params?: {
    status?: PairsBacktestJobPayload['status'];
    limit?: number;
  }): Promise<PairsBacktestJobPayload[]> => {
    const response = await api.get('/pairs/backtests/jobs', { params });
    return response.data;
  },

  getPairsBacktestJob: async (jobId: string): Promise<PairsBacktestJobPayload> => {
    const response = await api.get(`/pairs/backtests/jobs/${jobId}`);
    return response.data;
  },

  cancelPairsBacktestJob: async (jobId: string): Promise<PairsBacktestJobPayload> => {
    const response = await api.post(`/pairs/backtests/jobs/${jobId}/cancel`);
    return response.data;
  },

  resumePairsBacktestJob: async (jobId: string): Promise<PairsBacktestJobPayload> => {
    const response = await api.post(`/pairs/backtests/jobs/${jobId}/resume`);
    return response.data;
  },

  getPairsBacktestJobResponse: async (
    jobId: string
  ): Promise<PairsBacktestResultsPayload> => {
    const response = await api.get(`/pairs/backtests/jobs/${jobId}/response`);
    return response.data;
  },

  runBacktest: async (request: BacktestRequest): Promise<BacktestResponse> => {
    const response = await api.post('/backtest', request);
    return response.data;
  },

  runWege3RegraAScenario: async (
    request: Wege3RegraARunRequestPayload
  ): Promise<Wege3RegraAScenarioPayload> => {
    const response = await api.post('/scenarios/wege3-regra-a', request);
    return response.data;
  },

  createBacktestJob: async (request: BacktestRequest): Promise<BacktestJobPayload> => {
    const response = await api.post('/backtest/jobs', request);
    return response.data;
  },

  listBacktestJobs: async (params?: {
    status?: BacktestJobPayload['status'];
    limit?: number;
  }): Promise<BacktestJobPayload[]> => {
    const response = await api.get('/backtest/jobs', { params });
    return response.data;
  },

  getBacktestJob: async (jobId: string): Promise<BacktestJobPayload> => {
    const response = await api.get(`/backtest/jobs/${jobId}`);
    return response.data;
  },

  cancelBacktestJob: async (jobId: string): Promise<BacktestJobPayload> => {
    const response = await api.post(`/backtest/jobs/${jobId}/cancel`);
    return response.data;
  },

  resumeBacktestJob: async (jobId: string): Promise<BacktestJobPayload> => {
    const response = await api.post(`/backtest/jobs/${jobId}/resume`);
    return response.data;
  },

  getBacktestJobResponse: async (jobId: string): Promise<BacktestResponse> => {
    const response = await api.get(`/backtest/jobs/${jobId}/response`);
    return response.data;
  },

  listRuns: async (): Promise<RunSummary[]> => {
    const response = await api.get('/runs');
    return response.data;
  },

  getRunResponse: async (runId: string): Promise<BacktestResponse> => {
    const response = await api.get(`/runs/${runId}/response`);
    return response.data;
  },

  getRunConfig: async (runId: string): Promise<RunConfigSnapshot> => {
    const response = await api.get(`/runs/${runId}/config`);
    return response.data;
  },

  getRunDataProfile: async (runId: string): Promise<RunDataProfile> => {
    const response = await api.get(`/runs/${runId}/data-profile`);
    return response.data;
  },

  downloadCSV: async (runId: string, strategy: string): Promise<Blob> => {
    const response = await api.get(`/runs/${runId}/strategies/${strategy}/trades.csv`, {
      responseType: 'blob',
    });
    return response.data;
  },

  downloadHTML: async (runId: string): Promise<Blob> => {
    const response = await api.get(`/runs/${runId}/report.html`, {
      responseType: 'blob',
    });
    return response.data;
  },

  listDatasets: async (): Promise<DatasetSummary[]> => {
    const response = await api.get('/datasets');
    return response.data;
  },

  getDataset: async (datasetId: string): Promise<DatasetDetail> => {
    const response = await api.get(`/datasets/${datasetId}`);
    return response.data;
  },

  listDueDatasets: async (): Promise<DatasetSummary[]> => {
    const response = await api.get('/datasets/refresh-due');
    return response.data;
  },

  importDataset: async (request: DatasetImportRequestPayload): Promise<DatasetDetail> => {
    const response = await api.post('/datasets/import', request);
    return response.data;
  },

  refreshDataset: async (
    datasetId: string,
    request: DatasetRefreshRequestPayload
  ): Promise<DatasetDetail> => {
    const response = await api.post(`/datasets/${datasetId}/refresh`, request);
    return response.data;
  },

  setDatasetRefreshPolicy: async (
    datasetId: string,
    request: DatasetRefreshPolicyRequestPayload
  ): Promise<DatasetDetail> => {
    const response = await api.post(`/datasets/${datasetId}/refresh-policy`, request);
    return response.data;
  },

  refreshDueDatasets: async (
    request: DatasetRefreshDueRequestPayload = {}
  ): Promise<DatasetDetail[]> => {
    const response = await api.post('/datasets/refresh-due', request);
    return response.data;
  },

  listExperiments: async (params?: {
    experiment_type?: ExperimentRegistryRecord['experiment_type'];
    strategy_name?: string;
    limit?: number;
  }): Promise<ExperimentRegistryRecord[]> => {
    const response = await api.get('/experiments', { params });
    return response.data;
  },

  getExperiment: async (
    experimentType: ExperimentRegistryRecord['experiment_type'],
    experimentId: string
  ): Promise<ExperimentDetailPayload> => {
    const response = await api.get(`/experiments/${experimentType}/${experimentId}`);
    return response.data;
  },

  listResearchWorkspaces: async (): Promise<ResearchWorkspacePayload[]> => {
    const response = await api.get('/research-workspaces');
    return response.data;
  },

  saveResearchWorkspace: async (
    request: ResearchWorkspaceCreatePayload
  ): Promise<ResearchWorkspacePayload> => {
    const response = await api.post('/research-workspaces', request);
    return response.data;
  },

  getResearchWorkspace: async (workspaceId: string): Promise<ResearchWorkspacePayload> => {
    const response = await api.get(`/research-workspaces/${workspaceId}`);
    return response.data;
  },

  getResearchWorkspaceReport: async (
    workspaceId: string
  ): Promise<ResearchWorkspaceReportEnvelope> => {
    const response = await api.get(`/research-workspaces/${workspaceId}/report`);
    return response.data;
  },

  exportResearchWorkspaceReport: async (
    workspaceId: string,
    format: 'markdown' | 'html'
  ): Promise<string> => {
    const response = await api.get(`/research-workspaces/${workspaceId}/report`, {
      params: { format },
      responseType: 'text',
    });
    return response.data;
  },

  updateResearchWorkspace: async (
    workspaceId: string,
    request: ResearchWorkspaceUpdatePayload
  ): Promise<ResearchWorkspacePayload> => {
    const response = await api.patch(`/research-workspaces/${workspaceId}`, request);
    return response.data;
  },

  importResearchWorkspace: async (
    request: ResearchWorkspaceImportPayload
  ): Promise<ResearchWorkspacePayload> => {
    const response = await api.post('/research-workspaces/import', request);
    return response.data;
  },

  buildAllocationPlan: async (
    request: AllocationPlanRequestPayload
  ): Promise<AllocationPlanResponsePayload> => {
    const response = await api.post('/allocations/rebalance-plan', request);
    return response.data;
  },

  listAllocationWorkspaces: async (): Promise<AllocationWorkspacePayload[]> => {
    const response = await api.get('/allocations/workspaces');
    return response.data;
  },

  saveAllocationWorkspace: async (
    request: AllocationWorkspaceCreatePayload
  ): Promise<AllocationWorkspacePayload> => {
    const response = await api.post('/allocations/workspaces', request);
    return response.data;
  },

  getAllocationWorkspace: async (workspaceId: string): Promise<AllocationWorkspacePayload> => {
    const response = await api.get(`/allocations/workspaces/${workspaceId}`);
    return response.data;
  },

  updateAllocationWorkspace: async (
    workspaceId: string,
    request: AllocationWorkspaceUpdatePayload
  ): Promise<AllocationWorkspacePayload> => {
    const response = await api.patch(`/allocations/workspaces/${workspaceId}`, request);
    return response.data;
  },

  importAllocationWorkspace: async (
    request: AllocationWorkspaceImportPayload
  ): Promise<AllocationWorkspacePayload> => {
    const response = await api.post('/allocations/workspaces/import', request);
    return response.data;
  },

  deleteAllocationWorkspace: async (workspaceId: string): Promise<void> => {
    await api.delete(`/allocations/workspaces/${workspaceId}`);
  },

  planOptimization: async (request: OptimizationRequestPayload): Promise<OptimizationPlan> => {
    const response = await api.post('/optimizations/plan', request);
    return response.data;
  },

  runOptimization: async (
    request: OptimizationRequestPayload
  ): Promise<OptimizationResultsPayload> => {
    const response = await api.post('/optimizations', request);
    return response.data;
  },

  listOptimizations: async (): Promise<OptimizationManifest[]> => {
    const response = await api.get('/optimizations');
    return response.data;
  },

  getOptimizationManifest: async (optimizationId: string): Promise<OptimizationManifest> => {
    const response = await api.get(`/optimizations/${optimizationId}`);
    return response.data;
  },

  getOptimizationResults: async (
    optimizationId: string
  ): Promise<OptimizationResultsPayload> => {
    const response = await api.get(`/optimizations/${optimizationId}/results`);
    return response.data;
  },

  runWalkForward: async (
    request: WalkForwardRequestPayload
  ): Promise<WalkForwardResultsPayload> => {
    const response = await api.post('/walkforward', request);
    return response.data;
  },

  listWalkForwardExecutions: async (): Promise<WalkForwardManifest[]> => {
    const response = await api.get('/walkforward');
    return response.data;
  },

  getWalkForwardManifest: async (walkforwardId: string): Promise<WalkForwardManifest> => {
    const response = await api.get(`/walkforward/${walkforwardId}`);
    return response.data;
  },

  getWalkForwardResults: async (
    walkforwardId: string
  ): Promise<WalkForwardResultsPayload> => {
    const response = await api.get(`/walkforward/${walkforwardId}/results`);
    return response.data;
  },

  runMonteCarlo: async (
    request: MonteCarloRequestPayload
  ): Promise<MonteCarloResultsPayload> => {
    const response = await api.post('/montecarlo', request);
    return response.data;
  },

  listMonteCarloExecutions: async (): Promise<MonteCarloManifest[]> => {
    const response = await api.get('/montecarlo');
    return response.data;
  },

  getMonteCarloManifest: async (monteCarloId: string): Promise<MonteCarloManifest> => {
    const response = await api.get(`/montecarlo/${monteCarloId}`);
    return response.data;
  },

  getMonteCarloResults: async (
    monteCarloId: string
  ): Promise<MonteCarloResultsPayload> => {
    const response = await api.get(`/montecarlo/${monteCarloId}/results`);
    return response.data;
  },

  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },
};
