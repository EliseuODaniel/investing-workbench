import { useMemo } from 'react';
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import SeriesLegendButtons from '../charts/SeriesLegendButtons';
import { useSeriesLegendState } from '../../hooks/useSeriesLegendState';
import { TradesChartPanelProps } from './types';
import { formatCurrency } from './utils';

export default function TradesChartPanel({
  results,
  visibleStrategies,
  tradesData,
  getStrategyColor,
}: TradesChartPanelProps) {
  const legendItems = useMemo(
    () =>
      Object.keys(results)
        .filter((strategyName) => visibleStrategies.includes(strategyName))
        .map((strategyName) => ({
          id: strategyName,
          label: strategyName,
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
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="timestamp"
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              type="category"
              domain={['dataMin', 'dataMax']}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              tickFormatter={formatCurrency}
              domain={['dataMin - 1000', 'dataMax + 1000']}
            />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              content={({ active, payload }) => {
                if (!active || !payload || payload.length === 0) {
                  return null;
                }

                const data = payload[0].payload as (typeof tradesData)[number];
                return (
                  <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                    <p className="font-semibold">{data.strategy}</p>
                    <p>{data.timestamp.toLocaleDateString('pt-BR')}</p>
                    <p>Preço: {formatCurrency(data.price)}</p>
                    <p>Ação: {data.action}</p>
                    <p>PnL: {formatCurrency(data.pnl)}</p>
                    <p>Layer: {data.layer}</p>
                  </div>
                );
              }}
            />

            {Object.entries(results).map(([strategyName]) =>
              visibleStrategies.includes(strategyName) ? (
                <Scatter
                  key={strategyName}
                  name={strategyName}
                  data={tradesData.filter((trade) => trade.strategy === strategyName)}
                  hide={hiddenSeriesSet.has(strategyName)}
                  fill={getStrategyColor(strategyName)}
                  fillOpacity={activeSeriesId === null || activeSeriesId === strategyName ? 1 : 0.18}
                />
              ) : null
            )}
          </ScatterChart>
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
