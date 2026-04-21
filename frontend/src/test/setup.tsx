import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
});

// Mock Plotly
vi.mock('react-plotly.js', () => {
  return function MockPlot({ data, layout }: any) {
    return (
      <div data-testid="plotly-chart">
        <div data-testid="plotly-data">{JSON.stringify(data)}</div>
        <div data-testid="plotly-layout">{JSON.stringify(layout)}</div>
      </div>
    );
  };
});

// Mock API
vi.mock('../lib/api', () => ({
  apiClient: {
    getConfigs: vi.fn(),
    getSystemStatus: vi.fn(),
    getInvestmentCatalog: vi.fn(),
    compareInvestments: vi.fn(),
    listPairsUniverses: vi.fn(),
    resolvePairsUniverse: vi.fn(),
    screenPairs: vi.fn(),
    runPairsBacktest: vi.fn(),
    runPairsBatchBacktest: vi.fn(),
    listPairsBacktests: vi.fn(),
    getPairsBacktestManifest: vi.fn(),
    getPairsBacktestResults: vi.fn(),
    listOptimizations: vi.fn(),
    planOptimization: vi.fn(),
    runOptimization: vi.fn(),
    getOptimizationResults: vi.fn(),
    listResearchWorkspaces: vi.fn(),
    listExperiments: vi.fn(),
    listWalkForwardExecutions: vi.fn(),
    listMonteCarloExecutions: vi.fn(),
    listRuns: vi.fn(),
    runBacktest: vi.fn(),
    runWege3RegraAScenario: vi.fn(),
    createBacktestJob: vi.fn(),
    listBacktestJobs: vi.fn(),
    getBacktestJob: vi.fn(),
    cancelBacktestJob: vi.fn(),
    resumeBacktestJob: vi.fn(),
    getBacktestJobResponse: vi.fn(),
    downloadCSV: vi.fn(),
    healthCheck: vi.fn(),
  },
}));
