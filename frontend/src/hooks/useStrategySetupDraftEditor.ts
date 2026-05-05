import { useCallback, useState } from 'react';
import {
  applyStrategySetupDraft,
  buildStrategySetupDraft,
} from '../lib/strategySetupDrafts';
import type { StrategySetupDraft } from '../components/strategy/StrategySetupEditForm';
import type { SavedStrategyRadarItem } from './useSavedStrategyRadar';

type UseStrategySetupDraftEditorOptions = {
  updateStrategySetup: (item: SavedStrategyRadarItem) => void;
};

export function useStrategySetupDraftEditor({
  updateStrategySetup,
}: UseStrategySetupDraftEditorOptions) {
  const [editingStrategyId, setEditingStrategyId] = useState<string | null>(null);
  const [setupDraft, setSetupDraft] = useState<StrategySetupDraft | null>(null);

  const startEditingSetup = useCallback((item: SavedStrategyRadarItem) => {
    setEditingStrategyId(item.strategy_id);
    setSetupDraft(buildStrategySetupDraft(item));
  }, []);

  const cancelEditingSetup = useCallback(() => {
    setEditingStrategyId(null);
    setSetupDraft(null);
  }, []);

  const saveEditedSetup = useCallback(
    (item: SavedStrategyRadarItem) => {
      setSetupDraft((currentDraft) => {
        if (!currentDraft) {
          return currentDraft;
        }
        updateStrategySetup(applyStrategySetupDraft(item, currentDraft));
        setEditingStrategyId(null);
        return null;
      });
    },
    [updateStrategySetup]
  );

  const updateDraftField = useCallback(
    (field: keyof StrategySetupDraft, value: string) => {
      setSetupDraft((current) => (current ? { ...current, [field]: value } : current));
    },
    []
  );

  return {
    editingStrategyId,
    setupDraft,
    startEditingSetup,
    cancelEditingSetup,
    saveEditedSetup,
    updateDraftField,
  };
}
