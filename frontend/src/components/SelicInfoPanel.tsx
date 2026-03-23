import React from 'react';
import { TrendingUp, DollarSign, Info, FileText, AlertTriangle } from 'lucide-react';

interface SelicInfoPanelProps {
  useRealSelic?: boolean;
  selicRateAnnual?: number;
  selicFallbackRate?: number;
  selicRatesUsed?: Array<{ year: number; month: number; rate: number }>;
  totalInterestEarned?: number;
  selicPath?: string;
  capital?: number;
}

const SelicInfoPanel: React.FC<SelicInfoPanelProps> = ({
  useRealSelic,
  selicRateAnnual = 0.13,
  selicFallbackRate = 0.13,
  selicRatesUsed,
  totalInterestEarned = 0,
  selicPath,
  capital = 30000,
}) => {
  const getUniqueMonths = () => {
    if (!selicRatesUsed) return 0;
    const uniqueMonths = new Set(selicRatesUsed.map(rate => `${rate.year}-${rate.month}`));
    return uniqueMonths.size;
  };

  const getAverageRate = () => {
    if (!selicRatesUsed || selicRatesUsed.length === 0) return 0;
    return selicRatesUsed.reduce((sum, rate) => sum + rate.rate, 0) / selicRatesUsed.length;
  };

  const getYearRange = () => {
    if (!selicRatesUsed || selicRatesUsed.length === 0) return null;
    const years = selicRatesUsed.map(rate => rate.year);
    const minYear = Math.min(...years);
    const maxYear = Math.max(...years);
    return minYear === maxYear ? `${minYear}` : `${minYear}-${maxYear}`;
  };

  return (
    <div className="card bg-gradient-to-r from-emerald-50 to-teal-100 dark:from-emerald-900/20 dark:to-teal-900/20 border-emerald-200 dark:border-emerald-800">
      <div className="flex items-center mb-4">
        <div className="w-8 h-8 bg-emerald-100 dark:bg-emerald-800 rounded-full flex items-center justify-center mr-3">
          <TrendingUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
        </div>
        <h3 className="text-lg font-semibold text-emerald-900 dark:text-emerald-100">
          Painel SELIC
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Mode */}
        <div>
          <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium mb-1">Modo</div>
          <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              useRealSelic ? 'bg-green-500' : 'bg-blue-500'
            }`}></div>
            <span className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">
              {useRealSelic ? 'SELIC Real' : 'SELIC Fixa'}
            </span>
          </div>
        </div>

        {/* Rate */}
        <div>
          <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium mb-1">Taxa Aplicada</div>
          <div className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">
            {useRealSelic
              ? `${(getAverageRate() * 100).toFixed(3)}% mensal`
              : `${(selicRateAnnual * 100).toFixed(1)}% anual`
            }
          </div>
        </div>

        {/* Interest Earned */}
        <div>
          <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium mb-1">Rendimento Gerado</div>
          <div className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">
            R$ {totalInterestEarned.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-emerald-700 dark:text-emerald-300">
            {((totalInterestEarned / capital) * 100).toFixed(2)}% do capital
          </div>
        </div>

        {/* Coverage */}
        {useRealSelic && (
          <div>
            <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium mb-1">Cobertura</div>
            <div className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">
              {getUniqueMonths()} meses
            </div>
            <div className="text-xs text-emerald-700 dark:text-emerald-300">
              {getYearRange() || 'N/A'}
            </div>
          </div>
        )}
      </div>

      {/* Details Section */}
      <div className="space-y-4">
        {/* Mode Description */}
        <div className={`p-3 rounded-lg ${
          useRealSelic
            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700'
            : 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700'
        }`}>
          <div className="flex items-start">
            <Info className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0 text-emerald-600 dark:text-emerald-400" />
            <div>
              <h4 className="text-sm font-medium text-emerald-900 dark:text-emerald-100 mb-1">
                {useRealSelic ? 'SELIC Real Mensal' : 'SELIC Fixa Anual'}
              </h4>
              <p className="text-xs text-emerald-700 dark:text-emerald-300">
                {useRealSelic
                  ? 'Taxas históricas reais mês a mês do Banco Central do Brasil, refletindo a política monetária real de cada período.'
                  : `Taxa fixa de ${(selicRateAnnual * 100).toFixed(1)}% ao ano aplicada mensalmente sobre o capital ocioso.`
                }
              </p>
            </div>
          </div>
        </div>

        {/* Real SELIC Details */}
        {useRealSelic && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* File Info */}
            {selicPath && (
              <div className="flex items-start p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <FileText className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0 text-gray-500" />
                <div>
                  <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300">Arquivo de Dados</h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {selicPath === 'data/selic.csv' ? 'Padrão' : selicPath}
                  </p>
                </div>
              </div>
            )}

            {/* Fallback Rate */}
            <div className="flex items-start p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <AlertTriangle className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0 text-gray-500" />
              <div>
                <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300">Taxa Fallback</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {(selicFallbackRate * 100).toFixed(1)}% ao ano (para dados faltantes)
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Monthly Rates Preview */}
        {useRealSelic && selicRatesUsed && selicRatesUsed.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Amostra de Taxas Mensais</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {selicRatesUsed.slice(0, 12).map((rate, index) => (
                <div key={index} className="text-xs bg-gray-50 dark:bg-gray-800 p-2 rounded text-center">
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {rate.rate.toFixed(4)}%
                  </div>
                  <div className="text-gray-500">
                    {rate.month.toString().padStart(2, '0')}/{rate.year.toString().slice(2)}
                  </div>
                </div>
              ))}
              {selicRatesUsed.length > 12 && (
                <div className="text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded text-center text-gray-500">
                  +{selicRatesUsed.length - 12} mais...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Performance Impact */}
        <div className="border-t pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center text-xs text-gray-600 dark:text-gray-400">
              <DollarSign className="h-3 w-3 mr-1" />
              Impacto no capital total
            </div>
            <div className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">
              {((totalInterestEarned / capital) * 100).toFixed(2)}%
            </div>
          </div>
          {totalInterestEarned > 0 && (
            <div className="mt-2 bg-green-50 dark:bg-green-900/20 p-2 rounded">
              <p className="text-xs text-green-700 dark:text-green-300">
                O rendimento SELIC gerou R$ {totalInterestEarned.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                {' '}adicionais ao resultado da estratégia.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SelicInfoPanel;