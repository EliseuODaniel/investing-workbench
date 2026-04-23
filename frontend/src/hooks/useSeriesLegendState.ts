import { useEffect, useMemo, useState } from 'react';

interface SeriesLegendVisibilityState {
  activeSeriesId: string | null;
  hiddenSeriesIds: string[];
  toggleSeries: (seriesId: string) => void;
}

export function useSeriesLegendState(seriesIds: string[]): SeriesLegendVisibilityState {
  const visibleSeriesSet = useMemo(() => new Set(seriesIds), [seriesIds]);
  const [state, setState] = useState<{
    activeSeriesId: string | null;
    hiddenSeriesIds: string[];
  }>({
    activeSeriesId: null,
    hiddenSeriesIds: [],
  });

  useEffect(() => {
    setState((current) => {
      const nextHidden = current.hiddenSeriesIds.filter((seriesId) => visibleSeriesSet.has(seriesId));
      const nextActive =
        current.activeSeriesId && visibleSeriesSet.has(current.activeSeriesId)
          ? current.activeSeriesId
          : null;

      if (
        nextActive === current.activeSeriesId &&
        nextHidden.length === current.hiddenSeriesIds.length
      ) {
        return current;
      }

      return {
        activeSeriesId: nextActive,
        hiddenSeriesIds: nextHidden,
      };
    });
  }, [visibleSeriesSet]);

  const toggleSeries = (seriesId: string) => {
    setState((current) => {
      const isHidden = current.hiddenSeriesIds.includes(seriesId);
      if (isHidden) {
        return {
          ...current,
          hiddenSeriesIds: current.hiddenSeriesIds.filter((item) => item !== seriesId),
        };
      }

      if (current.activeSeriesId === seriesId) {
        return {
          activeSeriesId: null,
          hiddenSeriesIds: [...current.hiddenSeriesIds, seriesId],
        };
      }

      return {
        ...current,
        activeSeriesId: seriesId,
      };
    });
  };

  return {
    activeSeriesId: state.activeSeriesId,
    hiddenSeriesIds: state.hiddenSeriesIds,
    toggleSeries,
  };
}
