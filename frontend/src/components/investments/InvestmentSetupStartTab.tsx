import { Coins, Globe2, Landmark, ListChecks, SlidersHorizontal, Wallet } from 'lucide-react';
import type { InvestmentPresetPayload, InvestmentCatalogPayload } from '../../types/api';
import { formatDate } from '../../lib/utils';
import InvestmentMarketExplorerPanel from './InvestmentMarketExplorerPanel';
import InvestmentOrganizerParityPanel from './InvestmentOrganizerParityPanel';
import InvestmentProductDataPlanPanel from './InvestmentProductDataPlanPanel';

type InvestmentsEntryMode = 'guided' | 'manual';

interface InvestmentSetupPresetGroup {
  label: string;
  description: string;
  presets: InvestmentPresetPayload[];
}

interface InvestmentSetupStartTabProps {
  entryMode: InvestmentsEntryMode;
  presetGroups: InvestmentSetupPresetGroup[];
  selectedPresetId: string;
  investorEasyParity: InvestmentCatalogPayload['investor_easy_parity'];
  marketExplorer: InvestmentCatalogPayload['market_explorer'];
  productDataPlan: InvestmentCatalogPayload['product_data_plan'];
  onChooseGuided: () => void;
  onChooseManual: () => void;
  onApplyPreset: (presetId: string) => void;
  onClearManualSelection: () => void;
  onRefreshProductData?: () => Promise<void> | void;
  onReturnToGuided: () => void;
}

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
    return <Wallet className="h-4 w-4" />;
  }
  return <Wallet className="h-4 w-4" />;
}

export default function InvestmentSetupStartTab({
  entryMode,
  presetGroups,
  selectedPresetId,
  investorEasyParity,
  marketExplorer,
  productDataPlan,
  onChooseGuided,
  onChooseManual,
  onApplyPreset,
  onClearManualSelection,
  onRefreshProductData,
  onReturnToGuided,
}: InvestmentSetupStartTabProps) {
  return (
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
          <strong>“se eu tivesse colocado meu dinheiro aqui, quanto ele teria virado?”</strong>. A
          comparacao usa o mesmo capital inicial e os mesmos aportes para todas as alternativas.
        </p>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
          <Landmark className="h-4 w-4 text-blue-600 dark:text-blue-300" />
          1. Escolha como quer começar
        </div>
        <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          A principal diferença desta aba é esta: você pode começar por um <strong>estudo pronto</strong>
          , que já traz uma pergunta e uma seleção inicial de comparativos, ou pode{' '}
          <strong>montar do seu jeito</strong>.
        </p>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <button
            type="button"
            onClick={onChooseGuided}
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
              Melhor para começar rápido. O sistema já sugere quem comparar, qual período faz sentido e,
              em alguns casos, quais benchmarks usar.
            </p>
          </button>

          <button
            type="button"
            onClick={onChooseManual}
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
              Melhor para quem já sabe os ativos que quer colocar lado a lado ou quer sair do roteiro
              sugerido e construir a comparação do zero.
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
                Primeiro você escolhe a pergunta que quer responder. Depois, à direita, você só revisa
                quem entrou no estudo e decide se quer manter o roteiro ou personalizar.
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
                        onClick={() => onApplyPreset(preset.preset_id)}
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
              Agora o fluxo fica assim: primeiro você define o dinheiro e o período. Depois, à direita,
              escolhe exatamente quem entra na comparação.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={onClearManualSelection}
                className="rounded-full border border-emerald-300 bg-white px-4 py-2 text-sm font-medium text-emerald-800 transition hover:border-emerald-400 dark:border-emerald-700 dark:bg-gray-950 dark:text-emerald-200"
              >
                Limpar seleção atual
              </button>
              <button
                type="button"
                onClick={onReturnToGuided}
                className="rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-gray-400 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-200"
              >
                Voltar para estudos prontos
              </button>
            </div>
          </div>
        )}
      </div>

      <InvestmentOrganizerParityPanel parity={investorEasyParity} />

      <InvestmentMarketExplorerPanel
        explorer={marketExplorer}
        selectedPresetId={selectedPresetId}
      />
      <InvestmentProductDataPlanPanel
        plan={productDataPlan}
        onRefreshComplete={onRefreshProductData}
      />
    </div>
  );
}
