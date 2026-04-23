import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import Wege3ComparisonChart from './Wege3ComparisonChart';

describe('Wege3ComparisonChart', () => {
  it('highlights a series when its legend button is clicked', () => {
    render(
      <Wege3ComparisonChart
        chart={{
          reference_series_id: 'selic_cash',
          series: [
            { id: 'regra_a_base', label: 'Regra A base' },
            { id: 'buy_hold_wege3', label: 'Buy and hold WEGE3' },
            { id: 'selic_cash', label: 'Caixa SELIC' },
          ],
          points: [
            {
              date: '2021-01-04',
              regra_a_base: 40000,
              buy_hold_wege3: 40000,
              selic_cash: 40000,
            },
            {
              date: '2021-01-05',
              regra_a_base: 40500,
              buy_hold_wege3: 41000,
              selic_cash: 40010,
            },
          ],
        }}
      />
    );

    const startSlider = screen.getByLabelText('Início do intervalo do gráfico') as HTMLInputElement;
    const endSlider = screen.getByLabelText('Fim do intervalo do gráfico') as HTMLInputElement;
    expect(startSlider.value).toBe('0');
    expect(endSlider.value).toBe('1');

    const buyHoldButton = screen.getByRole('button', { name: 'Buy and hold WEGE3' });
    expect(buyHoldButton.getAttribute('aria-pressed')).toBe('false');
    expect(buyHoldButton.getAttribute('data-visibility-state')).toBe('visible');

    fireEvent.change(startSlider, { target: { value: '1' } });
    expect(screen.getByText(/Exibindo de/i).textContent).toContain('05/01/2021');

    fireEvent.click(buyHoldButton);
    expect(buyHoldButton.getAttribute('aria-pressed')).toBe('true');
    expect(buyHoldButton.getAttribute('data-visibility-state')).toBe('focused');

    fireEvent.click(buyHoldButton);
    expect(buyHoldButton.getAttribute('aria-pressed')).toBe('false');
    expect(buyHoldButton.getAttribute('data-visibility-state')).toBe('hidden');
    expect(screen.getByText('oculto')).toBeTruthy();

    fireEvent.click(buyHoldButton);
    expect(buyHoldButton.getAttribute('data-visibility-state')).toBe('visible');
  });
});
