import { BarChart3 } from 'lucide-react';
import { ResultsSummaryHeroProps } from './types';

export default function ResultsSummaryHero({
  backtestRequest,
  backtestResponse,
  totalTradesCount,
}: ResultsSummaryHeroProps) {
  const benchmarkLabels = [
    ...(backtestRequest.include_buy_hold_benchmark !== false ? ['Buy & Hold'] : []),
    ...(backtestRequest.include_selic_benchmark ? ['SELIC'] : []),
    ...(backtestRequest.benchmarks ?? []),
  ];
  const strategyResults = Object.values(backtestResponse.results);
  const totalFeesPaid = strategyResults.reduce(
    (total, result) => total + (result.metrics.total_fees_paid ?? 0),
    0
  );
  const partialFillCount = strategyResults.reduce(
    (total, result) => total + (result.execution_summary?.partial_fill_count ?? 0),
    0
  );
  const rejectedOrderCount = strategyResults.reduce(
    (total, result) => total + (result.execution_summary?.rejected_order_count ?? 0),
    0
  );
  const liquidityConstrainedStrategies = strategyResults.filter(
    (result) => result.execution_summary?.liquidity_constrained
  ).length;

  return (
    <div className="card border-green-200 bg-gradient-to-r from-green-50 to-emerald-100 dark:border-green-800 dark:from-green-900/20 dark:to-emerald-900/20">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-green-100 dark:bg-green-800">
            <BarChart3 className="h-4 w-4 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
              Resumo do Backtest
            </h3>
            <p className="mt-1 text-sm text-green-800 dark:text-green-200">
              Os graficos ficam na aba principal. Aqui entram o contexto do teste e a leitura
              numerica antes do detalhamento completo.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-green-900 dark:bg-green-950/40 dark:text-green-100">
            {backtestResponse.data_info.total_days} dias
          </span>
          <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-green-900 dark:bg-green-950/40 dark:text-green-100">
            {backtestRequest.strategies?.length || 0} estrategias
          </span>
          <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-green-900 dark:bg-green-950/40 dark:text-green-100">
            {benchmarkLabels.length} benchmarks
          </span>
          <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-green-900 dark:bg-green-950/40 dark:text-green-100">
            {totalTradesCount} trades
          </span>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div>
          <div className="mb-1 text-xs font-medium text-green-600 dark:text-green-400">Periodo</div>
          <div className="text-sm text-green-900 dark:text-green-100">
            {new Date(backtestResponse.data_info.start_date).toLocaleDateString('pt-BR')} -{' '}
            {new Date(backtestResponse.data_info.end_date).toLocaleDateString('pt-BR')}
          </div>
        </div>

        <div>
          <div className="mb-1 text-xs font-medium text-green-600 dark:text-green-400">
            Capital inicial
          </div>
          <div className="text-sm font-semibold text-green-900 dark:text-green-100">
            R${' '}
            {(backtestRequest.initial_capital || 0).toLocaleString('pt-BR', {
              minimumFractionDigits: 2,
            })}
          </div>
          {backtestRequest.apply_cash_yield && (
            <div className="text-xs text-green-700 dark:text-green-300">
              Caixa remunerado com SELIC {backtestRequest.use_real_selic ? 'real' : 'fixa'}
            </div>
          )}
        </div>

        <div>
          <div className="mb-1 text-xs font-medium text-green-600 dark:text-green-400">
            Estrategias
          </div>
          <div className="flex flex-wrap gap-1">
            {backtestRequest.strategies?.map((strategy) => (
              <span
                key={strategy}
                className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800 dark:bg-blue-800 dark:text-blue-200"
              >
                {strategy}
              </span>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-1 text-xs font-medium text-green-600 dark:text-green-400">
            Benchmarks ativos
          </div>
          <div className="flex flex-wrap gap-1">
            {benchmarkLabels.length > 0 ? (
              benchmarkLabels.map((benchmark) => (
                <span
                  key={benchmark}
                  className="rounded-full bg-white/70 px-2 py-1 text-xs font-medium text-green-900 dark:bg-green-950/40 dark:text-green-100"
                >
                  {benchmark}
                </span>
              ))
            ) : (
              <span className="text-sm text-green-900 dark:text-green-100">Nenhum benchmark</span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-green-200 bg-white/70 px-4 py-3 dark:border-green-800 dark:bg-green-950/30">
          <div className="text-xs font-medium text-green-600 dark:text-green-400">
            Custo total de execucao
          </div>
          <div className="mt-1 text-sm font-semibold text-green-900 dark:text-green-100">
            R$ {totalFeesPaid.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="rounded-xl border border-green-200 bg-white/70 px-4 py-3 dark:border-green-800 dark:bg-green-950/30">
          <div className="text-xs font-medium text-green-600 dark:text-green-400">
            Fills parciais
          </div>
          <div className="mt-1 text-sm font-semibold text-green-900 dark:text-green-100">
            {partialFillCount}
          </div>
          <div className="text-xs text-green-700 dark:text-green-300">
            {liquidityConstrainedStrategies} estrategia(s) sentiram limite de liquidez
          </div>
        </div>

        <div className="rounded-xl border border-green-200 bg-white/70 px-4 py-3 dark:border-green-800 dark:bg-green-950/30">
          <div className="text-xs font-medium text-green-600 dark:text-green-400">
            Ordens rejeitadas
          </div>
          <div className="mt-1 text-sm font-semibold text-green-900 dark:text-green-100">
            {rejectedOrderCount}
          </div>
          <div className="text-xs text-green-700 dark:text-green-300">
            Rejeicoes por caixa insuficiente ou liquidez indisponivel
          </div>
        </div>
      </div>

      {backtestResponse.run_info?.run_id && (
        <div className="mt-4 border-t border-green-200 pt-4 text-xs text-green-700 dark:border-green-700 dark:text-green-300">
          Run ID: <span className="font-mono">{backtestResponse.run_info.run_id}</span>
          {backtestResponse.run_info.data_fingerprint && (
            <>
              {' '}
              | Data:{' '}
              <span className="font-mono">
                {backtestResponse.run_info.data_fingerprint.slice(0, 12)}
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
