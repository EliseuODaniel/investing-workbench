import { useMemo } from 'react';
import { useWege3RegraA } from '../hooks/useWege3RegraA';
import {
  downloadCSV,
  downloadJSON,
  formatCurrency,
  formatDate,
  formatNumber,
  formatPercent,
} from '../lib/utils';
import { Wege3RegraATradePayload } from '../types/api';
import Wege3ComparisonChart from './wege3/Wege3ComparisonChart';

interface Wege3RegraAWorkspaceProps {
  onError: (message: string | null) => void;
}

type UnknownRecord = Record<string, unknown>;

function toTradesCsv(trades: Wege3RegraATradePayload[]): string {
  const header = [
    'timestamp',
    'action',
    'price',
    'notional',
    'quantity',
    'cash_after',
    'position_after',
    'reference_after',
  ];
  const rows = trades.map((trade) =>
    [
      trade.timestamp,
      trade.action,
      trade.price,
      trade.notional,
      trade.quantity,
      trade.cash_after,
      trade.position_after,
      trade.reference_after,
    ].join(',')
  );
  return [header.join(','), ...rows].join('\n');
}

function getNumber(payload: UnknownRecord, key: string): number {
  const value = payload[key];
  return typeof value === 'number' ? value : 0;
}

function getString(payload: UnknownRecord, key: string): string {
  const value = payload[key];
  return typeof value === 'string' ? value : 'n/a';
}

function getRecord(payload: UnknownRecord, key: string): UnknownRecord {
  const value = payload[key];
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as UnknownRecord)
    : {};
}

function getRecordArray(payload: UnknownRecord, key: string): UnknownRecord[] {
  const value = payload[key];
  return Array.isArray(value)
    ? value.filter((item): item is UnknownRecord => Boolean(item) && typeof item === 'object')
    : [];
}

