import { MonteCarloDraft } from '../../lib/monteCarloPayload';
import { MonteCarloManifest, MonteCarloResultsPayload } from '../../types/api';

export interface MonteCarloWorkspaceProps {
  selectedConfigPath?: string;
  currentRunId?: string;
  defaultStrategies: string[];
  onError: (message: string | null) => void;
}

export interface MonteCarloWorkspaceHeaderProps {
  isLoadingExecutions: boolean;
  onRefresh: () => void;
}

export interface MonteCarloFormPanelProps {
  draft: MonteCarloDraft;
  currentRunId?: string;
  selectedConfigPath?: string;
  canSubmit: boolean;
  isExecuting: boolean;
  onUpdateDraft: <K extends keyof MonteCarloDraft>(
    key: K,
    value: MonteCarloDraft[K],
  ) => void;
  onRun: () => void;
}

export interface MonteCarloJobsPanelProps {
  executions: MonteCarloManifest[];
  selectedExecutionId: string | null;
  onLoadExecution: (executionId: string) => void;
}

export interface MonteCarloSummaryPanelProps {
  activeResults: MonteCarloResultsPayload | null;
  selectedManifest: MonteCarloManifest | null;
  isLoadingSelected: boolean;
}
