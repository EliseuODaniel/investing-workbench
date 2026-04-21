interface SectionTabOption<T extends string = string> {
  id: T;
  label: string;
  badge?: string | number;
}

interface SectionTabsProps<T extends string = string> {
  tabs: SectionTabOption<T>[];
  activeTab: T;
  onChange: (tab: T) => void;
}

export default function SectionTabs<T extends string = string>({
  tabs,
  activeTab,
  onChange,
}: SectionTabsProps<T>) {
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === tab.id
              ? 'border-gray-900 bg-gray-900 text-white dark:border-gray-100 dark:bg-gray-100 dark:text-gray-900'
              : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:text-gray-900 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-gray-600 dark:hover:text-gray-100'
          }`}
        >
          {tab.label}
          {tab.badge !== undefined && (
            <span
              className={`ml-2 rounded-full px-2 py-0.5 text-xs ${
                activeTab === tab.id
                  ? 'bg-white/20 text-white dark:bg-gray-900/15 dark:text-gray-900'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-200'
              }`}
            >
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
