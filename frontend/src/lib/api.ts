import axios from 'axios';
import { ConfigInfo, BacktestRequest, BacktestResponse } from '../types/api';

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

  // Download operations
  downloadCSV: async (strategy: string): Promise<Blob> => {
    const response = await api.get(`/reports/${strategy}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },
};