import axios from 'axios';
import {
  ConfigInfo,
  BacktestRequest,
  BacktestResponse,
  OptimizationManifest,
  OptimizationPlan,
  OptimizationRequestPayload,
  OptimizationResultsPayload,
  RunConfigSnapshot,
  RunDataProfile,
  RunSummary,
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

  // Health check
  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },
};
