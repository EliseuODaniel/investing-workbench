import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import type { BacktestStrategyCatalogPayload } from '../types/api';
import { useSavedStrategyRadar } from './useSavedStrategyRadar';

const STRATEGY: BacktestStrategyCatalogPayload['strategies'][number] = {
  strategy_id: 'pairs_cointegration',
  label: 'Pairs por cointegracao',
  family: 'market_neutral',
  direction: 'long_short',
  required_inputs: ['formation_window'],
  parameter_defaults: { formation_window: 252, entry_zscore: 2 },
  universe_defaults: ['PETR4', 'VALE3'],
  supported_timeframes: ['daily'],
  execution_notes: ['Revalidar cointegracao por janela.'],
  risk_notes: ['Depende da validade temporal da relacao estatistica.'],
};

describe('useSavedStrategyRadar', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(apiClient.saveStrategyRadarItem).mockClear();
    vi.mocked(apiClient.deleteStrategyRadarItem).mockClear();
  });

  it('saves and removes strategy radar items locally and through the API', async () => {
    const { result } = renderHook(() => useSavedStrategyRadar());

    await waitFor(() => {
      expect(apiClient.listSavedStrategyRadarItems).toHaveBeenCalled();
    });

    act(() => {
      result.current.saveStrategy(STRATEGY);
    });

    expect(result.current.savedItems).toHaveLength(1);
    expect(result.current.savedStrategyIds.has('pairs_cointegration')).toBe(true);
    expect(result.current.savedItems[0].parameter_values?.formation_window).toBe(252);
    expect(result.current.savedItems[0].universe).toEqual(['PETR4', 'VALE3']);
    expect(apiClient.saveStrategyRadarItem).toHaveBeenCalledWith(
      expect.objectContaining({ strategy_id: 'pairs_cointegration' })
    );
    expect(window.localStorage.getItem('investing-workbench.strategy-radar.v1')).toContain(
      'pairs_cointegration'
    );

    act(() => {
      result.current.removeStrategy('pairs_cointegration');
    });

    expect(result.current.savedItems).toHaveLength(0);
    expect(result.current.savedStrategyIds.has('pairs_cointegration')).toBe(false);
    expect(apiClient.deleteStrategyRadarItem).toHaveBeenCalledWith('pairs_cointegration');
  });

  it('updates a saved strategy setup draft', async () => {
    const { result } = renderHook(() => useSavedStrategyRadar());

    await waitFor(() => {
      expect(apiClient.listSavedStrategyRadarItems).toHaveBeenCalled();
    });

    act(() => {
      result.current.saveStrategy(STRATEGY);
    });

    act(() => {
      result.current.updateStrategySetup({
        ...result.current.savedItems[0],
        parameter_values: { formation_window: 126, entry_zscore: 1.8 },
        universe: ['ITUB4', 'BBDC4'],
        timeframe: 'weekly',
        setup_notes: ['Teste semanal antes de escalar.'],
      });
    });

    expect(result.current.savedItems[0].parameter_values?.formation_window).toBe(126);
    expect(result.current.savedItems[0].universe).toEqual(['ITUB4', 'BBDC4']);
    expect(apiClient.saveStrategyRadarItem).toHaveBeenLastCalledWith(
      expect.objectContaining({
        strategy_id: 'pairs_cointegration',
        timeframe: 'weekly',
      })
    );
  });

  it('hydrates saved strategy radar items from localStorage', () => {
    window.localStorage.setItem(
      'investing-workbench.strategy-radar.v1',
      JSON.stringify([
        {
          strategy_id: 'martingale_v1',
          label: 'Martingale controlado',
          family: 'position_sizing',
          direction: 'long',
        },
      ])
    );

    const { result } = renderHook(() => useSavedStrategyRadar());

    expect(result.current.savedItems).toHaveLength(1);
    expect(result.current.savedItems[0].strategy_id).toBe('martingale_v1');
    expect(result.current.savedItems[0].saved_at).toBeTruthy();
  });
});
