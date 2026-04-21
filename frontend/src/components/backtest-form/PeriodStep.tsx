import { ChevronRight, DollarSign, TrendingUp } from 'lucide-react';
import { PeriodStepProps } from './types';

export default function PeriodStep({
  backtestRequest,
  onRequestChange,
  onNext,
  onPrevious,
  canProceed,
  isLoading,
}: PeriodStepProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-4 dark:border-gray-700 dark:bg-gray-900/40">
        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
          Preencha só o essencial para continuar
        </div>
        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Nesta etapa, o mínimo é definir a data inicial e o capital. O rendimento do caixa é opcional.
        </div>
      </div>

      <div>
        <label className="form-label mb-3 block">Período do Backtest</label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">
              Data Inicial
            </label>
            <input
              type="date"
              value={backtestRequest.start_date || ''}
              onChange={(e) => onRequestChange({ start_date: e.target.value || undefined })}
              className="form-input"
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">
              Data Final
            </label>
            <input
              type="date"
              value={backtestRequest.end_date || ''}
              onChange={(e) => onRequestChange({ end_date: e.target.value || undefined })}
              className="form-input"
              disabled={isLoading}
            />
          </div>
        </div>
      </div>

      <div>
        <label className="form-label mb-2 block flex items-center">
          <DollarSign className="h-4 w-4 mr-2" />
          Capital Inicial (BRL)
        </label>
        <input
          type="number"
          value={backtestRequest.initial_capital || ''}
          onChange={(e) =>
            onRequestChange({
              initial_capital: e.target.value ? parseFloat(e.target.value) : undefined,
            })
          }
          placeholder="30000"
          className="form-input"
          disabled={isLoading}
          min="1000"
          step="1000"
        />
        <div className="mt-2 flex flex-wrap gap-2">
          {[10000, 30000, 50000].map((capital) => (
            <button
              key={capital}
              type="button"
              onClick={() => onRequestChange({ initial_capital: capital })}
              className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              R$ {capital.toLocaleString('pt-BR')}
            </button>
          ))}
        </div>
      </div>

      <div className="border-t pt-6">
        <label className="form-label mb-4 block flex items-center">
          <TrendingUp className="h-4 w-4 mr-2" />
          Configuração de Rendimento do Caixa
        </label>

        <div className="space-y-4">
          <label className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <input
              type="checkbox"
              checked={backtestRequest.apply_cash_yield || false}
              onChange={(e) => {
                onRequestChange({ apply_cash_yield: e.target.checked });
                if (!e.target.checked) {
                  onRequestChange({ use_real_selic: false });
                }
              }}
              disabled={isLoading}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Aplicar rendimento SELIC ao caixa não investido
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Rende automaticamente sobre o capital ocioso durante a estratégia
              </div>
            </div>
          </label>

          {backtestRequest.apply_cash_yield && (
            <div className="space-y-4 pl-6 border-l-2 border-primary-200 dark:border-primary-800">
              <div className="space-y-3">
                <label className="flex items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg cursor-pointer">
                  <input
                    type="radio"
                    name="selic_type"
                    checked={!backtestRequest.use_real_selic}
                    onChange={() => {
                      onRequestChange({
                        use_real_selic: false,
                        selic_rate_annual: 0.13,
                      });
                    }}
                    disabled={isLoading}
                    className="text-primary-600 focus:ring-primary-500 mr-3"
                  />
                  <div>
                    <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                      Taxa SELIC fixa
                    </div>
                    <div className="text-xs text-blue-700 dark:text-blue-300">
                      Usar taxa anual fixa para todo o período
                    </div>
                  </div>
                </label>

                <label className="flex items-center rounded-lg border border-green-200 bg-green-50 p-3 cursor-pointer dark:border-green-800/60 dark:bg-green-950/30">
                  <input
                    type="radio"
                    name="selic_type"
                    checked={backtestRequest.use_real_selic || false}
                    onChange={() => onRequestChange({ use_real_selic: true })}
                    disabled={isLoading}
                    className="text-primary-600 focus:ring-primary-500 mr-3"
                  />
                  <div>
                    <div className="text-sm font-medium text-green-900 dark:text-green-100">
                      SELIC real mensal
                    </div>
                    <div className="text-xs text-green-700 dark:text-green-200">
                      Usar taxas reais do Banco Central mês a mês
                    </div>
                  </div>
                </label>
              </div>

              {!backtestRequest.use_real_selic && (
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                    Taxa SELIC anual (%)
                  </label>
                  <input
                    type="number"
                    value={((backtestRequest.selic_rate_annual || 0.13) * 100).toString()}
                    onChange={(e) => {
                      const value = e.target.value
                        ? parseFloat(e.target.value) / 100
                        : undefined;
                      onRequestChange({ selic_rate_annual: value });
                    }}
                    placeholder="13.0"
                    className="form-input"
                    disabled={isLoading}
                    min="0"
                    max="50"
                    step="0.1"
                  />
                </div>
              )}

              {backtestRequest.use_real_selic && (
                <div className="rounded-md border border-green-200 bg-green-50 p-4 dark:border-green-800/60 dark:bg-green-950/35">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <TrendingUp className="mt-0.5 h-5 w-5 text-green-600 dark:text-green-300" />
                    </div>
                    <div className="ml-3">
                      <div className="text-sm font-medium text-green-900 dark:text-green-100">
                        SELIC real ativado
                      </div>
                      <div className="mt-1 text-xs text-green-700 dark:text-green-200">
                        <p>Serão usadas as taxas históricas reais mês a mês do Banco Central.</p>
                        <p className="mt-1">
                          Taxa fallback:{' '}
                          {((backtestRequest.selic_fallback_rate || 0.13) * 100).toFixed(1)}% ao
                          ano
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between">
        <button onClick={onPrevious} className="btn-secondary">
          <ChevronRight className="h-4 w-4 mr-2 rotate-180" />
          Anterior: Configuração
        </button>
        <button
          onClick={onNext}
          disabled={!canProceed}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Próximo: Executar
          <ChevronRight className="h-4 w-4 ml-2" />
        </button>
      </div>
    </div>
  );
}
