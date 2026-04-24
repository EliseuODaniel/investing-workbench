import { useEffect, useMemo, useState } from 'react';
import {
  BarChart3,
  Coins,
  Globe2,
  Landmark,
  ListChecks,
  ShieldCheck,
  SlidersHorizontal,
  Wallet,
} from 'lucide-react';
import InteractiveSeriesChart from './charts/InteractiveSeriesChart';
import SectionTabs from './app-shell/SectionTabs';
import FixedIncomeDecisionGuidePanel from './investments/FixedIncomeDecisionGuidePanel';
import InvestmentDecisionProfileForm from './investments/InvestmentDecisionProfileForm';
import InvestmentMethodologyPanel from './investments/InvestmentMethodologyPanel';
import PortfolioObjectiveSummaryPanel from './investments/PortfolioObjectiveSummaryPanel';
import { useInvestmentsComparison } from '../hooks/useInvestmentsComparison';
import { formatCurrency, formatDate, formatNumber, formatPercent } from '../lib/utils';
import type {
  InvestmentInstrumentPayload,
  InvestmentPresetPayload,
  InvestmentFixedIncomeStudyPayload,
  InvestmentFixedIncomeWindowPayload,
} from '../types/api';

interface InvestmentsWorkspaceProps {
  onError: (message: string | null) => void;
}

type InvestmentsEntryMode = 'guided' | 'manual';
type InvestmentsWorkspaceTab = 'setup' | 'results';
type InvestmentsSetupTab = 'start' | 'scenario' | 'review';

function objectiveIcon(presetId: string) {
  if (presetId.startsWith('fixed_income_')) {
    return <Landmark className="h-4 w-4" />;
  }
  if (presetId === 'income_focus' || presetId === 'pre_retirement') {
    return <Coins className="h-4 w-4" />;
  }
  if (presetId === 'global_b3') {
    return <Globe2 className="h-4 w-4" />;
  }
  if (presetId === 'balanced_b3' || presetId === 'real_return') {
    return <ShieldCheck className="h-4 w-4" />;
  }
  return <Wallet className="h-4 w-4" />;
}

