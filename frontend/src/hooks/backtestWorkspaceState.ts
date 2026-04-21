import { BacktestRequest, BacktestResponse } from '../types/api';

export type BacktestWorkspaceTab = 'summary' | 'charts' | 'trades' | 'details';
export type BacktestWorkspaceAppState = 'idle' | 'loading' | 'success' | 'error';

export interface SuccessfulWorkspaceState {
  appState: BacktestWorkspaceAppState;
  activeTab: BacktestWorkspaceTab;
  backtestResponse: BacktestResponse;
}

export function deriveSuccessfulWorkspaceState(
  response: BacktestResponse
): SuccessfulWorkspaceState {
  return {
    appState: 'success',
    activeTab: 'charts',
    backtestResponse: response,
  };
}

export function deriveVisibleStrategies(response: BacktestResponse | null): string[] {
  return response ? Object.keys(response.results) : [];
}

export function deriveVisibleBenchmarks(
  response: BacktestResponse | null,
  backtestRequest: BacktestRequest
): string[] {
  if (!response) return [];

  const benchmarkNames: string[] = [];

  if (backtestRequest.include_buy_hold_benchmark !== false) {
    benchmarkNames.push('Buy & Hold');
  }
  if (backtestRequest.include_selic_benchmark) {
    benchmarkNames.push('SELIC');
  }
  if (response.benchmarks) {
    benchmarkNames.push(...Object.keys(response.benchmarks));
  }

  return benchmarkNames;
}
