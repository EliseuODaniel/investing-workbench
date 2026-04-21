import { StepIndicatorProps } from './types';

const stepLabels = ['Configuração', 'Período e SELIC', 'Executar'] as const;

export default function BacktestFormStepIndicator({ currentStep }: StepIndicatorProps) {
  return (
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
        {stepLabels.map((label, index) => (
          <span
            key={label}
            className={`text-xs ${
              currentStep >= index + 1
                ? 'text-primary-600 dark:text-primary-400 font-medium'
                : 'text-gray-500'
            }`}
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
