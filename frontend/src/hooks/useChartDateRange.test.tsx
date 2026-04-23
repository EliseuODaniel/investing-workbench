import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  filterRowsByDateRange,
  normalizeChartDateValue,
  useChartDateRange,
} from './useChartDateRange';
import { rebaseLineSeriesData } from '../lib/chartSeries';

describe('useChartDateRange', () => {
  it('initializes with the full available period and filters a smaller window', () => {
    const data = [
      { date: '2021-01-04', value: 100 },
      { date: '2021-01-05', value: 110 },
      { date: '2021-01-06', value: 120 },
    ];

    const { result } = renderHook(() => useChartDateRange(data, 'date'));

    expect(result.current.startDate).toBe('2021-01-04');
    expect(result.current.endDate).toBe('2021-01-06');
    expect(result.current.startIndex).toBe(0);
    expect(result.current.endIndex).toBe(2);
    expect(result.current.filteredData).toHaveLength(3);

    act(() => {
      result.current.setStartIndex(1);
      result.current.setEndIndex(1);
    });

    expect(result.current.filteredData).toEqual([{ date: '2021-01-05', value: 110 }]);
    expect(result.current.startDate).toBe('2021-01-05');
    expect(result.current.endDate).toBe('2021-01-05');
  });

  it('normalizes Date values and filters timestamped rows', () => {
    const trades = [
      { timestamp: new Date('2021-01-04T10:00:00Z'), price: 10 },
      { timestamp: new Date('2021-01-05T10:00:00Z'), price: 11 },
      { timestamp: new Date('2021-01-06T10:00:00Z'), price: 12 },
    ];

    expect(normalizeChartDateValue(trades[0].timestamp)).toBe('2021-01-04');
    expect(
      filterRowsByDateRange(trades, 'timestamp', '2021-01-05', '2021-01-06')
    ).toHaveLength(2);
  });

  it('rebases visible series to the same starting point after the selected start date', () => {
    const rebased = rebaseLineSeriesData(
      [
        { date: '2021-01-05', alpha: 200, beta: 100 },
        { date: '2021-01-06', alpha: 220, beta: 110 },
      ],
      ['alpha', 'beta'],
      'beta'
    );

    expect(rebased[0].alpha).toBe(100);
    expect(rebased[0].beta).toBe(100);
    expect(rebased[1].alpha as number).toBeCloseTo(110, 10);
    expect(rebased[1].beta as number).toBeCloseTo(110, 10);
  });
});
