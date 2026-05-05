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

vi.mock('../lib/utils', async () => {
  const actual = await vi.importActual<typeof import('../lib/utils')>('../lib/utils');
  return {
    ...actual,
    downloadCSV: vi.fn(),
  };
});

// Mock API
vi.mock('../lib/api', () => ({
  apiClient: {
    getConfigs: vi.fn(),
    getSystemStatus: vi.fn(),
    getBacktestStrategyCatalog: vi.fn(),
    buildStrategySetupPlan: vi.fn(async (payload) => ({
      plan_id: `strategy_setup_plan_${payload.strategy_id}`,
      strategy_id: payload.strategy_id,
      label: payload.label,
      family: payload.family,
      timeframe: payload.timeframe || 'daily',
      route_hint: '/backtest',
      readiness: 'ready_to_review',
      run_request: { strategies: [payload.strategy_id] },
      assumptions: ['Plano de teste.'],
      warnings: [],
      setup_notes: payload.setup_notes || [],
      next_actions: ['Executar backtest.'],
      generated_at: '2026-04-27T12:00:00Z',
    })),
    getInvestmentCatalog: vi.fn(),
    compareInvestments: vi.fn(),
    buildInvestmentMarketRankings: vi.fn(),
    listSavedInvestmentPortfolios: vi.fn().mockResolvedValue([]),
    saveInvestmentPortfolio: vi.fn(async (payload) => payload),
    deleteInvestmentPortfolio: vi.fn().mockResolvedValue(undefined),
    listSavedPairsRadarItems: vi.fn().mockResolvedValue([]),
    savePairsRadarItem: vi.fn().mockResolvedValue(undefined),
    deletePairsRadarItem: vi.fn().mockResolvedValue(undefined),
    listSavedStrategyRadarItems: vi.fn().mockResolvedValue([]),
    saveStrategyRadarItem: vi.fn(async (payload) => payload),
    deleteStrategyRadarItem: vi.fn().mockResolvedValue(undefined),
    listSavedStrategySetupRuns: vi.fn().mockResolvedValue([]),
    saveStrategySetupRun: vi.fn(async (payload) => payload),
    listStrategySetupScores: vi.fn().mockResolvedValue([]),
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
    getRunResponse: vi.fn(),
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
