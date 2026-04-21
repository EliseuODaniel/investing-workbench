import { useMemo, useState } from 'react';
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
import { CashChartPanelProps } from './types';
import { formatCurrency, toNumber } from './utils';

export default function CashChartPanel({
  results,
  visibleStrategies,
  equityData,
  getStrategyColor,
}: CashChartPanelProps) {
  const [activeSeriesId, setActiveSeriesId] = useState<string | null>(null);
  const legendItems = useMemo(
    () =>
      Object.keys(results)
        .filter((strategyName) => visibleStrategies.includes(strategyName))
        .map((strategyName) => ({
          id: `${strategyName}_cash`,
          label: `${strategyName} Caixa`,
          color: getStrategyColor(strategyName),
        })),
    [getStrategyColor, results, visibleStrategies]
  );

  return (
    <div>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={equityData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
            <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" tickFormatter={formatCurrency} />
            <Tooltip
              formatter={(value) => [formatCurrency(toNumber(value)), 'Caixa Disponível']}
              labelFormatter={(label) => label}
            />

            {Object.entries(results).map(([strategyName]) =>
              visibleStrategies.includes(strategyName) ? (
                <Line
                  key={`${strategyName}_cash`}
                  type="monotone"
                  dataKey={`${strategyName}_cash`}
                  stroke={getStrategyColor(strategyName)}
                  strokeWidth={activeSeriesId === `${strategyName}_cash` ? 4 : 2}
                  opacity={activeSeriesId === null || activeSeriesId === `${strategyName}_cash` ? 1 : 0.18}
                  strokeDasharray="2 2"
                  dot={false}
                  name={`${strategyName} Caixa`}
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
        onToggle={(seriesId) => setActiveSeriesId((current) => (current === seriesId ? null : seriesId))}
      />
    </div>
  );
}
