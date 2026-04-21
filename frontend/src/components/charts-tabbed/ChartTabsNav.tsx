import { ChartTabsNavProps } from './types';

export default function ChartTabsNav({ tabs, activeTab, onSelectTab }: ChartTabsNavProps) {
  return (
    <div className="border-b border-gray-200 dark:border-gray-700">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`group relative min-w-0 flex-1 overflow-hidden py-4 px-1 text-center text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <div className="flex items-center justify-center">
                <Icon className="h-4 w-4 mr-2" />
                {tab.name}
              </div>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
