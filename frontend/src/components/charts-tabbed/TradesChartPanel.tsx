import {
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { TradesChartPanelProps } from './types';
import { formatCurrency } from './utils';

export default function TradesChartPanel({
  results,
  visibleStrategies,
  tradesData,
  getStrategyColor,
}: TradesChartPanelProps) {
  return (
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
          <Legend />

          {Object.entries(results).map(([strategyName]) =>
            visibleStrategies.includes(strategyName) ? (
              <Scatter
                key={strategyName}
                name={strategyName}
                data={tradesData.filter((trade) => trade.strategy === strategyName)}
                fill={getStrategyColor(strategyName)}
              />
            ) : null,
          )}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
