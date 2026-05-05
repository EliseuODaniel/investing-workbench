import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios';
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
  BacktestStrategyCatalogPayload,
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
  InvestmentCustomPortfolioRequestPayload,
  InvestmentMarketRankingsRequestPayload,
  InvestmentMarketRankingsSnapshotPayload,
  InvestmentProductDataRefreshRequestPayload,
  InvestmentProductDataRefreshResponsePayload,
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
  SavedInvestmentPortfolioPayload,
  SavedPairsRadarItemPayload,
  SavedStrategyRadarItemPayload,
  SavedStrategySetupRunPayload,
  StrategySetupScorePayload,
  StrategySetupPlanPayload,
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

type ApiMethod = 'get' | 'post' | 'delete' | 'patch';

const REQUEST_TIMEOUT_MS = 300000;

const normalizeApiBase = (value: string | undefined): string => {
  if (!value) {
    return '';
  }
  const trimmed = value.trim();
  return trimmed.endsWith('/') && trimmed !== '/' ? trimmed.slice(0, -1) : trimmed;
};

const hasLocalFrontendPort = (port: string): boolean =>
  ['3001', '5173', '5174', '3000'].includes(port);

const buildApiBaseCandidates = (): string[] => {
  const envBase = normalizeApiBase((import.meta as any).env.VITE_API_BASE);
  const host = typeof window === 'undefined' ? '' : window.location.hostname;
  const port = typeof window === 'undefined' ? '' : window.location.port;
  const inferredLocalPortBackend = ['localhost', '127.0.0.1'].includes(host) && hasLocalFrontendPort(port);

  const candidates: string[] = [];
  const addBase = (candidate: string | undefined) => {
    const normalized = normalizeApiBase(candidate);
    if (!normalized) {
      return;
    }
    if (!candidates.includes(normalized)) {
      candidates.push(normalized);
    }
  };

  addBase(envBase);
  if (inferredLocalPortBackend) {
    addBase('http://127.0.0.1:18001');
    addBase('http://localhost:18001');
  }
  addBase('http://localhost:18001');
  addBase('http://127.0.0.1:18001');
  addBase('/api');
  addBase('http://localhost:8001');
  addBase('http://127.0.0.1:8001');

  return candidates;
};

const API_BASES = buildApiBaseCandidates();
const apiClients = API_BASES.map((base) =>
  axios.create({
    baseURL: base,
    timeout: REQUEST_TIMEOUT_MS,
  })
);

const isRetryableError = (error: unknown, method: ApiMethod): boolean => {
  if (!axios.isAxiosError(error)) {
    return method === 'get';
  }
  if (!error.response) {
    return true;
  }

  const contentType = String(error.response.headers?.['content-type'] || '').toLowerCase();
  const isJsonResponse = contentType.includes('json');
  const isLikelyJsonPayload = error.response.data == null || isJsonResponse;
  if (method === 'get' && !isLikelyJsonPayload) {
    return true;
  }

  const status = Number(error.response.status);
  if (status >= 500) {
    return true;
  }
  if (method === 'get' && status === 404) {
    return true;
  }
  return false;
};

const isLikelyHtmlOrTextResponse = (response: AxiosResponse): boolean => {
  const contentType = String(response.headers?.['content-type'] || '').toLowerCase();
  if (contentType.includes('application/json') || contentType.includes('+json')) {
    return false;
  }
  if (typeof response.data === 'string') {
    const body = response.data.trim().slice(0, 120).toLowerCase();
    return (
      body.startsWith('<!doctype html>') ||
      body.startsWith('<html') ||
      body.includes('<!doctype html>')
    );
  }
  return response.data == null;
};

let preferredClientIndex = 0;

const requestWithFallback = async <T>(
  method: ApiMethod,
  url: string,
  config: AxiosRequestConfig = {}
): Promise<AxiosResponse<T>> => {
  let lastError: unknown;

  for (let attempt = 0; attempt < apiClients.length; attempt++) {
    const clientIndex = (preferredClientIndex + attempt) % apiClients.length;
    const client = apiClients[clientIndex];

    try {
      const response = await client.request<T>({ ...config, method, url });
      if (
        method === 'get' &&
        isLikelyHtmlOrTextResponse(response as AxiosResponse<unknown>)
      ) {
        lastError = new Error('Non-json API response from fallback candidate');
        if (attempt === apiClients.length - 1) {
          throw lastError;
        }
        continue;
      }
      if (clientIndex !== preferredClientIndex) {
        preferredClientIndex = clientIndex;
      }
      return response;
    } catch (error) {
      lastError = error;
      if (!isRetryableError(error, method) || attempt === apiClients.length - 1) {
        throw error;
      }
    }
  }

  throw lastError;
};