function getStringArray(payload: UnknownRecord, key: string): string[] {
  const value = payload[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

export default function Wege3RegraAWorkspace({ onError }: Wege3RegraAWorkspaceProps) {
  const { draft, result, isRunning, updateDraft, runScenario } = useWege3RegraA(onError);

  const benchmarkRows = useMemo(() => {
    if (!result) return [];
    return Object.entries(result.benchmarks).map(([key, payload]) => ({
      id: key,
      label: key
        .replace('benchmark_', 'Benchmark ')
        .split('_')
        .join(' ')
        .replace('wege3', 'WEGE3'),
      finalTotal: getNumber(payload, 'final_total'),
      absoluteReturn: getNumber(payload, 'absolute_return'),
      percentageReturn: getNumber(payload, 'percentage_return'),
    }));
  }, [result]);

  const comparisonVariants = useMemo(
    () => (result?.comparison_variants as UnknownRecord[] | undefined) ?? [],
    [result]
  );
  const bestByFinal = useMemo(
    () => (result ? getRecord(result.best_strategy, 'by_final_total') : {}),
    [result]
  );
  const bestByTrading = useMemo(
    () => (result ? getRecord(result.best_strategy, 'by_trading_pnl') : {}),
    [result]
  );
  const parameterSearch = useMemo(() => result?.parameter_search ?? {}, [result]);
  const topProfiles = useMemo(
    () => getRecordArray(parameterSearch, 'top_profiles'),
    [parameterSearch]
  );
  const bestProgressiveProfile = useMemo(
    () => getRecord(parameterSearch, 'best_progressive_profile'),
    [parameterSearch]
  );
  const bestCashReserveProfile = useMemo(
    () => getRecord(parameterSearch, 'best_cash_reserve_profile'),
    [parameterSearch]
  );
  const strategyContext = useMemo(() => result?.strategy_context ?? {}, [result]);
  const comparisonChart = useMemo(() => result?.comparison_chart ?? {}, [result]);
  const assetProfile = useMemo(
    () => getRecord(strategyContext, 'asset_profile'),
    [strategyContext]
  );
  const recommendation = useMemo(
    () => getRecord(strategyContext, 'recommendation'),
    [strategyContext]
  );
  const idealContext = useMemo(
    () => getStringArray(strategyContext, 'ideal_context'),
    [strategyContext]
  );
  const idealTraits = useMemo(
    () => getStringArray(strategyContext, 'ideal_stock_traits'),
    [strategyContext]
  );
  const wegeAssessment = useMemo(
    () => getStringArray(strategyContext, 'wege_assessment'),
    [strategyContext]
  );

  const corporateActions =
    ((result?.audit.corporate_actions as Array<Record<string, unknown>> | undefined) ?? []);
  const dividendCount = corporateActions.filter((event) => event.type === 'dividend').length;
  const splitCount = corporateActions.filter((event) => event.type === 'stock_split').length;
  const dataSources = ((result?.audit.data_sources as string[] | undefined) ?? []).join(' · ');

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-4xl">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              WEGE3 long-only lab
            </h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              A regra base continua aqui, mas agora o lab compara variantes long-only
              parecidas, busca perfis melhores e explica em que tipo de papel essa familia
              tende a funcionar melhor.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <label className="flex min-w-[160px] flex-col gap-2">
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Inicio
              </span>
              <input
                type="date"
                className="input-field"
                value={draft.startDate}
                onChange={(event) => updateDraft('startDate', event.target.value)}
              />
            </label>
            <label className="flex min-w-[160px] flex-col gap-2">
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Fim
              </span>
              <input
                type="date"
                className="input-field"
                value={draft.endDate}
                onChange={(event) => updateDraft('endDate', event.target.value)}
              />
            </label>
            <label className="flex items-center gap-3 rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-700 dark:border-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={draft.forceDownload}
                onChange={(event) => updateDraft('forceDownload', event.target.checked)}
              />
              Atualizar dados
            </label>
            <button
              type="button"
              onClick={() => void runScenario()}
              disabled={isRunning}
              className="rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRunning ? 'Rodando comparacao...' : 'Rodar comparacao'}
            </button>
          </div>
        </div>
      </div>

      {result ? (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
            <div className="card">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Regra base
              </div>
              <div className="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {formatCurrency(getNumber(result.result, 'saldo_final_total'))}
              </div>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {formatPercent(getNumber(result.result, 'retorno_percentual'))}
              </div>
            </div>
            <div className="card">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Melhor variante
              </div>
              <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
                {getString(bestByFinal, 'label')}
              </div>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {formatCurrency(getNumber(getRecord(bestByFinal, 'result'), 'saldo_final_total'))}
              </div>
            </div>
            <div className="card">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Melhor trade P&L
              </div>
              <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
                {getString(bestByTrading, 'label')}
              </div>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {formatCurrency(getNumber(getRecord(bestByTrading, 'decomposition'), 'trading_pnl'))}
              </div>
            </div>
            <div className="card">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Melhor perfil progressivo
              </div>
              <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
                {getString(bestProgressiveProfile, 'label')}
              </div>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Caixa reserva:{' '}
                {formatCurrency(getNumber(getRecord(bestProgressiveProfile, 'parameters'), 'cash_reserve'))}
              </div>
            </div>
            <div className="card">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Ultimo pregao
              </div>
              <div className="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {formatDate(getString(result.dataset, 'end_session'))}
              </div>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                WEGE3.SA
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="card">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Regra base: estatisticas
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Resumo da estrategia original para servir de ancora da comparacao.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      downloadCSV(toTradesCsv(result.trades), `${result.scenario_id}_trades.csv`)
                    }
                    className="rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                  >
                    Exportar trades base
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadJSON(result, `${result.scenario_id}_summary.json`)}
                    className="rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                  >
                    Exportar resumo JSON
                  </button>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Compras / vendas
                  </div>
                  <div className="mt-2 text-sm text-gray-900 dark:text-gray-100">
                    {getNumber(result.statistics, 'numero_total_compras')} /{' '}
                    {getNumber(result.statistics, 'numero_total_vendas')}
                  </div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Preco medio final
                  </div>
                  <div className="mt-2 text-sm text-gray-900 dark:text-gray-100">
                    {formatCurrency(
                      getNumber(result.statistics, 'preco_medio_compra_posicao_final')
                    )}
                  </div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    P&L realizado / nao realizado
                  </div>
                  <div className="mt-2 text-sm text-gray-900 dark:text-gray-100">
                    {formatCurrency(getNumber(result.statistics, 'pnl_realizado'))} /{' '}
                    {formatCurrency(getNumber(result.statistics, 'pnl_nao_realizado'))}
                  </div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Caixa / proventos
                  </div>
                  <div className="mt-2 text-sm text-gray-900 dark:text-gray-100">
                    {formatCurrency(getNumber(result.statistics, 'rendimento_acumulado_caixa'))} /{' '}
                    {formatCurrency(getNumber(result.statistics, 'proventos_recebidos'))}
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Diagnostico do papel
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Leitura do contexto ideal para essa familia de estrategia.
              </p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Retorno anualizado
                  </div>
                  <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatPercent(getNumber(assetProfile, 'annualized_return'))}
                  </div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Volatilidade anual
                  </div>
                  <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatPercent(getNumber(assetProfile, 'annualized_volatility'))}
                  </div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Grid fit
                  </div>
                  <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatPercent(getNumber(assetProfile, 'grid_fit_score'))}
                  </div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Trend fit
                  </div>
                  <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatPercent(getNumber(assetProfile, 'trend_fit_score'))}
                  </div>
                </div>
              </div>
              <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900 dark:border-blue-900/60 dark:bg-blue-950/30 dark:text-blue-100">
                {getString(strategyContext, 'fit_summary')}
              </div>
            </div>
          </div>

          <Wege3ComparisonChart chart={comparisonChart} />

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Comparacao entre estrategias long-only
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Variantes proximas da Regra A, sem venda descoberta e sem operar alavancado.
            </p>
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    <th className="pb-3 pr-4">Estrategia</th>
                    <th className="pb-3 pr-4">Saldo final</th>
                    <th className="pb-3 pr-4">Trade P&L</th>
                    <th className="pb-3 pr-4">Caixa</th>
                    <th className="pb-3 pr-4">Max DD</th>
                    <th className="pb-3 pr-4">Sharpe</th>
                    <th className="pb-3 pr-4">Params</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {comparisonVariants.map((variant) => {
                    const variantResult = getRecord(variant, 'result');
                    const variantDecomposition = getRecord(variant, 'decomposition');
                    const variantMetrics = getRecord(variant, 'metrics');
                    const variantParameters = getRecord(variant, 'parameters');
                    return (
                      <tr key={getString(variant, 'strategy_id')}>
                        <td className="py-3 pr-4 align-top">
                          <div className="font-medium text-gray-900 dark:text-gray-100">
                            {getString(variant, 'label')}
                          </div>
                          <div className="mt-1 max-w-sm text-xs text-gray-500 dark:text-gray-400">
                            {getString(variant, 'description')}
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatCurrency(getNumber(variantResult, 'saldo_final_total'))}
                          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            {formatPercent(getNumber(variantResult, 'retorno_percentual'))}
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatCurrency(getNumber(variantDecomposition, 'trading_pnl'))}
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatCurrency(getNumber(variantDecomposition, 'cash_yield'))}
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatPercent(getNumber(variantMetrics, 'max_drawdown'))}
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatNumber(getNumber(variantMetrics, 'sharpe'), 2)}
                        </td>
                        <td className="py-3 pr-4 text-xs text-gray-500 dark:text-gray-400">
                          entrada {formatCurrency(getNumber(variantParameters, 'initial_investment'))}
                          <br />
                          lote {formatCurrency(getNumber(variantParameters, 'base_order_notional'))}
                          <br />
                          mult {formatNumber(getNumber(variantParameters, 'buy_multiplier'), 2)}
                          <br />
                          reserva {formatCurrency(getNumber(variantParameters, 'cash_reserve'))}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_1fr]">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Busca de parametros
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Perfis gerados para descobrir se compras progressivamente maiores e reservas
                de caixa melhoram o resultado.
              </p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Melhor progressivo
                  </div>
                  <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {getString(bestProgressiveProfile, 'label')}
                  </div>
                  <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    saldo {formatCurrency(getNumber(getRecord(bestProgressiveProfile, 'result'), 'saldo_final_total'))}
                  </div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/70">
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Melhor reserva
                  </div>
                  <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatCurrency(
                      getNumber(getRecord(bestCashReserveProfile, 'parameters'), 'cash_reserve')
                    )}
                  </div>
                  <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    saldo {formatCurrency(getNumber(getRecord(bestCashReserveProfile, 'result'), 'saldo_final_total'))}
                  </div>
                </div>
              </div>

              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      <th className="pb-3 pr-4">Perfil</th>
                      <th className="pb-3 pr-4">Saldo</th>
                      <th className="pb-3 pr-4">Mult</th>
                      <th className="pb-3 pr-4">Reserva</th>
                      <th className="pb-3 pr-4">Saida</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {topProfiles.slice(0, 6).map((profile) => {
                      const profileResult = getRecord(profile, 'result');
                      const profileParameters = getRecord(profile, 'parameters');
                      return (
                        <tr key={getString(profile, 'strategy_id')}>
                          <td className="py-3 pr-4 text-gray-900 dark:text-gray-100">
                            {getString(profile, 'label')}
                          </td>
                          <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                            {formatCurrency(getNumber(profileResult, 'saldo_final_total'))}
                          </td>
                          <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                            {formatNumber(getNumber(profileParameters, 'buy_multiplier'), 2)}
                          </td>
                          <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                            {formatCurrency(getNumber(profileParameters, 'cash_reserve'))}
                          </td>
                          <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                            {formatCurrency(getNumber(profileParameters, 'sell_grid_step'))}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Quando usar essa familia
              </h3>
              <div className="mt-4 space-y-4 text-sm text-gray-600 dark:text-gray-300">
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Contexto ideal
                  </div>
                  <ul className="mt-2 space-y-2">
                    {idealContext.map((item) => (
                      <li key={item}>- {item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Tipo de acao ideal
                  </div>
                  <ul className="mt-2 space-y-2">
                    {idealTraits.map((item) => (
                      <li key={item}>- {item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Leitura sobre WEGE
                  </div>
                  <ul className="mt-2 space-y-2">
                    {wegeAssessment.map((item) => (
                      <li key={item}>- {item}</li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 dark:border-sky-800/80 dark:bg-slate-950/80 dark:ring-1 dark:ring-sky-500/20">
                  <div className="text-xs uppercase tracking-wide text-blue-700 dark:text-sky-300">
                    Melhor abordagem testada
                  </div>
                  <div className="mt-2 text-sm font-semibold text-blue-900 dark:text-slate-50">
                    {getString(recommendation, 'best_strategy_label')}
                  </div>
                  <p className="mt-2 text-sm text-blue-800 dark:text-slate-200">
                    {getString(recommendation, 'why')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Comparacao com benchmarks
              </h3>
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      <th className="pb-3 pr-4">Benchmark</th>
                      <th className="pb-3 pr-4">Saldo final</th>
                      <th className="pb-3 pr-4">Retorno absoluto</th>
                      <th className="pb-3 pr-4">Retorno percentual</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {benchmarkRows.map((benchmark) => (
                      <tr key={benchmark.id}>
                        <td className="py-3 pr-4 font-medium text-gray-900 dark:text-gray-100">
                          {benchmark.label}
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatCurrency(benchmark.finalTotal)}
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatCurrency(benchmark.absoluteReturn)}
                        </td>
                        <td className="py-3 pr-4 text-gray-600 dark:text-gray-300">
                          {formatPercent(benchmark.percentageReturn)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Auditoria
              </h3>
              <div className="mt-4 space-y-3 text-sm text-gray-600 dark:text-gray-300">
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Artefatos gerados
                  </div>
                  <div className="mt-2 break-all">{result.artifacts.summary_output_path}</div>
                  <div className="break-all">{result.artifacts.trades_output_path}</div>
                  {result.artifacts.comparison_output_path ? (
                    <div className="break-all">{result.artifacts.comparison_output_path}</div>
                  ) : null}
                  {result.artifacts.search_output_path ? (
                    <div className="break-all">{result.artifacts.search_output_path}</div>
                  ) : null}
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Eventos corporativos
                  </div>
                  <div className="mt-2">
                    {dividendCount} dividendos/JCP e {splitCount} split ajustado
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Fonte dos dados
                  </div>
                  <div className="mt-2">{dataSources}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Comando de reproducao
                  </div>
                  <pre className="mt-2 overflow-x-auto rounded-xl bg-gray-950 px-4 py-3 text-xs text-gray-100">
                    {result.reproduction_command}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Trades da regra base
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {result.trades.length} operacoes auditaveis com caixa, posicao e referencia apos
              cada trade.
            </p>
            <div className="mt-4 max-h-[28rem] overflow-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800">
                <thead className="bg-gray-50 dark:bg-gray-900/40">
                  <tr className="text-left text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    <th className="px-3 py-2">Data</th>
                    <th className="px-3 py-2">Lado</th>
                    <th className="px-3 py-2">Preco</th>
                    <th className="px-3 py-2">Valor</th>
                    <th className="px-3 py-2">Quantidade</th>
                    <th className="px-3 py-2">Caixa apos</th>
                    <th className="px-3 py-2">Posicao apos</th>
                    <th className="px-3 py-2">Referencia apos</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {result.trades.map((trade, index) => (
                    <tr key={`${trade.timestamp}_${trade.action}_${index}`}>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
                        {formatDate(trade.timestamp)}
                      </td>
                      <td className="px-3 py-2 font-medium text-gray-900 dark:text-gray-100">
                        {trade.action}
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
                        {formatCurrency(trade.price)}
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
                        {formatCurrency(trade.notional)}
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
                        {formatNumber(trade.quantity, 6)}
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
                        {formatCurrency(trade.cash_after)}
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
                        {formatNumber(trade.position_after, 6)}
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
                        {formatCurrency(trade.reference_after)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="card text-sm text-gray-500 dark:text-gray-400">
          Rode o lab para comparar a regra base com outras variantes long-only e descobrir
          em que contexto essa familia faz mais sentido.
        </div>
      )}
    </div>
  );
}
