import { ChevronRight, Play } from 'lucide-react';
import { ReviewStepProps } from './types';

export default function ReviewStep({
  selectedConfig,
  backtestRequest,
  onRequestChange,
  onPrevious,
  onRunBacktest,
  canRun,
  isLoading,
}: ReviewStepProps) {
  const selectedStrategies = backtestRequest.strategies || [];
  const selectedBenchmarks = [
    ...(backtestRequest.include_buy_hold_benchmark !== false ? ['Buy & Hold'] : []),
    ...(backtestRequest.include_selic_benchmark ? ['SELIC'] : []),
    ...(backtestRequest.benchmarks || []),
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-4 dark:border-emerald-900/40 dark:bg-emerald-950/20">
        <div className="text-sm font-medium text-emerald-900 dark:text-emerald-100">
          Última checagem antes de executar
        </div>
        <div className="mt-1 text-xs text-emerald-700 dark:text-emerald-300">
          Revise o resumo. Os ajustes finos ficam recolhidos e só precisam ser mexidos se você souber o que quer testar.
        </div>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4">
          Resumo da Configuração
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
              Configuração
            </div>
            <div className="text-blue-900 dark:text-blue-100">
              {selectedConfig?.display_name || 'Nenhuma selecionada'}
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
              Estratégias ({selectedStrategies.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedStrategies.map((strategy) => (
                <span
                  key={strategy}
                  className="px-3 py-1 bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 text-xs font-medium rounded-full"
                >
                  {strategy}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
              Benchmarks ({selectedBenchmarks.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedBenchmarks.map((benchmark) => (
                <span
                  key={benchmark}
                  className="px-3 py-1 bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200 text-xs font-medium rounded-full"
                >
                  {benchmark}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
              Período
            </div>
            <div className="text-blue-900 dark:text-blue-100">
              {backtestRequest.start_date}{' '}
              {backtestRequest.end_date ? `até ${backtestRequest.end_date}` : 'até hoje'}
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
              Capital Inicial
            </div>
            <div className="text-blue-900 dark:text-blue-100">
              R${' '}
              {(backtestRequest.initial_capital || 0).toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
              })}
            </div>
          </div>

          {backtestRequest.apply_cash_yield && (
            <div>
              <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
                Rendimento do Caixa
              </div>
              <div className="text-blue-900 dark:text-blue-100">
                {backtestRequest.use_real_selic
                  ? 'SELIC real mensal (Banco Central)'
                  : `SELIC fixa de ${((backtestRequest.selic_rate_annual || 0.13) * 100).toFixed(1)}% ao ano`}
              </div>
            </div>
          )}
        </div>
      </div>

      <details className="border border-gray-200 dark:border-gray-700 rounded-lg">
        <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
          Ajustes finos da estratégia (opcional)
        </summary>
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 space-y-4">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Só mexa aqui se você quiser sobrescrever parâmetros do preset escolhido.
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Base Bet (%)
              </label>
              <input
                type="number"
                value={backtestRequest.base_bet || ''}
                onChange={(e) =>
                  onRequestChange({
                    base_bet: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                placeholder="1.0"
                className="form-input text-sm"
                disabled={isLoading}
                min="0.01"
                max="5"
                step="0.1"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Multiplicador
              </label>
              <input
                type="number"
                value={backtestRequest.multiplier || ''}
                onChange={(e) =>
                  onRequestChange({
                    multiplier: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                placeholder="2.0"
                className="form-input text-sm"
                disabled={isLoading}
                min="1.1"
                max="5"
                step="0.1"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Drop Step (%)
              </label>
              <input
                type="number"
                value={backtestRequest.drop_step || ''}
                onChange={(e) =>
                  onRequestChange({
                    drop_step: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                placeholder="5.0"
                className="form-input text-sm"
                disabled={isLoading}
                min="1"
                max="20"
                step="0.1"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Take Profit (%)
              </label>
              <input
                type="number"
                value={backtestRequest.take_profit || ''}
                onChange={(e) =>
                  onRequestChange({
                    take_profit: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                placeholder="3.0"
                className="form-input text-sm"
                disabled={isLoading}
                min="0.5"
                max="20"
                step="0.1"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              Max Layers
            </label>
            <input
              type="number"
              value={backtestRequest.max_layers || ''}
              onChange={(e) =>
                onRequestChange({
                  max_layers: e.target.value ? parseInt(e.target.value, 10) : undefined,
                })
              }
              placeholder="5"
              className="form-input text-sm"
              disabled={isLoading}
              min="1"
              max="20"
              step="1"
            />
          </div>
        </div>
      </details>

      <div className="flex justify-between">
        <button onClick={onPrevious} className="btn-secondary">
          <ChevronRight className="h-4 w-4 mr-2 rotate-180" />
          Anterior: Período e SELIC
        </button>
        <button
          onClick={onRunBacktest}
          disabled={isLoading || !canRun}
          className="btn-primary w-full py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3" />
              Executando Backtest...
            </>
          ) : (
            <>
              <Play className="h-5 w-5 mr-3" />
              Executar Backtest
            </>
          )}
        </button>
      </div>
    </div>
  );
}
