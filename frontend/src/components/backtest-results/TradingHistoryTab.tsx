import React, { Suspense } from 'react';
import LoadingSpinner from '../LoadingSpinner';
import { TradingHistoryTabProps } from './types';

const TradesTable = React.lazy(() => import('../TradesTable'));

function lazyPanelFallback(message: string) {
  return (
    <div className="card">
      <LoadingSpinner message={message} />
    </div>
  );
}

export default function TradingHistoryTab({
  backtestResponse,
  totalTradesCount,
}: TradingHistoryTabProps) {
  return (
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
            Total Trades: <span className="font-semibold">{totalTradesCount}</span>
          </div>
        </div>
      </div>
      <Suspense fallback={lazyPanelFallback('Loading trades...')}>
        <TradesTable results={backtestResponse.results} />
      </Suspense>
    </div>
  );
}
