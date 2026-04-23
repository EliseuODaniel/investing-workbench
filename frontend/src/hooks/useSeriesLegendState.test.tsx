import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useSeriesLegendState } from './useSeriesLegendState';

describe('useSeriesLegendState', () => {
  it('cycles a series through focused, hidden, and visible states', () => {
    const { result } = renderHook(() => useSeriesLegendState(['a', 'b']));

    expect(result.current.activeSeriesId).toBeNull();
    expect(result.current.hiddenSeriesIds).toEqual([]);

    act(() => {
      result.current.toggleSeries('a');
    });
    expect(result.current.activeSeriesId).toBe('a');
    expect(result.current.hiddenSeriesIds).toEqual([]);

    act(() => {
      result.current.toggleSeries('a');
    });
    expect(result.current.activeSeriesId).toBeNull();
    expect(result.current.hiddenSeriesIds).toEqual(['a']);

    act(() => {
      result.current.toggleSeries('a');
    });
    expect(result.current.activeSeriesId).toBeNull();
    expect(result.current.hiddenSeriesIds).toEqual([]);
  });

  it('drops hidden and active series that disappear from the available set', () => {
    const { result, rerender } = renderHook(
      ({ ids }) => useSeriesLegendState(ids),
      { initialProps: { ids: ['a', 'b'] } }
    );

    act(() => {
      result.current.toggleSeries('a');
      result.current.toggleSeries('a');
    });
    expect(result.current.hiddenSeriesIds).toEqual(['a']);

    rerender({ ids: ['b'] });

    expect(result.current.activeSeriesId).toBeNull();
    expect(result.current.hiddenSeriesIds).toEqual([]);
  });
});
