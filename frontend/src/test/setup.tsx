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
    runBacktest: vi.fn(),
    downloadCSV: vi.fn(),
    healthCheck: vi.fn(),
  },
}));
