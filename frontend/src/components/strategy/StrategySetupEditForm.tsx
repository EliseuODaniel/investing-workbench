import { Save, X } from 'lucide-react';

export type StrategySetupDraft = {
  universeText: string;
  timeframe: string;
  parametersText: string;
  notesText: string;
};

type StrategySetupEditFormProps = {
  draft: StrategySetupDraft;
  onChange: (field: keyof StrategySetupDraft, value: string) => void;
  onCancel: () => void;
  onSave: () => void;
};

export function StrategySetupEditForm({
  draft,
  onChange,
  onCancel,
  onSave,
}: StrategySetupEditFormProps) {
  return (
    <div className="mt-3 grid gap-2 border-t border-gray-100 pt-3 dark:border-gray-800">
      <label className="grid gap-1 text-[11px] font-medium text-gray-600 dark:text-gray-300">
        Timeframe
        <input
          className="rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs font-normal text-gray-900 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
          value={draft.timeframe}
          onChange={(event) => onChange('timeframe', event.target.value)}
        />
      </label>
      <label className="grid gap-1 text-[11px] font-medium text-gray-600 dark:text-gray-300">
        Universo
        <input
          className="rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs font-normal text-gray-900 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
          value={draft.universeText}
          onChange={(event) => onChange('universeText', event.target.value)}
        />
      </label>
      <label className="grid gap-1 text-[11px] font-medium text-gray-600 dark:text-gray-300">
        Parametros
        <textarea
          className="min-h-20 rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs font-normal text-gray-900 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
          value={draft.parametersText}
          onChange={(event) => onChange('parametersText', event.target.value)}
        />
      </label>
      <label className="grid gap-1 text-[11px] font-medium text-gray-600 dark:text-gray-300">
        Notas
        <textarea
          className="min-h-16 rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs font-normal text-gray-900 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
          value={draft.notesText}
          onChange={(event) => onChange('notesText', event.target.value)}
        />
      </label>
      <div className="flex flex-wrap justify-end gap-2">
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-2 py-1.5 text-xs text-gray-600 hover:border-gray-400 dark:border-gray-700 dark:text-gray-300"
          onClick={onCancel}
        >
          <X className="h-3.5 w-3.5" />
          Cancelar
        </button>
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded-lg border border-blue-300 bg-blue-50 px-2 py-1.5 text-xs font-medium text-blue-700 hover:border-blue-400 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-200"
          onClick={onSave}
        >
          <Save className="h-3.5 w-3.5" />
          Salvar setup
        </button>
      </div>
    </div>
  );
}
