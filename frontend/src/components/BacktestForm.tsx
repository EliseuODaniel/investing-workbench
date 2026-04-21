import { useState } from 'react';
import { Settings } from 'lucide-react';
import BacktestFormStepIndicator from './backtest-form/BacktestFormStepIndicator';
import ConfigurationStep from './backtest-form/ConfigurationStep';
import PeriodStep from './backtest-form/PeriodStep';
import ReviewStep from './backtest-form/ReviewStep';
import { BacktestFormProps, Step } from './backtest-form/types';

export default function BacktestForm({
  configs,
  selectedConfig,
  backtestRequest,
  onConfigChange,
  onRequestChange,
  onRunBacktest,
  isLoading,
}: BacktestFormProps) {
  const [currentStep, setCurrentStep] = useState<Step>(1);

  const nextStep = () => {
    setCurrentStep((current) => (current >= 3 ? current : ((current + 1) as Step)));
  };

  const previousStep = () => {
    setCurrentStep((current) => (current <= 1 ? current : ((current - 1) as Step)));
  };

  const canProceedToStep2 = Boolean(
    selectedConfig && backtestRequest.strategies && backtestRequest.strategies.length > 0,
  );
  const canProceedToStep3 = Boolean(
    canProceedToStep2 && backtestRequest.start_date && backtestRequest.initial_capital,
  );

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

      <BacktestFormStepIndicator currentStep={currentStep} />

      <div className="mt-6">
        {currentStep === 1 && (
          <ConfigurationStep
            configs={configs}
            selectedConfig={selectedConfig}
            backtestRequest={backtestRequest}
            onConfigChange={onConfigChange}
            onRequestChange={onRequestChange}
            onNext={nextStep}
            canProceed={canProceedToStep2}
            isLoading={isLoading}
          />
        )}

        {currentStep === 2 && (
          <PeriodStep
            backtestRequest={backtestRequest}
            onRequestChange={onRequestChange}
            onNext={nextStep}
            onPrevious={previousStep}
            canProceed={canProceedToStep3}
            isLoading={isLoading}
          />
        )}

        {currentStep === 3 && (
          <ReviewStep
            selectedConfig={selectedConfig}
            backtestRequest={backtestRequest}
            onRequestChange={onRequestChange}
            onPrevious={previousStep}
            onRunBacktest={onRunBacktest}
            canRun={canProceedToStep3}
            isLoading={isLoading}
          />
        )}
      </div>
    </div>
  );
}
