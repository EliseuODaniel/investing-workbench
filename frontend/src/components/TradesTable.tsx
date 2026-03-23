import React, { useState, useMemo } from 'react';
import { Download, Filter, ArrowUpDown } from 'lucide-react';
import { StrategyResult, Trade } from '../types/api';
import { formatCurrency, formatDateTime, downloadCSV } from '../lib/utils';

interface TradesTableProps {
  results: Record<string, StrategyResult>;
}

const TradesTable: React.FC<TradesTableProps> = ({ results }) => {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('all');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [layerFilter, setLayerFilter] = useState<string>('all');
  const [sortConfig, setSortConfig] = useState<{
    key: keyof Trade;
    direction: 'asc' | 'desc';
  } | null>(null);

  // Combine all trades from all strategies
  const allTrades = useMemo(() => {
    const trades: (Trade & { strategyName: string })[] = [];

    Object.entries(results).forEach(([strategyName, result]) => {
      result.trades.forEach(trade => {
        trades.push({ ...trade, strategyName });
      });
    });

    return trades;
  }, [results]);

  // Get available layers for filtering
  const availableLayers = useMemo(() => {
    const layers = new Set(allTrades.map(trade => trade.layer));
    return Array.from(layers).sort((a, b) => a - b);
  }, [allTrades]);

  // Filter trades
  const filteredTrades = useMemo(() => {
    let filtered = allTrades;

    if (selectedStrategy !== 'all') {
      filtered = filtered.filter(trade => trade.strategyName === selectedStrategy);
    }

    if (actionFilter !== 'all') {
      filtered = filtered.filter(trade => trade.action === actionFilter);
    }

    if (layerFilter !== 'all') {
      filtered = filtered.filter(trade => trade.layer === parseInt(layerFilter));
    }

    // Sort trades
    if (sortConfig) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;

        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return sortConfig.direction === 'asc'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        }

        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
        }

        return 0;
      });
    }

    return filtered;
  }, [allTrades, selectedStrategy, actionFilter, layerFilter, sortConfig]);

  const handleSort = (key: keyof Trade) => {
    setSortConfig(current => {
      if (!current || current.key !== key) {
        return { key, direction: 'asc' };
      }
      if (current.direction === 'asc') {
        return { key, direction: 'desc' };
      }
      return null;
    });
  };

  const downloadTradesCSV = () => {
    const headers = [
      'Timestamp', 'Strategy', 'Action', 'Price', 'Quantity', 'P&L', 'Layer'
    ];

    const csvContent = [
      headers.join(','),
      ...filteredTrades.map(trade => [
        `"${formatDateTime(trade.timestamp)}"`,
        `"${trade.strategyName}"`,
        `"${trade.action}"`,
        trade.price.toFixed(2),
        trade.quantity.toFixed(8),
        trade.pnl ? trade.pnl.toFixed(2) : '',
        trade.layer
      ].join(','))
    ].join('\n');

    downloadCSV(csvContent, `trades_${new Date().toISOString().split('T')[0]}.csv`);
  };

  const totalPnL = filteredTrades.reduce((sum, trade) =>
    sum + (trade.pnl || 0), 0
  );

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold flex items-center">
          <Filter className="h-5 w-5 mr-2" />
          Trading History ({filteredTrades.length} trades)
        </h3>
        <button
          onClick={downloadTradesCSV}
          disabled={filteredTrades.length === 0}
          className="btn-secondary flex items-center text-sm disabled:opacity-50"
        >
          <Download className="h-4 w-4 mr-1" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <label className="form-label mb-2 block">Strategy</label>
          <select
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
            className="form-input"
          >
            <option value="all">All Strategies</option>
            {Object.keys(results).map(strategy => (
              <option key={strategy} value={strategy}>{strategy}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="form-label mb-2 block">Action</label>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="form-input"
          >
            <option value="all">All Actions</option>
            <option value="BUY">Buy Only</option>
            <option value="SELL">Sell Only</option>
          </select>
        </div>

        <div>
          <label className="form-label mb-2 block">Layer</label>
          <select
            value={layerFilter}
            onChange={(e) => setLayerFilter(e.target.value)}
            className="form-input"
          >
            <option value="all">All Layers</option>
            {availableLayers.map(layer => (
              <option key={layer} value={layer}>Layer {layer}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="form-label mb-2 block">Summary</label>
          <div className="text-sm">
            <div>Total P&L: <span className={totalPnL >= 0 ? 'text-success-600' : 'text-danger-600'}>
              {formatCurrency(totalPnL)}
            </span></div>
            <div>Trades: {filteredTrades.length}</div>
          </div>
        </div>
      </div>

      {/* Trades Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                onClick={() => handleSort('timestamp')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Timestamp
                  <ArrowUpDown className="h-4 w-4 ml-1" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Strategy
              </th>
              <th
                onClick={() => handleSort('action')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Action
                  <ArrowUpDown className="h-4 w-4 ml-1" />
                </div>
              </th>
              <th
                onClick={() => handleSort('price')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Price
                  <ArrowUpDown className="h-4 w-4 ml-1" />
                </div>
              </th>
              <th
                onClick={() => handleSort('quantity')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Quantity
                  <ArrowUpDown className="h-4 w-4 ml-1" />
                </div>
              </th>
              <th
                onClick={() => handleSort('pnl')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  P&L
                  <ArrowUpDown className="h-4 w-4 ml-1" />
                </div>
              </th>
              <th
                onClick={() => handleSort('layer')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Layer
                  <ArrowUpDown className="h-4 w-4 ml-1" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredTrades.map((trade, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatDateTime(trade.timestamp)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {trade.strategyName}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    trade.action === 'BUY'
                      ? 'bg-success-100 text-success-800'
                      : 'bg-danger-100 text-danger-800'
                  }`}>
                    {trade.action}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatCurrency(trade.price)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {trade.quantity.toFixed(8)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {trade.pnl !== null && trade.pnl !== undefined ? (
                    <span className={trade.pnl >= 0 ? 'text-success-600' : 'text-danger-600'}>
                      {formatCurrency(trade.pnl)}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {trade.layer}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredTrades.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No trades found with the selected filters
          </div>
        )}
      </div>
    </div>
  );
};

export default TradesTable;