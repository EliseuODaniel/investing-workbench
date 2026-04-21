import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import AllocationWorkspace from './AllocationWorkspace';

const { buildAllocationPlan } = vi.hoisted(() => ({
  buildAllocationPlan: vi.fn().mockResolvedValue({
    total_equity: 9000,
    current_cash: 2000,
    target_cash: 1800,
    projected_cash: 1800,
    current_cash_weight: 0.2222,
    target_cash_weight: 0.2,
    turnover_notional: 2200,
    turnover_ratio: 0.2444,
    cash_gap_to_target: 0,
    max_abs_drift_weight: 0.3,
    needs_rebalance: true,
    actions: [
      {
        asset: 'ETH-USD',
        action: 'sell',
        price: 2000,
        current_quantity: 2,
        current_value: 4000,
        current_weight: 0.4444,
        target_quantity: 0.9,
        target_value: 1800,
        target_weight: 0.2,
        quantity_delta: -1.1,
        notional_delta: -2200,
        drift_weight: -0.2444,
        projected_quantity: 0.9,
        reason: 'Reduce to target weight',
      },
      {
        asset: 'SPY',
        action: 'buy',
        price: 900,
        current_quantity: 0,
        current_value: 0,
        current_weight: 0,
        target_quantity: 1,
        target_value: 900,
        target_weight: 0.1,
        quantity_delta: 1,
        notional_delta: 900,
        drift_weight: 0.1,
        projected_quantity: 1,
        reason: 'Increase to target weight',
      },
    ],
    warnings: ['Target allocation deploys more cash into risk assets; confirm position sizing.'],
  }),
}));

vi.mock('../lib/api', () => ({
  apiClient: {
    listAllocationWorkspaces: vi.fn().mockResolvedValue([]),
    buildAllocationPlan,
    saveAllocationWorkspace: vi.fn().mockResolvedValue(undefined),
    importAllocationWorkspace: vi.fn().mockResolvedValue(undefined),
  },
}));

describe('AllocationWorkspace', () => {
  it('builds and renders a rebalance plan from the example draft', async () => {
    const user = userEvent.setup();

    render(<AllocationWorkspace onError={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Workspaces Salvos')).toBeTruthy();
    });

    await user.click(screen.getByRole('button', { name: 'Carregar Exemplo' }));
    await user.click(screen.getByRole('button', { name: 'Planejar Rebalanceamento' }));

    expect(buildAllocationPlan).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('Acoes Recomendadas')).toBeTruthy();
    expect(screen.getByText('ETH-USD')).toBeTruthy();
    expect(screen.getByText('SPY')).toBeTruthy();
    expect(screen.getByText('Alertas do Plano')).toBeTruthy();
  });
});
