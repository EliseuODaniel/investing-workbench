import { formatDate } from '../../lib/utils';

interface ChartDateRangeControlsProps {
  startDate: string;
  endDate: string;
  minDate: string;
  maxDate: string;
  startIndex: number;
  endIndex: number;
  maxIndex: number;
  onStartIndexChange: (value: number) => void;
  onEndIndexChange: (value: number) => void;
  onReset: () => void;
}

export default function ChartDateRangeControls({
  startDate,
  endDate,
  minDate,
  maxDate,
  startIndex,
  endIndex,
  maxIndex,
  onStartIndexChange,
  onEndIndexChange,
  onReset,
}: ChartDateRangeControlsProps) {
  const startPercent = maxIndex > 0 ? (startIndex / maxIndex) * 100 : 0;
  const endPercent = maxIndex > 0 ? (endIndex / maxIndex) * 100 : 100;

  return (
    <div className="mt-4 rounded-2xl border border-gray-200 bg-gray-50/80 px-4 py-4 dark:border-gray-800 dark:bg-gray-900/40">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">
            Filtro do gráfico
          </div>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
            A simulação continua usando o período completo. Aqui você escolhe só o recorte visual
            da curva para enxergar melhor uma fase específica. Quando o início muda, as curvas são
            recalibradas para começar do mesmo ponto.
          </p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-gray-400 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-200 dark:hover:border-gray-600"
        >
          Ver período completo
        </button>
      </div>

      <div className="mt-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3 text-sm">
          <div className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-100">
            <div className="text-[11px] uppercase tracking-[0.16em] text-blue-700 dark:text-blue-300">
              Início do recorte
            </div>
            <div className="mt-1 font-semibold">{formatDate(startDate)}</div>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-100">
            <div className="text-[11px] uppercase tracking-[0.16em] text-emerald-700 dark:text-emerald-300">
              Fim do recorte
            </div>
            <div className="mt-1 font-semibold">{formatDate(endDate)}</div>
          </div>
        </div>

        <div className="relative h-12">
          <div className="absolute inset-x-0 top-1/2 h-2 -translate-y-1/2 rounded-full bg-gray-200 dark:bg-gray-800" />
          <div
            className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-blue-500 dark:bg-blue-400"
            style={{
              left: `${startPercent}%`,
              width: `${Math.max(endPercent - startPercent, 1)}%`,
            }}
          />
          <input
            aria-label="Início do intervalo do gráfico"
            className="range-slider"
            type="range"
            min={0}
            max={maxIndex}
            step={1}
            value={startIndex}
            onChange={(event) => onStartIndexChange(Number(event.target.value))}
          />
          <input
            aria-label="Fim do intervalo do gráfico"
            className="range-slider"
            type="range"
            min={0}
            max={maxIndex}
            step={1}
            value={endIndex}
            onChange={(event) => onEndIndexChange(Number(event.target.value))}
          />
        </div>

        <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{formatDate(minDate)}</span>
          <span>{formatDate(maxDate)}</span>
        </div>
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Arraste as extremidades da barra para reduzir ou ampliar o trecho exibido.
        </div>
      </div>

      <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
        Exibindo de <strong>{formatDate(startDate)}</strong> até <strong>{formatDate(endDate)}</strong>.
        Histórico disponível de <strong>{formatDate(minDate)}</strong> até{' '}
        <strong>{formatDate(maxDate)}</strong>.
      </div>
    </div>
  );
}