const api = {
  get: <T = any>(url: string, config: AxiosRequestConfig = {}): Promise<AxiosResponse<T>> =>
    requestWithFallback<T>('get', url, config),
  post: <T = any>(
    url: string,
    data?: unknown,
    config: AxiosRequestConfig = {}
  ): Promise<AxiosResponse<T>> =>
    requestWithFallback<T>('post', url, { ...config, data }),
  patch: <T = any>(
    url: string,
    data?: unknown,
    config: AxiosRequestConfig = {}
  ): Promise<AxiosResponse<T>> =>
    requestWithFallback<T>('patch', url, { ...config, data }),
  delete: <T = any>(url: string, config: AxiosRequestConfig = {}): Promise<AxiosResponse<T>> =>
    requestWithFallback<T>('delete', url, config),
};

export const apiClient = {
  getConfigs: async (): Promise<ConfigInfo[]> => {
    const response = await api.get('/configs');
    return response.data;
  },

  getSystemStatus: async (): Promise<SystemStatusPayload> => {
    const response = await api.get('/system/status');
    return response.data;
  },

  getBacktestStrategyCatalog: async (): Promise<BacktestStrategyCatalogPayload> => {
    const response = await api.get('/backtests/strategy-catalog');
    return response.data;
  },

  buildStrategySetupPlan: async (
    request: SavedStrategyRadarItemPayload
  ): Promise<StrategySetupPlanPayload> => {
    const response = await api.post('/backtests/strategy-setup-plan', request);
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

  buildInvestmentMarketRankings: async (
    request: InvestmentMarketRankingsRequestPayload
  ): Promise<InvestmentMarketRankingsSnapshotPayload> => {
    const response = await api.post('/investments/market-rankings', request);
    return response.data;
  },

  refreshInvestmentProductData: async (
    request: InvestmentProductDataRefreshRequestPayload
  ): Promise<InvestmentProductDataRefreshResponsePayload> => {
    const response = await api.post('/investments/product-data/refresh', request);
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

  listSavedInvestmentPortfolios: async (): Promise<SavedInvestmentPortfolioPayload[]> => {
    const response = await api.get('/investments/workspaces/portfolios');
    return response.data;
  },

  saveInvestmentPortfolio: async (
    request: InvestmentCustomPortfolioRequestPayload
  ): Promise<SavedInvestmentPortfolioPayload> => {
    const response = await api.post('/investments/workspaces/portfolios', request);
    return response.data;
  },

  deleteInvestmentPortfolio: async (portfolioId: string): Promise<void> => {
    await api.delete(`/investments/workspaces/portfolios/${portfolioId}`);
  },

  listSavedPairsRadarItems: async (): Promise<SavedPairsRadarItemPayload[]> => {
    const response = await api.get('/investments/workspaces/pairs-radar');
    return response.data;
  },

  savePairsRadarItem: async (
    request: SavedPairsRadarItemPayload
  ): Promise<SavedPairsRadarItemPayload> => {
    const response = await api.post('/investments/workspaces/pairs-radar', request);
    return response.data;
  },

  deletePairsRadarItem: async (pairsBacktestId: string): Promise<void> => {
    await api.delete(`/investments/workspaces/pairs-radar/${pairsBacktestId}`);
  },

  listSavedStrategyRadarItems: async (): Promise<SavedStrategyRadarItemPayload[]> => {
    const response = await api.get('/investments/workspaces/strategy-radar');
    return response.data;
  },

  saveStrategyRadarItem: async (
    request: SavedStrategyRadarItemPayload
  ): Promise<SavedStrategyRadarItemPayload> => {
    const response = await api.post('/investments/workspaces/strategy-radar', request);
    return response.data;
  },

  deleteStrategyRadarItem: async (strategyId: string): Promise<void> => {
    await api.delete(`/investments/workspaces/strategy-radar/${strategyId}`);
  },

  listSavedStrategySetupRuns: async (): Promise<SavedStrategySetupRunPayload[]> => {
    const response = await api.get('/investments/workspaces/strategy-setup-runs');
    return response.data;
  },

  saveStrategySetupRun: async (
    request: SavedStrategySetupRunPayload
  ): Promise<SavedStrategySetupRunPayload> => {
    const response = await api.post('/investments/workspaces/strategy-setup-runs', request);
    return response.data;
  },

  listStrategySetupScores: async (): Promise<StrategySetupScorePayload[]> => {
    const response = await api.get('/investments/workspaces/strategy-setup-scores');
    return response.data;
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
