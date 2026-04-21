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
import { CashChartPanelProps } from './types';
import { formatCurrency, toNumber } from './utils';

export default function CashChartPanel({
  results,
  visibleStrategies,
  equityData,
  getStrategyColor,
}: CashChartPanelProps) {
  return (
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
          <Legend />

          {Object.entries(results).map(([strategyName]) =>
            visibleStrategies.includes(strategyName) ? (
              <Line
                key={`${strategyName}_cash`}
                type="monotone"
                dataKey={`${strategyName}_cash`}
                stroke={getStrategyColor(strategyName)}
                strokeWidth={2}
                strokeDasharray="2 2"
                dot={false}
                name={`${strategyName} Caixa`}
                connectNulls={false}
              />
            ) : null,
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
