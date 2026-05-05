import { useEffect, useMemo, useState } from 'react';
import SectionTabs from './app-shell/SectionTabs';
import InvestmentResultsPanel from './investments/InvestmentResultsPanel';
import InvestmentSetupStartTab from './investments/InvestmentSetupStartTab';
import InvestmentSetupScenarioTab from './investments/InvestmentSetupScenarioTab';
import InvestmentSetupReviewTab from './investments/InvestmentSetupReviewTab';
import { useInvestmentsComparison } from '../hooks/useInvestmentsComparison';
import type { InvestmentInstrumentPayload, InvestmentPresetPayload } from '../types/api';

interface InvestmentsWorkspaceProps {
  onError: (message: string | null) => void;
}

type InvestmentsEntryMode = 'guided' | 'manual';
type InvestmentsWorkspaceTab = 'setup' | 'results';
type InvestmentsSetupTab = 'start' | 'scenario' | 'review';

function compareStringArrays(left: string[] | null | undefined, right: string[] | null | undefined) {
  const normalizedLeft = [...(left ?? [])].sort();
  const normalizedRight = [...(right ?? [])].sort();
  if (normalizedLeft.length !== normalizedRight.length) {
    return false;
  }
  return normalizedLeft.every((value, index) => value === normalizedRight[index]);
}

