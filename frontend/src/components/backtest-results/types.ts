import React from 'react';
import { BacktestRequest, BacktestResponse, RunConfigSnapshot, RunDataProfile } from '../../types/api';
import { WarningItem } from '../WarningsPanel';

export interface BacktestResultsWorkspaceProps {
  activeTab: 'summary' | 'charts' | 'trades' | 'details';
  backtestRequest: BacktestRequest;
  backtestResponse: BacktestResponse;
  exportContainerRef: React.RefObject<HTMLDivElement>;
  isLoadingArtifacts: boolean;
  onCopyLink: () => void;
  onCopySummary: () => void;
  onDownloadCSV: (strategy: string) => void;
  onDownloadHTML: () => void;
  onDownloadPNG: () => void;
  onSaveProject: () => void;
  onSetActiveTab: (tab: 'summary' | 'charts' | 'trades' | 'details') => void;
  onShareResults: () => void;
  onToggleAllBenchmarks: (visible: boolean) => void;
  onToggleAllStrategies: (visible: boolean) => void;
  onToggleBenchmarkVisibility: (benchmark: string) => void;
  onToggleStrategyVisibility: (strategy: string) => void;
  runConfigSnapshot: RunConfigSnapshot | null;
  runDataProfile: RunDataProfile | null;
  strategyNames: string[];
  totalTradesCount: number;
  visibleBenchmarks: string[];
  visibleStrategies: string[];
  warnings: WarningItem[];
}

export interface ResultsSummaryHeroProps {
  backtestRequest: BacktestRequest;
  backtestResponse: BacktestResponse;
  totalTradesCount: number;
}

export interface ResultsTabsPanelProps {
  activeTab: 'summary' | 'charts' | 'trades' | 'details';
  backtestRequest: BacktestRequest;
  backtestResponse: BacktestResponse;
  isLoadingArtifacts: boolean;
  onCopyLink: () => void;
  onCopySummary: () => void;
  onDownloadCSV: (strategy: string) => void;
  onDownloadHTML: () => void;
  onDownloadPNG: () => void;
  onSaveProject: () => void;
  onShareResults: () => void;
  onToggleAllBenchmarks: (visible: boolean) => void;
  onToggleAllStrategies: (visible: boolean) => void;
  onToggleBenchmarkVisibility: (benchmark: string) => void;
  onToggleStrategyVisibility: (strategy: string) => void;
  runConfigSnapshot: RunConfigSnapshot | null;
  runDataProfile: RunDataProfile | null;
  strategyNames: string[];
  totalTradesCount: number;
  visibleStrategies: string[];
  visibleBenchmarks: string[];
  warnings: WarningItem[];
  onSetActiveTab: (tab: 'summary' | 'charts' | 'trades' | 'details') => void;
}

export interface ResultsOverviewTabProps {
  backtestResponse: BacktestResponse;
  visibleStrategies: string[];
  visibleBenchmarks: string[];
  mode?: 'summary' | 'charts';
}

export interface TradingHistoryTabProps {
  backtestResponse: BacktestResponse;
  totalTradesCount: number;
}

export interface ResultsDetailsTabProps {
  backtestRequest: BacktestRequest;
  backtestResponse: BacktestResponse;
  isLoadingArtifacts: boolean;
  onCopyLink: () => void;
  onCopySummary: () => void;
  onDownloadCSV: (strategy: string) => void;
  onDownloadHTML: () => void;
  onDownloadPNG: () => void;
  onSaveProject: () => void;
  onShareResults: () => void;
  onToggleAllBenchmarks: (visible: boolean) => void;
  onToggleAllStrategies: (visible: boolean) => void;
  onToggleBenchmarkVisibility: (benchmark: string) => void;
  onToggleStrategyVisibility: (strategy: string) => void;
  runConfigSnapshot: RunConfigSnapshot | null;
  runDataProfile: RunDataProfile | null;
  strategyNames: string[];
  visibleStrategies: string[];
  visibleBenchmarks: string[];
  warnings: WarningItem[];
}
