import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { SavedStrategyRadarItem } from './useSavedStrategyRadar';
import { useStrategySetupDraftEditor } from './useStrategySetupDraftEditor';

const SETUP: SavedStrategyRadarItem = {
  strategy_id: 'pairs_cointegration',
  label: 'Pairs',
  family: 'market_neutral',
  direction: 'long_short',
  parameter_values: { formation_window: 252, entry_zscore: 2 },
  universe: ['PETR4', 'VALE3'],
  timeframe: 'daily',
  setup_notes: ['Revalidar janela.'],
};

describe('useStrategySetupDraftEditor', () => {
  it('starts, updates, saves, and clears an editable setup draft', () => {
    const updateStrategySetup = vi.fn();
    const { result } = renderHook(() =>
      useStrategySetupDraftEditor({ updateStrategySetup })
    );

    act(() => {
      result.current.startEditingSetup(SETUP);
    });

    expect(result.current.editingStrategyId).toBe('pairs_cointegration');
    expect(result.current.setupDraft).toMatchObject({
      universeText: 'PETR4, VALE3',
      timeframe: 'daily',
    });

    act(() => {
      result.current.updateDraftField('universeText', 'itub4, bbdc4');
      result.current.updateDraftField('timeframe', ' weekly ');
      result.current.updateDraftField('parametersText', 'formation_window: 126');
    });

    act(() => {
      result.current.saveEditedSetup(SETUP);
    });

    expect(updateStrategySetup).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy_id: 'pairs_cointegration',
        universe: ['ITUB4', 'BBDC4'],
        timeframe: 'weekly',
        parameter_values: { formation_window: 126 },
      })
    );
    expect(result.current.editingStrategyId).toBeNull();
    expect(result.current.setupDraft).toBeNull();
  });

  it('cancels an edit without saving', () => {
    const updateStrategySetup = vi.fn();
    const { result } = renderHook(() =>
      useStrategySetupDraftEditor({ updateStrategySetup })
    );

    act(() => {
      result.current.startEditingSetup(SETUP);
      result.current.cancelEditingSetup();
    });

    expect(result.current.editingStrategyId).toBeNull();
    expect(result.current.setupDraft).toBeNull();
    expect(updateStrategySetup).not.toHaveBeenCalled();
  });
});
