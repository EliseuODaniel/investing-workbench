import { PairsDraft } from '../../lib/pairsPayload';
import { PairsUniversePresetPayload } from '../../types/api';

interface PairsControlsCardProps {
  draft: PairsDraft;
  presets: PairsUniversePresetPayload[];
  selectedPreset?: PairsUniversePresetPayload | null;
  isResolving: boolean;
  isScreening: boolean;
  isRunning: boolean;
  updateDraft: <K extends keyof PairsDraft>(key: K, value: PairsDraft[K]) => void;
  onResolveUniverse: () => void;
  onRunScreen: () => void;
  onRunBacktest: () => void;
  onRunBatch: () => void;
  onRunResearchBatch: () => void;
}

export function PairsControlsCard({
  draft,
  presets,
  selectedPreset = null,
  isResolving,
  isScreening,
  isRunning,
  updateDraft,
  onResolveUniverse,
  onRunScreen,
  onRunBacktest,
  onRunBatch,
  onRunResearchBatch,
}: PairsControlsCardProps) {
  return (
    <div className="card space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-3xl">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Pairs Trading B3
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Universe builder, screener de cointegração, batch de cenários e leitura de robustez
            para long-short em ações brasileiras.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={onResolveUniverse}
            disabled={isResolving}
          >
            Resolver universo
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={onRunScreen}
            disabled={isScreening}
          >
            Rodar screener
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={onRunBacktest}
            disabled={isRunning}
          >
            Backtest único
          </button>
          <button type="button" className="btn-secondary" onClick={onRunBatch} disabled={isRunning}>
            Batch padrão
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={onRunResearchBatch}
            disabled={isRunning}
          >
            Batch de pesquisa
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">Preset</span>
          <select
            className="input-field"
            value={draft.presetId}
            onChange={(event) => updateDraft('presetId', event.target.value)}
          >
            {presets.map((preset) => (
              <option key={preset.preset_id} value={preset.preset_id}>
                {preset.label}
              </option>
            ))}
          </select>
          {selectedPreset && (
            <span className="mt-1 block text-xs text-gray-500 dark:text-gray-400">
              {selectedPreset.description}
            </span>
          )}
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">Inicio</span>
          <input
            className="input-field"
            type="date"
            value={draft.startDate}
            onChange={(event) => updateDraft('startDate', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">Fim</span>
          <input
            className="input-field"
            type="date"
            value={draft.endDate}
            onChange={(event) => updateDraft('endDate', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Snapshot Ibov
          </span>
          <input
            className="input-field"
            type="date"
            value={draft.asOfDate}
            onChange={(event) => updateDraft('asOfDate', event.target.value)}
          />
          <span className="mt-1 block text-xs text-gray-500 dark:text-gray-400">
            Para `ibov_historical`, vazio usa a data de início.
          </span>
        </label>

        <label className="block text-sm md:col-span-2 xl:col-span-3">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Tickers customizados
          </span>
          <input
            className="input-field"
            type="text"
            placeholder="PETR4, VALE3, ITUB4"
            value={draft.tickersText}
            onChange={(event) => updateDraft('tickersText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Formação
          </span>
          <input
            className="input-field"
            type="number"
            value={draft.formationWindowText}
            onChange={(event) => updateDraft('formationWindowText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">Teste</span>
          <input
            className="input-field"
            type="number"
            value={draft.testWindowText}
            onChange={(event) => updateDraft('testWindowText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">Step</span>
          <input
            className="input-field"
            type="number"
            value={draft.stepWindowText}
            onChange={(event) => updateDraft('stepWindowText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Max pares
          </span>
          <input
            className="input-field"
            type="number"
            value={draft.maxPairsText}
            onChange={(event) => updateDraft('maxPairsText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Top-N screener
          </span>
          <input
            className="input-field"
            type="number"
            value={draft.topNText}
            onChange={(event) => updateDraft('topNText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Retorno corr. min
          </span>
          <input
            className="input-field"
            type="number"
            step="0.01"
            value={draft.minReturnCorrText}
            onChange={(event) => updateDraft('minReturnCorrText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Level corr. min
          </span>
          <input
            className="input-field"
            type="number"
            step="0.01"
            value={draft.minLevelCorrText}
            onChange={(event) => updateDraft('minLevelCorrText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            p-value max
          </span>
          <input
            className="input-field"
            type="number"
            step="0.01"
            value={draft.maxCointPvalueText}
            onChange={(event) => updateDraft('maxCointPvalueText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Half-life min/max
          </span>
          <div className="grid grid-cols-2 gap-2">
            <input
              className="input-field"
              type="number"
              step="0.1"
              value={draft.minHalfLifeText}
              onChange={(event) => updateDraft('minHalfLifeText', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.1"
              value={draft.maxHalfLifeText}
              onChange={(event) => updateDraft('maxHalfLifeText', event.target.value)}
            />
          </div>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Estabilidade mín.
          </span>
          <input
            className="input-field"
            type="number"
            step="0.01"
            value={draft.minStabilityScoreText}
            onChange={(event) => updateDraft('minStabilityScoreText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Break risk máx.
          </span>
          <input
            className="input-field"
            type="number"
            step="0.01"
            value={draft.maxStructuralBreakRiskText}
            onChange={(event) => updateDraft('maxStructuralBreakRiskText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Beta abs min/max
          </span>
          <div className="grid grid-cols-2 gap-2">
            <input
              className="input-field"
              type="number"
              step="0.01"
              value={draft.minBetaAbsText}
              onChange={(event) => updateDraft('minBetaAbsText', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.01"
              value={draft.maxBetaAbsText}
              onChange={(event) => updateDraft('maxBetaAbsText', event.target.value)}
            />
          </div>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Entry / Exit / Stop
          </span>
          <div className="grid grid-cols-3 gap-2">
            <input
              className="input-field"
              type="number"
              step="0.1"
              value={draft.entryZscoreText}
              onChange={(event) => updateDraft('entryZscoreText', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.1"
              value={draft.exitZscoreText}
              onChange={(event) => updateDraft('exitZscoreText', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.1"
              value={draft.stopZscoreText}
              onChange={(event) => updateDraft('stopZscoreText', event.target.value)}
            />
          </div>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Capital inicial
          </span>
          <input
            className="input-field"
            type="number"
            value={draft.initialCapitalText}
            onChange={(event) => updateDraft('initialCapitalText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Alocação por par
          </span>
          <input
            className="input-field"
            type="number"
            step="0.01"
            value={draft.pairAllocationPctText}
            onChange={(event) => updateDraft('pairAllocationPctText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Construção de portfólio
          </span>
          <select
            className="input-field"
            value={draft.portfolioConstruction}
            onChange={(event) =>
              updateDraft(
                'portfolioConstruction',
                event.target.value as 'equal_notional' | 'risk_parity'
              )
            }
          >
            <option value="equal_notional">Equal notional</option>
            <option value="risk_parity">Risk parity</option>
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Vol alvo por par
          </span>
          <input
            className="input-field"
            type="number"
            step="0.01"
            value={draft.targetPairVolatilityText}
            onChange={(event) => updateDraft('targetPairVolatilityText', event.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Fee / Slippage / Borrow
          </span>
          <div className="grid grid-cols-3 gap-2">
            <input
              className="input-field"
              type="number"
              step="0.0001"
              value={draft.feeRateText}
              onChange={(event) => updateDraft('feeRateText', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.0001"
              value={draft.slippageText}
              onChange={(event) => updateDraft('slippageText', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.001"
              value={draft.shortBorrowRateText}
              onChange={(event) => updateDraft('shortBorrowRateText', event.target.value)}
            />
          </div>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Limite gross / net
          </span>
          <div className="grid grid-cols-2 gap-2">
            <input
              className="input-field"
              type="number"
              step="0.01"
              value={draft.maxGrossExposurePctText}
              onChange={(event) => updateDraft('maxGrossExposurePctText', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.01"
              value={draft.maxNetExposurePctText}
              onChange={(event) => updateDraft('maxNetExposurePctText', event.target.value)}
            />
          </div>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Máx. pares por setor
          </span>
          <input
            className="input-field"
            type="number"
            step="1"
            value={draft.maxSectorPairsText}
            onChange={(event) => updateDraft('maxSectorPairsText', event.target.value)}
          />
        </label>

        <label className="block text-sm md:col-span-2 xl:col-span-3">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Benchmarks
          </span>
          <input
            className="input-field"
            type="text"
            value={draft.benchmarkIdsText}
            onChange={(event) => updateDraft('benchmarkIdsText', event.target.value)}
          />
        </label>

        <label className="block text-sm md:col-span-2 xl:col-span-3">
          <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
            Snapshot de borrow
          </span>
          <input
            className="input-field"
            type="text"
            value={draft.borrowSnapshotPathText}
            onChange={(event) => updateDraft('borrowSnapshotPathText', event.target.value)}
            placeholder="data/borrow/b3_snapshot.csv"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
          <input
            type="checkbox"
            checked={draft.useProxyShortBorrow}
            onChange={(event) => updateDraft('useProxyShortBorrow', event.target.checked)}
          />
          Proxy de borrow
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
          <input
            type="checkbox"
            checked={draft.requireCointegration}
            onChange={(event) => updateDraft('requireCointegration', event.target.checked)}
          />
          Exigir cointegração
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
          <input
            type="checkbox"
            checked={draft.applyCashYield}
            onChange={(event) => updateDraft('applyCashYield', event.target.checked)}
          />
          Aplicar SELIC em caixa
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
          <input
            type="checkbox"
            checked={draft.explicitMarginModel}
            onChange={(event) => updateDraft('explicitMarginModel', event.target.checked)}
          />
          Modelo explícito de margem
        </label>
      </div>

      <div className="rounded-2xl border border-gray-200 px-4 py-4 dark:border-gray-800">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Batch de pesquisa
            </h3>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Gera cenários variando um parâmetro por vez, mais baseline, frictionless e sem filtro.
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
              Entry z list
            </span>
            <input
              className="input-field"
              type="text"
              value={draft.researchEntryZscoresText}
              onChange={(event) => updateDraft('researchEntryZscoresText', event.target.value)}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
              Exit z list
            </span>
            <input
              className="input-field"
              type="text"
              value={draft.researchExitZscoresText}
              onChange={(event) => updateDraft('researchExitZscoresText', event.target.value)}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
              Z-window list
            </span>
            <input
              className="input-field"
              type="text"
              value={draft.researchZscoreWindowsText}
              onChange={(event) => updateDraft('researchZscoreWindowsText', event.target.value)}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-gray-700 dark:text-gray-200">
              Max pairs list
            </span>
            <input
              className="input-field"
              type="text"
              value={draft.researchMaxPairsText}
              onChange={(event) => updateDraft('researchMaxPairsText', event.target.value)}
            />
          </label>
        </div>

        <label className="mt-4 flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
          <input
            type="checkbox"
            checked={draft.researchIncludeDynamicBeta}
            onChange={(event) => updateDraft('researchIncludeDynamicBeta', event.target.checked)}
          />
          Incluir cenário com beta dinâmico
        </label>
      </div>
    </div>
  );
}
