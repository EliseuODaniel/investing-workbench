// @ts-nocheck
import React from 'react';
import { AlertTriangle, Info, AlertCircle } from 'lucide-react';

interface WarningItem {
  type: 'warning' | 'info' | 'error';
  title: string;
  message: string;
  strategy?: string;
}

interface WarningsPanelProps {
  warnings: WarningItem[];
  onDismiss?: (index: number) => void;
}

const WarningsPanel: React.FC<WarningsPanelProps> = ({ warnings, onDismiss }) => {
  if (warnings.length === 0) return null;

  const getIcon = (type: WarningItem['type']) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getContainerClass = (type: WarningItem['type']) => {
    switch (type) {
      case 'error':
        return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20';
      case 'info':
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20';
    }
  };

  const getTextClass = (type: WarningItem['type']) => {
    switch (type) {
      case 'error':
        return 'text-red-800 dark:text-red-200';
      case 'warning':
        return 'text-yellow-800 dark:text-yellow-200';
      case 'info':
        return 'text-blue-800 dark:text-blue-200';
    }
  };

  return (
    <div className="space-y-3 mb-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center">
          <AlertTriangle className="h-4 w-4 mr-2" />
          Alertas e Informações ({warnings.length})
        </h3>
      </div>

      {warnings.map((warning, index) => (
        <div
          key={index}
          className={`border rounded-lg p-4 ${getContainerClass(warning.type)}`}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 mt-0.5">
              {getIcon(warning.type)}
            </div>
            <div className="ml-3 flex-1">
              <div className="flex items-center justify-between">
                <h4 className={`text-sm font-medium ${getTextClass(warning.type)}`}>
                  {warning.title}
                  {warning.strategy && (
                    <span className="ml-2 px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                      {warning.strategy}
                    </span>
                  )}
                </h4>
                {onDismiss && (
                  <button
                    onClick={() => onDismiss(index)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 ml-4"
                  >
                    ×
                  </button>
                )}
              </div>
              <p className={`text-sm mt-1 ${getTextClass(warning.type)} opacity-90`}>
                {warning.message}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Helper function to generate warnings from backtest response
export const generateWarnings = (backtestResponse: any, backtestRequest: any): WarningItem[] => {
  const warnings: WarningItem[] = [];

  // Check for strategies with no trades
  if (backtestResponse.results) {
    Object.entries(backtestResponse.results).forEach(([strategyName, strategyData]: [string, any]) => {
      if (!strategyData.trades || strategyData.trades.length === 0) {
        warnings.push({
          type: 'warning',
          title: 'Estratégia sem trades',
          message: 'Nenhuma operação foi executada durante o período. Verifique os parâmetros da estratégia ou o período selecionado.',
          strategy: strategyName,
        });
      }

      // Check for low hit rate
      if (strategyData.metrics && strategyData.metrics.hit_rate < 0.3) {
        warnings.push({
          type: 'warning',
          title: 'Baixa Taxa de Acerto',
          message: `Taxa de acerto de ${(strategyData.metrics.hit_rate * 100).toFixed(1)}%. Considere ajustar os parâmetros da estratégia.`,
          strategy: strategyName,
        });
      }

      // Check for extreme drawdown
      if (strategyData.metrics && strategyData.metrics.max_drawdown < -0.5) {
        warnings.push({
          type: 'error',
          title: 'Drawdown Extremo',
          message: `Drawdown máximo de ${(strategyData.metrics.max_drawdown * 100).toFixed(1)}%. Esta estratégia apresentou alta volatilidade e risco.`,
          strategy: strategyName,
        });
      }
    });
  }

  // Check for benchmark data issues
  if (backtestRequest.benchmarks && backtestRequest.benchmarks.length > 0) {
    if (!backtestResponse.benchmarks || Object.keys(backtestResponse.benchmarks).length === 0) {
      warnings.push({
        type: 'error',
        title: 'Dados de Benchmarks Indisponíveis',
        message: 'Não foi possível obter dados para os benchmarks selecionados. Verifique a conexão com a internet ou os tickers informados.',
      });
    }
  }

  // SELIC warnings
  if (backtestRequest.apply_cash_yield && backtestRequest.use_real_selic) {
    const firstResult = Object.values(backtestResponse.results)[0] as any;
    if (firstResult && firstResult.metrics) {
      const selicRatesUsed = firstResult.metrics.selic_rates_used;
      if (!selicRatesUsed || selicRatesUsed.length === 0) {
        warnings.push({
          type: 'warning',
          title: 'Dados SELIC Não Utilizados',
          message: 'SELIC real foi configurada mas não foi possível obter os dados. Foi utilizada a taxa fallback.',
        });
      }
    }
  }

  // Period warnings
  if (backtestResponse.data_info) {
    const totalDays = backtestResponse.data_info.total_days;
    if (totalDays < 30) {
      warnings.push({
        type: 'info',
        title: 'Período Curto',
        message: `O backtest foi executado com apenas ${totalDays} dias. Resultados podem não ser estatisticamente significativos.`,
      });
    }
  }

  // Capital warnings
  if (backtestRequest.initial_capital && backtestRequest.initial_capital < 5000) {
    warnings.push({
      type: 'info',
      title: 'Capital Reduzido',
      message: 'Capital inicial baixo pode limitar a eficácia de estratégias com múltiplas posições.',
    });
  }

  return warnings;
};

export default WarningsPanel;
