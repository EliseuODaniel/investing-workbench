// @ts-nocheck
import React, { useState } from 'react';
import { LineChart, TrendingDown, DollarSign } from 'lucide-react';
import Plot from 'react-plotly.js';
import { StrategyResult, EquityPoint, Trade } from '../types/api';
import { formatCurrency, formatPercent, formatNumber } from '../lib/utils';

interface ChartsSectionProps {
  results: Record<string, StrategyResult>;
  buyHoldEquity: EquityPoint[];
}

const ChartsSection: React.FC<ChartsSectionProps> = ({ results, buyHoldEquity }) => {
  const [selectedChart, setSelectedChart] = useState<'equity' | 'drawdown' | 'cash'>('equity');

  const strategyNames = Object.keys(results);
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  // Prepare equity data for Plotly
  const prepareEquityData = () => {
    const traces: any[] = [];

    // Add Buy & Hold
    if (buyHoldEquity.length > 0) {
      traces.push({
        x: buyHoldEquity.map(point => point.timestamp),
        y: buyHoldEquity.map(point => point.equity),
        type: 'scatter',
        mode: 'lines',
        name: 'Buy & Hold',
        line: { color: '#9ca3af', width: 2, dash: 'dash' },
      });
    }

    // Add strategies
    strategyNames.forEach((strategyName, index) => {
      const result = results[strategyName];
      if (result.equity.length > 0) {
        traces.push({
          x: result.equity.map(point => point.timestamp),
          y: result.equity.map(point => point.equity),
          type: 'scatter',
          mode: 'lines',
          name: strategyName,
          line: { color: colors[index % colors.length], width: 2 },
        });
      }
    });

    return traces;
  };

  // Prepare drawdown data
  const prepareDrawdownData = () => {
    const traces: any[] = [];

    strategyNames.forEach((strategyName, index) => {
      const result = results[strategyName];
      if (result.equity.length > 0) {
        const equityValues = result.equity.map(point => point.equity);
        const peaks: number[] = [];
        let maxSoFar = equityValues[0];

        equityValues.forEach(value => {
          maxSoFar = Math.max(maxSoFar, value);
          peaks.push(maxSoFar);
        });

        const drawdowns = equityValues.map((value, i) => ((value - peaks[i]) / peaks[i]) * 100);

        traces.push({
          x: result.equity.map(point => point.timestamp),
          y: drawdowns,
          type: 'scatter',
          mode: 'lines',
          name: strategyName,
          line: { color: colors[index % colors.length], width: 2 },
          fill: index === 0 ? 'tonexty' : 'none',
        });
      }
    });

    return traces;
  };

  // Prepare cash allocation data
  const prepareCashData = () => {
    const traces: any[] = [];

    strategyNames.forEach((strategyName, index) => {
      const result = results[strategyName];
      if (result.equity.length > 0) {
        traces.push({
          x: result.equity.map(point => point.timestamp),
          y: result.equity.map(point => point.cash),
          type: 'scatter',
          mode: 'lines',
          name: strategyName,
          line: { color: colors[index % colors.length], width: 2 },
        });
      }
    });

    return traces;
  };

  // Get candlestick data with trades for the first strategy
  const prepareCandlestickData = () => {
    if (strategyNames.length === 0) return { candlestick: [], buyTrades: [], sellTrades: [] };

    const firstStrategy = results[strategyNames[0]];
    const trades = firstStrategy.trades;

    // For simplicity, we'll use Close price for candlestick
    // In a real implementation, you'd need OHLC data
    const buyTrades = trades.filter(trade => trade.action === 'BUY');
    const sellTrades = trades.filter(trade => trade.action === 'SELL');

    return {
      candlestick: firstStrategy.equity.map(point => ({
        x: point.timestamp,
        y: point.equity,
      })),
      buyTrades: buyTrades.map(trade => ({
        x: trade.timestamp,
        y: trade.price,
      })),
      sellTrades: sellTrades.map(trade => ({
        x: trade.timestamp,
        y: trade.price,
      }))
    };
  };

  const equityData = prepareEquityData();
  const drawdownData = prepareDrawdownData();
  const cashData = prepareCashData();
  const candlestickData = prepareCandlestickData();

  const chartConfig = {
    displayModeBar: true,
    displaylogo: false,
    responsive: true,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold flex items-center">
        <LineChart className="h-5 w-5 mr-2" />
        Interactive Charts
      </h3>

      {/* Chart Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'equity', label: 'Equity Curve', icon: <TrendingDown className="h-4 w-4" /> },
            { id: 'drawdown', label: 'Drawdown', icon: <TrendingDown className="h-4 w-4" /> },
            { id: 'cash', label: 'Cash Allocation', icon: <DollarSign className="h-4 w-4" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedChart(tab.id as any)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                selectedChart === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              <span className="ml-2">{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Main Chart */}
        <div className="lg:col-span-2">
          <div className="bg-white p-4 rounded-lg border">
            {selectedChart === 'equity' && (
              <Plot
                data={equityData}
                layout={{
                  title: 'Portfolio Equity Comparison',
                  xaxis: { title: 'Date' },
                  yaxis: {
                    title: 'Portfolio Value (BRL)',
                    tickformat: ',.0f',
                  },
                  showlegend: true,
                  hovermode: 'x unified',
                }}
                config={chartConfig}
                style={{ width: '100%', height: '500px' }}
              />
            )}

            {selectedChart === 'drawdown' && (
              <Plot
                data={drawdownData}
                layout={{
                  title: 'Drawdown Analysis',
                  xaxis: { title: 'Date' },
                  yaxis: {
                    title: 'Drawdown (%)',
                    tickformat: '.1f',
                  },
                  showlegend: true,
                  hovermode: 'x unified',
                }}
                config={chartConfig}
                style={{ width: '100%', height: '500px' }}
              />
            )}

            {selectedChart === 'cash' && (
              <Plot
                data={cashData}
                layout={{
                  title: 'Cash Allocation Over Time',
                  xaxis: { title: 'Date' },
                  yaxis: {
                    title: 'Available Cash (BRL)',
                    tickformat: ',.0f',
                  },
                  showlegend: true,
                  hovermode: 'x unified',
                }}
                config={chartConfig}
                style={{ width: '100%', height: '500px' }}
              />
            )}
          </div>
        </div>

        {/* Price Chart with Trades */}
        <div className="lg:col-span-2">
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="text-md font-medium mb-4">Price Action with Trading Signals</h4>
            <Plot
              data={[
                {
                  x: candlestickData.candlestick.map(point => point.x),
                  y: candlestickData.candlestick.map(point => point.y),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Portfolio Value',
                  line: { color: 'black', width: 1 },
                },
                {
                  x: candlestickData.buyTrades.map(point => point.x),
                  y: candlestickData.buyTrades.map(point => point.y),
                  type: 'scatter',
                  mode: 'markers',
                  name: 'BUY',
                  marker: {
                    color: 'green',
                    symbol: 'triangle-up',
                    size: 10,
                  },
                },
                {
                  x: candlestickData.sellTrades.map(point => point.x),
                  y: candlestickData.sellTrades.map(point => point.y),
                  type: 'scatter',
                  mode: 'markers',
                  name: 'SELL',
                  marker: {
                    color: 'red',
                    symbol: 'triangle-down',
                    size: 10,
                  },
                },
              ]}
              layout={{
                title: 'Trade Entry/Exit Points',
                xaxis: { title: 'Date' },
                yaxis: {
                  title: 'Value (BRL)',
                  tickformat: ',.0f',
                },
                showlegend: true,
                hovermode: 'closest',
              }}
              config={chartConfig}
              style={{ width: '100%', height: '400px' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartsSection;
