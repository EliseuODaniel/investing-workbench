import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { EquityChartPanelProps } from './types';
import { formatCurrency, toNumber } from './utils';

export default function EquityChartPanel({
  results,
  benchmarks,
  visibleStrategies,
  visibleBenchmarks,
  equityData,
  getStrategyColor,
}: EquityChartPanelProps) {
  return (
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
          <Legend />

          {Object.entries(results).map(([strategyName]) =>
            visibleStrategies.includes(strategyName) ? (
              <Line
                key={strategyName}
                type="monotone"
                dataKey={strategyName}
                stroke={getStrategyColor(strategyName)}
                strokeWidth={2}
                dot={false}
                name={strategyName}
                connectNulls={false}
              />
            ) : null,
          )}

          {visibleBenchmarks.includes('Buy & Hold') && (
            <Line
              type="monotone"
              dataKey="Buy & Hold"
              stroke="#9333ea"
              strokeWidth={2}
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
                  stroke="#6b7280"
                  strokeWidth={2}
                  strokeDasharray="3 3"
                  dot={false}
                  name={name}
                  connectNulls={false}
                />
              ) : null,
            )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
