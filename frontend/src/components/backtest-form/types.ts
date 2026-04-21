import { BacktestRequest, ConfigInfo } from '../../types/api';

export type Step = 1 | 2 | 3;

export interface BacktestFormProps {
  configs: ConfigInfo[];
  selectedConfig: ConfigInfo | null;
  backtestRequest: BacktestRequest;
  onConfigChange: (config: ConfigInfo) => void;
  onRequestChange: (updates: Partial<BacktestRequest>) => void;
  onRunBacktest: () => void;
  isLoading: boolean;
}

export interface StepIndicatorProps {
  currentStep: Step;
}

export interface ConfigurationStepProps {
  configs: ConfigInfo[];
  selectedConfig: ConfigInfo | null;
  backtestRequest: BacktestRequest;
  onConfigChange: (config: ConfigInfo) => void;
  onRequestChange: (updates: Partial<BacktestRequest>) => void;
  onNext: () => void;
  canProceed: boolean;
  isLoading: boolean;
}

export interface PeriodStepProps {
  backtestRequest: BacktestRequest;
  onRequestChange: (updates: Partial<BacktestRequest>) => void;
  onNext: () => void;
  onPrevious: () => void;
  canProceed: boolean;
  isLoading: boolean;
}

export interface ReviewStepProps {
  selectedConfig: ConfigInfo | null;
  backtestRequest: BacktestRequest;
  onRequestChange: (updates: Partial<BacktestRequest>) => void;
  onPrevious: () => void;
  onRunBacktest: () => void;
  canRun: boolean;
  isLoading: boolean;
}
