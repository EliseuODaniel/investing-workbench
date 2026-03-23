import React, { useState } from 'react';
import { Play, Settings, TrendingUp, BarChart3, DollarSign, ChevronRight } from 'lucide-react';
import { ConfigInfo, BacktestRequest } from '../types/api';

interface BacktestFormProps {
  configs: ConfigInfo[];
  selectedConfig: ConfigInfo | null;
  backtestRequest: BacktestRequest;
  onConfigChange: (config: ConfigInfo) => void;
  onRequestChange: (updates: Partial<BacktestRequest>) => void;
  onRunBacktest: () => void;
  isLoading: boolean;
}

type Step = 1 | 2 | 3;

const BacktestForm: React.FC<BacktestFormProps> = ({
  configs,
  selectedConfig,
  backtestRequest,
  onConfigChange,
  onRequestChange,
  onRunBacktest,
  isLoading,
}) => {
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const nextStep = () => {
    setCurrentStep(prev => {
      if (prev >= 3) return prev;
      const next = (prev + 1) as Step;
      return next > 3 ? (3 as Step) : next;
    });
  };

  const prevStep = () => {
    setCurrentStep(prev => {
      if (prev <= 1) return prev;
      const next = (prev - 1) as Step;
      return next < 1 ? (1 as Step) : next;
    });
  };

  const canProceedToStep2 = () => {
    return selectedConfig && backtestRequest.strategies && backtestRequest.strategies.length > 0;
  };

  const canProceedToStep3 = () => {
    return canProceedToStep2() && backtestRequest.start_date && backtestRequest.initial_capital;
  };

  const StepIndicator = () => (
    <div className="mb-6">
      <div className="flex items-center justify-between">
        {[1, 2, 3].map((step) => (
          <div key={step} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                currentStep === step
                  ? 'bg-primary-600 text-white'
                  : currentStep > step
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
              }`}
            >
              {currentStep > step ? '✓' : step}
            </div>
            {step < 3 && (
              <div
                className={`w-12 h-1 mx-2 ${
                  currentStep > step ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
                }`}
              />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-between mt-2">
        <span className={`text-xs ${currentStep >= 1 ? 'text-primary-600 dark:text-primary-400 font-medium' : 'text-gray-500'}`}>
          Configuração
        </span>
        <span className={`text-xs ${currentStep >= 2 ? 'text-primary-600 dark:text-primary-400 font-medium' : 'text-gray-500'}`}>
          Período e SELIC
        </span>
        <span className={`text-xs ${currentStep >= 3 ? 'text-primary-600 dark:text-primary-400 font-medium' : 'text-gray-500'}`}>
          Executar
        </span>
      </div>
    </div>
  );

  const Step1Content = () => (
    <div className="space-y-6">
      {/* Config Selection */}
      <div>
        <label className="form-label mb-2 block flex items-center">
          <Settings className="h-4 w-4 mr-2" />
          Perfil de Configuração
        </label>
        <select
          value={selectedConfig?.name || ''}
          onChange={(e) => {
            const config = configs.find(c => c.name === e.target.value);
            if (config) onConfigChange(config);
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

      {/* Strategy Selection */}
      <div>
        <label className="form-label mb-3 block flex items-center">
          <BarChart3 className="h-4 w-4 mr-2" />
          Estratégias para Testar
        </label>
        {selectedConfig?.strategies && selectedConfig.strategies.length > 0 ? (
          <div className="grid grid-cols-1 gap-2">
            {selectedConfig.strategies.map((strategy) => (
              <label
                key={strategy}
                className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <input
                  type="checkbox"
                  checked={backtestRequest.strategies?.includes(strategy) || false}
                  onChange={(e) => {
                    const strategies = backtestRequest.strategies || [];
                    if (e.target.checked) {
                      onRequestChange({
                        strategies: [...strategies, strategy]
                      });
                    } else {
                      onRequestChange({
                        strategies: strategies.filter(s => s !== strategy)
                      });
                    }
                  }}
                  disabled={isLoading}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{strategy}</span>
                </div>
                {backtestRequest.strategies?.includes(strategy) && (
                  <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                )}
              </label>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Selecione uma configuração para ver as estratégias disponíveis
            </p>
          </div>
        )}
      </div>

      {/* Benchmarks */}
      <div>
        <label className="form-label mb-3 block flex items-center">
          <TrendingUp className="h-4 w-4 mr-2" />
          Benchmarks de Referência
        </label>

        <div className="space-y-3">
          {/* Buy & Hold Benchmark */}
          <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <input
              type="checkbox"
              checked={backtestRequest.include_buy_hold_benchmark !== false}
              onChange={(e) => onRequestChange({ include_buy_hold_benchmark: e.target.checked })}
              disabled={isLoading}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">Bitcoin Buy & Hold</div>
              <div className="text-xs text-gray-500">Manter Bitcoin como referência de mercado</div>
            </div>
          </label>

          {/* SELIC Benchmark */}
          <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <input
              type="checkbox"
              checked={backtestRequest.include_selic_benchmark || false}
              onChange={(e) => onRequestChange({ include_selic_benchmark: e.target.checked })}
              disabled={isLoading}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">SELIC (Renda Fixa)</div>
              <div className="text-xs text-gray-500">Renda fixa brasileira como comparação conservadora</div>
            </div>
          </label>

          {/* Market Benchmarks */}
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              Índices de Mercado
            </label>
            <input
              type="text"
              value={(backtestRequest.benchmarks || []).join(', ')}
              onChange={(e) => {
                const tickers = e.target.value
                  .split(',')
                  .map(t => t.trim().toUpperCase())
                  .filter(t => t.length > 0);
                onRequestChange({
                  benchmarks: tickers.length > 0 ? tickers : undefined
                });
              }}
              placeholder="^BVSP, SPY, ETH-USD"
              className="form-input text-sm"
              disabled={isLoading}
            />
            <div className="mt-2 flex flex-wrap gap-2">
              {['^BVSP', 'SPY', 'ETH-USD', 'QQQ'].map((ticker) => (
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
      </div>

      <div className="flex justify-end">
        <button
          onClick={nextStep}
          disabled={!canProceedToStep2()}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Próximo: Período e SELIC
          <ChevronRight className="h-4 w-4 ml-2" />
        </button>
      </div>
    </div>
  );

  const Step2Content = () => (
    <div className="space-y-6">
      {/* Date Range */}
      <div>
        <label className="form-label mb-3 block">Período do Backtest</label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Data Inicial</label>
            <input
              type="date"
              value={backtestRequest.start_date || ''}
              onChange={(e) => onRequestChange({ start_date: e.target.value || undefined })}
              className="form-input"
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Data Final</label>
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

      {/* Initial Capital */}
      <div>
        <label className="form-label mb-2 block flex items-center">
          <DollarSign className="h-4 w-4 mr-2" />
          Capital Inicial (BRL)
        </label>
        <input
          type="number"
          value={backtestRequest.initial_capital || ''}
          onChange={(e) => onRequestChange({
            initial_capital: e.target.value ? parseFloat(e.target.value) : undefined
          })}
          placeholder="30000"
          className="form-input"
          disabled={isLoading}
          min="1000"
          step="1000"
        />
      </div>

      {/* Cash Yield Configuration */}
      <div className="border-t pt-6">
        <label className="form-label mb-4 block flex items-center">
          <TrendingUp className="h-4 w-4 mr-2" />
          Configuração de Rendimento do Caixa
        </label>

        <div className="space-y-4">
          {/* Enable Cash Yield */}
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
              {/* SELIC Rate Type Selection */}
              <div className="space-y-3">
                <label className="flex items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg cursor-pointer">
                  <input
                    type="radio"
                    name="selic_type"
                    checked={!backtestRequest.use_real_selic}
                    onChange={() => {
                      onRequestChange({
                        use_real_selic: false,
                        selic_rate_annual: 0.13
                      });
                    }}
                    disabled={isLoading}
                    className="text-primary-600 focus:ring-primary-500 mr-3"
                  />
                  <div>
                    <div className="text-sm font-medium text-blue-900 dark:text-blue-100">Taxa SELIC fixa</div>
                    <div className="text-xs text-blue-700 dark:text-blue-300">Usar taxa anual fixa para todo o período</div>
                  </div>
                </label>

                <label className="flex items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg cursor-pointer">
                  <input
                    type="radio"
                    name="selic_type"
                    checked={backtestRequest.use_real_selic || false}
                    onChange={() => onRequestChange({ use_real_selic: true })}
                    disabled={isLoading}
                    className="text-primary-600 focus:ring-primary-500 mr-3"
                  />
                  <div>
                    <div className="text-sm font-medium text-green-900 dark:text-green-100">SELIC real mensal</div>
                    <div className="text-xs text-green-700 dark:text-green-300">Usar taxas reais do Banco Central mês a mês</div>
                  </div>
                </label>
              </div>

              {/* Fixed Rate Input */}
              {!backtestRequest.use_real_selic && (
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                    Taxa SELIC anual (%)
                  </label>
                  <input
                    type="number"
                    value={((backtestRequest.selic_rate_annual || 0.13) * 100).toString()}
                    onChange={(e) => {
                      const value = e.target.value ? parseFloat(e.target.value) / 100 : undefined;
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

              {/* Real SELIC Info */}
              {backtestRequest.use_real_selic && (
                <div className="bg-green-50 border border-green-200 rounded-md p-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-5 w-5 text-green-500 mt-0.5" />
                    </div>
                    <div className="ml-3">
                      <div className="text-sm font-medium text-green-900 dark:text-green-100">SELIC real ativado</div>
                      <div className="text-xs text-green-700 dark:text-green-300 mt-1">
                        <p>Serão usadas as taxas históricas reais mês a mês do Banco Central.</p>
                        <p className="mt-1">Taxa fallback: {((backtestRequest.selic_fallback_rate || 0.13) * 100).toFixed(1)}% ao ano</p>
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
        <button
          onClick={prevStep}
          className="btn-secondary"
        >
          <ChevronRight className="h-4 w-4 mr-2 rotate-180" />
          Anterior: Configuração
        </button>
        <button
          onClick={nextStep}
          disabled={!canProceedToStep3()}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Próximo: Executar
          <ChevronRight className="h-4 w-4 ml-2" />
        </button>
      </div>
    </div>
  );

  const Step3Content = () => {
    const selectedStrategies = backtestRequest.strategies || [];
    const selectedBenchmarks = [
      ...(backtestRequest.include_buy_hold_benchmark !== false ? ['Buy & Hold'] : []),
      ...(backtestRequest.include_selic_benchmark ? ['SELIC'] : []),
      ...(backtestRequest.benchmarks || [])
    ];

    return (
      <div className="space-y-6">
        {/* Summary */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4">Resumo da Configuração</h3>

          <div className="space-y-4">
            {/* Configuration */}
            <div>
              <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">Configuração</div>
              <div className="text-blue-900 dark:text-blue-100">
                {selectedConfig?.display_name || 'Nenhuma selecionada'}
              </div>
            </div>

            {/* Strategies */}
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

            {/* Benchmarks */}
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

            {/* Period */}
            <div>
              <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">Período</div>
              <div className="text-blue-900 dark:text-blue-100">
                {backtestRequest.start_date} {backtestRequest.end_date ? `até ${backtestRequest.end_date}` : 'até hoje'}
              </div>
            </div>

            {/* Capital */}
            <div>
              <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">Capital Inicial</div>
              <div className="text-blue-900 dark:text-blue-100">
                R$ {(backtestRequest.initial_capital || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>

            {/* Cash Yield */}
            {backtestRequest.apply_cash_yield && (
              <div>
                <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">Rendimento do Caixa</div>
                <div className="text-blue-900 dark:text-blue-100">
                  {backtestRequest.use_real_selic
                    ? 'SELIC real mensal (Banco Central)'
                    : `SELIC fixa de ${((backtestRequest.selic_rate_annual || 0.13) * 100).toFixed(1)}% ao ano`
                  }
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Advanced Options (Collapsible) */}
        <details className="border border-gray-200 dark:border-gray-700 rounded-lg">
          <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            Opções Avançadas de Estratégia
          </summary>
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                  Base Bet (%)
                </label>
                <input
                  type="number"
                  value={backtestRequest.base_bet || ''}
                  onChange={(e) => onRequestChange({
                    base_bet: e.target.value ? parseFloat(e.target.value) : undefined
                  })}
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
                  onChange={(e) => onRequestChange({
                    multiplier: e.target.value ? parseFloat(e.target.value) : undefined
                  })}
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
                  onChange={(e) => onRequestChange({
                    drop_step: e.target.value ? parseFloat(e.target.value) : undefined
                  })}
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
                  onChange={(e) => onRequestChange({
                    take_profit: e.target.value ? parseFloat(e.target.value) : undefined
                  })}
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
                onChange={(e) => onRequestChange({
                  max_layers: e.target.value ? parseInt(e.target.value) : undefined
                })}
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
          <button
            onClick={prevStep}
            className="btn-secondary"
          >
            <ChevronRight className="h-4 w-4 mr-2 rotate-180" />
            Anterior: Período e SELIC
          </button>
          <button
            onClick={onRunBacktest}
            disabled={isLoading || !canProceedToStep3()}
            className="btn-primary w-full py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
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
  };

  return (
    <div className="card">
      <div className="mb-6">
        <h2 className="text-xl font-semibold flex items-center">
          <Settings className="h-5 w-5 mr-2" />
          Configurar Backtest
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Configure em 3 passos simples a sua simulação de estratégias
        </p>
      </div>

      <StepIndicator />

      <div className="mt-6">
        {currentStep === 1 && <Step1Content />}
        {currentStep === 2 && <Step2Content />}
        {currentStep === 3 && <Step3Content />}
      </div>
    </div>
  );
};

export default BacktestForm;
