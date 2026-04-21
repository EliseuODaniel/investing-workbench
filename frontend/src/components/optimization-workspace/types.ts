import {
  OptimizationDraft,
} from '../../lib/optimizationPayload';
import {
  OptimizationManifest,
  OptimizationPlan,
  OptimizationResultsPayload,
} from '../../types/api';

export interface OptimizationWorkspaceProps {
  selectedConfigPath?: string;
  defaultStrategies: string[];
  onError: (message: string | null) => void;
}

export interface OptimizationWorkspaceHeaderProps {
  isLoadingOptimizations: boolean;
  onRefresh: () => void;
}

export interface OptimizationFormPanelProps {
  draft: OptimizationDraft;
  canSubmit: boolean;
  isPlanning: boolean;
  isExecuting: boolean;
  onUpdateDraft: <K extends keyof OptimizationDraft>(
    key: K,
    value: OptimizationDraft[K],
  ) => void;
  onPreviewPlan: () => void;
  onRunOptimization: () => void;
}

export interface OptimizationPlanPreviewProps {
  plan: OptimizationPlan | null;
}

export interface OptimizationJobsPanelProps {
  optimizations: OptimizationManifest[];
  selectedOptimizationId: string | null;
  isLoadingOptimizations: boolean;
  onLoadOptimization: (optimizationId: string) => void;
}

export interface OptimizationResultsPanelProps {
  latestExecution: OptimizationResultsPayload | null;
  selectedResults: OptimizationResultsPayload | null;
  selectedManifest: OptimizationManifest | null;
  isLoadingSelected: boolean;
}
