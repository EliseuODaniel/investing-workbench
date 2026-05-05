import InteractiveSeriesChart from '../charts/InteractiveSeriesChart';
import { formatCurrency, formatDate } from '../../lib/utils';
import type { InvestmentComparisonChartPayload } from '../../types/api';

export type InvestmentResultChartMode = 'nominal' | 'real';

interface InvestmentResultChartPanelProps {
  chart: InvestmentComparisonChartPayload;
  realChart: InvestmentComparisonChartPayload;
  chartMode: InvestmentResultChartMode;
  onChartModeChange: (mode: InvestmentResultChartMode) => void;
}

export default function InvestmentResultChartPanel({
  chart,
  realChart,
  chartMode,
  onChartModeChange,
}: InvestmentResultChartPanelProps) {
  const currentChart = chartMode === 'real' ? realChart : chart;

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Visualizacao do patrimonio em valores nominais ou ajustados pelo IPCA.
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onChartModeChange('nominal')}
            className={`rounded-full border px-4 py-2 text-sm transition ${
              chartMode === 'nominal'
                ? 'border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200'
                : 'border-gray-200 bg-white text-gray-600 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300'
            }`}
          >
            Visao nominal
          </button>
          <button
            type="button"
            onClick={() => onChartModeChange('real')}
            className={`rounded-full border px-4 py-2 text-sm transition ${
              chartMode === 'real'
                ? 'border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200'
                : 'border-gray-200 bg-white text-gray-600 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300'
            }`}
          >
            Ajustado pelo IPCA
          </button>
        </div>
      </div>

      <InteractiveSeriesChart
        title={
          chartMode === 'real'
            ? 'Evolucao do patrimonio em poder de compra'
            : 'Evolucao do patrimonio'
        }
        description={
          chartMode === 'real'
            ? 'Cada linha mostra quanto o mesmo fluxo de dinheiro teria valido em poder de compra do inicio do periodo.'
            : 'Cada linha mostra quanto o mesmo fluxo de dinheiro teria virado em cada alternativa. A linha tracejada representa a SELIC.'
        }
        data={currentChart.points}
        xKey="date"
        series={currentChart.series}
        referenceSeriesId={currentChart.reference_series_id}
        xTickFormatter={(value) => formatDate(String(value))}
        yTickFormatter={(value) => formatCurrency(value)}
        tooltipLabelFormatter={(value) => formatDate(String(value))}
        tooltipValueFormatter={(value) => formatCurrency(value)}
        heightClassName="h-[28rem]"
        enableDateFilter
        rebaseOnDateFilter
      />
    </>
  );
}
