import { useState } from 'react';
import { apiClient } from '../../lib/api';
import type { InvestmentCatalogPayload } from '../../types/api';
import { formatPercent } from '../../lib/utils';

interface InvestmentProductDataPlanPanelProps {
  plan?: InvestmentCatalogPayload['product_data_plan'];
  onRefreshComplete?: () => Promise<void> | void;
}

export default function InvestmentProductDataPlanPanel({
  plan,
  onRefreshComplete,
}: InvestmentProductDataPlanPanelProps) {
  const [refreshStatus, setRefreshStatus] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState('b3_fii_listed');
  const [forceRefresh, setForceRefresh] = useState(true);

  if (!plan) {
    return null;
  }

  async function refreshSelectedSource() {
    setIsRefreshing(true);
    setRefreshError(null);
    setRefreshStatus(null);
    try {
      const response = await apiClient.refreshInvestmentProductData({
        source_id: selectedSourceId,
        force: forceRefresh,
      });
      const rowCount = response.manifest?.row_count ?? 0;
      if (onRefreshComplete) {
        await onRefreshComplete();
      }
      setRefreshStatus(`${response.status_label}: ${rowCount} linha(s) em cache. Catálogo recarregado.`);
    } catch (error: any) {
      setRefreshError(
        error?.response?.data?.detail || 'Nao foi possivel atualizar os dados de produto.'
      );
    } finally {
      setIsRefreshing(false);
    }
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {plan.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {plan.plain_language_summary}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {typeof plan.roadmap_completion_pct === 'number' ? (
            <div className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
              Roadmap {formatPercent(plan.roadmap_completion_pct)} concluído
            </div>
          ) : null}
          <div className="rounded-full border border-blue-300 bg-blue-50 px-3 py-2 text-xs font-medium text-blue-800 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-200">
            {plan.connected_source_count + plan.partial_source_count}/{plan.source_count} fontes em uso
          </div>
        </div>
      </div>

      {plan.source_manifest ? (
        <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
                {plan.source_manifest.title}
              </div>
              <p className="mt-1 text-xs leading-5 text-blue-900/80 dark:text-blue-100/80">
                {plan.source_manifest.plain_language_summary}
              </p>
            </div>
            <div className="rounded-full border border-blue-300 bg-white px-3 py-2 text-xs font-medium text-blue-800 dark:border-blue-800 dark:bg-gray-950/40 dark:text-blue-200">
              {plan.source_manifest.warm_source_count}/{plan.source_manifest.source_count} com cache
            </div>
            <label className="text-xs font-medium text-blue-900 dark:text-blue-100">
              <span className="sr-only">Fonte</span>
              <select
                value={selectedSourceId}
                onChange={(event) => setSelectedSourceId(event.target.value)}
                className="rounded-full border border-blue-300 bg-white px-3 py-2 text-xs text-blue-900 dark:border-blue-800 dark:bg-gray-950/40 dark:text-blue-100"
              >
                {plan.sources.map((source) => (
                  <option key={source.source_id} value={source.source_id}>
                    {source.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs font-medium text-blue-900 dark:text-blue-100">
              <input
                type="checkbox"
                checked={forceRefresh}
                onChange={(event) => setForceRefresh(event.target.checked)}
              />
              forçar
            </label>
            <button
              type="button"
              className="btn-secondary"
              disabled={isRefreshing}
              onClick={() => void refreshSelectedSource()}
            >
              {isRefreshing ? 'Atualizando...' : 'Atualizar fonte'}
            </button>
          </div>
          {refreshStatus ? (
            <div className="mt-3 rounded-lg border border-emerald-300 bg-white px-3 py-2 text-xs text-emerald-800 dark:border-emerald-800 dark:bg-gray-950/40 dark:text-emerald-200">
              {refreshStatus}
            </div>
          ) : null}
          {refreshError ? (
            <div className="mt-3 rounded-lg border border-red-300 bg-white px-3 py-2 text-xs text-red-800 dark:border-red-800 dark:bg-gray-950/40 dark:text-red-200">
              {refreshError}
            </div>
          ) : null}
          <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
            {plan.source_manifest.sources.map((source) => (
              <div
                key={source.source_id}
                className="rounded-lg border border-blue-200 bg-white p-3 text-xs dark:border-blue-900/60 dark:bg-gray-950/40"
              >
                <div className="font-semibold text-blue-950 dark:text-blue-100">
                  {source.cache_key}
                </div>
                <div className="mt-1 text-blue-900/80 dark:text-blue-100/80">
                  {source.file_count} arquivo(s) · {source.freshness_label}
                </div>
                {source.row_count ? (
                  <div className="mt-1 text-blue-900/70 dark:text-blue-100/70">
                    {source.row_count} linha(s) · {source.schema_version}
                  </div>
                ) : null}
                <div className="mt-2">
                  <StatusBadge status={source.connector_status} />
                </div>
                {source.refresh_history?.length ? (
                  <div className="mt-2 text-[11px] leading-5 text-blue-900/70 dark:text-blue-100/70">
                    Último refresh: {source.refresh_history[0].status_label}
                    {source.refresh_history[0].duration_ms !== undefined
                      ? ` · ${source.refresh_history[0].duration_ms} ms`
                      : ''}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 xl:grid-cols-4">
        {plan.sources.map((source) => (
          <article
            key={source.source_id}
            className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40"
          >
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              {source.label}
            </div>
            <p className="mt-2 text-xs leading-5 text-gray-600 dark:text-gray-300">
              {source.coverage}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <StatusBadge status={source.integration_status} />
              {source.connector_status ? <StatusBadge status={source.connector_status} /> : null}
              <span className="rounded-full border border-gray-300 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300">
                {source.freshness_policy}
              </span>
            </div>
            {source.expected_fields?.length ? (
              <div className="mt-3 text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                Campos: {source.expected_fields.slice(0, 3).join(', ')}
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            Cobertura por família
          </div>
          <div className="mt-3 space-y-2">
            {plan.family_coverage.slice(0, 6).map((family) => (
              <div
                key={family.family_id}
                className="flex flex-wrap items-center justify-between gap-3 text-sm text-gray-600 dark:text-gray-300"
              >
                <span>{family.label}</span>
                <span className="font-semibold text-gray-950 dark:text-gray-100">
                  {formatPercent(family.coverage_score)} · {family.external_data_status}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
          <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
            Próximos pacotes
          </div>
          <div className="mt-3 space-y-3">
            {plan.next_release_candidates.map((candidate) => (
              <div key={candidate.release_id}>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
                    {candidate.label}
                  </div>
                  {candidate.status ? <StatusBadge status={candidate.status} /> : null}
                </div>
                <p className="mt-1 text-xs leading-5 text-emerald-900/80 dark:text-emerald-100/80">
                  {candidate.user_value}
                </p>
                {candidate.ranking_candidates?.length ? (
                  <div className="mt-2 text-[11px] leading-5 text-emerald-900/70 dark:text-emerald-100/70">
                    Rankings: {candidate.ranking_candidates.join(', ')}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        {plan.catalog_enrichment?.length ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              Enriquecimento do catálogo
            </div>
            <div className="mt-3 space-y-3">
              {plan.catalog_enrichment.map((item) => (
                <div key={`${item.family_id}-${item.source_id}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-600 dark:text-gray-300">
                    <span>{item.family_id}</span>
                    <StatusBadge status={item.status} />
                  </div>
                  <div className="mt-1 text-xs text-gray-600 dark:text-gray-300">
                    {item.matched_instrument_count}/{item.cached_row_count} item(ns) ligados.
                  </div>
                  <div className="mt-2 text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                    {item.next_action}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {plan.identity_map?.length ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              Identidade FII
            </div>
            <div className="mt-3 text-xs leading-5 text-gray-600 dark:text-gray-300">
              {plan.identity_map.length} ticker(s) mapeados entre fonte externa e catálogo.
            </div>
          </div>
        ) : null}

        {plan.fii_cvm_bridge ? (
          <div className="rounded-xl border border-teal-200 bg-teal-50/70 p-4 dark:border-teal-900/50 dark:bg-teal-950/20">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-teal-950 dark:text-teal-100">
                Ponte FII ↔ CVM
              </div>
              <StatusBadge status={plan.fii_cvm_bridge.status} />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-teal-900 dark:text-teal-100">
              <Metric
                label="Mapeados"
                value={String(plan.fii_cvm_bridge.mapped_instrument_count)}
              />
              <Metric
                label="No cache CVM"
                value={`${plan.fii_cvm_bridge.matched_cvm_cache_count} · ${formatPercent(plan.fii_cvm_bridge.coverage_ratio)}`}
              />
            </div>
            {plan.fii_cvm_bridge.rows.length ? (
              <div className="mt-3 space-y-1 text-[11px] text-teal-900 dark:text-teal-100">
                {plan.fii_cvm_bridge.rows.slice(0, 3).map((row) => (
                  <div key={`${row.ticker}-${row.cnpj_fundo}`} className="flex justify-between gap-3">
                    <span>
                      {row.ticker} · {row.cnpj_fundo}
                    </span>
                    <span>{row.latest_date ?? 'aguardando cache'}</span>
                  </div>
                ))}
              </div>
            ) : null}
            <p className="mt-3 text-[11px] leading-5 text-teal-900/80 dark:text-teal-100/80">
              {plan.fii_cvm_bridge.methodology}
            </p>
          </div>
        ) : null}

        {plan.cvm_fund_profile ? (
          <div className="rounded-xl border border-sky-200 bg-sky-50/70 p-4 dark:border-sky-900/50 dark:bg-sky-950/20">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-sky-950 dark:text-sky-100">
                Perfil CVM de fundos
              </div>
              <StatusBadge status={plan.cvm_fund_profile.status} />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-sky-900 dark:text-sky-100">
              <Metric label="Linhas" value={String(plan.cvm_fund_profile.row_count)} />
              <Metric label="Data" value={plan.cvm_fund_profile.latest_date ?? 'sem cache'} />
              <Metric
                label="PL"
                value={formatCurrencyShort(plan.cvm_fund_profile.total_net_worth)}
              />
              <Metric
                label="Fluxo líquido"
                value={formatCurrencyShort(plan.cvm_fund_profile.net_flow)}
              />
            </div>
            <p className="mt-3 text-[11px] leading-5 text-sky-900/80 dark:text-sky-100/80">
              {plan.cvm_fund_profile.methodology}
            </p>
            {plan.cvm_fund_profile.sample_largest_funds.length ? (
              <div className="mt-3 space-y-1 text-[11px] text-sky-900 dark:text-sky-100">
                {plan.cvm_fund_profile.sample_largest_funds.slice(0, 3).map((fund) => (
                  <div
                    key={`${fund.cnpj_fundo}-${fund.net_worth}`}
                    className="flex justify-between gap-3"
                  >
                    <span>{fund.cnpj_fundo}</span>
                    <span>{formatCurrencyShort(fund.net_worth)}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        {plan.cvm_fund_rankings?.length ? (
          <div className="rounded-xl border border-sky-200 bg-sky-50/70 p-4 dark:border-sky-900/50 dark:bg-sky-950/20">
            <div className="text-sm font-semibold text-sky-950 dark:text-sky-100">
              Rankings CVM iniciais
            </div>
            <div className="mt-3 space-y-3">
              {plan.cvm_fund_rankings.slice(0, 3).map((ranking) => (
                <div key={ranking.ranking_id}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-sky-950 dark:text-sky-100">
                      {ranking.label}
                    </span>
                    <StatusBadge status={ranking.status} />
                  </div>
                  <div className="mt-2 space-y-1 text-[11px] text-sky-900 dark:text-sky-100">
                    {ranking.rows.slice(0, 3).map((row) => (
                      <div key={`${ranking.ranking_id}-${row.cnpj_fundo}`} className="flex justify-between gap-3">
                        <span>
                          {row.rank}. {row.cnpj_fundo}
                        </span>
                        <span>{formatRankingScore(row.score, row.score_label)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[11px] leading-5 text-sky-900/80 dark:text-sky-100/80">
              {plan.cvm_fund_rankings[0].methodology}
            </p>
          </div>
        ) : null}

        {plan.etf_bdr_profile ? (
          <div className="rounded-xl border border-indigo-200 bg-indigo-50/70 p-4 dark:border-indigo-900/50 dark:bg-indigo-950/20">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-indigo-950 dark:text-indigo-100">
                ETFs/BDRs B3
              </div>
              <StatusBadge status={plan.etf_bdr_profile.status} />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-indigo-900 dark:text-indigo-100">
              <Metric label="Produtos" value={String(plan.etf_bdr_profile.row_count)} />
              <Metric
                label="Taxa média"
                value={
                  typeof plan.etf_bdr_profile.average_fee_pct === 'number'
                    ? `${plan.etf_bdr_profile.average_fee_pct.toFixed(2)}%`
                    : 'n/d'
                }
              />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {plan.etf_bdr_profile.product_type_counts.map((item) => (
                <span
                  key={item.product_type}
                  className="rounded-full border border-indigo-200 bg-white px-2 py-1 text-[11px] text-indigo-800 dark:border-indigo-800 dark:bg-gray-950/30 dark:text-indigo-100"
                >
                  {item.product_type} · {item.count}
                </span>
              ))}
            </div>
            {plan.etf_bdr_rankings?.length ? (
              <div className="mt-3 space-y-1 text-[11px] text-indigo-900 dark:text-indigo-100">
                {plan.etf_bdr_rankings[0].rows.slice(0, 3).map((row) => (
                  <div key={`${row.ticker}-${row.score}`} className="flex justify-between gap-3">
                    <span>
                      {row.rank}. {row.ticker} · {row.reference_index}
                    </span>
                    <span>{row.score.toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            ) : null}
            <p className="mt-3 text-[11px] leading-5 text-indigo-900/80 dark:text-indigo-100/80">
              {plan.etf_bdr_profile.methodology}
            </p>
          </div>
        ) : null}

        {plan.methodology_readiness_ranking?.rows.length ? (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
                {plan.methodology_readiness_ranking.label}
              </div>
              <StatusBadge status={plan.methodology_readiness_ranking.status} />
            </div>
            <div className="mt-3 space-y-2 text-[11px] text-emerald-900 dark:text-emerald-100">
              {plan.methodology_readiness_ranking.rows.slice(0, 4).map((row) => (
                <div key={row.instrument_id} className="rounded-lg border border-emerald-200 bg-white px-3 py-2 dark:border-emerald-800 dark:bg-gray-950/30">
                  <div className="flex justify-between gap-3">
                    <span>
                      {row.rank}. {row.ticker} · {row.product_family}
                    </span>
                    <span>{row.score.toFixed(1)}</span>
                  </div>
                  <div className="mt-1 text-emerald-900/75 dark:text-emerald-100/75">
                    {row.caveat}
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[11px] leading-5 text-emerald-900/80 dark:text-emerald-100/80">
              {plan.methodology_readiness_ranking.methodology}
            </p>
          </div>
        ) : null}

        {plan.roadmap_steps?.length ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              Roadmap 1-9
            </div>
            {typeof plan.roadmap_completed_step_count === 'number' &&
            typeof plan.roadmap_step_count === 'number' ? (
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {plan.roadmap_completed_step_count}/{plan.roadmap_step_count} etapa(s) prontas.
              </div>
            ) : null}
            <div className="mt-3 space-y-2">
              {plan.roadmap_steps.map((step, index) => (
                <div
                  key={step.step_id}
                  className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-600 dark:text-gray-300"
                >
                  <span>
                    {index + 1}. {step.label}
                  </span>
                  <StatusBadge status={step.status} />
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {plan.market_filter_backlog?.length ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              Filtros de mercado
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {plan.market_filter_backlog.map((filter) => (
                <span
                  key={filter.filter_id}
                  className="rounded-full border border-gray-300 bg-white px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:bg-gray-900/70 dark:text-gray-300"
                >
                  {filter.label}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {plan.validation_plan?.length ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
            <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
              Gates de validação
            </div>
            <div className="mt-3 space-y-2 text-xs text-gray-600 dark:text-gray-300">
              {plan.validation_plan.map((gate) => (
                <div key={gate.gate_id}>
                  <span className="font-semibold text-gray-950 dark:text-gray-100">
                    {gate.label}:
                  </span>{' '}
                  {gate.checks.slice(0, 2).join(', ')}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-sky-200 bg-white px-3 py-2 dark:border-sky-800 dark:bg-gray-950/30">
      <div className="text-[11px] text-sky-900/70 dark:text-sky-100/70">{label}</div>
      <div className="mt-1 font-semibold text-sky-950 dark:text-sky-100">{value}</div>
    </div>
  );
}

function formatCurrencyShort(value: number) {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) {
    return `R$ ${(value / 1_000_000_000).toFixed(1)} bi`;
  }
  if (abs >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)} mi`;
  }
  if (abs >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(1)} mil`;
  }
  return `R$ ${value.toFixed(0)}`;
}

function formatRankingScore(value: number, label: string) {
  if (label === 'Cotistas') {
    return `${value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })} cotistas`;
  }
  return formatCurrencyShort(value);
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'connected') {
    return (
      <span className="rounded-full border border-emerald-300 bg-emerald-50 px-2 py-1 text-[11px] font-medium text-emerald-700 dark:border-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">
        conectado
      </span>
    );
  }
  if (status === 'partial') {
    return (
      <span className="rounded-full border border-blue-300 bg-blue-50 px-2 py-1 text-[11px] font-medium text-blue-700 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
        parcial
      </span>
    );
  }
  if (
    status === 'available' ||
    status === 'available_seed' ||
    status === 'connected_next' ||
    status === 'connected_seeded' ||
    status === 'manifest_available' ||
    status === 'gated' ||
    status === 'enriched' ||
    status === 'refreshed' ||
    status === 'cache_hit'
  ) {
    return (
      <span className="rounded-full border border-cyan-300 bg-cyan-50 px-2 py-1 text-[11px] font-medium text-cyan-700 dark:border-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200">
        pronto
      </span>
    );
  }
  if (status === 'specified' || status === 'mapped' || status === 'backlog_mapped') {
    return (
      <span className="rounded-full border border-violet-300 bg-violet-50 px-2 py-1 text-[11px] font-medium text-violet-700 dark:border-violet-700 dark:bg-violet-950/30 dark:text-violet-200">
        mapeado
      </span>
    );
  }
  return (
    <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-700 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-200">
      planejado
    </span>
  );
}
