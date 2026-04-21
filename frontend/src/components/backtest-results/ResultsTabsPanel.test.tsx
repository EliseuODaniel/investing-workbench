import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ResultsTabsPanel from './ResultsTabsPanel';

vi.mock('./ResultsOverviewTab', () => ({
  default: ({ mode }: { mode?: 'summary' | 'charts' }) => (
    <div>{mode === 'charts' ? 'Charts View' : 'Summary View'}</div>
  ),
}));

vi.mock('./ResultsSummaryHero', () => ({
  default: () => <div>Summary Hero</div>,
}));

vi.mock('./TradingHistoryTab', () => ({
  default: () => <div>Trading History</div>,
}));

vi.mock('./ResultsDetailsTab', () => ({
  default: () => <div>Details View</div>,
}));

const backtestRequest = {
  strategies: ['Simple Martingale'],
  initial_capital: 10000,
};

const backtestResponse = {
  results: {
    'Simple Martingale': {
      strategy_name: 'Simple Martingale',
      equity: [],
      trades: [],
      metrics: {
        total_return: 0.12,
        cagr: 0.12,
        sharpe_ratio: 1.2,
        sortino_ratio: 1.5,
        max_drawdown: -0.08,
        hit_rate: 0.6,
        profit_factor: 1.4,
        total_trades: 0,
        avg_trade_pnl: 0,
        volatility: 0.2,
        total_interest_earned: 0,
      },
      start_price: 100,
      end_price: 110,
    },
  },
  buy_hold_equity: [],
  data_info: {
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    total_days: 365,
    initial_price: 100,
    final_price: 110,
  },
};

function renderPanel(activeTab: 'summary' | 'charts' | 'trades' | 'details') {
  render(
    <ResultsTabsPanel
      activeTab={activeTab}
      backtestRequest={backtestRequest}
      backtestResponse={backtestResponse}
      isLoadingArtifacts={false}
      onCopyLink={vi.fn()}
      onCopySummary={vi.fn()}
      onDownloadCSV={vi.fn()}
      onDownloadHTML={vi.fn()}
      onDownloadPNG={vi.fn()}
      onSaveProject={vi.fn()}
      onShareResults={vi.fn()}
      onToggleAllBenchmarks={vi.fn()}
      onToggleAllStrategies={vi.fn()}
      onToggleBenchmarkVisibility={vi.fn()}
      onToggleStrategyVisibility={vi.fn()}
      runConfigSnapshot={null}
      runDataProfile={null}
      strategyNames={['Simple Martingale']}
      totalTradesCount={0}
      visibleStrategies={['Simple Martingale']}
      visibleBenchmarks={[]}
      warnings={[]}
      onSetActiveTab={vi.fn()}
    />
  );
}

describe('ResultsTabsPanel', () => {
  it('puts charts first and avoids the summary hero in chart mode', () => {
    renderPanel('charts');

    expect(screen.getByText(/Comece pelos graficos/i)).toBeTruthy();
    expect(screen.queryByText('Summary Hero')).toBeNull();
    expect(screen.getByText('Charts View')).toBeTruthy();

    const tabButtons = screen
      .getAllByRole('button')
      .slice(0, 4)
      .map((button) => button.textContent);
    expect(tabButtons).toEqual(['Graficos', 'Resumo', 'Trades', 'Detalhes']);
  });

  it('shows the summary hero only inside the summary tab', () => {
    renderPanel('summary');

    expect(screen.getByText('Summary Hero')).toBeTruthy();
    expect(screen.getByText('Summary View')).toBeTruthy();
  });
});
