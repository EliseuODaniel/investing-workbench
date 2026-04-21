import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import ConfigurationStep from './ConfigurationStep';

describe('ConfigurationStep', () => {
  it('shows strategy help and glossary for the selected preset', async () => {
    const user = userEvent.setup();

    render(
      <ConfigurationStep
        configs={[
          {
            name: 'test',
            path: 'configs/test.yaml',
            display_name: 'Test',
            strategies: ['Simple Martingale'],
          },
        ]}
        selectedConfig={{
          name: 'test',
          path: 'configs/test.yaml',
          display_name: 'Test',
          strategies: ['Simple Martingale'],
        }}
        backtestRequest={{ strategies: [] }}
        onConfigChange={vi.fn()}
        onRequestChange={vi.fn()}
        onNext={vi.fn()}
        canProceed={false}
        isLoading={false}
      />
    );

    await user.click(screen.getByRole('button', { name: 'Info sobre Simple Martingale' }));
    expect(screen.getByText(/Faz compras em camadas nas quedas/i)).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'Abrir dicionário rápido' }));
    expect(screen.getByText(/Escolha as estratégias com menos chute/i)).toBeTruthy();
  });
});
