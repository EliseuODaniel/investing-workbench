import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import type {
  BacktestStrategyCatalogPayload,
  SavedStrategyRadarItemPayload,
} from '../types/api';

const STORAGE_KEY = 'investing-workbench.strategy-radar.v1';

export type SavedStrategyRadarItem = SavedStrategyRadarItemPayload;
type CatalogStrategy = BacktestStrategyCatalogPayload['strategies'][number];

export function useSavedStrategyRadar() {
  const [savedItems, setSavedItems] = useState<SavedStrategyRadarItem[]>(() =>
    readSavedStrategyRadar()
  );

  useEffect(() => {
    let isMounted = true;
    const localItems = readSavedStrategyRadar();
    apiClient
      .listSavedStrategyRadarItems()
      .then((remoteItems) => {
        if (!isMounted) {
          return;
        }
        const merged = mergeStrategyRadarItems(remoteItems, localItems);
        setSavedItems(merged);
        writeSavedStrategyRadar(merged);
      })
      .catch(() => {
        if (isMounted) {
          setSavedItems(localItems);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const savedStrategyIds = useMemo(
    () => new Set(savedItems.map((item) => item.strategy_id)),
    [savedItems]
  );

  const saveStrategy = useCallback((strategy: CatalogStrategy) => {
    const item: SavedStrategyRadarItem = {
      strategy_id: strategy.strategy_id,
      label: strategy.label,
      family: strategy.family,
      direction: strategy.direction,
      parameter_values: strategy.parameter_defaults ?? {},
      universe: strategy.universe_defaults ?? [],
      timeframe: strategy.supported_timeframes[0] ?? null,
      setup_notes: strategy.execution_notes ?? [],
      saved_at: new Date().toISOString(),
    };
    setSavedItems((current) => {
      const next = [
        item,
        ...current.filter((existing) => existing.strategy_id !== item.strategy_id),
      ].slice(0, 12);
      writeSavedStrategyRadar(next);
      void apiClient.saveStrategyRadarItem(item).catch(() => undefined);
      return next;
    });
  }, []);

  const removeStrategy = useCallback((strategyId: string) => {
    setSavedItems((current) => {
      const next = current.filter((item) => item.strategy_id !== strategyId);
      writeSavedStrategyRadar(next);
      void apiClient.deleteStrategyRadarItem(strategyId).catch(() => undefined);
      return next;
    });
  }, []);

  const updateStrategySetup = useCallback((item: SavedStrategyRadarItem) => {
    const nextItem = normalizeSavedStrategyRadarItem({
      ...item,
      saved_at: new Date().toISOString(),
    });
    setSavedItems((current) => {
      const next = [
        nextItem,
        ...current.filter((existing) => existing.strategy_id !== nextItem.strategy_id),
      ].slice(0, 12);
      writeSavedStrategyRadar(next);
      void apiClient.saveStrategyRadarItem(nextItem).catch(() => undefined);
      return next;
    });
  }, []);

  return {
    savedItems,
    savedStrategyIds,
    saveStrategy,
    removeStrategy,
    updateStrategySetup,
  };
}

function readSavedStrategyRadar(): SavedStrategyRadarItem[] {
  if (typeof window === 'undefined') {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isSavedStrategyRadarItem).map(normalizeSavedStrategyRadarItem);
  } catch {
    return [];
  }
}

function writeSavedStrategyRadar(items: SavedStrategyRadarItem[]) {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

function mergeStrategyRadarItems(
  remoteItems: SavedStrategyRadarItem[],
  localItems: SavedStrategyRadarItem[]
) {
  const byId = new Map<string, SavedStrategyRadarItem>();
  [...localItems, ...remoteItems].forEach((item) => {
    byId.set(item.strategy_id, normalizeSavedStrategyRadarItem(item));
  });
  return Array.from(byId.values()).sort((left, right) =>
    savedAtValue(right).localeCompare(savedAtValue(left))
  );
}

function normalizeSavedStrategyRadarItem(
  item: SavedStrategyRadarItem
): SavedStrategyRadarItem {
  return {
    ...item,
    parameter_values: item.parameter_values ?? {},
    universe: item.universe ?? [],
    setup_notes: item.setup_notes ?? [],
    saved_at: item.saved_at || new Date(0).toISOString(),
  };
}

function savedAtValue(item: SavedStrategyRadarItem): string {
  return item.saved_at || '';
}

function isSavedStrategyRadarItem(value: unknown): value is SavedStrategyRadarItem {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as Partial<SavedStrategyRadarItem>;
  return (
    typeof candidate.strategy_id === 'string' &&
    typeof candidate.label === 'string' &&
    typeof candidate.family === 'string' &&
    typeof candidate.direction === 'string'
  );
}
