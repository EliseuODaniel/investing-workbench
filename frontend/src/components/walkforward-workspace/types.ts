import { WalkForwardDraft } from '../../lib/walkForwardPayload';
import { WalkForwardManifest, WalkForwardResultsPayload } from '../../types/api';

export interface WalkForwardWorkspaceProps {
  selectedConfigPath?: string;
  defaultStrategies: string[];
  onError: (message: string | null) => void;
}

export interface WalkForwardWorkspaceHeaderProps {
  isLoadingExecutions: boolean;
  onRefresh: () => void;
}

export interface WalkForwardFormPanelProps {
  draft: WalkForwardDraft;
  canSubmit: boolean;
  isExecuting: boolean;
  onUpdateDraft: <K extends keyof WalkForwardDraft>(
    key: K,
    value: WalkForwardDraft[K],
  ) => void;
  onRun: () => void;
}

export interface WalkForwardJobsPanelProps {
  executions: WalkForwardManifest[];
  selectedExecutionId: string | null;
  onLoadExecution: (executionId: string) => void;
}

export interface WalkForwardSummaryPanelProps {
  activeResults: WalkForwardResultsPayload | null;
  selectedManifest: WalkForwardManifest | null;
  isLoadingSelected: boolean;
}