function presetFamily(
  preset: InvestmentPresetPayload,
  instrumentLookup: Map<string, InvestmentInstrumentPayload>
): { label: string; description: string } {
  if (preset.preset_id.startsWith('fixed_income_')) {
    return {
      label: 'Renda fixa guiada',
      description: 'Estudos com CDI, duration, Tesouro Direto e juros reais.',
    };
  }

  const hasGuidedPortfolio = preset.asset_ids.some(
    (assetId) => instrumentLookup.get(assetId)?.source_kind === 'model_portfolio'
  );
  if (hasGuidedPortfolio) {
    return {
      label: 'Carteiras guiadas',
      description: 'Simulações prontas inspiradas em vídeos e alocações-modelo.',
    };
  }

  if (preset.preset_id === 'global_b3') {
    return {
      label: 'Exterior e diversificação',
      description: 'Comparações para quem quer sair do Brasil sem abrir conta fora.',
    };
  }

  if (
    preset.preset_id === 'income_focus' ||
    preset.preset_id === 'pre_retirement' ||
    preset.preset_id === 'real_return'
  ) {
    return {
      label: 'Renda, proteção e aposentadoria',
      description: 'Estudos voltados para renda, inflação e preservação do patrimônio.',
    };
  }

  return {
    label: 'Começo e comparações amplas',
    description: 'Presets para aprender as grandes famílias de investimento sem complicação.',
  };
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
    isCustomPortfolioEnabled,
    customPortfolioName,
    customPortfolioDescription,
    customPortfolioWeights,
    customPortfolioAssets,
    savedPortfolios,
    applyPreset,
    updateRequest,
    toggleAsset,
    toggleBenchmark,
    setIsCustomPortfolioEnabled,
    setCustomPortfolioName,
    setCustomPortfolioDescription,
    updateCustomPortfolioWeight,
    saveCurrentCustomPortfolio,
    applySavedPortfolio,
    deleteSavedPortfolio,
    compare,
    reloadCatalog,
  } = useInvestmentsComparison(onError);
  const [chartMode, setChartMode] = useState<'nominal' | 'real'>('nominal');
  const [entryMode, setEntryMode] = useState<InvestmentsEntryMode>('guided');
  const [isAssetEditorExpanded, setIsAssetEditorExpanded] = useState(false);
  const [workspaceTab, setWorkspaceTab] = useState<InvestmentsWorkspaceTab>(
    comparison ? 'results' : 'setup'
  );
  const [setupTab, setSetupTab] = useState<InvestmentsSetupTab>('start');

  const instrumentsByCategory = useMemo(() => {
    if (!catalog) {
      return [];
    }
    return catalog.categories.map((category) => ({
      ...category,
      instruments: catalog.instruments.filter((item) => item.category_id === category.category_id),
    }));
  }, [catalog]);


  const selectedGuidedPortfolios = useMemo(() => {
    if (!catalog) {
      return [];
    }
    const selectedIds = new Set(request.asset_ids ?? []);
    return catalog.instruments.filter(
      (instrument) =>
        selectedIds.has(instrument.instrument_id) && instrument.source_kind === 'model_portfolio'
    );
  }, [catalog, request.asset_ids]);

  const instrumentLookup = useMemo(() => {
    return new Map(
      (catalog?.instruments ?? []).map((instrument) => [instrument.instrument_id, instrument])
    );
  }, [catalog]);
  const selectedAssets = useMemo(() => {
    if (!catalog) {
      return [];
    }
    const selectedIds = new Set(request.asset_ids ?? []);
    return catalog.instruments.filter((instrument) => selectedIds.has(instrument.instrument_id));
  }, [catalog, request.asset_ids]);
  const selectedBenchmarkOptions = useMemo(() => {
    if (!catalog) {
      return [];
    }
    const selectedIds = new Set(request.benchmark_ids ?? []);
    return catalog.benchmark_options.filter((benchmark) => selectedIds.has(benchmark.benchmark_id));
  }, [catalog, request.benchmark_ids]);
  const presetGroups = useMemo(() => {
    if (!catalog) {
      return [];
    }

    const groups = new Map<
      string,
      { label: string; description: string; presets: InvestmentPresetPayload[] }
    >();

    for (const preset of catalog.presets) {
      const family = presetFamily(preset, instrumentLookup);
      const current = groups.get(family.label);
      if (current) {
        current.presets.push(preset);
        continue;
      }
      groups.set(family.label, {
        label: family.label,
        description: family.description,
        presets: [preset],
      });
    }

    return Array.from(groups.values());
  }, [catalog, instrumentLookup]);

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
  }, [
    comparison?.request.end_date,
    comparison?.request.start_date,
    request.end_date,
    request.initial_capital,
    request.monthly_contribution,
    request.start_date,
  ]);

  const customPortfolioPreview = useMemo(() => {
    const activeComponents = customPortfolioAssets.filter(
      (asset) => (customPortfolioWeights[asset.instrument_id] ?? 0) > 0
    );
    const totalWeight = activeComponents.reduce(
      (sum, asset) => sum + (customPortfolioWeights[asset.instrument_id] ?? 0),
      0
    );
    return {
      activeCount: activeComponents.length,
      totalWeight,
    };
  }, [customPortfolioAssets, customPortfolioWeights]);

  const isAssetEditorVisible = entryMode === 'manual' || isAssetEditorExpanded;
  const presetCustomized = useMemo(() => {
    if (!selectedPreset) {
      return false;
    }

    const benchmarkMatchesPreset =
      selectedPreset.default_benchmark_ids === undefined ||
      selectedPreset.default_benchmark_ids === null ||
      compareStringArrays(request.benchmark_ids ?? [], selectedPreset.default_benchmark_ids);

    return !(
      compareStringArrays(request.asset_ids ?? [], selectedPreset.asset_ids) &&
      benchmarkMatchesPreset &&
      (selectedPreset.default_start_date === undefined ||
        request.start_date === selectedPreset.default_start_date) &&
      (selectedPreset.default_end_date === undefined ||
        (request.end_date ?? '') === (selectedPreset.default_end_date ?? ''))
    );
  }, [
    request.asset_ids,
    request.benchmark_ids,
    request.end_date,
    request.start_date,
    selectedPreset,
  ]);
  const hasFixedIncomeSelection = useMemo(() => {
    if (!catalog) {
      return false;
    }
    const selectedIds = new Set(request.asset_ids ?? []);
    return catalog.instruments.some(
      (instrument) =>
        selectedIds.has(instrument.instrument_id) &&
        (instrument.source_kind === 'fixed_income_index' ||
          instrument.source_kind === 'tesouro_direct_strategy')
    );
  }, [catalog, request.asset_ids]);
  const selectedSimpleAssetCount = selectedAssets.filter(
    (instrument) => instrument.source_kind !== 'model_portfolio'
  ).length;

  const handleApplyPreset = (presetId: string) => {
    setEntryMode('guided');
    setIsAssetEditorExpanded(false);
    applyPreset(presetId);
  };

  const handleToggleAsset = (instrumentId: string) => {
    if (entryMode === 'guided') {
      setIsAssetEditorExpanded(true);
    }
    toggleAsset(instrumentId);
  };

  useEffect(() => {
    if (comparison) {
      setWorkspaceTab('results');
    }
  }, [comparison]);

  const workspaceTabs = [
    { id: 'setup' as const, label: 'Montagem do estudo' },
    {
      id: 'results' as const,
      label: 'Resultado',
      badge: comparison ? comparison.results.length : undefined,
    },
  ];
  const setupTabs = [
    { id: 'start' as const, label: '1. Começo' },
    { id: 'scenario' as const, label: '2. Cenário' },
    {
      id: 'review' as const,
      label: '3. Revisão',
      badge: request.asset_ids?.length ?? 0,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Navegação interna da análise
            </div>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Vamos experimentar um fluxo menos carregado: primeiro você monta o estudo em etapas,
              depois abre o resultado em uma aba separada.
            </p>
          </div>
          {comparison ? (
            <button
              type="button"
              onClick={() => setWorkspaceTab('results')}
              className="rounded-full border border-blue-300 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-800 transition hover:border-blue-400 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200"
            >
              Abrir último resultado
            </button>
          ) : null}
        </div>
        <div className="mt-4">
          <SectionTabs
            tabs={workspaceTabs}
            activeTab={workspaceTab}
            onChange={setWorkspaceTab}
          />
        </div>
      </div>

      {workspaceTab === 'setup' ? (
        <>
          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Montagem do estudo em etapas
            </div>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Só a etapa ativa fica aberta. Assim a tela fica mais leve enquanto você define como
              quer começar, ajusta o cenário e revisa a comparação.
            </p>
            <div className="mt-4">
              <SectionTabs tabs={setupTabs} activeTab={setupTab} onChange={setSetupTab} />
            </div>
          </div>

          <div className="grid gap-6">
            {setupTab === 'start' ? (
              <InvestmentSetupStartTab
                entryMode={entryMode}
                presetGroups={presetGroups}
                selectedPresetId={selectedPresetId}
                investorEasyParity={catalog?.investor_easy_parity}
                marketExplorer={catalog?.market_explorer}
                productDataPlan={catalog?.product_data_plan}
                onChooseGuided={() => {
                  setEntryMode('guided');
                  setIsAssetEditorExpanded(false);
                }}
                onChooseManual={() => {
                  setEntryMode('manual');
                  setIsAssetEditorExpanded(true);
                }}
                onApplyPreset={handleApplyPreset}
                onClearManualSelection={() => {
                  updateRequest('asset_ids', []);
                  setIsCustomPortfolioEnabled(false);
                }}
                onRefreshProductData={reloadCatalog}
                onReturnToGuided={() => {
                  setEntryMode('guided');
                }}
              />
            ) : null}
            {setupTab === 'scenario' ? (
              <InvestmentSetupScenarioTab
                request={request}
                investedTotal={investedTotal}
                hasFixedIncomeSelection={hasFixedIncomeSelection}
                onDecisionProfileChange={(profile) =>
                  updateRequest('decision_profile', profile)}
                onRequestChange={(key, value) => {
                  updateRequest(key, value as never);
                }}
              />
            ) : null}
            {setupTab === 'review' ? (
              <InvestmentSetupReviewTab
                entryMode={entryMode}
                catalog={catalog}
                request={request}
                selectedPreset={selectedPreset}
                selectedAssets={selectedAssets}
                selectedBenchmarkOptions={selectedBenchmarkOptions}
                selectedSimpleAssetCount={selectedSimpleAssetCount}
                selectedGuidedPortfolioCount={selectedGuidedPortfolios.length}
                presetCustomized={presetCustomized}
                isAssetEditorExpanded={isAssetEditorExpanded}
                isAssetEditorVisible={isAssetEditorVisible}
                instrumentLookup={instrumentLookup}
                isCustomPortfolioEnabled={isCustomPortfolioEnabled}
                customPortfolioName={customPortfolioName}
                customPortfolioDescription={customPortfolioDescription}
                customPortfolioAssets={customPortfolioAssets}
                customPortfolioWeights={customPortfolioWeights}
                customPortfolioPreview={customPortfolioPreview}
                savedPortfolios={savedPortfolios}
                instrumentsByCategory={instrumentsByCategory}
                isLoadingCatalog={isLoadingCatalog}
                isComparing={isComparing}
                compare={compare}
                onToggleAsset={handleToggleAsset}
                onToggleAssetEditor={() => setIsAssetEditorExpanded((current) => !current)}
                onToggleBenchmark={toggleBenchmark}
                onToggleCustomPortfolio={(enabled) => setIsCustomPortfolioEnabled(enabled)}
                onChangeCustomPortfolioName={setCustomPortfolioName}
                onChangeCustomPortfolioDescription={setCustomPortfolioDescription}
                onUpdateCustomPortfolioWeight={updateCustomPortfolioWeight}
                onSaveCustomPortfolio={() => {
                  void saveCurrentCustomPortfolio();
                }}
                onApplySavedPortfolio={applySavedPortfolio}
                onDeleteSavedPortfolio={deleteSavedPortfolio}
              />
            ) : null}
          </div>
        </>
      ) : (
        <div className="space-y-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Resultado em uma aba separada
                </div>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  A leitura do estudo fica isolada aqui para você não precisar olhar formulário,
                  configuração e análise tudo ao mesmo tempo.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setWorkspaceTab('setup')}
                className="rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300"
              >
                Voltar para montagem
              </button>
            </div>
          </div>

          <InvestmentResultsPanel
            comparison={comparison}
            catalog={catalog}
            isLoadingCatalog={isLoadingCatalog}
            chartMode={chartMode}
            onChartModeChange={setChartMode}
          />
        </div>
      )}
    </div>
  );
}
