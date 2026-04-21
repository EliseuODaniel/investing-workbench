import { useMemo, useState } from 'react';
import { Activity, BarChart3, DollarSign, TrendingDown } from 'lucide-react';
import CashChartPanel from './charts-tabbed/CashChartPanel';
import ChartControlsFooter from './charts-tabbed/ChartControlsFooter';
import ChartTabsNav from './charts-tabbed/ChartTabsNav';
import DrawdownChartPanel from './charts-tabbed/DrawdownChartPanel';
import EquityChartPanel from './charts-tabbed/EquityChartPanel';
import TradesChartPanel from './charts-tabbed/TradesChartPanel';
import { ChartTabDefinition, ChartTabId, ChartsTabbedProps } from './charts-tabbed/types';
import { getStrategyColorFactory } from './charts-tabbed/utils';
import { useChartsTabbedData } from '../hooks/useChartsTabbedData';

const tabs: ChartTabDefinition[] = [
  {
    id: 'equity',
    name: 'Equity',
    icon: BarChart3,
    description: 'Evolução do patrimônio ao longo do tempo',
  },
  {
    id: 'drawdown',
    name: 'Drawdown',
    icon: TrendingDown,
    description: 'Quedas máximas do patrimônio',
  },
  {
    id: 'cash',
    name: 'Caixa',
    icon: DollarSign,
    description: 'Evolução do capital disponível',
  },
  {
    id: 'trades',
    name: 'Trades',
    icon: Activity,
    description: 'Pontos de entrada e saída',
  },
];

export default function ChartsTabbed({
  results,
  buyHoldEquity,
  visibleStrategies,
  visibleBenchmarks,
  benchmarks,
}: ChartsTabbedProps) {
  const [activeTab, setActiveTab] = useState<ChartTabId>('equity');
  const { equityData, drawdownData, tradesData } = useChartsTabbedData({
    results,
    buyHoldEquity,
    benchmarks,
    visibleStrategies,
    visibleBenchmarks,
  });

  const getStrategyColor = useMemo(
    () => getStrategyColorFactory(Object.keys(results)),
    [results],
  );

  const activeTabDefinition = tabs.find((tab) => tab.id === activeTab);

  const tabContent = (() => {
    switch (activeTab) {
      case 'equity':
        return (
          <EquityChartPanel
            results={results}
            benchmarks={benchmarks}
            visibleStrategies={visibleStrategies}
            visibleBenchmarks={visibleBenchmarks}
            equityData={equityData}
            getStrategyColor={getStrategyColor}
          />
        );
      case 'drawdown':
        return (
          <DrawdownChartPanel
            results={results}
            visibleStrategies={visibleStrategies}
            drawdownData={drawdownData}
          />
        );
      case 'cash':
        return (
          <CashChartPanel
            results={results}
            visibleStrategies={visibleStrategies}
            equityData={equityData}
            getStrategyColor={getStrategyColor}
          />
        );
      case 'trades':
        return (
          <TradesChartPanel
            results={results}
            visibleStrategies={visibleStrategies}
            tradesData={tradesData}
            getStrategyColor={getStrategyColor}
          />
        );
      default:
        return null;
    }
  })();

  return (
    <div className="card">
      <ChartTabsNav tabs={tabs} activeTab={activeTab} onSelectTab={setActiveTab} />

      <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {activeTabDefinition?.description}
        </p>
      </div>

      <div className="mt-6">{tabContent}</div>

      <ChartControlsFooter description="Configure a visibilidade dos elementos no painel de controles" />
    </div>
  );
}
