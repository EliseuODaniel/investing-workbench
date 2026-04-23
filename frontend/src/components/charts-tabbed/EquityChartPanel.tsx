import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import SeriesLegendButtons from '../charts/SeriesLegendButtons';
import { useSeriesLegendState } from '../../hooks/useSeriesLegendState';
import { EquityChartPanelProps } from './types';
import { formatCurrency, toNumber } from './utils';

export default function EquityChartPanel({
  results,
  benchmarks,
  visibleStrategies,
  visibleBenchmarks,
  equityData,
  getStrategyColor,
  getBenchmarkColor,
}: EquityChartPanelProps) {
  const legendItems = useMemo(() => {
    const strategyItems = Object.entries(results)
      .filter(([strategyName]) => visibleStrategies.includes(strategyName))
      .map(([strategyName]) => ({
        id: strategyName,
        label: strategyName,
        color: getStrategyColor(strategyName),
      }));

    const benchmarkItems = [
      ...(visibleBenchmarks.includes('Buy & Hold')
        ? [{ id: 'Buy & Hold', label: 'Buy & Hold', color: getBenchmarkColor('Buy & Hold') }]
        : []),
      ...Object.keys(benchmarks ?? {})
        .filter((name) => visibleBenchmarks.includes(name))
        .map((name) => ({
          id: name,
          label: name,
          color: getBenchmarkColor(name),
        })),
    ];

    return [...strategyItems, ...benchmarkItems];
  }, [benchmarks, getBenchmarkColor, getStrategyColor, results, visibleBenchmarks, visibleStrategies]);
  const { activeSeriesId, hiddenSeriesIds, toggleSeries } = useSeriesLegendState(
    legendItems.map((item) => item.id)
  );
  const hiddenSeriesSet = useMemo(() => new Set(hiddenSeriesIds), [hiddenSeriesIds]);

  return (
    <div>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={equityData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
            <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" tickFormatter={formatCurrency} />
            <Tooltip
              formatter={(value) => [formatCurrency(toNumber(value)), 'Patrimônio']}
              labelFormatter={(label) => label}
            />

            {Object.entries(results).map(([strategyName]) =>
              visibleStrategies.includes(strategyName) ? (
                <Line
                  key={strategyName}
                  type="monotone"
                  dataKey={strategyName}
                  hide={hiddenSeriesSet.has(strategyName)}
                  stroke={getStrategyColor(strategyName)}
                  strokeWidth={activeSeriesId === strategyName ? 4 : 2}
                  opacity={activeSeriesId === null || activeSeriesId === strategyName ? 1 : 0.18}
                  dot={false}
                  name={strategyName}
                  connectNulls={false}
                />
              ) : null
            )}

            {visibleBenchmarks.includes('Buy & Hold') && (
              <Line
                type="monotone"
                dataKey="Buy & Hold"
                hide={hiddenSeriesSet.has('Buy & Hold')}
                stroke={getBenchmarkColor('Buy & Hold')}
                strokeWidth={activeSeriesId === 'Buy & Hold' ? 4 : 2}
                opacity={activeSeriesId === null || activeSeriesId === 'Buy & Hold' ? 1 : 0.18}
                strokeDasharray="5 5"
                dot={false}
                name="Buy & Hold"
                connectNulls={false}
              />
            )}

            {benchmarks &&
              Object.entries(benchmarks).map(([name]) =>
                visibleBenchmarks.includes(name) ? (
                  <Line
                    key={name}
                    type="monotone"
                    dataKey={name}
                    hide={hiddenSeriesSet.has(name)}
                    stroke={getBenchmarkColor(name)}
                    strokeWidth={activeSeriesId === name ? 4 : 2}
                    opacity={activeSeriesId === null || activeSeriesId === name ? 1 : 0.18}
                    strokeDasharray="3 3"
                    dot={false}
                    name={name}
                    connectNulls={false}
                  />
                ) : null
              )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <SeriesLegendButtons
        items={legendItems}
        activeSeriesId={activeSeriesId}
        hiddenSeriesIds={hiddenSeriesIds}
        onToggle={toggleSeries}
      />
    </div>
  );
}
