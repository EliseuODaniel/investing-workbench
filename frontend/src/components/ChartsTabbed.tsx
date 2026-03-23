// @ts-nocheck
import React, { useState, useMemo } from 'react';
import { BarChart3, TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter
} from 'recharts';
import { StrategyResult, BenchmarkResult, EquityPoint, Trade } from '../types/api';

interface ChartsTabbedProps {
  results: Record<string, StrategyResult>;
  buyHoldEquity: EquityPoint[];
  visibleStrategies: string[];
  visibleBenchmarks: string[];
  benchmarks?: Record<string, BenchmarkResult>;
}

const ChartsTabbed: React.FC<ChartsTabbedProps> = ({
  results,
  buyHoldEquity,
  visibleStrategies,
  visibleBenchmarks,
  benchmarks,
}) => {
  const [activeTab, setActiveTab] = useState<'equity' | 'drawdown' | 'cash' | 'trades'>('equity');

  const tabs = [
    {
      id: 'equity' as const,
      name: 'Equity',
      icon: BarChart3,
      description: 'Evolução do patrimônio ao longo do tempo',
    },
    {
      id: 'drawdown' as const,
      name: 'Drawdown',
      icon: TrendingDown,
      description: 'Quedas máximas do patrimônio',
    },
    {
      id: 'cash' as const,
      name: 'Caixa',
      icon: DollarSign,
      description: 'Evolução do capital disponível',
    },
    {
      id: 'trades' as const,
      name: 'Trades',
      icon: Activity,
      description: 'Pontos de entrada e saída',
    },
  ];

  // Prepare equity data for charts
  const equityData = useMemo(() => {
    const allTimestamps = new Set<string>();

    // Collect all timestamps
    Object.values(results).forEach(result => {
      if (visibleStrategies.includes(result.strategy_name)) {
        result.equity.forEach(point => {
          allTimestamps.add(point.timestamp);
        });
      }
    });

    // Add Buy & Hold timestamps
    if (visibleBenchmarks.includes('Buy & Hold')) {
      buyHoldEquity.forEach(point => {
        allTimestamps.add(point.timestamp);
      });
    }

    // Add benchmark timestamps
    if (benchmarks) {
      Object.entries(benchmarks).forEach(([name, benchmark]) => {
        if (visibleBenchmarks.includes(name)) {
          benchmark.equity.forEach(point => {
            allTimestamps.add(point.timestamp);
          });
        }
      });
    }

    const sortedTimestamps = Array.from(allTimestamps).sort();

    // Create data structure for each timestamp
    return sortedTimestamps.map(timestamp => {
      const dataPoint: any = {
        timestamp,
        date: new Date(timestamp).toLocaleDateString('pt-BR')
      };

      // Add strategy data
      Object.values(results).forEach(result => {
        if (visibleStrategies.includes(result.strategy_name)) {
          const point = result.equity.find(p => p.timestamp === timestamp);
          dataPoint[result.strategy_name] = point?.equity || null;
          dataPoint[`${result.strategy_name}_cash`] = point?.cash || null;
        }
      });

      // Add Buy & Hold data
      if (visibleBenchmarks.includes('Buy & Hold')) {
        const point = buyHoldEquity.find(p => p.timestamp === timestamp);
        dataPoint['Buy & Hold'] = point?.equity || null;
      }

      // Add benchmark data
      if (benchmarks) {
        Object.entries(benchmarks).forEach(([name, benchmark]) => {
          if (visibleBenchmarks.includes(name)) {
            const point = benchmark.equity.find(p => p.timestamp === timestamp);
            dataPoint[name] = point?.equity || null;
          }
        });
      }

      return dataPoint;
    });
  }, [results, buyHoldEquity, benchmarks, visibleStrategies, visibleBenchmarks]);

  // Calculate drawdown data
  const drawdownData = useMemo(() => {
    return equityData.map((point, index) => {
      const dataPoint: any = {
        timestamp: point.timestamp,
        date: point.date
      };

      // Calculate drawdown for each strategy
      Object.keys(results).forEach(strategyName => {
        if (visibleStrategies.includes(strategyName)) {
          const strategyEquity = Object.values(results)
            .find(r => r.strategy_name === strategyName)?.equity || [];

          if (index === 0 || !point[strategyName]) {
            dataPoint[`${strategyName}_drawdown`] = 0;
          } else {
            const valuesUpToNow = equityData.slice(0, index + 1)
              .map(p => p[strategyName])
              .filter(v => v !== null);

            if (valuesUpToNow.length > 0) {
              const peak = Math.max(...valuesUpToNow);
              const current = point[strategyName];
              const drawdown = current !== null ? ((current - peak) / peak) * 100 : 0;
              dataPoint[`${strategyName}_drawdown`] = drawdown;
            } else {
              dataPoint[`${strategyName}_drawdown`] = 0;
            }
          }
        }
      });

      return dataPoint;
    });
  }, [equityData, results, visibleStrategies]);

  // Prepare trades data for scatter plot
  const tradesData = useMemo(() => {
    const allTrades: any[] = [];

    Object.entries(results).forEach(([strategyName, result]) => {
      if (visibleStrategies.includes(strategyName)) {
        result.trades.forEach(trade => {
          // Find corresponding equity value for color coding
          const equityPoint = result.equity.find(p => p.timestamp === trade.timestamp);
          const equityValue = equityPoint?.equity || 0;

          allTrades.push({
            timestamp: new Date(trade.timestamp),
            price: trade.price,
            action: trade.action,
            strategy: strategyName,
            pnl: trade.pnl || 0,
            layer: trade.layer,
            equity: equityValue,
            color: trade.action === 'BUY' ? '#10b981' : '#ef4444'
          });
        });
      }
    });

    return allTrades.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  }, [results, visibleStrategies]);

  // Get colors for strategies
  const getStrategyColor = (strategyName: string, index: number) => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];
    const strategyIndex = Object.keys(results).indexOf(strategyName);
    return colors[strategyIndex % colors.length];
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getTabContent = () => {
    switch (activeTab) {
      case 'equity':
        return (
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  tickFormatter={formatCurrency}
                />
                <Tooltip
                  formatter={(value: any) => [formatCurrency(value), 'Patrimônio']}
                  labelFormatter={(label) => label}
                />
                <Legend />

                {/* Strategy lines */}
                {Object.entries(results).map(([strategyName]) => (
                  visibleStrategies.includes(strategyName) && (
                    <Line
                      key={strategyName}
                      type="monotone"
                      dataKey={strategyName}
                      stroke={getStrategyColor(strategyName, 0)}
                      strokeWidth={2}
                      dot={false}
                      name={strategyName}
                      connectNulls={false}
                    />
                  )
                ))}

                {/* Buy & Hold line */}
                {visibleBenchmarks.includes('Buy & Hold') && (
                  <Line
                    type="monotone"
                    dataKey="Buy & Hold"
                    stroke="#9333ea"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Buy & Hold"
                    connectNulls={false}
                  />
                )}

                {/* Benchmark lines */}
                {benchmarks && Object.entries(benchmarks).map(([name]) => (
                  visibleBenchmarks.includes(name) && (
                    <Line
                      key={name}
                      type="monotone"
                      dataKey={name}
                      stroke="#6b7280"
                      strokeWidth={2}
                      strokeDasharray="3 3"
                      dot={false}
                      name={name}
                      connectNulls={false}
                    />
                  )
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'drawdown':
        return (
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={drawdownData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  tickFormatter={(value) => `${value.toFixed(1)}%`}
                />
                <Tooltip
                  formatter={(value: any) => [`${value.toFixed(2)}%`, 'Drawdown']}
                  labelFormatter={(label) => label}
                />
                <Legend />

                {/* Strategy drawdown lines */}
                {Object.entries(results).map(([strategyName]) => (
                  visibleStrategies.includes(strategyName) && (
                    <Line
                      key={`${strategyName}_drawdown`}
                      type="monotone"
                      dataKey={`${strategyName}_drawdown`}
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={false}
                      name={`${strategyName} DD`}
                      fill="#ef4444"
                      fillOpacity={0.1}
                    />
                  )
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'cash':
        return (
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  tickFormatter={formatCurrency}
                />
                <Tooltip
                  formatter={(value: any) => [formatCurrency(value), 'Caixa Disponível']}
                  labelFormatter={(label) => label}
                />
                <Legend />

                {/* Cash lines */}
                {Object.entries(results).map(([strategyName]) => (
                  visibleStrategies.includes(strategyName) && (
                    <Line
                      key={`${strategyName}_cash`}
                      type="monotone"
                      dataKey={`${strategyName}_cash`}
                      stroke={getStrategyColor(strategyName, 0)}
                      strokeWidth={2}
                      strokeDasharray="2 2"
                      dot={false}
                      name={`${strategyName} Caixa`}
                      connectNulls={false}
                    />
                  )
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'trades':
        return (
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  type="category"
                  domain={['dataMin', 'dataMax']}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  tickFormatter={formatCurrency}
                  domain={['dataMin - 1000', 'dataMax + 1000']}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold">{data.strategy}</p>
                          <p>{data.timestamp.toLocaleDateString('pt-BR')}</p>
                          <p>Preço: {formatCurrency(data.price)}</p>
                          <p>Ação: {data.action}</p>
                          <p>PnL: {formatCurrency(data.pnl)}</p>
                          <p>Layer: {data.layer}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />

                {/* Trades scatter points */}
                {Object.entries(results).map(([strategyName]) => (
                  visibleStrategies.includes(strategyName) && (
                    <Scatter
                      key={strategyName}
                      name={strategyName}
                      data={tradesData.filter(t => t.strategy === strategyName)}
                      fill={getStrategyColor(strategyName, 0)}
                    />
                  )
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="card">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group relative min-w-0 flex-1 overflow-hidden py-4 px-1 text-center text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-b-2 border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <div className="flex items-center justify-center">
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.name}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Description */}
      <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {tabs.find(tab => tab.id === activeTab)?.description}
        </p>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {getTabContent()}
      </div>

      {/* Chart Controls */}
      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Configure a visibilidade dos elementos no painel de controles
          </div>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors">
              🔍 Zoom
            </button>
            <button className="px-3 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors">
              📊 Configurar
            </button>
            <button className="px-3 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors">
              📷 Capturar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartsTabbed;
