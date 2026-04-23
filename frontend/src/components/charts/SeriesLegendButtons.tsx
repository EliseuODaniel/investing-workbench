interface SeriesLegendButtonItem {
  id: string;
  label: string;
  color: string;
}

interface SeriesLegendButtonsProps {
  items: SeriesLegendButtonItem[];
  activeSeriesId: string | null;
  hiddenSeriesIds?: string[];
  onToggle: (seriesId: string) => void;
  helperText?: string;
}

export default function SeriesLegendButtons({
  items,
  activeSeriesId,
  hiddenSeriesIds = [],
  onToggle,
  helperText = 'Um clique destaca, dois ocultam a curva escolhida e o próximo clique traz essa curva de volta.',
}: SeriesLegendButtonsProps) {
  if (items.length === 0) {
    return null;
  }

  const hiddenSeriesSet = new Set(hiddenSeriesIds);

  return (
    <div className="mt-4">
      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const isActive = activeSeriesId === item.id;
          const isHidden = hiddenSeriesSet.has(item.id);
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onToggle(item.id)}
              aria-pressed={isActive}
              data-visibility-state={isHidden ? 'hidden' : isActive ? 'focused' : 'visible'}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition ${
                isActive
                  ? 'border-slate-300 bg-slate-100 text-slate-950 dark:border-slate-500 dark:bg-slate-800 dark:text-slate-50'
                  : isHidden
                    ? 'border-dashed border-gray-300 bg-gray-50 text-gray-400 dark:border-gray-700 dark:bg-gray-900/70 dark:text-gray-500'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300 hover:text-gray-900 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:text-gray-100'
              }`}
            >
              <span
                aria-hidden="true"
                className={`h-2.5 w-2.5 rounded-full ${isHidden ? 'opacity-40' : ''}`}
                style={{ backgroundColor: item.color }}
              />
              <span className={isHidden ? 'line-through' : ''}>{item.label}</span>
              {isHidden ? (
                <span className="rounded-full border border-gray-300 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-gray-500 dark:border-gray-700 dark:text-gray-400">
                  oculto
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">{helperText}</p>
    </div>
  );
}
