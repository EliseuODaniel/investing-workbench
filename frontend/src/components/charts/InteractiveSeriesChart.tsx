import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  useYAxisScale,
  XAxis,
  YAxis,
} from 'recharts';
import SeriesLegendButtons from './SeriesLegendButtons';
import ChartDateRangeControls from './ChartDateRangeControls';
import { useChartDateRange } from '../../hooks/useChartDateRange';
import { useSeriesLegendState } from '../../hooks/useSeriesLegendState';
import { rebaseLineSeriesData } from '../../lib/chartSeries';
import {
  pickNearestTooltipPayload,
  type ChartTooltipEntry,
} from '../../lib/chartTooltip';

export interface InteractiveSeriesDefinition {
  id: string;
  label: string;
  color: string;
  dashed?: boolean;
  strokeWidth?: number;
}

interface InteractiveSeriesTooltipContentProps {
  active?: boolean;
  label?: string | number;
  payload?: readonly ChartTooltipEntry[];
  seriesById: Map<string, InteractiveSeriesDefinition>;
  labelFormatter?: (value: string | number) => string;
  valueFormatter?: (value: number, series: InteractiveSeriesDefinition) => string;
}

interface NearestInteractiveSeriesTooltipContentProps
  extends InteractiveSeriesTooltipContentProps {
  coordinateY?: number;
}

function NearestInteractiveSeriesTooltipContent({
  active = false,
  coordinateY,
  payload = [],
  ...props
}: NearestInteractiveSeriesTooltipContentProps) {
  const yScale = useYAxisScale();
  const filteredPayload = useMemo(
    () => pickNearestTooltipPayload(payload, coordinateY, yScale),
    [coordinateY, payload, yScale]
  );

  return (
    <InteractiveSeriesTooltipContent
      active={active && filteredPayload.length > 0}
      payload={filteredPayload}
      {...props}
    />
  );
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
  enableDateFilter?: boolean;
  rebaseOnDateFilter?: boolean;
}

function toNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

export function InteractiveSeriesTooltipContent({
  active = false,
  label,
  payload = [],
  seriesById,
  labelFormatter,
  valueFormatter,
}: InteractiveSeriesTooltipContentProps) {
  if (!active || payload.length === 0) {
    return null;
  }

  const renderedLabel =
    label === undefined
      ? ''
      : labelFormatter
        ? labelFormatter(label)
        : String(label);

  return (
    <div className="rounded-xl border border-slate-700/40 bg-slate-950/95 px-4 py-3 shadow-xl">
      <div className="text-sm font-medium text-slate-300">{renderedLabel}</div>
      <div className="mt-3 space-y-2">
        {payload.map((entry) => {
          const seriesId = String(entry.dataKey ?? entry.name ?? '');
          const seriesDefinition = seriesById.get(seriesId);
          const parsedValue = toNumber(entry.value);
          const renderedValue =
            parsedValue === null
              ? 'n/a'
              : valueFormatter && seriesDefinition
                ? valueFormatter(parsedValue, seriesDefinition)
                : String(parsedValue);
          const renderedSeriesLabel = seriesDefinition?.label ?? String(entry.name ?? seriesId);
          const seriesColor = entry.color ?? seriesDefinition?.color ?? '#e2e8f0';

          return (
            <div
              key={seriesId}
              data-testid={`tooltip-row-${seriesId}`}
              className="flex items-start justify-between gap-4 text-sm"
              style={{ color: seriesColor }}
            >
              <div className="flex min-w-0 items-center gap-2">
                <span
                  aria-hidden="true"
                  className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: seriesColor }}
                />
                <span className="truncate">{renderedSeriesLabel}</span>
              </div>
              <span className="shrink-0 font-medium">{renderedValue}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
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
  enableDateFilter = false,
  rebaseOnDateFilter = false,
}: InteractiveSeriesChartProps) {
  const dateRange = useChartDateRange(data, xKey);
  const filteredChartData = enableDateFilter ? dateRange.filteredData : data;
  const shouldRebase =
    rebaseOnDateFilter &&
    enableDateFilter &&
    Boolean(dateRange.minDate) &&
    dateRange.startDate !== dateRange.minDate;
  const chartData = useMemo(() => {
    if (!shouldRebase) {
      return filteredChartData;
    }
    return rebaseLineSeriesData(
      filteredChartData,
      series.map((item) => item.id),
      referenceSeriesId
    );
  }, [filteredChartData, referenceSeriesId, series, shouldRebase]);

  const availableSeries = useMemo(
    () => series.filter((item) => chartData.some((row) => toNumber(row[item.id]) !== null)),
    [chartData, series]
  );
  const { activeSeriesId, hiddenSeriesIds, toggleSeries } = useSeriesLegendState(
    availableSeries.map((item) => item.id)
  );
  const hiddenSeriesSet = useMemo(() => new Set(hiddenSeriesIds), [hiddenSeriesIds]);
  const seriesById = useMemo(
    () => new Map(availableSeries.map((item) => [item.id, item])),
    [availableSeries]
  );
  const visibleSeries = useMemo(
    () => availableSeries.filter((item) => !hiddenSeriesSet.has(item.id)),
    [availableSeries, hiddenSeriesSet]
  );

  if (chartData.length === 0 || availableSeries.length === 0) {
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
          <LineChart data={chartData}>
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
              content={({ active, coordinate, payload, label }) => {
                return (
                  <NearestInteractiveSeriesTooltipContent
                    active={active}
                    coordinateY={coordinate?.y}
                    payload={(payload as readonly ChartTooltipEntry[] | undefined) ?? []}
                    label={label as string | number | undefined}
                    seriesById={seriesById}
                    labelFormatter={tooltipLabelFormatter}
                    valueFormatter={tooltipValueFormatter}
                  />
                );
              }}
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

      {visibleSeries.length === 0 ? (
        <div className="mt-4 rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
          Todas as curvas foram ocultadas. Clique na legenda para trazer alguma de volta ao gráfico.
        </div>
      ) : null}

      {enableDateFilter && dateRange.hasDateRange ? (
        <ChartDateRangeControls
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          minDate={dateRange.minDate ?? dateRange.startDate}
          maxDate={dateRange.maxDate ?? dateRange.endDate}
          startIndex={dateRange.startIndex}
          endIndex={dateRange.endIndex}
          maxIndex={dateRange.maxIndex}
          onStartIndexChange={dateRange.setStartIndex}
          onEndIndexChange={dateRange.setEndIndex}
          onReset={dateRange.resetRange}
        />
      ) : null}

      <SeriesLegendButtons
        items={availableSeries.map((item) => ({
          id: item.id,
          label: item.label,
          color: item.color,
        }))}
        activeSeriesId={activeSeriesId}
        hiddenSeriesIds={hiddenSeriesIds}
        onToggle={toggleSeries}
      />
    </div>
  );
}
