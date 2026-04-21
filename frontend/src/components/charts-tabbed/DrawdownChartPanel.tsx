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
import { DrawdownChartPanelProps } from './types';
import { toNumber } from './utils';

export default function DrawdownChartPanel({
  results,
  visibleStrategies,
  drawdownData,
}: DrawdownChartPanelProps) {
  return (
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
          <Legend />

          {Object.entries(results).map(([strategyName]) =>
            visibleStrategies.includes(strategyName) ? (
              <Line
                key={`${strategyName}_drawdown`}
                type="monotone"
                dataKey={`${strategyName}_drawdown`}
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                name={`${strategyName} DD`}
                fill="#ef4444"
                fillOpacity={0.1}
              />
            ) : null,
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
