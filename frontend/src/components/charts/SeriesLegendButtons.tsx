interface SeriesLegendButtonItem {
  id: string;
  label: string;
  color: string;
}

interface SeriesLegendButtonsProps {
  items: SeriesLegendButtonItem[];
  activeSeriesId: string | null;
  onToggle: (seriesId: string) => void;
  helperText?: string;
}

export default function SeriesLegendButtons({
  items,
  activeSeriesId,
  onToggle,
  helperText = 'Clique novamente no item selecionado para voltar a mostrar todas as curvas.',
}: SeriesLegendButtonsProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const isActive = activeSeriesId === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onToggle(item.id)}
              aria-pressed={isActive}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition ${
                isActive
                  ? 'border-slate-300 bg-slate-100 text-slate-950 dark:border-slate-500 dark:bg-slate-800 dark:text-slate-50'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300 hover:text-gray-900 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:text-gray-100'
              }`}
            >
              <span
                aria-hidden="true"
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">{helperText}</p>
    </div>
  );
}
