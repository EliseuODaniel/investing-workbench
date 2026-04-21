import { useCallback, useState } from 'react';
import { apiClient } from '../lib/api';
import { Wege3RegraAScenarioPayload } from '../types/api';

export interface Wege3RegraADraft {
  startDate: string;
  endDate: string;
  forceDownload: boolean;
}

const DEFAULT_DRAFT: Wege3RegraADraft = {
  startDate: '2021-01-01',
  endDate: '',
  forceDownload: false,
};

export function useWege3RegraA(onError: (message: string | null) => void) {
  const [draft, setDraft] = useState<Wege3RegraADraft>(DEFAULT_DRAFT);
  const [result, setResult] = useState<Wege3RegraAScenarioPayload | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const updateDraft = useCallback(
    <Key extends keyof Wege3RegraADraft>(field: Key, value: Wege3RegraADraft[Key]) => {
      setDraft((current) => ({ ...current, [field]: value }));
    },
    []
  );

  const runScenario = useCallback(async () => {
    setIsRunning(true);
    onError(null);
    try {
      const response = await apiClient.runWege3RegraAScenario({
        start_date: draft.startDate,
        end_date: draft.endDate || null,
        force_download: draft.forceDownload,
      });
      setResult(response);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Nao foi possivel rodar o cenario WEGE3.';
      onError(message);
    } finally {
      setIsRunning(false);
    }
  }, [draft.endDate, draft.forceDownload, draft.startDate, onError]);

  return {
    draft,
    result,
    isRunning,
    updateDraft,
    runScenario,
  };
}
