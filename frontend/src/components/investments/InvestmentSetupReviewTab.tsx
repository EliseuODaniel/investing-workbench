import { BarChart3, Save, Trash2, Wallet } from 'lucide-react';
import type {
  InvestmentBenchmarkOptionPayload,
  InvestmentCustomPortfolioRequestPayload,
  InvestmentInstrumentPayload,
  InvestmentPresetPayload,
  InvestmentCompareRequestPayload,
  InvestmentCatalogPayload,
} from '../../types/api';
import { formatDate, formatNumber, formatPercent } from '../../lib/utils';
import InvestmentReviewStatsPanel from './InvestmentReviewStatsPanel';

interface InstrumentByCategory {
  category_id: string;
  label: string;
  instruments: InvestmentInstrumentPayload[];
}

interface InvestmentSetupReviewTabProps {
  entryMode: 'guided' | 'manual';
  catalog: InvestmentCatalogPayload | null;
  request: InvestmentCompareRequestPayload;
  selectedPreset: InvestmentPresetPayload | null;
  selectedAssets: InvestmentInstrumentPayload[];
  selectedBenchmarkOptions: InvestmentBenchmarkOptionPayload[];
  selectedSimpleAssetCount: number;
  selectedGuidedPortfolioCount: number;
  presetCustomized: boolean;
  isAssetEditorExpanded: boolean;
  isAssetEditorVisible: boolean;
  instrumentLookup: Map<string, InvestmentInstrumentPayload>;
  isCustomPortfolioEnabled: boolean;
  customPortfolioName: string;
  customPortfolioDescription: string;
  customPortfolioAssets: InvestmentInstrumentPayload[];
  customPortfolioWeights: Record<string, number>;
  customPortfolioPreview: {
    activeCount: number;
    totalWeight: number;
  };
  savedPortfolios: Array<InvestmentCustomPortfolioRequestPayload & {
    portfolio_id: string;
    created_at: string;
    updated_at: string;
  }>;
  instrumentsByCategory: InstrumentByCategory[];
  isLoadingCatalog: boolean;
  isComparing: boolean;
  compare: () => Promise<void> | void;
  onToggleAsset: (instrumentId: string) => void;
  onToggleAssetEditor: () => void;
  onToggleBenchmark: (benchmarkId: string) => void;
  onToggleCustomPortfolio: (enabled: boolean) => void;
  onChangeCustomPortfolioName: (value: string) => void;
  onChangeCustomPortfolioDescription: (value: string) => void;
  onUpdateCustomPortfolioWeight: (instrumentId: string, weight: number) => void;
  onSaveCustomPortfolio: () => void;
  onApplySavedPortfolio: (
    portfolio: InvestmentCustomPortfolioRequestPayload & {
      portfolio_id: string;
      created_at: string;
      updated_at: string;
    }
  ) => void;
  onDeleteSavedPortfolio: (portfolioId: string) => void;
}

