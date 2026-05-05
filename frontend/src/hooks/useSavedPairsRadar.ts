import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  PairsBacktestManifestPayload,
  PairsBacktestResultsPayload,
  SavedPairsRadarItemPayload,
} from '../types/api';

const STORAGE_KEY = 'investing-workbench.saved-pairs-radar.v1';

export type SavedPairsRadarItem = SavedPairsRadarItemPayload;

export function useSavedPairsRadar(
  backtests: PairsBacktestManifestPayload[],
  activeBacktest?: PairsBacktestResultsPayload | null
) {
  const [savedItems, setSavedItems] = useState<SavedPairsRadarItem[]>(() =>
    readSavedPairsRadar()
  );

  useEffect(() => {
    let isMounted = true;
    const localItems = readSavedPairsRadar();
    apiClient
      .listSavedPairsRadarItems()
      .then((remoteItems) => {
        if (!isMounted) {
          return;
        }
        const merged = mergeRadarItems(remoteItems, localItems);
        setSavedItems(merged);
        writeSavedPairsRadar(merged);
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

  const activeManifest = useMemo(
    () => findActiveManifest(backtests, activeBacktest),
    [activeBacktest, backtests]
  );
  const savedIds = useMemo(
    () => new Set(savedItems.map((item) => item.pairs_backtest_id)),
    [savedItems]
  );
  const isActiveSaved = activeManifest
    ? savedIds.has(activeManifest.pairs_backtest_id)
    : false;

  const saveActiveBacktest = useCallback(() => {
    if (!activeManifest) {
      return;
    }
    const nextItem = buildSavedItem(activeManifest);
    setSavedItems((current) => {
      const withoutCurrent = current.filter(
        (item) => item.pairs_backtest_id !== nextItem.pairs_backtest_id
      );
      const next = [nextItem, ...withoutCurrent].slice(0, 12);
      writeSavedPairsRadar(next);
      void apiClient.savePairsRadarItem(nextItem).catch(() => undefined);
      return next;
    });
  }, [activeManifest]);

  const removeSavedBacktest = useCallback((pairsBacktestId: string) => {
    setSavedItems((current) => {
      const next = current.filter((item) => item.pairs_backtest_id !== pairsBacktestId);
      writeSavedPairsRadar(next);
      void apiClient.deletePairsRadarItem(pairsBacktestId).catch(() => undefined);
      return next;
    });
  }, []);

  const clearSavedBacktests = useCallback(() => {
    setSavedItems([]);
    writeSavedPairsRadar([]);
  }, []);

  return {
    savedItems,
    activeManifest,
    isActiveSaved,
    saveActiveBacktest,
    removeSavedBacktest,
    clearSavedBacktests,
  };
}

function mergeRadarItems(remote: SavedPairsRadarItem[], local: SavedPairsRadarItem[]) {
  const byId = new Map<string, SavedPairsRadarItem>();
  [...local, ...remote].forEach((item) => {
    byId.set(item.pairs_backtest_id, item);
  });
  return Array.from(byId.values()).sort((left, right) =>
    right.saved_at.localeCompare(left.saved_at)
  );
}

function findActiveManifest(
  backtests: PairsBacktestManifestPayload[],
  activeBacktest?: PairsBacktestResultsPayload | null
) {
  if (!activeBacktest) {
    return null;
  }
  const persisted = backtests.find(
    (item) => item.pairs_backtest_id === activeBacktest.pairs_backtest_id
  );
  if (persisted) {
    return persisted;
  }
  const manifest = activeBacktest.manifest;
  if (isPairsManifest(manifest)) {
    return manifest;
  }
  return null;
}

function buildSavedItem(manifest: PairsBacktestManifestPayload): SavedPairsRadarItem {
  return {
    pairs_backtest_id: manifest.pairs_backtest_id,
    label: `${manifest.preset_label} · ${manifest.start_date}`,
    preset_label: manifest.preset_label,
    created_at: manifest.created_at,
    saved_at: new Date().toISOString(),
    scenario_count: manifest.scenario_count,
    candidate_pair_count: manifest.candidate_pair_count,
    benchmark_ids: manifest.benchmark_ids,
  };
}

function isPairsManifest(value: unknown): value is PairsBacktestManifestPayload {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as Partial<PairsBacktestManifestPayload>;
  return (
    typeof candidate.pairs_backtest_id === 'string' &&
    typeof candidate.preset_label === 'string' &&
    typeof candidate.start_date === 'string' &&
    Array.isArray(candidate.benchmark_ids)
  );
}

function readSavedPairsRadar(): SavedPairsRadarItem[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isSavedPairsRadarItem);
  } catch {
    return [];
  }
}

function writeSavedPairsRadar(items: SavedPairsRadarItem[]) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Local storage is a convenience layer; failed writes should not break analysis.
  }
}

function isSavedPairsRadarItem(value: unknown): value is SavedPairsRadarItem {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as Partial<SavedPairsRadarItem>;
  return (
    typeof candidate.pairs_backtest_id === 'string' &&
    typeof candidate.label === 'string' &&
    typeof candidate.preset_label === 'string' &&
    typeof candidate.created_at === 'string' &&
    typeof candidate.saved_at === 'string'
  );
}
