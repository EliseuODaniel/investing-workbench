import { useCallback, useEffect, useState } from 'react';
import { Play, BarChart3, AlertCircle, TrendingUp, List, DollarSign } from 'lucide-react';
import { apiClient } from './lib/api';
import { BacktestResponse } from './types/api';
import { formatCurrency, formatPercent } from './lib/utils';
import BacktestForm from './components/BacktestForm';
import MetricsCards from './components/MetricsCards';
import ChartsTabbed from './components/ChartsTabbed';
import TradesTable from './components/TradesTable';
import LoadingSpinner from './components/LoadingSpinner';
import DarkModeToggle from './components/DarkModeToggle';
import VisibilityControls from './components/VisibilityControls';
import SelicInfoPanel from './components/SelicInfoPanel';
import WarningsPanel, { generateWarnings } from './components/WarningsPanel';
import QuickActions from './components/QuickActions';
import RunArtifactsPanel from './components/RunArtifactsPanel';
import RunComparisonPanel from './components/RunComparisonPanel';
import { useConfigs } from './hooks/useConfigs';
import { useRunHistory } from './hooks/useRunHistory';
import { useRunComparison } from './hooks/useRunComparison';
import { useRunPermalink } from './hooks/useRunPermalink';
import RunHistoryPanel from './components/RunHistoryPanel';
import { RunConfigSnapshot, RunDataProfile } from './types/api';

type AppState = 'idle' | 'loading' | 'success' | 'error';

