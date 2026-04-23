import { useEffect, useMemo, useState } from 'react';

function isValidDate(value: Date): boolean {
  return !Number.isNaN(value.getTime());
}

export function normalizeChartDateValue(value: unknown): string | null {
  if (value instanceof Date) {
    return isValidDate(value) ? value.toISOString().slice(0, 10) : null;
  }

  if (typeof value === 'string') {
    const normalizedValue = value.trim();
    if (!normalizedValue) {
      return null;
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(normalizedValue)) {
      return normalizedValue;
    }
    const parsed = new Date(normalizedValue);
    return isValidDate(parsed) ? parsed.toISOString().slice(0, 10) : null;
  }

  if (typeof value === 'number') {
    const parsed = new Date(value);
    return isValidDate(parsed) ? parsed.toISOString().slice(0, 10) : null;
  }

  return null;
}

function clampDate(date: string, minDate: string, maxDate: string): string {
  if (!date) {
    return minDate;
  }
  if (date < minDate) {
    return minDate;
  }
  if (date > maxDate) {
    return maxDate;
  }
  return date;
}

export function filterRowsByDateRange<T extends object>(
  data: T[],
  dateKey: string,
  startDate: string,
  endDate: string
): T[] {
  const lowerBound = startDate && endDate && startDate > endDate ? endDate : startDate;
  const upperBound = startDate && endDate && startDate > endDate ? startDate : endDate;

  return data.filter((row) => {
    const normalizedDate = normalizeChartDateValue((row as Record<string, unknown>)[dateKey]);
    if (!normalizedDate) {
      return false;
    }
    if (lowerBound && normalizedDate < lowerBound) {
      return false;
    }
    if (upperBound && normalizedDate > upperBound) {
      return false;
    }
    return true;
  });
}

export function useChartDateRange<T extends object>(data: T[], dateKey: string) {
  const availableDates = useMemo(() => {
    const normalizedDates = data
      .map((row) => normalizeChartDateValue((row as Record<string, unknown>)[dateKey]))
      .filter((value): value is string => Boolean(value))
      .sort();

    return Array.from(new Set(normalizedDates));
  }, [data, dateKey]);

  const minDate = availableDates[0] ?? null;
  const maxDate = availableDates[availableDates.length - 1] ?? null;
  const maxIndex = Math.max(availableDates.length - 1, 0);

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    if (!minDate || !maxDate) {
      setStartDate('');
      setEndDate('');
      return;
    }

    setStartDate((current) => clampDate(current || minDate, minDate, maxDate));
    setEndDate((current) => clampDate(current || maxDate, minDate, maxDate));
  }, [maxDate, minDate]);

  const resolvedStartDate = startDate || minDate || '';
  const resolvedEndDate = endDate || maxDate || '';

  const filteredData = useMemo(() => {
    if (!minDate || !maxDate) {
      return data;
    }
    return filterRowsByDateRange(data, dateKey, resolvedStartDate, resolvedEndDate);
  }, [data, dateKey, maxDate, minDate, resolvedEndDate, resolvedStartDate]);

  const startIndex = Math.max(availableDates.indexOf(resolvedStartDate), 0);
  const endIndex = Math.max(availableDates.indexOf(resolvedEndDate), 0);

  return {
    availableDates,
    filteredData,
    minDate,
    maxDate,
    maxIndex,
    startDate: resolvedStartDate,
    endDate: resolvedEndDate,
    setStartDate,
    setEndDate,
    startIndex,
    endIndex,
    setStartIndex: (value: number) => {
      if (!availableDates.length) {
        return;
      }
      const clampedIndex = Math.max(0, Math.min(value, endIndex, maxIndex));
      setStartDate(availableDates[clampedIndex]);
    },
    setEndIndex: (value: number) => {
      if (!availableDates.length) {
        return;
      }
      const clampedIndex = Math.max(startIndex, Math.min(value, maxIndex));
      setEndDate(availableDates[clampedIndex]);
    },
    resetRange: () => {
      if (!minDate || !maxDate) {
        return;
      }
      setStartDate(minDate);
      setEndDate(maxDate);
    },
    hasDateRange: Boolean(minDate && maxDate && minDate !== maxDate),
  };
}
