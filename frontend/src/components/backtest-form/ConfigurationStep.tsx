import { useMemo, useState } from 'react';
import { BarChart3, BookOpen, ChevronRight, Info, Settings, TrendingUp } from 'lucide-react';
import { getStrategyGuide } from '../../lib/strategyGuide';
import { ConfigurationStepProps } from './types';

const quickBenchmarks = ['^BVSP', 'SPY', 'ETH-USD', 'QQQ'];

export default function ConfigurationStep({
  configs,
  selectedConfig,
  backtestRequest,
  onConfigChange,
  onRequestChange,
  onNext,
  canProceed,
  isLoading,
}: ConfigurationStepProps) {
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  const [showGlossary, setShowGlossary] = useState(false);
  const [showBenchmarks, setShowBenchmarks] = useState(false);
  const glossaryEntries = useMemo(
    () => (selectedConfig?.strategies ?? []).map((strategy) => [strategy, getStrategyGuide(strategy)] as const),
    [selectedConfig?.strategies],
  );
  const selectedBenchmarkCount =
    (backtestRequest.include_buy_hold_benchmark !== false ? 1 : 0) +
    (backtestRequest.include_selic_benchmark ? 1 : 0) +
    (backtestRequest.benchmarks?.length ?? 0);

  return (
    <div className="space-y-6">
      <div>
        <label className="form-label mb-2 block flex items-center">
          <Settings className="h-4 w-4 mr-2" />
          Perfil de Configuração
        </label>
        <select
          value={selectedConfig?.name || ''}
          onChange={(e) => {
            const config = configs.find((item) => item.name === e.target.value);
            if (config) {
              onConfigChange(config);
            }
          }}
          className="form-input"
          disabled={isLoading}
        >
          <option value="">Selecione uma configuração</option>
          {configs.map((config) => (
            <option key={config.name} value={config.name}>
              {config.display_name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="form-label mb-3 block flex items-center">
          <BarChart3 className="h-4 w-4 mr-2" />
          Estratégias para Testar
        </label>
        <div className="mb-3 flex items-center justify-between gap-3 rounded-lg border border-sky-200 bg-sky-50 px-3 py-3 dark:border-sky-900/50 dark:bg-sky-950/20">
          <div className="text-xs text-sky-800 dark:text-sky-200">
            Escolha as estratégias com menos chute. Use o <span className="font-semibold">(i)</span>{' '}
            em cada linha ou abra o dicionário rápido.
          </div>
          <button
            type="button"
            onClick={() => setShowGlossary((current) => !current)}
            className="shrink-0 rounded-full border border-sky-300 bg-white px-3 py-1.5 text-xs font-medium text-sky-800 transition-colors hover:bg-sky-100 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-200 dark:hover:bg-sky-900/40"
          >
            <BookOpen className="mr-1 inline h-3 w-3" />
            {showGlossary ? 'Fechar dicionário' : 'Abrir dicionário rápido'}
          </button>
        </div>
        {selectedConfig?.strategies && selectedConfig.strategies.length > 0 ? (
          <div className="space-y-2">
            {selectedConfig.strategies.map((strategy) => {
              const guide = getStrategyGuide(strategy);
              const isSelected = backtestRequest.strategies?.includes(strategy) || false;
              const isExpanded = expandedStrategy === strategy;

              return (
                <div
                  key={strategy}
                  className="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900/40"
                >
                  <div className="flex items-start gap-3 p-3">
                    <label className="flex flex-1 cursor-pointer items-start">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => {
                          const strategies = backtestRequest.strategies || [];
                          onRequestChange({
                            strategies: e.target.checked
                              ? [...strategies, strategy]
                              : strategies.filter((item) => item !== strategy),
                          });
                        }}
                        disabled={isLoading}
                        className="mt-0.5 rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {strategy}
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                            {guide.category}
                          </span>
                          <span className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
                            Risco {guide.risk}
                          </span>
                        </div>
                      </div>
                    </label>

                    <button
                      type="button"
                      onClick={() =>
                        setExpandedStrategy((current) => (current === strategy ? null : strategy))
                      }
                      className="rounded-full border border-gray-200 p-2 text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-900 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
                      aria-label={`Info sobre ${strategy}`}
                    >
                      <Info className="h-4 w-4" />
                    </button>

                    {isSelected && <div className="mt-2 h-2 w-2 rounded-full bg-primary-600" />}
                  </div>

                  {isExpanded && (
                    <div className="border-t border-gray-200 px-4 py-3 text-sm dark:border-gray-700">
                      <div className="text-gray-800 dark:text-gray-200">{guide.summary}</div>
                      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        Melhor para: {guide.bestFor}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Selecione uma configuração para ver as estratégias disponíveis
            </p>
          </div>
        )}

        {showGlossary && glossaryEntries.length > 0 && (
          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/40">
            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Dicionário rápido das estratégias deste preset
            </div>
            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Escolha a estratégia pelo comportamento esperado, não só pelo nome.
            </div>
            <div className="mt-4 grid grid-cols-1 gap-3">
              {glossaryEntries.map(([strategy, guide]) => (
                <div
                  key={strategy}
                  className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {strategy}
                    </div>
                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                      {guide.category}
                    </span>
                    <span className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
                      Risco {guide.risk}
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                    {guide.summary}
                  </div>
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Melhor para: {guide.bestFor}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div>
        <label className="form-label mb-3 block flex items-center">
          <TrendingUp className="h-4 w-4 mr-2" />
          Referências de comparação
        </label>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/40">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Comparar com benchmarks é opcional
              </div>
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Hoje: {selectedBenchmarkCount} referências ativas.
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowBenchmarks((current) => !current)}
              className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
            >
              {showBenchmarks ? 'Fechar referências' : 'Comparar com referências'}
            </button>
          </div>

          {showBenchmarks && (
            <div className="mt-4 space-y-3">
              <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <input
                  type="checkbox"
                  checked={backtestRequest.include_buy_hold_benchmark !== false}
                  onChange={(e) => onRequestChange({ include_buy_hold_benchmark: e.target.checked })}
                  disabled={isLoading}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Bitcoin Buy & Hold
                  </div>
                  <div className="text-xs text-gray-500">
                    Linha de base mais simples para saber se a estratégia supera só segurar BTC.
                  </div>
                </div>
              </label>

              <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <input
                  type="checkbox"
                  checked={backtestRequest.include_selic_benchmark || false}
                  onChange={(e) => onRequestChange({ include_selic_benchmark: e.target.checked })}
                  disabled={isLoading}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    SELIC (Renda Fixa)
                  </div>
                  <div className="text-xs text-gray-500">
                    Referência conservadora para comparar contra uma alternativa de baixo risco.
                  </div>
                </div>
              </label>

              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                  Índices ou ativos extras
                </label>
                <input
                  type="text"
                  value={(backtestRequest.benchmarks || []).join(', ')}
                  onChange={(e) => {
                    const tickers = e.target.value
                      .split(',')
                      .map((ticker) => ticker.trim().toUpperCase())
                      .filter((ticker) => ticker.length > 0);
                    onRequestChange({
                      benchmarks: tickers.length > 0 ? tickers : undefined,
                    });
                  }}
                  placeholder="^BVSP, SPY, ETH-USD"
                  className="form-input text-sm"
                  disabled={isLoading}
                />
                <div className="mt-2 flex flex-wrap gap-2">
                  {quickBenchmarks.map((ticker) => (
                    <button
                      key={ticker}
                      type="button"
                      onClick={() => {
                        const currentBenchmarks = backtestRequest.benchmarks || [];
                        if (!currentBenchmarks.includes(ticker)) {
                          onRequestChange({ benchmarks: [...currentBenchmarks, ticker] });
                        }
                      }}
                      className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                      disabled={isLoading}
                    >
                      + {ticker}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={onNext}
          disabled={!canProceed}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Próximo: Período e SELIC
          <ChevronRight className="h-4 w-4 ml-2" />
        </button>
      </div>
    </div>
  );
}
