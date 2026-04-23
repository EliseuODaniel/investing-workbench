import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  InteractiveSeriesTooltipContent,
  type InteractiveSeriesDefinition,
} from './InteractiveSeriesChart';

describe('InteractiveSeriesTooltipContent', () => {
  it('renders each series in the tooltip using its corresponding chart color', () => {
    const series = new Map<string, InteractiveSeriesDefinition>([
      ['cdi_index', { id: 'cdi_index', label: 'CDI / caixa', color: '#10b981' }],
      ['idka_ipca_2a', { id: 'idka_ipca_2a', label: 'IDkA IPCA 2A', color: '#f97316' }],
    ]);

    render(
      <InteractiveSeriesTooltipContent
        active
        label="2026-03-31"
        payload={[
          {
            dataKey: 'cdi_index',
            name: 'cdi_index',
            value: 7220.76,
            color: '#10b981',
          },
          {
            dataKey: 'idka_ipca_2a',
            name: 'idka_ipca_2a',
            value: 10370.39,
            color: '#f97316',
          },
        ]}
        seriesById={series}
        labelFormatter={(value) => `Data ${value}`}
        valueFormatter={(value) => `R$ ${value.toFixed(2)}`}
      />
    );

    expect(screen.queryByText('Data 2026-03-31')).not.toBeNull();
    expect(screen.queryByText('CDI / caixa')).not.toBeNull();
    expect(screen.queryByText('IDkA IPCA 2A')).not.toBeNull();
    expect((screen.getByTestId('tooltip-row-cdi_index') as HTMLElement).style.color).toBe(
      'rgb(16, 185, 129)'
    );
    expect((screen.getByTestId('tooltip-row-idka_ipca_2a') as HTMLElement).style.color).toBe(
      'rgb(249, 115, 22)'
    );
  });
});