function groupRollingWindows(rows: InvestmentFixedIncomeWindowPayload[]) {
  const grouped = new Map<number, InvestmentFixedIncomeWindowPayload[]>();
  for (const row of rows) {
    const current = grouped.get(row.window_years) ?? [];
    current.push(row);
    grouped.set(row.window_years, current);
  }
  return Array.from(grouped.entries())
    .sort(([left], [right]) => left - right)
    .map(([windowYears, groupedRows]) => ({
      windowYears,
      rows: [...groupedRows].sort((left, right) => right.win_rate - left.win_rate),
    }));
}

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
    applyPreset,
    updateRequest,
    toggleAsset,
    toggleBenchmark,
    setIsCustomPortfolioEnabled,
    setCustomPortfolioName,
    setCustomPortfolioDescription,
    updateCustomPortfolioWeight,
    compare,
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

  const topPerformer = comparison?.highlights.best_final_value;
  const bestReal = comparison?.highlights.best_real_cagr;
  const mostDefensive = comparison?.highlights.most_defensive;
  const fixedIncomeBacktest = comparison?.fixed_income_backtest;
  const fixedIncomeStudies = fixedIncomeBacktest?.studies ?? [];

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

  const currentChart = chartMode === 'real' ? comparison?.real_chart : comparison?.chart;
  const portfolioResults = comparison?.results.filter((row) => row.component_breakdown.length > 0) ?? [];
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

          <div
            className={`grid gap-6 ${
              setupTab === 'review' ? 'xl:grid-cols-[0.95fr_1.35fr]' : 'xl:grid-cols-1'
            }`}
          >
        <div className="space-y-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-300">
              Novo fluxo principal
            </div>
            <h3 className="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">
              Compare investimentos da B3 do jeito que uma pessoa comum pensa.
            </h3>
            <p className="mt-3 text-sm leading-7 text-gray-600 dark:text-gray-300">
              Em vez de começar por modulo tecnico, este comparador parte da pergunta natural:{' '}
              <strong>“se eu tivesse colocado meu dinheiro aqui, quanto ele teria virado?”</strong>
              . A comparacao usa o mesmo capital inicial e os mesmos aportes para todas as
              alternativas.
            </p>
          </div>

          {setupTab === 'start' ? (
          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <Landmark className="h-4 w-4 text-blue-600 dark:text-blue-300" />
              1. Escolha como quer começar
            </div>
            <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
              A principal diferença desta aba é esta: você pode começar por um{' '}
              <strong>estudo pronto</strong>, que já traz uma pergunta e uma seleção inicial de
              comparativos, ou pode <strong>montar do seu jeito</strong>.
            </p>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <button
                type="button"
                onClick={() => {
                  setEntryMode('guided');
                  setIsAssetEditorExpanded(false);
                }}
                className={`rounded-2xl border p-4 text-left transition ${
                  entryMode === 'guided'
                    ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950/30'
                    : 'border-gray-200 bg-gray-50 hover:border-gray-300 dark:border-gray-800 dark:bg-gray-950/40 dark:hover:border-gray-700'
                }`}
              >
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  <ListChecks className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                  Quero um estudo pronto
                </div>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  Melhor para começar rápido. O sistema já sugere quem comparar, qual período faz
                  sentido e, em alguns casos, quais benchmarks usar.
                </p>
              </button>

              <button
                type="button"
                onClick={() => {
                  setEntryMode('manual');
                  setIsAssetEditorExpanded(true);
                }}
                className={`rounded-2xl border p-4 text-left transition ${
                  entryMode === 'manual'
                    ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950/30'
                    : 'border-gray-200 bg-gray-50 hover:border-gray-300 dark:border-gray-800 dark:bg-gray-950/40 dark:hover:border-gray-700'
                }`}
              >
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  <SlidersHorizontal className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                  Quero montar manualmente
                </div>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  Melhor para quem já sabe os ativos que quer colocar lado a lado ou quer sair do
                  roteiro sugerido e construir a comparação do zero.
                </p>
              </button>
            </div>

            {entryMode === 'guided' ? (
              <div className="mt-5 space-y-4">
                <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
                  <div className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                    Estudos prontos deixam o começo mais simples
                  </div>
                  <p className="mt-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
                    Primeiro você escolhe a pergunta que quer responder. Depois, à direita, você
                    só revisa quem entrou no estudo e decide se quer manter o roteiro ou
                    personalizar.
                  </p>
                </div>

                {presetGroups.map((group) => (
                  <div key={group.label}>
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {group.label}
                    </div>
                    <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      {group.description}
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      {group.presets.map((preset) => {
                        const active = preset.preset_id === selectedPresetId;
                        return (
                          <button
                            key={preset.preset_id}
                            type="button"
                            onClick={() => handleApplyPreset(preset.preset_id)}
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
                            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-gray-500 dark:text-gray-400">
                              <span className="rounded-full border border-gray-300 px-2 py-1 dark:border-gray-700">
                                {preset.asset_ids.length} comparativos
                              </span>
                              {preset.default_start_date ? (
                                <span className="rounded-full border border-gray-300 px-2 py-1 dark:border-gray-700">
                                  começa em {formatDate(preset.default_start_date)}
                                </span>
                              ) : null}
                              {preset.default_benchmark_ids?.length ? (
                                <span className="rounded-full border border-gray-300 px-2 py-1 dark:border-gray-700">
                                  {preset.default_benchmark_ids.length} benchmark(s)
                                </span>
                              ) : null}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
                <div className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">
                  Você está montando a comparação manualmente
                </div>
                <p className="mt-2 text-sm leading-6 text-emerald-900/90 dark:text-emerald-100/90">
                  Agora o fluxo fica assim: primeiro você define o dinheiro e o período. Depois,
                  à direita, escolhe exatamente quem entra na comparação.
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      updateRequest('asset_ids', []);
                      setIsCustomPortfolioEnabled(false);
                    }}
                    className="rounded-full border border-emerald-300 bg-white px-4 py-2 text-sm font-medium text-emerald-800 transition hover:border-emerald-400 dark:border-emerald-700 dark:bg-gray-950 dark:text-emerald-200"
                  >
                    Limpar seleção atual
                  </button>
                  <button
                    type="button"
                    onClick={() => setEntryMode('guided')}
                    className="rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-gray-400 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-200"
                  >
                    Voltar para estudos prontos
                  </button>
                </div>
              </div>
            )}
          </div>
          ) : null}

          {setupTab === 'scenario' ? (
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
              Este comparador considera o mesmo fluxo de aportes em todas as alternativas. No
              recorte atual, o valor investido seria aproximadamente{' '}
              <strong>{formatCurrency(investedTotal)}</strong>.
            </div>

            <div className="mt-4">
              <InvestmentDecisionProfileForm
                profile={request.decision_profile}
                onChange={(profile) => updateRequest('decision_profile', profile)}
              />
            </div>

            {hasFixedIncomeSelection ? (
              <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
                <div className="text-sm font-semibold text-amber-900 dark:text-amber-100">
                  Configuração extra para renda fixa
                </div>
                <p className="mt-2 text-sm text-amber-900/80 dark:text-amber-100/80">
                  Este bloco só aparece quando a comparação inclui juros. É aqui que você decide
                  se quer olhar índice teórico, produto real do Tesouro ou os dois juntos.
                </p>
                <div className="mt-4 grid gap-4 md:grid-cols-3">
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700 dark:text-gray-200">
                      Modo de estudo
                    </span>
                    <select
                      className="input-field"
                      value={request.fixed_income_study_mode ?? 'auto'}
                      onChange={(event) =>
                        updateRequest('fixed_income_study_mode', event.target.value)
                      }
                    >
                      <option value="auto">Automático</option>
                      <option value="index_duration">Índice por duration</option>
                      <option value="retail_treasury">Tesouro Direto real</option>
                      <option value="both">Mostrar os dois</option>
                    </select>
                  </label>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700 dark:text-gray-200">
                      Visão tributária
                    </span>
                    <select
                      className="input-field"
                      value={request.fixed_income_tax_treatment ?? 'gross'}
                      onChange={(event) =>
                        updateRequest('fixed_income_tax_treatment', event.target.value)
                      }
                    >
                      <option value="gross">Bruta</option>
                      <option value="net">Líquida estimada</option>
                      <option value="both">Líquida com bruto visível</option>
                    </select>
                  </label>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700 dark:text-gray-200">
                      Janelas móveis
                    </span>
                    <select
                      className="input-field"
                      value={request.fixed_income_window_frequency ?? 'monthly'}
                      onChange={(event) =>
                        updateRequest('fixed_income_window_frequency', event.target.value)
                      }
                    >
                      <option value="monthly">Início mensal</option>
                      <option value="daily">Início diário</option>
                    </select>
                  </label>
                </div>
              </div>
            ) : null}
          </div>
          ) : null}
        </div>

        {setupTab === 'review' ? (
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

            <div className="mt-5 grid gap-4 xl:grid-cols-4">
              <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700 dark:text-blue-300">
                  Comparativos
                </div>
                <div className="mt-2 text-xl font-semibold text-blue-900 dark:text-blue-100">
                  {selectedAssets.length}
                </div>
                <div className="mt-1 text-sm text-blue-800 dark:text-blue-200">
                  ativos, ETFs ou carteiras entram na disputa
                </div>
              </div>
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
                  Benchmarks
                </div>
                <div className="mt-2 text-xl font-semibold text-emerald-900 dark:text-emerald-100">
                  {selectedBenchmarkOptions.length}
                </div>
                <div className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
                  referências para dizer se o risco valeu a pena
                </div>
              </div>
              <div className="rounded-2xl border border-violet-200 bg-violet-50 p-4 dark:border-violet-900/50 dark:bg-violet-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-700 dark:text-violet-300">
                  Carteiras guiadas
                </div>
                <div className="mt-2 text-xl font-semibold text-violet-900 dark:text-violet-100">
                  {selectedGuidedPortfolios.length}
                </div>
                <div className="mt-1 text-sm text-violet-800 dark:text-violet-200">
                  seleções prontas com rebalanceamento embutido
                </div>
              </div>
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700 dark:text-amber-300">
                  Jeito de começar
                </div>
                <div className="mt-2 text-xl font-semibold text-amber-900 dark:text-amber-100">
                  {entryMode === 'guided' ? 'Estudo pronto' : 'Manual'}
                </div>
                <div className="mt-1 text-sm text-amber-800 dark:text-amber-200">
                  {entryMode === 'guided'
                    ? 'você revisa primeiro, depois personaliza se quiser'
                    : 'você define os comparativos diretamente'}
                </div>
              </div>
            </div>

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
                Este bloco existe para tirar a ambiguidade: aqui você vê claramente quem está na
                disputa. Em estudo pronto, isso é uma revisão. Em modo manual, isso é a montagem
                da seleção.
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
                      Se o estudo já parece certo, você pode seguir direto. Se quiser trocar
                      comparativos, abra o editor abaixo.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsAssetEditorExpanded((current) => !current)}
                    className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                      isAssetEditorExpanded
                        ? 'border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200'
                        : 'border-gray-300 bg-white text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300'
                    }`}
                  >
                    {isAssetEditorExpanded
                      ? 'Fechar personalização'
                      : 'Quero personalizar os comparativos'}
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
                              onChange={() => handleToggleAsset(instrument.instrument_id)}
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
            ) : null}
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <Wallet className="h-4 w-4 text-blue-600 dark:text-blue-300" />
              4. Benchmarks e carteira pessoal
            </div>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Depois de definir quem entra na disputa, você decide quais referências deixam a
              leitura mais justa e se quer incluir uma carteira própria.
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

            <div className="mt-6 rounded-2xl border border-dashed border-gray-300 p-4 dark:border-gray-700">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    Carteira pessoal (opcional)
                  </div>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                    Use os ativos simples já selecionados para comparar uma alocação sua contra
                    ativos avulsos e carteiras guiadas.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCustomPortfolioEnabled(!isCustomPortfolioEnabled)}
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
                    Selecione pelo menos dois ativos simples para montar uma carteira
                    personalizada. Carteiras guiadas não entram aqui para evitar comparação
                    circular.
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
                          onChange={(event) => setCustomPortfolioName(event.target.value)}
                        />
                      </label>
                      <label className="space-y-2 text-sm">
                        <span className="font-medium text-gray-700 dark:text-gray-200">
                          Descrição curta
                        </span>
                        <input
                          className="input-field"
                          value={customPortfolioDescription}
                          onChange={(event) => setCustomPortfolioDescription(event.target.value)}
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
                                updateCustomPortfolioWeight(
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
                        <>
                          A carteira <strong>{customPortfolioName || 'Minha carteira'}</strong> vai
                          entrar como comparativo com{' '}
                          <strong>{customPortfolioPreview.activeCount} sleeves</strong>. O backend
                          normaliza os pesos automaticamente a partir do total informado de{' '}
                          <strong>{formatNumber(customPortfolioPreview.totalWeight, 0)}</strong>.
                        </>
                      ) : (
                        'Defina peso positivo para pelo menos dois ativos para gerar a carteira personalizada.'
                      )}
                    </div>
                  </div>
                )
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

          <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Resultado didatico
        </div>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
          O objetivo aqui nao e adivinhar o futuro. E mostrar, com um fluxo de aportes
          consistente, qual alternativa teria rendido mais, sofrido menos e preservado melhor o
          poder de compra.
        </p>

        {!comparison ? (
          <div className="mt-5 rounded-2xl border border-dashed border-gray-300 px-4 py-10 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
            {isLoadingCatalog
              ? 'Carregando catalogo de investimentos...'
              : 'Escolha um objetivo, confirme os ativos e rode a comparacao.'}
          </div>
        ) : (
          <div className="mt-6 space-y-6">
            <div className="grid gap-4 xl:grid-cols-4">
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

              <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-4 dark:border-cyan-900/50 dark:bg-cyan-950/20">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-300">
                  Melhor retorno real
                </div>
                <div className="mt-2 text-xl font-semibold text-cyan-900 dark:text-cyan-100">
                  {bestReal?.label ?? 'n/a'}
                </div>
                <div className="mt-1 text-sm text-cyan-800 dark:text-cyan-200">
                  {bestReal ? formatPercent(bestReal.real_cagr) : 'n/a'} ao ano
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
                  Acima da inflacao
                </div>
                <div className="mt-2 text-xl font-semibold text-amber-900 dark:text-amber-100">
                  {comparison.highlights.beats_inflation_count ?? 0} / {comparison.results.length}
                </div>
                <div className="mt-1 text-sm text-amber-800 dark:text-amber-200">
                  comparativos preservaram poder de compra
                </div>
              </div>
            </div>

            <InvestmentMethodologyPanel guide={comparison.methodology_guide} />

            <PortfolioObjectiveSummaryPanel summary={comparison.portfolio_objective_summary} />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Visualizacao do patrimonio em valores nominais ou ajustados pelo IPCA.
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setChartMode('nominal')}
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
                  onClick={() => setChartMode('real')}
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
              data={currentChart?.points ?? []}
              xKey="date"
              series={currentChart?.series ?? []}
              referenceSeriesId={currentChart?.reference_series_id}
              xTickFormatter={(value) => formatDate(String(value))}
              yTickFormatter={(value) => formatCurrency(value)}
              tooltipLabelFormatter={(value) => formatDate(String(value))}
              tooltipValueFormatter={(value) => formatCurrency(value)}
              heightClassName="h-[28rem]"
              enableDateFilter
              rebaseOnDateFilter
            />

            <FixedIncomeDecisionGuidePanel guide={comparison.fixed_income_decision_guide} />

            {fixedIncomeBacktest ? (
              <div className="space-y-5 rounded-2xl border border-gray-200 p-5 dark:border-gray-800">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      Backtests de renda fixa
                    </div>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                      Esta área separa o que é índice teórico de duration constante do que é
                      experiência real de Tesouro Direto com preços oficiais e visão líquida.
                    </p>
                  </div>
                  {fixedIncomeBacktest.methodology.video_reference_match ? (
                    <div className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-200">
                      Recorte alinhado ao vídeo
                    </div>
                  ) : null}
                </div>

                {fixedIncomeBacktest.summary?.takeaways?.length ? (
                  <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
                    <div className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                      O que muda quando trocamos a metodologia
                    </div>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
                      {fixedIncomeBacktest.summary.takeaways.map((item) => (
                        <li key={item}>- {item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {fixedIncomeStudies.map((study: InvestmentFixedIncomeStudyPayload) => {
                  const leaders = study.full_period.leaders;
                  const overallLeader = leaders.overall;
                  const prefixadoLeader = leaders.prefixado;
                  const ipcaLeader = leaders.ipca_plus;
                  const consistentLeader = leaders.most_consistent;
                  const groupedWindows = groupRollingWindows(study.rolling_windows);
                  return (
                    <div
                      key={study.study_id}
                      className="rounded-2xl border border-gray-200 p-5 dark:border-gray-800"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                            {study.study_label}
                          </div>
                          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                            {study.methodology.study_scope_label ?? study.methodology.index_methodology_label}
                          </p>
                        </div>
                        <div className="rounded-xl bg-gray-50 px-3 py-2 text-xs text-gray-600 dark:bg-gray-900/60 dark:text-gray-300">
                          Métrica principal: {study.methodology.comparison_metric_label ?? 'valor final'}
                        </div>
                      </div>

                      <div className="mt-5 grid gap-4 xl:grid-cols-4">
                        <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
                          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700 dark:text-blue-300">
                            Líder geral
                          </div>
                          <div className="mt-2 text-xl font-semibold text-blue-900 dark:text-blue-100">
                            {overallLeader?.label ?? 'n/a'}
                          </div>
                          <div className="mt-1 text-sm text-blue-800 dark:text-blue-200">
                            {overallLeader ? formatCurrency(overallLeader.display_value) : 'n/a'}
                          </div>
                        </div>
                        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
                          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700 dark:text-amber-300">
                            Melhor prefixado
                          </div>
                          <div className="mt-2 text-xl font-semibold text-amber-900 dark:text-amber-100">
                            {prefixadoLeader?.label ?? 'n/a'}
                          </div>
                          <div className="mt-1 text-sm text-amber-800 dark:text-amber-200">
                            {prefixadoLeader ? formatCurrency(prefixadoLeader.display_value) : 'n/a'}
                          </div>
                        </div>
                        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
                          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
                            Melhor IPCA+
                          </div>
                          <div className="mt-2 text-xl font-semibold text-emerald-900 dark:text-emerald-100">
                            {ipcaLeader?.label ?? 'n/a'}
                          </div>
                          <div className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
                            {ipcaLeader ? formatCurrency(ipcaLeader.display_value) : 'n/a'}
                          </div>
                        </div>
                        <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-4 dark:border-cyan-900/50 dark:bg-cyan-950/20">
                          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-300">
                            Mais consistente
                          </div>
                          <div className="mt-2 text-xl font-semibold text-cyan-900 dark:text-cyan-100">
                            {consistentLeader?.label ?? 'n/a'}
                          </div>
                          <div className="mt-1 text-sm text-cyan-800 dark:text-cyan-200">
                            {consistentLeader
                              ? `${formatPercent(consistentLeader.win_rate)} em 5 anos`
                              : 'n/a'}
                          </div>
                        </div>
                      </div>

                      <div className="mt-5 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
                        <div className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
                          <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
                              <thead className="bg-gray-50 dark:bg-gray-900/50">
                                <tr className="text-left text-xs uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
                                  <th className="px-4 py-3">Instrumento</th>
                                  <th className="px-4 py-3">Família</th>
                                  <th className="px-4 py-3">Valor final</th>
                                  <th className="px-4 py-3">Valor real</th>
                                  <th className="px-4 py-3">Vs benchmark</th>
                                  <th className="px-4 py-3">CAGR</th>
                                  <th className="px-4 py-3">DD máx</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                                {study.full_period.results.map((row) => (
                                  <tr key={`${study.study_id}-${row.instrument_id}`}>
                                    <td className="px-4 py-4 align-top">
                                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                                        {row.label}
                                      </div>
                                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                        {row.duration_years
                                          ? `duration alvo de ${formatNumber(row.duration_years, 1)} anos`
                                          : 'referência pós-fixada'}
                                      </div>
                                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                        {row.source_method_label}
                                      </div>
                                    </td>
                                    <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                                      {row.family_label}
                                    </td>
                                    <td className="px-4 py-4 text-gray-900 dark:text-gray-100">
                                      <div className="font-semibold">{formatCurrency(row.display_value)}</div>
                                      <div className="text-xs text-gray-500 dark:text-gray-400">
                                        lucro {formatCurrency(row.display_profit)}
                                      </div>
                                      {Math.abs(row.final_value_net - row.final_value) > 0.01 ? (
                                        <div className="text-xs text-gray-500 dark:text-gray-400">
                                          bruto {formatCurrency(row.final_value)} | líquido{' '}
                                          {formatCurrency(row.final_value_net)}
                                        </div>
                                      ) : null}
                                    </td>
                                    <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                                      <div>{formatCurrency(row.display_value_real)}</div>
                                      <div className="text-xs text-gray-500 dark:text-gray-400">
                                        CAGR real {formatPercent(row.display_real_cagr)}
                                      </div>
                                    </td>
                                    <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                                      <div>{formatPercent(row.relative_gap_vs_benchmark)}</div>
                                      <div className="text-xs text-gray-500 dark:text-gray-400">
                                        {formatCurrency(row.value_gap_vs_benchmark)}
                                      </div>
                                    </td>
                                    <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                                      <div>{formatPercent(row.display_cagr)}</div>
                                      <div className="text-xs text-gray-500 dark:text-gray-400">
                                        real {formatPercent(row.display_real_cagr)}
                                      </div>
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
                              Isso mede
                            </div>
                            <div className="mt-3 rounded-xl bg-gray-50 px-3 py-3 text-sm text-gray-600 dark:bg-gray-900/60 dark:text-gray-300">
                              {study.methodology.what_it_measures ?? study.methodology.index_methodology_label}
                            </div>
                          </div>

                          <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
                            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                              Isso não mede
                            </div>
                            <div className="mt-3 rounded-xl bg-gray-50 px-3 py-3 text-sm text-gray-600 dark:bg-gray-900/60 dark:text-gray-300">
                              {study.methodology.what_it_does_not_measure ?? study.methodology.full_period_note}
                            </div>
                          </div>

                          <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
                            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                              Leitura do estudo
                            </div>
                            <ul className="mt-3 space-y-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
                              {study.takeaways.map((item) => (
                                <li key={item}>- {item}</li>
                              ))}
                            </ul>
                          </div>

                          <div className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
                            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                              Fontes e método
                            </div>
                            <div className="mt-3 space-y-3 text-sm text-gray-600 dark:text-gray-300">
                              <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
                                {study.methodology.index_methodology_label}
                              </div>
                              <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
                                {study.methodology.series_source_label}
                              </div>
                              <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
                                {study.methodology.rolling_window_note}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="mt-5 grid gap-4 xl:grid-cols-4">
                        {groupedWindows.map((group) => (
                          <div
                            key={`${study.study_id}-${group.windowYears}`}
                            className="rounded-2xl border border-gray-200 p-4 dark:border-gray-800"
                          >
                            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                              Janelas de {group.windowYears} {group.windowYears === 1 ? 'ano' : 'anos'}
                            </div>
                            <div className="mt-3 space-y-3">
                              {group.rows.map((row) => (
                                <div
                                  key={`${study.study_id}-${row.instrument_id}-${group.windowYears}`}
                                  className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-900/60"
                                >
                                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                                    {row.label}
                                  </div>
                                  <div className="mt-1 text-gray-600 dark:text-gray-300">
                                    venceu o benchmark em {formatPercent(row.win_rate)}
                                  </div>
                                  <div className="text-gray-500 dark:text-gray-400">
                                    {formatNumber(row.windows_count, 0)} janelas
                                  </div>
                                  <div className="text-gray-500 dark:text-gray-400">
                                    excesso médio {formatPercent(row.average_excess_return)}
                                  </div>
                                  {row.best_window_start && row.best_window_end ? (
                                    <div className="text-gray-500 dark:text-gray-400">
                                      melhor janela {formatDate(row.best_window_start)} até{' '}
                                      {formatDate(row.best_window_end)}
                                    </div>
                                  ) : null}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}

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
                            {row.component_breakdown.length > 0 ? (
                              <div className="mt-2 inline-flex rounded-full border border-emerald-300 px-2 py-1 text-[11px] font-medium text-emerald-800 dark:border-emerald-700 dark:text-emerald-200">
                                carteira rebalanceada
                              </div>
                            ) : null}
                          </td>
                          <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                            {row.category_label}
                          </td>
                          <td className="px-4 py-4 text-gray-900 dark:text-gray-100">
                            <div className="font-semibold">{formatCurrency(row.final_value)}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              real {formatCurrency(row.final_value_real)}
                            </div>
                          </td>
                          <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                            <div>{formatCurrency(row.net_profit)}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              real {formatCurrency(row.net_profit_real)}
                            </div>
                          </td>
                          <td className="px-4 py-4 text-gray-600 dark:text-gray-300">
                            <div>{formatPercent(row.cagr)}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              real {formatPercent(row.real_cagr)}
                            </div>
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
                    Inflacao e retorno real
                  </div>
                  <div className="mt-3 space-y-3 text-sm">
                    <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                        {comparison.inflation.label}
                      </div>
                      <div className="mt-1 text-gray-600 dark:text-gray-300">
                        acumulado {formatPercent(comparison.inflation.accumulated_rate)}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">
                        perda de poder de compra{' '}
                        {formatPercent(comparison.inflation.purchasing_power_loss)}
                      </div>
                    </div>
                    <div className="rounded-xl bg-gray-50 px-3 py-3 dark:bg-gray-900/60">
                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                        Melhor CAGR real
                      </div>
                      <div className="mt-1 text-gray-600 dark:text-gray-300">
                        {bestReal?.label ?? 'n/a'}
                      </div>
                      <div className="text-gray-500 dark:text-gray-400">
                        {bestReal ? formatPercent(bestReal.real_cagr) : 'n/a'}
                      </div>
                    </div>
                  </div>
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
                          CAGR real medio {formatPercent(row.average_real_cagr)}
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
                      <div
                        key={benchmark.benchmark_id}
                        className="rounded-xl bg-gray-50 px-3 py-3 text-sm dark:bg-gray-900/60"
                      >
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                          {benchmark.label}
                        </div>
                        <div className="mt-1 text-gray-600 dark:text-gray-300">
                          final {formatCurrency(benchmark.final_value)}
                        </div>
                        <div className="text-gray-500 dark:text-gray-400">
                          real {formatCurrency(benchmark.final_value_real)}
                        </div>
                        <div className="text-gray-500 dark:text-gray-400">
                          CAGR {formatPercent(benchmark.cagr)} | real{' '}
                          {formatPercent(benchmark.real_cagr)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {portfolioResults.length > 0 ? (
              <div className="rounded-2xl border border-gray-200 p-5 dark:border-gray-800">
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Contribuicao por sleeve e por familia
                </div>
                <div className="mt-4 grid gap-4 xl:grid-cols-2">
                  {portfolioResults.map((row) => (
                    <div
                      key={row.instrument_id}
                      className="rounded-2xl bg-gray-50 p-4 dark:bg-gray-900/60"
                    >
                      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {row.label}
                      </div>
                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        valor final {formatCurrency(row.final_value)} | real{' '}
                        {formatCurrency(row.final_value_real)}
                      </div>

                      <div className="mt-4 grid gap-3 md:grid-cols-2">
                        {row.component_breakdown.map((component) => (
                          <div
                            key={`${row.instrument_id}-${component.component_id}`}
                            className="rounded-xl border border-gray-200 bg-white px-3 py-3 text-sm dark:border-gray-800 dark:bg-gray-950/50"
                          >
                            <div className="font-semibold text-gray-900 dark:text-gray-100">
                              {component.label}
                            </div>
                            <div className="mt-1 text-gray-600 dark:text-gray-300">
                              alvo {formatPercent(component.target_weight)}
                            </div>
                            <div className="text-gray-500 dark:text-gray-400">
                              fim {formatPercent(component.ending_weight)}
                            </div>
                            <div className="text-gray-500 dark:text-gray-400">
                              contribuiu {formatCurrency(component.final_value)}
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {row.category_breakdown.map((category) => (
                          <div
                            key={`${row.instrument_id}-${category.category_label}`}
                            className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200"
                          >
                            {category.category_label}: alvo {formatPercent(category.target_weight)} |
                            fim {formatPercent(category.ending_weight)}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {comparison.warnings.length > 0 ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">
                <div className="font-semibold">Atencoes sobre o recorte</div>
                <ul className="mt-2 space-y-1">
                  {comparison.warnings.map((warning) => (
                    <li key={warning}>- {warning}</li>
                  ))}
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
      )}
    </div>
  );
}