function App() {
  const [backtestResponse, setBacktestResponse] = useState<BacktestResponse | null>(null);
  const [appState, setAppState] = useState<AppState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'trades'>('overview');
  const {
    configs,
    selectedConfig,
    backtestRequest,
    handleConfigChange,
    handleRequestChange,
  } = useConfigs(setError);
  const { runs, isLoadingRuns, refreshRuns, loadRunResponse, loadRunArtifacts } =
    useRunHistory(setError);
  const {
    selectedRunIds,
    comparisonRuns,
    isLoadingComparison,
    toggleRunSelection,
    clearComparison,
  } = useRunComparison(runs, setError);
  const [runConfigSnapshot, setRunConfigSnapshot] = useState<RunConfigSnapshot | null>(null);
  const [runDataProfile, setRunDataProfile] = useState<RunDataProfile | null>(null);
  const [isLoadingArtifacts, setIsLoadingArtifacts] = useState(false);

  // Visibility controls state
  const [visibleStrategies, setVisibleStrategies] = useState<string[]>([]);
  const [visibleBenchmarks, setVisibleBenchmarks] = useState<string[]>([]);

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

      setBacktestResponse(response);
      setAppState('success');
      setActiveTab('overview');
      await hydrateRunArtifacts(runId);
    },
    [hydrateRunArtifacts, loadRunResponse]
  );

  const { updatePermalink, copyRunUrl, shareRunUrl } = useRunPermalink({
    isReady: !isLoadingRuns,
    onLoadRun: handleLoadRun,
    onError: setError,
  });

  // Calculate total trades count
  const getTotalTradesCount = () => {
    if (!backtestResponse?.results) return 0;
    return Object.values(backtestResponse.results).reduce(
      (total, strategy) => total + strategy.trades.length,
      0
    );
  };

  const handleRunBacktest = async () => {
    if (!selectedConfig) return;

    setAppState('loading');
    setError(null);
    setRunConfigSnapshot(null);
    setRunDataProfile(null);

    try {
      const response = await apiClient.runBacktest({
        ...backtestRequest,
        config_path: selectedConfig.path,
      });

      setBacktestResponse(response);
      setAppState('success');
      refreshRuns();
      if (response.run_info?.run_id) {
        updatePermalink(response.run_info.run_id);
        await hydrateRunArtifacts(response.run_info.run_id);
      }
    } catch (err: any) {
      console.error('Backtest failed:', err);
      setError(err.response?.data?.detail || 'Failed to run backtest');
      setAppState('error');
      setRunConfigSnapshot(null);
      setRunDataProfile(null);
    }
  };

  // Initialize visibility controls when backtest completes
  useEffect(() => {
    if (backtestResponse) {
      const strategyNames = Object.keys(backtestResponse.results);
      const benchmarkNames = [];

      if (backtestRequest.include_buy_hold_benchmark !== false) {
        benchmarkNames.push('Buy & Hold');
      }
      if (backtestRequest.include_selic_benchmark) {
        benchmarkNames.push('SELIC');
      }
      if (backtestResponse.benchmarks) {
        benchmarkNames.push(...Object.keys(backtestResponse.benchmarks));
      }

      setVisibleStrategies(strategyNames);
      setVisibleBenchmarks(benchmarkNames);
    }
  }, [backtestResponse, backtestRequest]);

  // Generate warnings from backtest results
  const warnings = backtestResponse ? generateWarnings(backtestResponse, backtestRequest) : [];

  // Prepare strategy names for actions
  const strategyNames = backtestResponse ? Object.keys(backtestResponse.results) : [];

  const downloadCSV = (strategyName: string) => {
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
        setError('Failed to download CSV for persisted run');
      });
  };

  const downloadPNG = () => {
    // TODO: Implement chart download functionality
    console.log('Download PNG not implemented yet');
  };

  const downloadHTML = () => {
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
        setError('Failed to download HTML report for persisted run');
      });
  };

  const shareResults = () => {
    const runId = backtestResponse?.run_info?.run_id;
    if (!runId) return;

    shareRunUrl(runId).catch((err) => {
      console.error('Share failed:', err);
      setError('Failed to share run URL');
    });
  };

  const copySummary = () => {
    if (!backtestResponse) return;

    const summary = `Backtest Results:\n${Object.entries(backtestResponse.results).map(([name, result]: [string, any]) =>
      `${name}: ${formatPercent(result.metrics.total_return)} return, ${result.metrics.sharpe_ratio.toFixed(2)} Sharpe`
    ).join('\n')}`;

    navigator.clipboard.writeText(summary);
  };

  const copyRunLink = () => {
    const runId = backtestResponse?.run_info?.run_id;
    if (!runId) return;

    copyRunUrl(runId).catch((err) => {
      console.error('Copy URL failed:', err);
      setError('Failed to copy run URL');
    });
  };

  useEffect(() => {
    if (backtestResponse?.run_info?.run_id) {
      updatePermalink(backtestResponse.run_info.run_id);
    }
  }, [backtestResponse?.run_info?.run_id, updatePermalink]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Bitcoin Martingale Backtest
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Interactive backtesting platform for Bitcoin trading strategies
            </p>
          </div>
          <DarkModeToggle />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar - Form */}
          <div className="lg:col-span-1">
            <BacktestForm
              configs={configs}
              selectedConfig={selectedConfig}
              backtestRequest={backtestRequest}
              onConfigChange={handleConfigChange}
              onRequestChange={handleRequestChange}
              onRunBacktest={handleRunBacktest}
              isLoading={appState === 'loading'}
            />
            <RunHistoryPanel
              runs={runs}
              isLoading={isLoadingRuns}
              onRefresh={refreshRuns}
              onLoadRun={handleLoadRun}
              selectedRunIds={selectedRunIds}
              onToggleCompare={toggleRunSelection}
            />
          </div>

          {/* Main Results Area */}
          <div className="lg:col-span-2">
            {/* Error State */}
            {appState === 'error' && error && (
              <div className="card mb-6 border-red-200 bg-red-50">
                <div className="flex items-center">
                  <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
                  <div>
                    <h3 className="text-red-800 font-medium">Error</h3>
                    <p className="text-red-600 text-sm mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {appState === 'loading' && (
              <LoadingSpinner message="Running backtest analysis..." />
            )}

            <RunComparisonPanel
              comparisonRuns={comparisonRuns}
              isLoading={isLoadingComparison}
              onClear={clearComparison}
            />

            {/* Results */}
            {appState === 'success' && backtestResponse && (
              <div className="space-y-6">
                {/* Execution Summary Card */}
                <div className="card bg-gradient-to-r from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800">
                  <div className="flex items-center mb-4">
                    <div className="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-full flex items-center justify-center mr-3">
                      <BarChart3 className="h-4 w-4 text-green-600 dark:text-green-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
                      Backtest Concluído com Sucesso
                    </h3>
                  </div>

                  {/* Selected Items */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    {/* Period */}
                    <div>
                      <div className="text-xs text-green-600 dark:text-green-400 font-medium mb-2">Período</div>
                      <div className="text-sm text-green-900 dark:text-green-100">
                        {new Date(backtestResponse.data_info.start_date).toLocaleDateString('pt-BR')} - {new Date(backtestResponse.data_info.end_date).toLocaleDateString('pt-BR')}
                      </div>
                      <div className="text-xs text-green-700 dark:text-green-300">
                        {backtestResponse.data_info.total_days} dias
                      </div>
                    </div>

                    {/* Strategies */}
                    <div>
                      <div className="text-xs text-green-600 dark:text-green-400 font-medium mb-2">
                        Estratégias ({backtestRequest.strategies?.length || 0})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {backtestRequest.strategies?.map((strategy) => (
                          <span
                            key={strategy}
                            className="px-2 py-1 bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 text-xs font-medium rounded-full"
                          >
                            {strategy}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Benchmarks */}
                    <div>
                      <div className="text-xs text-green-600 dark:text-green-400 font-medium mb-2">
                        Benchmarks
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {backtestRequest.include_buy_hold_benchmark !== false && (
                          <span className="px-2 py-1 bg-purple-100 dark:bg-purple-800 text-purple-800 dark:text-purple-200 text-xs font-medium rounded-full">
                            Buy & Hold
                          </span>
                        )}
                        {backtestRequest.include_selic_benchmark && (
                          <span className="px-2 py-1 bg-yellow-100 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200 text-xs font-medium rounded-full">
                            SELIC
                          </span>
                        )}
                        {backtestRequest.benchmarks?.map((benchmark) => (
                          <span
                            key={benchmark}
                            className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs font-medium rounded-full"
                          >
                            {benchmark}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Capital */}
                    <div>
                      <div className="text-xs text-green-600 dark:text-green-400 font-medium mb-2">Capital Inicial</div>
                      <div className="text-sm text-green-900 dark:text-green-100 font-semibold">
                        R$ {(backtestRequest.initial_capital || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </div>
                      {backtestRequest.apply_cash_yield && (
                        <div className="text-xs text-green-700 dark:text-green-300">
                          + SELIC {backtestRequest.use_real_selic ? 'real' : 'fixa'}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Quick Stats */}
                  <div className="border-t border-green-200 dark:border-green-700 pt-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-xs text-green-600 dark:text-green-400">Preço Inicial</div>
                        <div className="text-green-900 dark:text-green-100 font-medium">
                          {formatCurrency(backtestResponse.data_info.initial_price)}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-green-600 dark:text-green-400">Preço Final</div>
                        <div className="text-green-900 dark:text-green-100 font-medium">
                          {formatCurrency(backtestResponse.data_info.final_price)}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-green-600 dark:text-green-400">Total de Trades</div>
                        <div className="text-green-900 dark:text-green-100 font-medium">
                          {getTotalTradesCount()}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-green-600 dark:text-green-400">Estratégias Testadas</div>
                        <div className="text-green-900 dark:text-green-100 font-medium">
                          {Object.keys(backtestResponse.results).length}
                        </div>
                      </div>
                    </div>
                    {backtestResponse.run_info?.run_id && (
                      <div className="mt-4 text-center text-xs text-green-700 dark:text-green-300">
                        Run ID: <span className="font-mono">{backtestResponse.run_info.run_id}</span>
                        {backtestResponse.run_info.data_fingerprint && (
                          <>
                            {' '}| Data:{' '}
                            <span className="font-mono">
                              {backtestResponse.run_info.data_fingerprint.slice(0, 12)}
                            </span>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Warnings Panel */}
                {warnings.length > 0 && (
              <WarningsPanel
                    warnings={warnings}
                    onDismiss={() => {
                      /* In this view we only display warnings; stateful dismissal can be added later */
                    }}
                  />
                )}

                <RunArtifactsPanel
                  runId={backtestResponse.run_info?.run_id}
                  configSnapshot={runConfigSnapshot}
                  dataProfile={runDataProfile}
                  isLoading={isLoadingArtifacts}
                />

                {/* SELIC Info Panel */}
                {backtestRequest.apply_cash_yield && (
                  <SelicInfoPanel
                    useRealSelic={backtestRequest.use_real_selic}
                    selicFallbackRate={backtestRequest.selic_fallback_rate}
                    selicRatesUsed={Object.values(backtestResponse.results)[0]?.metrics?.selic_rates_used}
                    selicRateAnnual={backtestRequest.selic_fallback_rate}
                    capital={backtestRequest.initial_capital}
                  />
                )}

                {/* Visibility Controls */}
                <VisibilityControls
                  strategies={Object.keys(backtestResponse.results)}
                  benchmarks={visibleBenchmarks}
                  visibleStrategies={visibleStrategies}
                  visibleBenchmarks={visibleBenchmarks}
                  onStrategyToggle={(strategy) => {
                    setVisibleStrategies(prev =>
                      prev.includes(strategy)
                        ? prev.filter(s => s !== strategy)
                        : [...prev, strategy]
                    );
                  }}
                  onBenchmarkToggle={(benchmark) => {
                    setVisibleBenchmarks(prev =>
                      prev.includes(benchmark)
                        ? prev.filter(b => b !== benchmark)
                        : [...prev, benchmark]
                    );
                  }}
                  onToggleAllStrategies={(visible) => {
                    setVisibleStrategies(visible ? Object.keys(backtestResponse.results) : []);
                  }}
                  onToggleAllBenchmarks={(visible) => {
                    setVisibleBenchmarks(visible ? visibleBenchmarks : []);
                  }}
                />

                {/* Quick Actions */}
                <QuickActions
                  strategies={strategyNames}
                  onDownloadCSV={downloadCSV}
                  onDownloadPNG={downloadPNG}
                  onDownloadHTML={downloadHTML}
                  onShareResults={shareResults}
                  onCopySummary={copySummary}
                  onCopyLink={copyRunLink}
                />

                {/* Tabs Navigation */}
                <div className="card">
                  <div className="border-b border-gray-200 dark:border-gray-700">
                    <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                      <button
                        onClick={() => setActiveTab('overview')}
                        className={`tab-button ${
                          activeTab === 'overview' ? 'active' : 'inactive'
                        }`}
                      >
                        <TrendingUp className="h-4 w-4 mr-2" />
                        Overview & Charts
                      </button>
                      <button
                        onClick={() => setActiveTab('trades')}
                        className={`tab-button ${
                          activeTab === 'trades' ? 'active' : 'inactive'
                        }`}
                      >
                        <List className="h-4 w-4 mr-2" />
                        Trading History
                        {getTotalTradesCount() > 0 && (
                          <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full">
                            {getTotalTradesCount()}
                          </span>
                        )}
                      </button>
                    </nav>
                  </div>

                  {/* Tab Content */}
                  <div className="mt-6">
                    {activeTab === 'overview' && (
                      <div className="space-y-6">
                        {/* Metrics Cards */}
                        <MetricsCards
  results={backtestResponse.results}
  benchmarks={backtestResponse.benchmarks}
/>

                        {/* Charts */}
                        <ChartsTabbed
                          results={backtestResponse.results}
                          buyHoldEquity={backtestResponse.buy_hold_equity}
                          visibleStrategies={visibleStrategies}
                          visibleBenchmarks={visibleBenchmarks}
                          benchmarks={backtestResponse.benchmarks}
                        />
                      </div>
                    )}

                    {activeTab === 'trades' && (
                      <div className="space-y-4">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
                          <div>
                            <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                              Trading History
                            </h4>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              Complete list of all trades executed during backtest
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              Total Trades: <span className="font-semibold">{getTotalTradesCount()}</span>
                            </div>
                          </div>
                        </div>
                        <TradesTable results={backtestResponse.results} />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Initial State - Enhanced Empty State */}
            {appState === 'idle' && (
              <div className="space-y-6">
                {/* Welcome Card */}
                <div className="card bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
                  <div className="text-center">
                    <div className="mx-auto w-16 h-16 bg-blue-100 dark:bg-blue-800 rounded-full flex items-center justify-center mb-4">
                      <BarChart3 className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                      Bem-vindo ao Bitcoin Martingale Backtest
                    </h3>
                    <p className="text-gray-600 dark:text-gray-300 mb-6 max-w-2xl mx-auto">
                      Teste diferentes estratégias de trading com análise comparativa completa.
                      Configure em 3 passos simples e obtenha insights detalhados sobre performance.
                    </p>

                    {/* Quick Steps */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 max-w-3xl mx-auto">
                      <div className="flex flex-col items-center p-4 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-700">
                        <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-2">
                          <span className="text-sm font-bold text-blue-600 dark:text-blue-400">1</span>
                        </div>
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">Configure</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Escolha estratégias e benchmarks</p>
                      </div>
                      <div className="flex flex-col items-center p-4 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-700">
                        <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-2">
                          <span className="text-sm font-bold text-blue-600 dark:text-blue-400">2</span>
                        </div>
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">Ajuste</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Defina período e rendimento</p>
                      </div>
                      <div className="flex flex-col items-center p-4 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-700">
                        <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-2">
                          <span className="text-sm font-bold text-blue-600 dark:text-blue-400">3</span>
                        </div>
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">Execute</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Analise resultados detalhados</p>
                      </div>
                    </div>

                    {/* Call to Action */}
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-blue-200 dark:border-blue-700">
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                        Comece sua análise agora
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                        Configure seus parâmetros no painel esquerdo e clique em "Executar Backtest"
                      </p>
                      <div className="flex items-center justify-center space-x-4">
                        <div className="flex items-center text-sm text-gray-500">
                          <Play className="h-4 w-4 mr-2" />
                          Configure ao lado
                        </div>
                        <div className="text-gray-300">→</div>
                        <div className="flex items-center text-sm text-gray-500">
                          <BarChart3 className="h-4 w-4 mr-2" />
                          Veja os resultados
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Features Card */}
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Recursos Disponíveis
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <TrendingUp className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Múltiplas Estratégias</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Teste diferentes abordagens Martingale</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <BarChart3 className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Benchmarks</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Compare com SELIC, IBOVESPA e mais</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <DollarSign className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Rendimento do Caixa</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">SELIC real sobre capital ocioso</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <List className="h-5 w-5 text-purple-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Análise Detalhada</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Métricas, trades e visualizações</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
