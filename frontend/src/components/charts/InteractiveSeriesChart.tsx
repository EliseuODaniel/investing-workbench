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
import SeriesLegendButtons from './SeriesLegendButtons';

export interface InteractiveSeriesDefinition {
  id: string;
  label: string;
  color: string;
  dashed?: boolean;
  strokeWidth?: number;
}

interface InteractiveSeriesChartProps {
  title: string;
  description: string;
  data: Array<Record<string, string | number | null | undefined>>;
  xKey: string;
  series: InteractiveSeriesDefinition[];
  xTickFormatter?: (value: string | number) => string;
  yTickFormatter?: (value: number) => string;
  tooltipLabelFormatter?: (value: string | number) => string;
  tooltipValueFormatter?: (value: number, series: InteractiveSeriesDefinition) => string;
  referenceSeriesId?: string | null;
  emptyText?: string;
  heightClassName?: string;
}

function toNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

export default function InteractiveSeriesChart({
  title,
  description,
  data,
  xKey,
  series,
  xTickFormatter,
  yTickFormatter,
  tooltipLabelFormatter,
  tooltipValueFormatter,
  referenceSeriesId = null,
  emptyText = 'Sem dados suficientes para gerar o gráfico.',
  heightClassName = 'h-[24rem]',
}: InteractiveSeriesChartProps) {
  const [activeSeriesId, setActiveSeriesId] = useState<string | null>(null);

  const visibleSeries = useMemo(
    () => series.filter((item) => data.some((row) => toNumber(row[item.id]) !== null)),
    [data, series]
  );

  if (data.length === 0 || visibleSeries.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
        {emptyText}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-200 px-4 py-4 dark:border-gray-800">
      <div className="flex flex-col gap-2">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{title}</h4>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>

      <div className={`mt-4 ${heightClassName}`}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 12 }}
              stroke="#94a3b8"
              minTickGap={24}
              tickFormatter={(value) =>
                xTickFormatter ? xTickFormatter(value as string | number) : String(value)
              }
            />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="#94a3b8"
              width={92}
              tickFormatter={(value) =>
                yTickFormatter ? yTickFormatter(Number(value)) : String(value)
              }
            />
            <Tooltip
              labelFormatter={(label) =>
                tooltipLabelFormatter
                  ? tooltipLabelFormatter(label as string | number)
                  : String(label)
              }
              formatter={(value: unknown, name: string | number | undefined) => {
                const parsed = toNumber(value);
                const definition = visibleSeries.find((item) => item.id === String(name));
                const label = definition?.label ?? String(name ?? '');
                const renderedValue =
                  parsed === null
                    ? 'n/a'
                    : tooltipValueFormatter && definition
                      ? tooltipValueFormatter(parsed, definition)
                      : String(parsed);
                return [renderedValue, label];
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
            {visibleSeries.map((item) => {
              const isActive = activeSeriesId === null || activeSeriesId === item.id;
              const isFocused = activeSeriesId === item.id;
              return (
                <Line
                  key={item.id}
                  type="monotone"
                  dataKey={item.id}
                  name={item.label}
                  stroke={item.color}
                  strokeWidth={
                    isFocused
                      ? 4
                      : item.strokeWidth ?? (item.id === referenceSeriesId ? 2.5 : 2)
                  }
                  strokeDasharray={item.dashed || item.id === referenceSeriesId ? '6 6' : undefined}
                  dot={false}
                  connectNulls={false}
                  opacity={isActive ? 1 : 0.18}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <SeriesLegendButtons
        items={visibleSeries.map((item) => ({
          id: item.id,
          label: item.label,
          color: item.color,
        }))}
        activeSeriesId={activeSeriesId}
        onToggle={(seriesId) =>
          setActiveSeriesId((current) => (current === seriesId ? null : seriesId))
        }
      />
    </div>
  );
}
