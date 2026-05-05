import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import InvestmentResultChartPanel from './InvestmentResultChartPanel';

vi.mock('../charts/InteractiveSeriesChart', () => ({
  default: ({
    title,
    description,
    data,
  }: {
    title: string;
    description: string;
    data: Array<Record<string, string | number | null>>;
  }) => (
    <div data-testid="mock-chart">
      <div>{title}</div>
      <p>{description}</p>
      <span>{data.length} ponto(s)</span>
    </div>
  ),
}));

const nominalChart = {
  series: [{ id: 'WEGE3', label: 'WEGE3', color: '#2563eb' }],
  points: [{ date: '2024-01-01', WEGE3: 12000 }],
};

const realChart = {
  series: [{ id: 'WEGE3', label: 'WEGE3 real', color: '#2563eb' }],
  points: [
    { date: '2024-01-01', WEGE3: 11000 },
    { date: '2024-02-01', WEGE3: 11100 },
  ],
};

describe('InvestmentResultChartPanel', () => {
  it('renders the selected chart mode and exposes mode controls', async () => {
    const user = userEvent.setup();
    const onChartModeChange = vi.fn();

    render(
      <InvestmentResultChartPanel
        chart={nominalChart}
        realChart={realChart}
        chartMode="real"
        onChartModeChange={onChartModeChange}
      />
    );

    expect(screen.getByText('Evolucao do patrimonio em poder de compra')).toBeTruthy();
    expect(screen.getByText('2 ponto(s)')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'Visao nominal' }));

    expect(onChartModeChange).toHaveBeenCalledWith('nominal');
  });
});
