import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import {
  InvestmentCustomPortfolioRequestPayload,
  SavedInvestmentPortfolioPayload,
} from '../types/api';

const STORAGE_KEY = 'investing-workbench.saved-investment-portfolios.v1';

export function useSavedInvestmentPortfolios() {
  const [savedPortfolios, setSavedPortfolios] = useState<SavedInvestmentPortfolioPayload[]>([]);

  useEffect(() => {
    let isMounted = true;
    const localPortfolios = readSavedPortfolios();
    setSavedPortfolios(localPortfolios);
    apiClient
      .listSavedInvestmentPortfolios()
      .then((remotePortfolios) => {
        if (!isMounted) {
          return;
        }
        const merged = mergePortfolios(remotePortfolios, localPortfolios);
        setSavedPortfolios(merged);
        writeSavedPortfolios(merged);
      })
      .catch(() => {
        if (isMounted) {
          setSavedPortfolios(localPortfolios);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const persist = useCallback((next: SavedInvestmentPortfolioPayload[]) => {
    const ordered = [...next].sort((left, right) => right.updated_at.localeCompare(left.updated_at));
    setSavedPortfolios(ordered);
    writeSavedPortfolios(ordered);
  }, []);

  const savePortfolio = useCallback(
    async (
      portfolio: InvestmentCustomPortfolioRequestPayload
    ): Promise<SavedInvestmentPortfolioPayload | null> => {
      const components = portfolio.components.filter((component) => component.weight > 0);
      if (components.length < 2) {
        return null;
      }

      const now = new Date().toISOString();
      const label = portfolio.label.trim() || 'Minha carteira';
      const existing = savedPortfolios.find(
        (item) => normalizeLabel(item.label) === normalizeLabel(label)
      );
      const draft: SavedInvestmentPortfolioPayload = {
        ...portfolio,
        portfolio_id: existing?.portfolio_id ?? buildPortfolioId(label),
        label,
        description: portfolio.description?.trim() || null,
        rebalance_frequency: portfolio.rebalance_frequency ?? 'monthly',
        components,
        created_at: existing?.created_at ?? now,
        updated_at: now,
      };
      const saved = await apiClient.saveInvestmentPortfolio(draft).catch(() => draft);
      persist([
        saved,
        ...savedPortfolios.filter((item) => item.portfolio_id !== saved.portfolio_id),
      ]);
      return saved;
    },
    [persist, savedPortfolios]
  );

  const deletePortfolio = useCallback(
    async (portfolioId: string) => {
      await apiClient.deleteInvestmentPortfolio(portfolioId).catch(() => undefined);
      persist(savedPortfolios.filter((item) => item.portfolio_id !== portfolioId));
    },
    [persist, savedPortfolios]
  );

  return {
    savedPortfolios,
    savePortfolio,
    deletePortfolio,
  };
}

function mergePortfolios(
  remote: SavedInvestmentPortfolioPayload[],
  local: SavedInvestmentPortfolioPayload[]
) {
  const byId = new Map<string, SavedInvestmentPortfolioPayload>();
  [...local, ...remote].forEach((portfolio) => {
    byId.set(portfolio.portfolio_id, portfolio);
  });
  return Array.from(byId.values()).sort((left, right) =>
    right.updated_at.localeCompare(left.updated_at)
  );
}

function readSavedPortfolios(): SavedInvestmentPortfolioPayload[] {
  if (typeof window === 'undefined') {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isSavedPortfolio).sort((left, right) =>
      right.updated_at.localeCompare(left.updated_at)
    );
  } catch {
    return [];
  }
}

function writeSavedPortfolios(portfolios: SavedInvestmentPortfolioPayload[]) {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(portfolios));
}

function isSavedPortfolio(value: unknown): value is SavedInvestmentPortfolioPayload {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as SavedInvestmentPortfolioPayload;
  return (
    typeof candidate.portfolio_id === 'string' &&
    typeof candidate.label === 'string' &&
    Array.isArray(candidate.components) &&
    candidate.components.length >= 2
  );
}

function normalizeLabel(label: string) {
  return label.trim().toLowerCase();
}

function buildPortfolioId(label: string) {
  const slug = normalizeLabel(label)
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 48);
  return `saved_${slug || 'portfolio'}_${Date.now()}`;
}
