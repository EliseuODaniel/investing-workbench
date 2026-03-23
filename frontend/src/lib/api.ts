import axios from 'axios';
import {
  ConfigInfo,
  BacktestRequest,
  BacktestResponse,
  DatasetDetail,
  DatasetImportRequestPayload,
  DatasetRefreshRequestPayload,
  DatasetSummary,
  MonteCarloManifest,
  MonteCarloRequestPayload,
  MonteCarloResultsPayload,
  OptimizationManifest,
  OptimizationPlan,
  OptimizationRequestPayload,
  OptimizationResultsPayload,
  RunConfigSnapshot,
  RunDataProfile,
  RunSummary,
  WalkForwardManifest,
  WalkForwardRequestPayload,
  WalkForwardResultsPayload,
} from '../types/api';

const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 minutes timeout for long backtests
});

export const apiClient = {
  // Config management
  getConfigs: async (): Promise<ConfigInfo[]> => {
    const response = await api.get('/configs');
    return response.data;
  },

  // Backtest operations
  runBacktest: async (request: BacktestRequest): Promise<BacktestResponse> => {
    const response = await api.post('/backtest', request);
    return response.data;
  },

  // Persisted run operations
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

  // Dataset catalog operations
  listDatasets: async (): Promise<DatasetSummary[]> => {
    const response = await api.get('/datasets');
    return response.data;
  },

  getDataset: async (datasetId: string): Promise<DatasetDetail> => {
    const response = await api.get(`/datasets/${datasetId}`);
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

  // Optimization operations
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

  // Walk-forward operations
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

  // Monte Carlo operations
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

  // Health check
  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },
};
