function toFiniteNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function findFirstSeriesValue<T extends Record<string, unknown>>(
  data: T[],
  seriesId: string
): number | null {
  for (const row of data) {
    const value = toFiniteNumber(row[seriesId]);
    if (value !== null && value !== 0) {
      return value;
    }
  }
  return null;
}

export function rebaseLineSeriesData<T extends Record<string, unknown>>(
  data: T[],
  seriesIds: string[],
  referenceSeriesId?: string | null
): T[] {
  if (data.length === 0 || seriesIds.length === 0) {
    return data;
  }

  const baselineBySeries = new Map<string, number>();
  for (const seriesId of seriesIds) {
    const baseline = findFirstSeriesValue(data, seriesId);
    if (baseline !== null) {
      baselineBySeries.set(seriesId, baseline);
    }
  }

  const orderedCandidates = [
    ...(referenceSeriesId ? [referenceSeriesId] : []),
    ...seriesIds,
  ];
  const commonBaseline =
    orderedCandidates
      .map((seriesId) => baselineBySeries.get(seriesId))
      .find((value): value is number => typeof value === 'number' && Number.isFinite(value)) ?? null;

  if (commonBaseline === null) {
    return data;
  }

  return data.map((row) => {
    const nextRow: Record<string, unknown> = { ...row };
    for (const seriesId of seriesIds) {
      const value = toFiniteNumber(row[seriesId]);
      const baseline = baselineBySeries.get(seriesId);
      if (value === null || baseline === undefined || baseline === 0) {
        continue;
      }
      nextRow[seriesId] = (value / baseline) * commonBaseline;
    }
    return nextRow as T;
  });
}

export function buildDrawdownSeriesFromEquity<
  T extends Record<string, string | number | null>,
>(
  equityData: T[],
  seriesIds: string[]
): Array<Record<string, string | number>> {
  const peaks = new Map<string, number>();

  return equityData.map((point) => {
    const row: Record<string, string | number> = {
      timestamp: String(point.timestamp ?? ''),
      date: String(point.date ?? ''),
    };

    for (const seriesId of seriesIds) {
      const value = toFiniteNumber(point[seriesId]);
      const drawdownKey = `${seriesId}_drawdown`;
      if (value === null) {
        row[drawdownKey] = 0;
        continue;
      }

      const peak = Math.max(peaks.get(seriesId) ?? value, value);
      peaks.set(seriesId, peak);
      row[drawdownKey] = peak === 0 ? 0 : ((value - peak) / peak) * 100;
    }

    return row;
  });
}
