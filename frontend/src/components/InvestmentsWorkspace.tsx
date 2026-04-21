import { useMemo } from 'react';
import { BarChart3, Coins, Globe2, Landmark, ShieldCheck, Wallet } from 'lucide-react';
import InteractiveSeriesChart from './charts/InteractiveSeriesChart';
import { useInvestmentsComparison } from '../hooks/useInvestmentsComparison';
import { formatCurrency, formatDate, formatPercent } from '../lib/utils';

interface InvestmentsWorkspaceProps {
  onError: (message: string | null) => void;
}

function objectiveIcon(presetId: string) {
  if (presetId === 'income_focus') {
    return <Coins className="h-4 w-4" />;
  }
  if (presetId === 'global_b3') {
    return <Globe2 className="h-4 w-4" />;
  }
  if (presetId === 'balanced_b3') {
    return <ShieldCheck className="h-4 w-4" />;
  }
  return <Wallet className="h-4 w-4" />;
}

export default function InvestmentsWorkspace({ onError }: InvestmentsWorkspaceProps) {
  const {
    catalog,
    comparison,
    request,
    selectedPreset,
    selectedPresetId,
    isLoadingCatalog,
    isComparing,
    applyPreset,
    updateRequest,
    toggleAsset,
    toggleBenchmark,
    compare,
  } = useInvestmentsComparison(onError);

  const instrumentsByCategory = useMemo(() => {
    if (!catalog) {
      return [];
    }
    return catalog.categories.map((category) => ({
      ...category,
      instruments: catalog.instruments.filter((item) => item.category_id === category.category_id),
    }));
  }, [catalog]);

  const topPerformer = comparison?.highlights.best_final_value;
  const mostDefensive = comparison?.highlights.most_defensive;
  const investedTotal = useMemo(() => {
    const endDate = request.end_date || comparison?.request.end_date;
    const startDate = request.start_date || comparison?.request.start_date;
    if (!startDate) {
      return request.initial_capital ?? 0;
    }
    const start = new Date(startDate);
    const end = new Date(endDate || new Date().toISOString().slice(0, 10));
    const months =
      Math.max(
        0,
        (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth())
      ) || 0;
    return (request.initial_capital ?? 0) + months * (request.monthly_contribution ?? 0);
  }, [comparison?.request.end_date, comparison?.request.start_date, request.end_date, request.initial_capital, request.monthly_contribution, request.start_date]);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <div className="space-y-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-300">
              Novo fluxo principal
            </div>
            <h3 className="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">
              Compare investimentos da B3 do jeito que uma pessoa comum pensa.
            </h3>
            <p className="mt-3 text-sm leading-7 text-gray-600 dark:text-gray-300">
              Em vez de começar por modulo tecnico, este comparador parte da pergunta
              natural: <strong>“se eu tivesse colocado meu dinheiro aqui, quanto ele teria virado?”</strong>
              A comparacao usa o mesmo capital inicial e os mesmos aportes para todas as alternativas.
            </p>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <Landmark className="h-4 w-4 text-blue-600 dark:text-blue-300" />
              1. Escolha um objetivo simples
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {catalog?.presets.map((preset) => {
                const active = preset.preset_id === selectedPresetId;
                return (
                  <button
                    key={preset.preset_id}
                    type="button"
                    onClick={() => applyPreset(preset.preset_id)}
                    className={`rounded-2xl border p-4 text-left transition ${
                      active
                        ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950/30'
                        : 'border-gray-200 bg-gray-50 hover:border-gray-300 dark:border-gray-800 dark:bg-gray-950/40 dark:hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {objectiveIcon(preset.preset_id)}
                      {preset.label}
                    </div>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                      {preset.description}
                    </p>
                    <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                      {preset.goal_label}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <Wallet className="h-4 w-4 text-blue-600 dark:text-blue-300" />
              2. Defina o dinheiro e o periodo
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm">
                <span className="font-medium text-gray-700 dark:text-gray-200">Capital inicial</span>
                <input
                  className="input-field"
                  type="number"
                  min="1000"
                  step="100"
                  value={request.initial_capital ?? 10000}
                  onChange={(event) =>
                    updateRequest('initial_capital', Number(event.target.value) || 0)
                  }
                />
              </label>
              <label className="space-y-2 text-sm">
                <span className="font-medium text-gray-700 dark:text-gray-200">Aporte mensal</span>
                <input
                  className="input-field"
                  type="number"
                  min="0"
                  step="100"
                  value={request.monthly_contribution ?? 0}
                  onChange={(event) =>
                    updateRequest('monthly_contribution', Number(event.target.value) || 0)
                  }
                />
              </label>
              <label className="space-y-2 text-sm">
                <span className="font-medium text-gray-700 dark:text-gray-200">Data inicial</span>
                <input
                  className="input-field"
                  type="date"
                  value={request.start_date ?? '2021-01-01'}
                  onChange={(event) => updateRequest('start_date', event.target.value)}
                />
              </label>
              <label className="space-y-2 text-sm">
                <span className="font-medium text-gray-700 dark:text-gray-200">Data final</span>
                <input
                  className="input-field"
                  type="date"
                  value={request.end_date ?? ''}
                  onChange={(event) => updateRequest('end_date', event.target.value)}
                />
              </label>
            </div>
            <div className="mt-4 rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:bg-gray-800/70 dark:text-gray-300">
              Este comparador considera o mesmo fluxo de aportes em todas as alternativas.
              No recorte atual, o valor investido seria aproximadamente{' '}
              <strong>{formatCurrency(investedTotal)}</strong>.
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <BarChart3 className="h-4 w-4 text-blue-600 dark:text-blue-300" />
              3. Monte a comparacao
            </div>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Selecione o que voce quer colocar lado a lado. O comparador ja traz listas
              prontas, mas voce pode trocar ativos e benchmarks.
            </p>

            <div className="mt-5 space-y-5">
              {instrumentsByCategory.map((category) => (
                <div key={category.category_id}>
                  <div className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {category.label}
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {category.instruments.map((instrument) => {
                      const checked = (request.asset_ids ?? []).includes(instrument.instrument_id);
                      return (
                        <label
                          key={instrument.instrument_id}
                          className={`flex cursor-pointer gap-3 rounded-2xl border p-4 transition ${
                            checked
                              ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950/30'
                              : 'border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950/40'
                          }`}
                        >
                          <input
                            className="mt-1"
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleAsset(instrument.instrument_id)}
                          />
                          <div>
                            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                              {instrument.label}
                              <span className="ml-2 text-xs font-normal text-gray-500 dark:text-gray-400">
                                {instrument.risk_label}
                              </span>
                            </div>
                            <div className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                              {instrument.description}
                            </div>
                            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                              {instrument.rationale}
                            </div>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 border-t border-gray-200 pt-5 dark:border-gray-800">
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Benchmarks sempre visiveis
              </div>
              <div className="mt-3 flex flex-wrap gap-3">
                {catalog?.benchmark_options.map((benchmark) => {
                  const checked = (request.benchmark_ids ?? []).includes(benchmark.benchmark_id);
                  return (
                    <button
                      key={benchmark.benchmark_id}
                      type="button"
                      onClick={() => toggleBenchmark(benchmark.benchmark_id)}
                      className={`rounded-full border px-4 py-2 text-sm transition ${
                        checked
                          ? 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200'
                          : 'border-gray-200 bg-white text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300'
                      }`}
                    >
                      {benchmark.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => void compare()}
                disabled={isLoadingCatalog || isComparing || (request.asset_ids ?? []).length === 0}
                className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isComparing ? 'Comparando...' : 'Comparar investimentos'}
              </button>
              {selectedPreset ? (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Sugestao ativa: <strong>{selectedPreset.label}</strong>
                </div>
              ) : null}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Metodologia em linguagem simples
            </div>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
              {catalog?.notes.map((note) => <li key={note}>- {note}</li>)}
            </ul>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Resultado didatico
        </div>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
          O objetivo aqui nao e adivinhar o futuro. E mostrar, com um fluxo de aportes
          consistente, qual alternativa teria rendido mais, sofrido menos ou ficado no meio do caminho.
        </p>

        {!comparison ? (
          <div className="mt-5 rounded-2xl border border-dashed border-gray-300 px-4 py-10 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
            {isLoadingCatalog
              ? 'Carregando catalogo de investimentos...'
              : 'Escolha um objetivo, confirme os ativos e rode a comparacao.'}
          </div>
        ) : (
          <div className="mt-6 space-y-6">
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
                  Melhor valor final
                </div>
                <div className="mt-2 text-xl font-semibold text-emerald-900 dark:text-emerald-100">
                  {topPerformer?.label ?? 'n/a'}
                </div>
                <div className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
                  {topPerformer ? formatCurrency(topPerformer.final_value) : 'n/a'}
                </div>
              </div>

              <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700 dark:text-blue-300">
                  Mais defensivo
                </div>
                <div className="mt-2 text-xl font-semibold text-blue-900 dark:text-blue-100">
                  {mostDefensive?.label ?? 'n/a'}
                </div>
                <div className="mt-1 text-sm text-blue-800 dark:text-blue-200">
                  drawdown maximo{' '}
                  {mostDefensive ? formatPercent(mostDefensive.max_drawdown) : 'n/a'}
                </div>
              </div>

              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700 dark:text-amber-300">
                  Valeu correr risco?
                </div>
                <div className="mt-2 text-xl font-semibold text-amber-900 dark:text-amber-100">
                  {comparison.highlights.beats_selic_count ?? 0} / {comparison.results.length}
                </div>
                <div className="mt-1 text-sm text-amber-800 dark:text-amber-200">
                  ativos terminaram acima da SELIC
                </div>
              </div>
            </div>

            <InteractiveSeriesChart
              title="Evolucao do patrimonio"
              description="Cada linha mostra quanto o mesmo fluxo de dinheiro teria virado em cada alternativa. A linha tracejada representa a SELIC."
              data={comparison.chart.points}
              xKey="date"
              series={comparison.chart.series}
              referenceSeriesId={comparison.chart.reference_series_id}
              xTickFormatter={(value) => formatDate(String(value))}
              yTickFormatter={(value) => formatCurrency(value)}
              tooltipLabelFormatter={(value) => formatDate(String(value))}
              tooltipValueFormatter={(value) => formatCurrency(value)}
              heightClassName="h-[28rem]"
            />

            <div className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
              <div className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
                    <thead className="bg-gray-50 dark:bg-gray-900/50">
                      <tr className="text-left text-xs uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
                        <th className="px-4 py-3">Investimento</th>
                        <th className="px-4 py-3">Classe</th>
                        <th className="px-4 py-3">Valor final</th>
                        <th className="px-4 py-3">Lucro</th>
                        <th className="px-4 py-3">CAGR</th>
                        <th className="px-4 py-3">DD max</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                      {comparison.results.map((row) => (
                        <tr key={row.instrument_id}>
                          <td className="px-4 py-4 align-top">
                            <div className="font-semibold text-gray-900 dark:text-gray-100">
                              {row.label}
                            </div>
                            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                              {row.description}
                            </div>
                          </td>
                          <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                            {row.category_label}
                          </td>
                          <td className="px-4 py-4 font-semibold text-gray-900 dark:text-gray-100">
                            {formatCurrency(row.final_value)}
                          </td>
                          <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                            {formatCurrency(row.net_profit)}
                          </td>
                          <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                            {formatPercent(row.cagr)}
                          </td>
                          <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                            {formatPercent(row.max_drawdown)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
                  <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    Leituras rapidas
                  </div>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
                    {comparison.highlights.insights?.map((insight) => (
                      <li key={insight}>- {insight}</li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
                  <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    Resumo por familia
                  </div>
                  <div className="mt-3 space-y-3">
                    {comparison.class_summary.map((row) => (
                      <div
                        key={row.category_label}
                        className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-900/60"
                      >
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                          {row.category_label}
                        </div>
                        <div className="mt-1 text-gray-600 dark:text-gray-300">
                          media final {formatCurrency(row.average_final_value)}
                        </div>
                        <div className="text-gray-500 dark:text-gray-400">
                          lider: {row.leader_label}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
                  <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    Benchmarks usados
                  </div>
                  <div className="mt-3 space-y-3">
                    {comparison.benchmarks.map((benchmark) => (
                      <div key={benchmark.benchmark_id} className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-900/60">
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                          {benchmark.label}
                        </div>
                        <div className="mt-1 text-gray-600 dark:text-gray-300">
                          final {formatCurrency(benchmark.final_value)}
                        </div>
                        <div className="text-gray-500 dark:text-gray-400">
                          CAGR {formatPercent(benchmark.cagr)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {comparison.warnings.length > 0 ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">
                <div className="font-semibold">Atencoes sobre o recorte</div>
                <ul className="mt-2 space-y-1">
                  {comparison.warnings.map((warning) => <li key={warning}>- {warning}</li>)}
                </ul>
              </div>
            ) : null}

            <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-4 text-sm text-gray-600 dark:border-gray-800 dark:bg-gray-900/50 dark:text-gray-300">
              <div className="font-semibold text-gray-900 dark:text-gray-100">
                Fontes e cobertura
              </div>
              <div className="mt-2 space-y-1">
                {catalog?.sources.map((source) => (
                  <div key={source.url}>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-700 hover:underline dark:text-blue-300"
                    >
                      {source.label}
                    </a>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
