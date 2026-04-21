import InteractiveSeriesChart, {
  InteractiveSeriesDefinition,
} from '../charts/InteractiveSeriesChart';
import { formatCurrency, formatDate } from '../../lib/utils';

type UnknownRecord = Record<string, unknown>;

interface Wege3ComparisonChartProps {
  chart: UnknownRecord;
}

type ChartPoint = Record<string, string | number | null | undefined>;

const SERIES_COLORS = [
  '#2563eb',
  '#f59e0b',
  '#22c55e',
  '#8b5cf6',
  '#ef4444',
  '#06b6d4',
];

const SPECIAL_SERIES_COLORS: Record<string, string> = {
  selic_cash: '#10b981',
  buy_hold_wege3: '#38bdf8',
};

function getRecordArray(payload: UnknownRecord, key: string): UnknownRecord[] {
  const value = payload[key];
  return Array.isArray(value)
    ? value.filter((item): item is UnknownRecord => Boolean(item) && typeof item === 'object')
    : [];
}

function toChartPoints(points: UnknownRecord[]): ChartPoint[] {
  return points.map((point) => point as ChartPoint);
}

function getString(payload: UnknownRecord, key: string): string {
  const value = payload[key];
  return typeof value === 'string' ? value : '';
}

function buildSeries(series: UnknownRecord[]): InteractiveSeriesDefinition[] {
  return series.reduce<InteractiveSeriesDefinition[]>((accumulator, item, index) => {
    const id = getString(item, 'id');
    const label = getString(item, 'label');
    if (!id || !label) {
      return accumulator;
    }

    accumulator.push({
      id,
      label,
      color: SPECIAL_SERIES_COLORS[id] ?? SERIES_COLORS[index % SERIES_COLORS.length],
      strokeWidth: id === 'buy_hold_wege3' ? 2.5 : undefined,
    });
    return accumulator;
  }, []);
}

export default function Wege3ComparisonChart({ chart }: Wege3ComparisonChartProps) {
  const rawSeries = getRecordArray(chart, 'series');
  const points = toChartPoints(getRecordArray(chart, 'points'));
  const referenceSeriesId = getString(chart, 'reference_series_id');
  const series = buildSeries(rawSeries);

  return (
    <InteractiveSeriesChart
      title="Progressao dos resultados"
      description="Evolucao do patrimonio de cada estrategia. A linha tracejada em verde e a referencia de caixa rendendo SELIC. Clique na legenda para destacar uma curva especifica."
      data={points}
      xKey="date"
      series={series}
      referenceSeriesId={referenceSeriesId}
      xTickFormatter={(value) => formatDate(String(value))}
      yTickFormatter={(value) => formatCurrency(value)}
      tooltipLabelFormatter={(value) => formatDate(String(value))}
      tooltipValueFormatter={(value) => formatCurrency(value)}
      emptyText="Sem dados suficientes para gerar a comparacao das estrategias WEGE3."
    />
  );
}