export default function InvestmentSetupReviewTab({
  entryMode,
  catalog,
  request,
  selectedPreset,
  selectedAssets,
  selectedBenchmarkOptions,
  selectedSimpleAssetCount,
  selectedGuidedPortfolioCount,
  presetCustomized,
  isAssetEditorExpanded,
  isAssetEditorVisible,
  instrumentLookup,
  isCustomPortfolioEnabled,
  customPortfolioName,
  customPortfolioDescription,
  customPortfolioAssets,
  customPortfolioWeights,
  customPortfolioPreview,
  savedPortfolios,
  instrumentsByCategory,
  isLoadingCatalog,
  isComparing,
  compare,
  onToggleAsset,
  onToggleAssetEditor,
  onToggleBenchmark,
  onToggleCustomPortfolio,
  onChangeCustomPortfolioName,
  onChangeCustomPortfolioDescription,
  onUpdateCustomPortfolioWeight,
  onSaveCustomPortfolio,
  onApplySavedPortfolio,
  onDeleteSavedPortfolio,
}: InvestmentSetupReviewTabProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
          <BarChart3 className="h-4 w-4 text-blue-600 dark:text-blue-300" />
          3. Revise quem entra na comparacao
        </div>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
          {entryMode === 'guided'
            ? 'O estudo pronto já trouxe uma seleção inicial. Aqui você entende o que entrou e decide se quer manter o roteiro ou personalizar.'
            : 'Como você escolheu montar manualmente, este é o passo em que define exatamente quem será comparado.'}
        </p>

        <InvestmentReviewStatsPanel
          selectedAssetCount={selectedAssets.length}
          selectedBenchmarkCount={selectedBenchmarkOptions.length}
          selectedGuidedPortfolioCount={selectedGuidedPortfolioCount}
          entryMode={entryMode}
        />

        {entryMode === 'guided' && selectedPreset ? (
          <div className="mt-5 rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                  Estudo ativo: {selectedPreset.label}
                </div>
                <p className="mt-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
                  {selectedPreset.goal_label}
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-[11px]">
                <span className="rounded-full border border-blue-300 px-2 py-1 font-medium text-blue-800 dark:border-blue-700 dark:text-blue-200">
                  {selectedPreset.asset_ids.length} comparativos sugeridos
                </span>
                {selectedPreset.default_start_date ? (
                  <span className="rounded-full border border-blue-300 px-2 py-1 font-medium text-blue-800 dark:border-blue-700 dark:text-blue-200">
                    início sugerido {formatDate(selectedPreset.default_start_date)}
                  </span>
                ) : null}
                {presetCustomized ? (
                  <span className="rounded-full border border-amber-300 bg-white/80 px-2 py-1 font-medium text-amber-800 dark:border-amber-700 dark:bg-gray-950/40 dark:text-amber-200">
                    você personalizou o estudo
                  </span>
                ) : (
                  <span className="rounded-full border border-emerald-300 bg-white/80 px-2 py-1 font-medium text-emerald-800 dark:border-emerald-700 dark:bg-gray-950/40 dark:text-emerald-200">
                    estudo ainda no formato sugerido
                  </span>
                )}
              </div>
            </div>
          </div>
        ) : null}

        <div className="mt-5 rounded-2xl border border-gray-200 bg-gray-50/60 p-4 dark:border-gray-800 dark:bg-gray-950/30">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            O que está entrando agora na comparação
          </div>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Este bloco existe para tirar a ambiguidade: aqui você vê claramente quem está na disputa.
            Em estudo pronto, isso é uma revisão. Em modo manual, isso é a montagem da seleção.
          </p>

          {selectedAssets.length === 0 ? (
            <div className="mt-4 rounded-xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
              Nenhum comparativo foi selecionado ainda. Escolha um estudo pronto ou abra a
              personalização para montar a lista manualmente.
            </div>
          ) : (
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {selectedAssets.map((instrument) =>
                instrument.source_kind === 'model_portfolio' ? (
                  <div
                    key={instrument.instrument_id}
                    className="rounded-2xl border border-emerald-200 bg-white p-4 dark:border-emerald-900/50 dark:bg-gray-950/40"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {instrument.label}
                      </div>
                      <span className="rounded-full border border-emerald-300 px-2 py-1 text-[11px] font-medium text-emerald-800 dark:border-emerald-700 dark:text-emerald-200">
                        carteira guiada
                      </span>
                      {instrument.rebalance_frequency ? (
                        <span className="rounded-full border border-blue-300 px-2 py-1 text-[11px] font-medium text-blue-800 dark:border-blue-700 dark:text-blue-200">
                          rebalanceamento {instrument.rebalance_frequency}
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                      {instrument.description}
                    </p>
                    {instrument.implementation_note ? (
                      <div className="mt-3 rounded-xl bg-gray-50 px-3 py-3 text-sm text-gray-700 dark:bg-gray-900/70 dark:text-gray-200">
                        {instrument.implementation_note}
                      </div>
                    ) : null}
                    <ProductProfileSummary instrument={instrument} />
                    <div className="mt-3 flex flex-wrap gap-2">
                      {instrument.components.map((component) => {
                        const componentMeta = instrumentLookup.get(component.component_id);
                        return (
                          <span
                            key={`${instrument.instrument_id}-${component.component_id}`}
                            className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-900/60 dark:text-gray-200"
                          >
                            {componentMeta?.label ?? component.component_id}:{' '}
                            {formatPercent(component.weight)}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div
                    key={instrument.instrument_id}
                    className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-950/40"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {instrument.label}
                      </div>
                      <span className="rounded-full border border-gray-300 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300">
                        {instrument.category_label}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {instrument.risk_label} • {instrument.region_label}
                    </div>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                      {instrument.description}
                    </p>
                    <ProductProfileSummary instrument={instrument} />
                  </div>
                )
              )}
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            {selectedBenchmarkOptions.map((benchmark) => (
              <span
                key={benchmark.benchmark_id}
                className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-200"
              >
                benchmark: {benchmark.label}
              </span>
            ))}
          </div>
        </div>

        {entryMode === 'guided' ? (
          <div className="mt-5 rounded-2xl border border-dashed border-gray-300 p-4 dark:border-gray-700">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Quer manter o roteiro ou personalizar?
                </div>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                  Se o estudo já parece certo, você pode seguir direto. Se quiser trocar comparativos,
                  abra o editor abaixo.
                </p>
              </div>
              <button
                type="button"
                onClick={onToggleAssetEditor}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                  isAssetEditorExpanded
                    ? 'border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200'
                    : 'border-gray-300 bg-white text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300'
                }`}
              >
                {isAssetEditorExpanded ? 'Fechar personalização' : 'Quero personalizar os comparativos'}
              </button>
            </div>
          </div>
        ) : null}

        {isAssetEditorVisible ? (
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
                          onChange={() => onToggleAsset(instrument.instrument_id)}
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
                          <ProductProfileSummary instrument={instrument} compact />
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
          <Wallet className="h-4 w-4 text-blue-600 dark:text-blue-300" />
          4. Benchmarks e carteira pessoal
        </div>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
          Depois de definir quem entra na disputa, você decide quais referências deixam a leitura mais
          justa e se quer incluir uma carteira própria.
        </p>

        <div className="mt-5">
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Benchmarks sempre visíveis
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            {catalog?.benchmark_options.map((benchmark) => {
              const checked = (request.benchmark_ids ?? []).includes(benchmark.benchmark_id);
              return (
                <button
                  key={benchmark.benchmark_id}
                  type="button"
                  onClick={() => onToggleBenchmark(benchmark.benchmark_id)}
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

        <div className="mt-6 rounded-2xl border border-dashed border-gray-300 p-4 dark:border-gray-700">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Carteira pessoal (opcional)
              </div>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                Use os ativos simples já selecionados para comparar uma alocação sua contra ativos
                avulsos e carteiras guiadas.
              </p>
            </div>
                <button
                  type="button"
                  onClick={() => onToggleCustomPortfolio(!isCustomPortfolioEnabled)}
                  className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                    isCustomPortfolioEnabled
                      ? 'border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200'
                      : 'border-gray-300 bg-white text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300'
                  }`}
                >
              {isCustomPortfolioEnabled ? 'Carteira ativa' : 'Ativar carteira'}
            </button>
          </div>

          {isCustomPortfolioEnabled ? (
            customPortfolioAssets.length < 2 ? (
              <div className="mt-4 rounded-xl bg-gray-50 px-3 py-3 text-sm text-gray-600 dark:bg-gray-900/60 dark:text-gray-300">
                Selecione pelo menos dois ativos simples para montar uma carteira personalizada.
                Carteiras guiadas não entram aqui para evitar comparação circular.
              </div>
            ) : (
              <div className="mt-4 space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700 dark:text-gray-200">
                      Nome da carteira
                    </span>
                    <input
                      className="input-field"
                      value={customPortfolioName}
                      onChange={(event) => onChangeCustomPortfolioName(event.target.value)}
                    />
                  </label>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700 dark:text-gray-200">
                      Descrição curta
                    </span>
                    <input
                      className="input-field"
                      value={customPortfolioDescription}
                      onChange={(event) =>
                        onChangeCustomPortfolioDescription(event.target.value)
                      }
                    />
                  </label>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  {customPortfolioAssets.map((asset) => (
                    <label
                      key={asset.instrument_id}
                      className="rounded-2xl border border-gray-200 bg-gray-50 p-4 text-sm dark:border-gray-800 dark:bg-gray-950/40"
                    >
                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                        {asset.label}
                      </div>
                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {asset.category_label}
                      </div>
                      <div className="mt-3 flex items-center gap-3">
                        <input
                          className="input-field"
                          type="number"
                          min="0"
                          step="1"
                          value={customPortfolioWeights[asset.instrument_id] ?? 0}
                          onChange={(event) =>
                            onUpdateCustomPortfolioWeight(
                              asset.instrument_id,
                              Number(event.target.value) || 0
                            )
                          }
                        />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          peso bruto
                        </span>
                      </div>
                    </label>
                  ))}
                </div>

                <div className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900 dark:bg-emerald-950/20 dark:text-emerald-100">
                  {customPortfolioPreview.activeCount >= 2 ? (
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <span>
                        A carteira <strong>{customPortfolioName || 'Minha carteira'}</strong> vai
                        entrar como comparativo com{' '}
                        <strong>{customPortfolioPreview.activeCount} sleeves</strong>. O backend
                        normaliza os pesos automaticamente a partir do total informado de{' '}
                        <strong>{formatNumber(customPortfolioPreview.totalWeight, 0)}</strong>.
                      </span>
                      <button
                        type="button"
                        className="inline-flex items-center gap-2 rounded-full border border-emerald-300 bg-white px-3 py-2 text-xs font-semibold text-emerald-800 transition hover:border-emerald-400 dark:border-emerald-700 dark:bg-gray-950/40 dark:text-emerald-100"
                        onClick={onSaveCustomPortfolio}
                      >
                        <Save className="h-3.5 w-3.5" />
                        Salvar carteira
                      </button>
                    </div>
                  ) : (
                    'Defina peso positivo para pelo menos dois ativos para gerar a carteira personalizada.'
                  )}
                </div>
              </div>
            )
          ) : null}

          {savedPortfolios.length > 0 ? (
            <div className="mt-5 rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30">
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Carteiras salvas
              </div>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                Reaplique uma alocação já montada para usar a mesma carteira em novas comparações,
                rankings e cenários.
              </p>
              <div className="mt-3 grid gap-3 lg:grid-cols-2">
                {savedPortfolios.map((portfolio) => (
                  <article
                    key={portfolio.portfolio_id}
                    className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900/60"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                          {portfolio.label}
                        </div>
                        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          {portfolio.components.length} sleeves · rebalanceamento{' '}
                          {portfolio.rebalance_frequency ?? 'monthly'}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="rounded-full border border-blue-300 px-3 py-1.5 text-xs font-semibold text-blue-800 transition hover:border-blue-400 dark:border-blue-700 dark:text-blue-200"
                          onClick={() => onApplySavedPortfolio(portfolio)}
                        >
                          Usar
                        </button>
                        <button
                          type="button"
                          className="inline-flex items-center rounded-full border border-gray-300 px-2.5 py-1.5 text-xs text-gray-600 transition hover:border-red-300 hover:text-red-700 dark:border-gray-700 dark:text-gray-300 dark:hover:border-red-700 dark:hover:text-red-200"
                          onClick={() => onDeleteSavedPortfolio(portfolio.portfolio_id)}
                          aria-label={`Excluir ${portfolio.label}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                    {portfolio.description ? (
                      <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
                        {portfolio.description}
                      </p>
                    ) : null}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {portfolio.components.map((component) => (
                        <span
                          key={`${portfolio.portfolio_id}-${component.component_id}`}
                          className="rounded-full border border-gray-200 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300"
                        >
                          {instrumentLookup.get(component.component_id)?.label ??
                            component.component_id}
                          : {formatNumber(component.weight, 0)}
                        </span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => void compare()}
            disabled={isLoadingCatalog || isComparing || (request.asset_ids ?? []).length === 0}
            className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isComparing
              ? 'Comparando...'
              : entryMode === 'guided'
                ? 'Rodar estudo'
                : 'Comparar seleção manual'}
          </button>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {entryMode === 'guided' && selectedPreset ? (
              <>
                Você está partindo de <strong>{selectedPreset.label}</strong> com{' '}
                <strong>{selectedAssets.length}</strong> comparativos.
              </>
            ) : (
              <>
                Você está montando uma comparação com <strong>{selectedAssets.length}</strong>{' '}
                comparativos e <strong>{selectedSimpleAssetCount}</strong> ativos simples.
              </>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Metodologia em linguagem simples
        </div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          {catalog?.notes.map((note) => (
            <li key={note}>- {note}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ProductProfileSummary({
  instrument,
  compact = false,
}: {
  instrument: InvestmentInstrumentPayload;
  compact?: boolean;
}) {
  if (!instrument.product_profile) {
    return null;
  }

  const profile = instrument.product_profile;
  const items = compact
    ? [profile.investment_type_label, profile.investability_label, profile.liquidity_label]
    : [
        profile.investment_type_label,
        profile.investability_label,
        profile.liquidity_label,
        profile.tax_treatment_label,
        profile.income_policy_label,
      ];

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={`${instrument.instrument_id}-${item}`}
          className="rounded-full border border-gray-200 bg-gray-50 px-2 py-1 text-[11px] leading-4 text-gray-600 dark:border-gray-700 dark:bg-gray-900/60 dark:text-gray-300"
        >
          {item}
        </span>
      ))}
    </div>
  );
}
