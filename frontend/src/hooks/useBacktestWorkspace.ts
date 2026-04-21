import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type RefObject,
  type SetStateAction,
} from 'react';
import { apiClient } from '../lib/api';
import { downloadNodeAsPng } from '../lib/exportImage';
import { downloadJSON, formatPercent } from '../lib/utils';
import { generateWarnings, type WarningItem } from '../components/WarningsPanel';
import {
  BacktestRequest,
  BacktestResponse,
  ConfigInfo,
  RunConfigSnapshot,
  RunDataProfile,
} from '../types/api';
import {
  deriveSuccessfulWorkspaceState,
  deriveVisibleBenchmarks,
  deriveVisibleStrategies,
  type BacktestWorkspaceAppState,
} from './backtestWorkspaceState';

interface RunArtifactsLoaderResult {
  configSnapshot: RunConfigSnapshot | null;
  dataProfile: RunDataProfile | null;
}

interface UseBacktestWorkspaceOptions {
  backtestRequest: BacktestRequest;
  selectedConfig: ConfigInfo | null;
  refreshRuns: () => void;
  loadRunResponse: (runId: string) => Promise<BacktestResponse | null>;
  loadRunArtifacts: (runId: string) => Promise<RunArtifactsLoaderResult | null>;
  updatePermalink: (runId: string) => void;
  copyRunUrl: (runId: string) => Promise<unknown>;
  shareRunUrl: (runId: string) => Promise<unknown>;
  onError: (message: string | null) => void;
}

