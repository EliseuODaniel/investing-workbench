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
import { DrawdownChartPanelProps } from './types';
import { toNumber } from './utils';

export default function DrawdownChartPanel({
  results,
  visibleStrategies,
  drawdownData,
  getStrategyColor,
}: DrawdownChartPanelProps) {
  const legendItems = useMemo(
    () =>
      Object.keys(results)
        .filter((strategyName) => visibleStrategies.includes(strategyName))
        .map((strategyName) => ({
          id: `${strategyName}_drawdown`,
          label: `${strategyName} DD`,
          color: getStrategyColor(strategyName),
        })),
    [getStrategyColor, results, visibleStrategies]
  );
  const { activeSeriesId, hiddenSeriesIds, toggleSeries } = useSeriesLegendState(
    legendItems.map((item) => item.id)
  );
  const hiddenSeriesSet = useMemo(() => new Set(hiddenSeriesIds), [hiddenSeriesIds]);

  return (
    <div>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={drawdownData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              tickFormatter={(value: number) => `${value.toFixed(1)}%`}
            />
            <Tooltip
              formatter={(value) => [`${toNumber(value).toFixed(2)}%`, 'Drawdown']}
              labelFormatter={(label) => label}
            />

            {Object.entries(results).map(([strategyName]) =>
              visibleStrategies.includes(strategyName) ? (
                <Line
                  key={`${strategyName}_drawdown`}
                  type="monotone"
                  dataKey={`${strategyName}_drawdown`}
                  hide={hiddenSeriesSet.has(`${strategyName}_drawdown`)}
                  stroke={getStrategyColor(strategyName)}
                  strokeWidth={activeSeriesId === `${strategyName}_drawdown` ? 4 : 2}
                  opacity={
                    activeSeriesId === null || activeSeriesId === `${strategyName}_drawdown`
                      ? 1
                      : 0.18
                  }
                  dot={false}
                  name={`${strategyName} DD`}
                  fill={getStrategyColor(strategyName)}
                  fillOpacity={0.1}
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
