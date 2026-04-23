import { useMemo, useState } from 'react';
import { Activity, BarChart3, DollarSign, TrendingDown } from 'lucide-react';
import ChartDateRangeControls from './charts/ChartDateRangeControls';
import CashChartPanel from './charts-tabbed/CashChartPanel';
import ChartControlsFooter from './charts-tabbed/ChartControlsFooter';
import ChartTabsNav from './charts-tabbed/ChartTabsNav';
import DrawdownChartPanel from './charts-tabbed/DrawdownChartPanel';
import EquityChartPanel from './charts-tabbed/EquityChartPanel';
import TradesChartPanel from './charts-tabbed/TradesChartPanel';
import { ChartTabDefinition, ChartTabId, ChartsTabbedProps, DrawdownChartPoint } from './charts-tabbed/types';
import { getBenchmarkColorFactory, getStrategyColorFactory } from './charts-tabbed/utils';
import { useChartsTabbedData } from '../hooks/useChartsTabbedData';
import { filterRowsByDateRange, useChartDateRange } from '../hooks/useChartDateRange';
import { buildDrawdownSeriesFromEquity, rebaseLineSeriesData } from '../lib/chartSeries';

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
  const { equityData, tradesData } = useChartsTabbedData({
    results,
    buyHoldEquity,
    benchmarks,
    visibleStrategies,
    visibleBenchmarks,
  });
  const dateRange = useChartDateRange(equityData, 'timestamp');
  const shouldRebase = Boolean(dateRange.minDate) && dateRange.startDate !== dateRange.minDate;
  const equitySeriesIds = useMemo(
    () => [
      ...visibleStrategies,
      ...(visibleBenchmarks.includes('Buy & Hold') ? ['Buy & Hold'] : []),
      ...Object.keys(benchmarks ?? {}).filter((name) => visibleBenchmarks.includes(name)),
    ],
    [benchmarks, visibleBenchmarks, visibleStrategies]
  );
  const filteredEquityData = useMemo(
    () =>
      shouldRebase
        ? rebaseLineSeriesData(
            dateRange.filteredData,
            equitySeriesIds,
            visibleBenchmarks.includes('Buy & Hold') ? 'Buy & Hold' : equitySeriesIds[0] ?? null
          )
        : dateRange.filteredData,
    [dateRange.filteredData, equitySeriesIds, shouldRebase, visibleBenchmarks]
  );
  const filteredCashData = useMemo(
    () =>
      shouldRebase
        ? rebaseLineSeriesData(
            dateRange.filteredData,
            visibleStrategies.map((strategyName) => `${strategyName}_cash`),
            visibleStrategies.length > 0 ? `${visibleStrategies[0]}_cash` : null
          )
        : dateRange.filteredData,
    [dateRange.filteredData, shouldRebase, visibleStrategies]
  );
  const filteredDrawdownData = useMemo(
    () =>
      buildDrawdownSeriesFromEquity(dateRange.filteredData, visibleStrategies) as DrawdownChartPoint[],
    [dateRange.filteredData, visibleStrategies]
  );
  const filteredTradesData = useMemo(
    () =>
      filterRowsByDateRange(tradesData, 'timestamp', dateRange.startDate, dateRange.endDate),
    [dateRange.endDate, dateRange.startDate, tradesData]
  );

  const getStrategyColor = useMemo(
    () => getStrategyColorFactory(Object.keys(results)),
    [results],
  );
  const getBenchmarkColor = useMemo(
    () => getBenchmarkColorFactory([
      'Buy & Hold',
      ...Object.keys(benchmarks ?? {}),
    ]),
    [benchmarks]
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
            equityData={filteredEquityData}
            getStrategyColor={getStrategyColor}
            getBenchmarkColor={getBenchmarkColor}
          />
        );
      case 'drawdown':
        return (
          <DrawdownChartPanel
            results={results}
            visibleStrategies={visibleStrategies}
            drawdownData={filteredDrawdownData}
            getStrategyColor={getStrategyColor}
          />
        );
      case 'cash':
        return (
          <CashChartPanel
            results={results}
            visibleStrategies={visibleStrategies}
            equityData={filteredCashData}
            getStrategyColor={getStrategyColor}
          />
        );
      case 'trades':
        return (
          <TradesChartPanel
            results={results}
            visibleStrategies={visibleStrategies}
            tradesData={filteredTradesData}
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

      {dateRange.hasDateRange ? (
        <ChartDateRangeControls
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          minDate={dateRange.minDate ?? dateRange.startDate}
          maxDate={dateRange.maxDate ?? dateRange.endDate}
          startIndex={dateRange.startIndex}
          endIndex={dateRange.endIndex}
          maxIndex={dateRange.maxIndex}
          onStartIndexChange={dateRange.setStartIndex}
          onEndIndexChange={dateRange.setEndIndex}
          onReset={dateRange.resetRange}
        />
      ) : null}

      <ChartControlsFooter description="Configure a visibilidade dos elementos no painel de controles" />
    </div>
  );
}