export function useBacktestWorkspace({
  backtestRequest,
  selectedConfig,
  refreshRuns,
  loadRunResponse,
  loadRunArtifacts,
  updatePermalink,
  copyRunUrl,
  shareRunUrl,
  onError,
}: UseBacktestWorkspaceOptions) {
  const [backtestResponse, setBacktestResponse] = useState<BacktestResponse | null>(null);
  const [appState, setAppState] = useState<BacktestWorkspaceAppState>('idle');
  const [activeTab, setActiveTab] = useState<'summary' | 'charts' | 'trades' | 'details'>('charts');
  const [runConfigSnapshot, setRunConfigSnapshot] = useState<RunConfigSnapshot | null>(null);
  const [runDataProfile, setRunDataProfile] = useState<RunDataProfile | null>(null);
  const [isLoadingArtifacts, setIsLoadingArtifacts] = useState(false);
  const [visibleStrategies, setVisibleStrategies] = useState<string[]>([]);
  const [visibleBenchmarks, setVisibleBenchmarks] = useState<string[]>([]);
  const exportContainerRef = useRef<HTMLDivElement>(null);

  const hydrateRunArtifacts = useCallback(
    async (runId: string) => {
      setIsLoadingArtifacts(true);
      try {
        const artifacts = await loadRunArtifacts(runId);
        setRunConfigSnapshot(artifacts?.configSnapshot ?? null);
        setRunDataProfile(artifacts?.dataProfile ?? null);
      } finally {
        setIsLoadingArtifacts(false);
      }
    },
    [loadRunArtifacts]
  );

  const handleLoadRun = useCallback(
    async (runId: string) => {
      setRunConfigSnapshot(null);
      setRunDataProfile(null);
      const response = await loadRunResponse(runId);
      if (!response) return;

      const successState = deriveSuccessfulWorkspaceState(response);
      setBacktestResponse(successState.backtestResponse);
      setAppState(successState.appState);
      setActiveTab(successState.activeTab);
      await hydrateRunArtifacts(runId);
    },
    [hydrateRunArtifacts, loadRunResponse]
  );

  const handleRunBacktest = useCallback(async () => {
    if (!selectedConfig) return;

    setAppState('loading');
    onError(null);
    setRunConfigSnapshot(null);
    setRunDataProfile(null);

    try {
      const response = await apiClient.runBacktest({
        ...backtestRequest,
        config_path: selectedConfig.path,
      });

      const successState = deriveSuccessfulWorkspaceState(response);
      setBacktestResponse(successState.backtestResponse);
      setAppState(successState.appState);
      setActiveTab(successState.activeTab);
      refreshRuns();
      if (response.run_info?.run_id) {
        updatePermalink(response.run_info.run_id);
        await hydrateRunArtifacts(response.run_info.run_id);
      }
    } catch (err: any) {
      console.error('Backtest failed:', err);
      onError(err.response?.data?.detail || 'Failed to run backtest');
      setAppState('error');
      setRunConfigSnapshot(null);
      setRunDataProfile(null);
    }
  }, [
    backtestRequest,
    hydrateRunArtifacts,
    onError,
    refreshRuns,
    selectedConfig,
    updatePermalink,
  ]);

  useEffect(() => {
    if (!backtestResponse) return;

    setVisibleStrategies(deriveVisibleStrategies(backtestResponse));
    setVisibleBenchmarks(deriveVisibleBenchmarks(backtestResponse, backtestRequest));
  }, [backtestResponse, backtestRequest]);

  useEffect(() => {
    if (backtestResponse?.run_info?.run_id) {
      updatePermalink(backtestResponse.run_info.run_id);
    }
  }, [backtestResponse?.run_info?.run_id, updatePermalink]);

  const warnings: WarningItem[] = useMemo(
    () => (backtestResponse ? generateWarnings(backtestResponse, backtestRequest) : []),
    [backtestRequest, backtestResponse]
  );
  const strategyNames = backtestResponse ? Object.keys(backtestResponse.results) : [];

  const totalTradesCount = backtestResponse?.results
    ? Object.values(backtestResponse.results).reduce(
        (total, strategy) => total + strategy.trades.length,
        0
      )
    : 0;

  const downloadCSV = useCallback(
    (strategyName: string) => {
      if (!backtestResponse?.run_info?.run_id) return;

      apiClient
        .downloadCSV(backtestResponse.run_info.run_id, strategyName)
        .then((blob) => {
          const link = document.createElement('a');
          const url = URL.createObjectURL(blob);
          link.setAttribute('href', url);
          link.setAttribute('download', `${strategyName}_trades.csv`);
          link.style.visibility = 'hidden';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        })
        .catch((err) => {
          console.error('CSV download failed:', err);
          onError('Failed to download CSV for persisted run');
        });
    },
    [backtestResponse?.run_info?.run_id, onError]
  );

  const downloadPNG = useCallback(() => {
    if (!exportContainerRef.current) return;

    const filename = backtestResponse?.run_info?.run_id
      ? `${backtestResponse.run_info.run_id}_dashboard.png`
      : 'backtest_dashboard.png';

    downloadNodeAsPng(exportContainerRef.current, filename).catch((err) => {
      console.error('PNG download failed:', err);
      onError('Failed to download PNG snapshot');
    });
  }, [backtestResponse?.run_info?.run_id, onError]);

  const downloadHTML = useCallback(() => {
    if (!backtestResponse?.run_info?.run_id) return;

    apiClient
      .downloadHTML(backtestResponse.run_info.run_id)
      .then((blob) => {
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `${backtestResponse.run_info?.run_id}_report.html`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      })
      .catch((err) => {
        console.error('HTML download failed:', err);
        onError('Failed to download HTML report for persisted run');
      });
  }, [backtestResponse?.run_info?.run_id, onError]);

  const shareResults = useCallback(() => {
    const runId = backtestResponse?.run_info?.run_id;
    if (!runId) return;

    shareRunUrl(runId).catch((err) => {
      console.error('Share failed:', err);
      onError('Failed to share run URL');
    });
  }, [backtestResponse?.run_info?.run_id, onError, shareRunUrl]);

  const copySummary = useCallback(() => {
    if (!backtestResponse) return;

    const summaryLines = Object.entries(backtestResponse.results).map(
      ([name, result]) =>
        `${name}: ${formatPercent(result.metrics.total_return)} return, ${result.metrics.sharpe_ratio.toFixed(2)} Sharpe`
    );
    if (backtestResponse.warnings && backtestResponse.warnings.length > 0) {
      summaryLines.push('', 'Execution warnings:');
      summaryLines.push(...backtestResponse.warnings.map((warning) => `- ${warning}`));
    }

    const summary = `Backtest Results:\n${summaryLines.join('\n')}`;

    navigator.clipboard.writeText(summary);
  }, [backtestResponse]);

  const copyRunLink = useCallback(() => {
    const runId = backtestResponse?.run_info?.run_id;
    if (!runId) return;

    copyRunUrl(runId).catch((err) => {
      console.error('Copy URL failed:', err);
      onError('Failed to copy run URL');
    });
  }, [backtestResponse?.run_info?.run_id, copyRunUrl, onError]);

  const saveProjectBundle = useCallback(() => {
    if (!backtestResponse) return;

    const runId = backtestResponse.run_info?.run_id ?? 'unsaved-run';
    const payload = {
      exported_at: new Date().toISOString(),
      run_id: runId,
      request: {
        config_path: selectedConfig?.path ?? null,
        ...backtestRequest,
      },
      warnings,
      run_info: backtestResponse.run_info ?? null,
      data_info: backtestResponse.data_info,
      config_snapshot: runConfigSnapshot,
      data_profile: runDataProfile,
      response: backtestResponse,
    };

    downloadJSON(payload, `${runId}_project_bundle.json`);
  }, [
    backtestRequest,
    backtestResponse,
    runConfigSnapshot,
    runDataProfile,
    selectedConfig?.path,
    warnings,
  ]);

  const toggleStrategyVisibility = useCallback((strategy: string) => {
    setVisibleStrategies((prev) =>
      prev.includes(strategy) ? prev.filter((item) => item !== strategy) : [...prev, strategy]
    );
  }, []);

  const toggleBenchmarkVisibility = useCallback((benchmark: string) => {
    setVisibleBenchmarks((prev) =>
      prev.includes(benchmark) ? prev.filter((item) => item !== benchmark) : [...prev, benchmark]
    );
  }, []);

  const toggleAllStrategies = useCallback(
    (visible: boolean) => {
      setVisibleStrategies(visible && backtestResponse ? Object.keys(backtestResponse.results) : []);
    },
    [backtestResponse]
  );

  const toggleAllBenchmarks = useCallback(
    (visible: boolean) => {
      setVisibleBenchmarks(visible ? [...visibleBenchmarks] : []);
    },
    [visibleBenchmarks]
  );

  return {
    appState,
    activeTab,
    backtestResponse,
    exportContainerRef: exportContainerRef as RefObject<HTMLDivElement>,
    handleLoadRun,
    handleRunBacktest,
    isLoadingArtifacts,
    runConfigSnapshot,
    runDataProfile,
    setActiveTab: setActiveTab as Dispatch<SetStateAction<'summary' | 'charts' | 'trades' | 'details'>>,
    strategyNames,
    totalTradesCount,
    visibleBenchmarks,
    visibleStrategies,
    warnings,
    actions: {
      copyRunLink,
      copySummary,
      downloadCSV,
      downloadHTML,
      downloadPNG,
      saveProjectBundle,
      shareResults,
    },
    visibility: {
      toggleAllBenchmarks,
      toggleAllStrategies,
      toggleBenchmarkVisibility,
      toggleStrategyVisibility,
    },
  };
}
