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
import { formatCurrency, formatDate } from '../../lib/utils';

type UnknownRecord = Record<string, unknown>;

interface Wege3ComparisonChartProps {
  chart: UnknownRecord;
}

const SERIES_COLORS = [
  '#2563eb',
  '#f59e0b',
  '#22c55e',
  '#8b5cf6',
  '#ef4444',
  '#06b6d4',
];

function getRecordArray(payload: UnknownRecord, key: string): UnknownRecord[] {
  const value = payload[key];
  return Array.isArray(value)
    ? value.filter((item): item is UnknownRecord => Boolean(item) && typeof item === 'object')
    : [];
}

function getString(payload: UnknownRecord, key: string): string {
  const value = payload[key];
  return typeof value === 'string' ? value : '';
}

function toNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function buildSeriesColorMap(series: UnknownRecord[]): Record<string, string> {
  return series.reduce<Record<string, string>>((accumulator, item, index) => {
    const id = getString(item, 'id');
    if (!id) {
      return accumulator;
    }
    accumulator[id] = id === 'selic_cash' ? '#10b981' : SERIES_COLORS[index % SERIES_COLORS.length];
    return accumulator;
  }, {});
}

export default function Wege3ComparisonChart({ chart }: Wege3ComparisonChartProps) {
  const series = getRecordArray(chart, 'series');
  const points = getRecordArray(chart, 'points');
  const referenceSeriesId = getString(chart, 'reference_series_id');
  const colorMap = buildSeriesColorMap(series);

  if (series.length === 0 || points.length === 0) {
    return null;
  }

  return (
    <div className="card">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Progressao dos resultados
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Evolucao do patrimonio de cada estrategia. A linha tracejada em verde e a referencia
            de caixa rendendo SELIC.
          </p>
        </div>
      </div>

      <div className="mt-4 h-[24rem]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              stroke="#94a3b8"
              minTickGap={32}
              tickFormatter={(value) => formatDate(String(value))}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="#94a3b8"
              tickFormatter={(value) => formatCurrency(Number(value))}
              width={88}
            />
            <Tooltip
              labelFormatter={(label) => formatDate(String(label))}
              formatter={(value: unknown, name: string | number | undefined) => {
                const parsed = toNumber(value);
                return [parsed === null ? 'n/a' : formatCurrency(parsed), String(name ?? '')];
              }}
              contentStyle={{
                backgroundColor: '#020617',
                border: '1px solid rgba(148, 163, 184, 0.25)',
                borderRadius: '0.75rem',
                color: '#e2e8f0',
              }}
              itemStyle={{ color: '#e2e8f0' }}
              labelStyle={{ color: '#cbd5e1' }}
            />
            <Legend />
            {series.map((item) => {
              const id = getString(item, 'id');
              const label = getString(item, 'label');
              if (!id || !label) {
                return null;
              }
              return (
                <Line
                  key={id}
                  type="monotone"
                  dataKey={id}
                  name={label}
                  stroke={colorMap[id]}
                  strokeWidth={id === referenceSeriesId ? 2.5 : 2}
                  strokeDasharray={id === referenceSeriesId ? '6 6' : undefined}
                  dot={false}
                  connectNulls={false}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
