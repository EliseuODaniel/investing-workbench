import { Wallet } from 'lucide-react';
import type { InvestmentCompareRequestPayload } from '../../types/api';
import { formatCurrency } from '../../lib/utils';
import InvestmentDecisionProfileForm from './InvestmentDecisionProfileForm';

type InvestmentCompareRequestValue = InvestmentCompareRequestPayload[keyof InvestmentCompareRequestPayload];

interface InvestmentSetupScenarioTabProps {
  request: InvestmentCompareRequestPayload;
  investedTotal: number;
  hasFixedIncomeSelection: boolean;
  onDecisionProfileChange: (profile: InvestmentCompareRequestPayload['decision_profile']) => void;
  onRequestChange: (key: keyof InvestmentCompareRequestPayload, value: InvestmentCompareRequestValue) => void;
}

export default function InvestmentSetupScenarioTab({
  request,
  investedTotal,
  hasFixedIncomeSelection,
  onDecisionProfileChange,
  onRequestChange,
}: InvestmentSetupScenarioTabProps) {
  return (
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
            onChange={(event) => onRequestChange('initial_capital', Number(event.target.value) || 0)}
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
              onRequestChange('monthly_contribution', Number(event.target.value) || 0)
            }
          />
        </label>
        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">Data inicial</span>
          <input
            className="input-field"
            type="date"
            value={request.start_date ?? '2021-01-01'}
            onChange={(event) => onRequestChange('start_date', event.target.value)}
          />
        </label>
        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">Data final</span>
          <input
            className="input-field"
            type="date"
            value={request.end_date ?? ''}
            onChange={(event) => onRequestChange('end_date', event.target.value)}
          />
        </label>
      </div>
      <div className="mt-4 rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:bg-gray-800/70 dark:text-gray-300">
        Este comparador considera o mesmo fluxo de aportes em todas as alternativas. No recorte atual,
        o valor investido seria aproximadamente <strong>{formatCurrency(investedTotal)}</strong>.
      </div>

      <div className="mt-4">
        <InvestmentDecisionProfileForm
          profile={request.decision_profile}
          onChange={(profile) => onDecisionProfileChange(profile)}
        />
      </div>

      {hasFixedIncomeSelection ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
          <div className="text-sm font-semibold text-amber-900 dark:text-amber-100">
            Configuração extra para renda fixa
          </div>
          <p className="mt-2 text-sm text-amber-900/80 dark:text-amber-100/80">
            Este bloco só aparece quando a comparação inclui juros. É aqui que você decide se quer
            olhar índice teórico, produto real do Tesouro ou os dois juntos.
          </p>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <label className="space-y-2 text-sm">
              <span className="font-medium text-gray-700 dark:text-gray-200">Modo de estudo</span>
              <select
                className="input-field"
                value={request.fixed_income_study_mode ?? 'auto'}
                onChange={(event) => onRequestChange('fixed_income_study_mode', event.target.value)}
              >
                <option value="auto">Automático</option>
                <option value="index_duration">Índice por duration</option>
                <option value="retail_treasury">Tesouro Direto real</option>
                <option value="both">Mostrar os dois</option>
              </select>
            </label>
            <label className="space-y-2 text-sm">
              <span className="font-medium text-gray-700 dark:text-gray-200">Visão tributária</span>
              <select
                className="input-field"
                value={request.fixed_income_tax_treatment ?? 'gross'}
                onChange={(event) =>
                  onRequestChange('fixed_income_tax_treatment', event.target.value)
                }
              >
                <option value="gross">Bruta</option>
                <option value="net">Líquida estimada</option>
                <option value="both">Líquida com bruto visível</option>
              </select>
            </label>
            <label className="space-y-2 text-sm">
              <span className="font-medium text-gray-700 dark:text-gray-200">Janelas móveis</span>
              <select
                className="input-field"
                value={request.fixed_income_window_frequency ?? 'monthly'}
                onChange={(event) =>
                  onRequestChange('fixed_income_window_frequency', event.target.value)
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
  );
}
