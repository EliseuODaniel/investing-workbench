import { useState } from 'react';
import { apiClient } from '../../lib/api';
import type {
  InvestmentCatalogPayload,
  InvestmentMarketRankingsSnapshotPayload,
} from '../../types/api';
import InvestmentMarketRankingsPanel from './InvestmentMarketRankingsPanel';
import InvestmentMarketScreenersPanel from './InvestmentMarketScreenersPanel';

interface InvestmentMarketExplorerPanelProps {
  explorer?: InvestmentCatalogPayload['market_explorer'];
  selectedPresetId?: string;
}

export default function InvestmentMarketExplorerPanel({
  explorer,
  selectedPresetId = 'first_steps',
}: InvestmentMarketExplorerPanelProps) {
  const [snapshot, setSnapshot] = useState<InvestmentMarketRankingsSnapshotPayload | null>(null);
  const [isLoadingSnapshot, setIsLoadingSnapshot] = useState(false);
  const [snapshotError, setSnapshotError] = useState<string | null>(null);

  if (!explorer) {
    return null;
  }

  async function buildMarketSnapshot() {
    setIsLoadingSnapshot(true);
    setSnapshotError(null);
    try {
      const response = await apiClient.buildInvestmentMarketRankings({
        preset_id: selectedPresetId,
        benchmark_ids: ['selic_cash'],
      });
      setSnapshot(response);
    } catch (error: any) {
      setSnapshotError(
        error?.response?.data?.detail || 'Nao foi possivel gerar os rankings de mercado.'
      );
    } finally {
      setIsLoadingSnapshot(false);
    }
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {explorer.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {explorer.plain_language_summary}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="rounded-full border border-gray-300 bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200">
            {(explorer.curated_lists?.length ?? explorer.category_lists.length)} listas
          </div>
          <button
            type="button"
            className="btn-secondary"
            disabled={isLoadingSnapshot}
            onClick={() => void buildMarketSnapshot()}
          >
            {isLoadingSnapshot ? 'Gerando...' : 'Gerar rankings'}
          </button>
        </div>
      </div>

      {explorer.curated_lists?.length ? (
        <div className="mt-5">
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            Listas temáticas
          </div>
          <div className="mt-3 grid gap-4 xl:grid-cols-3">
            {explorer.curated_lists.slice(0, 6).map((list) => (
              <article
                key={list.list_id}
                className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
                    {list.label}
                  </div>
                  <span className="rounded-full border border-emerald-300 bg-white px-2 py-1 text-[11px] text-emerald-700 dark:border-emerald-800 dark:bg-gray-950/40 dark:text-emerald-200">
                    {list.count}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-emerald-900/80 dark:text-emerald-100/80">
                  {list.description}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {list.sample_labels.map((label) => (
                    <span
                      key={`${list.list_id}-${label}`}
                      className="rounded-full border border-emerald-200 bg-white px-2 py-1 text-[11px] text-emerald-700 dark:border-emerald-800 dark:bg-gray-950/40 dark:text-emerald-200"
                    >
                      {label}
                    </span>
                  ))}
                </div>
                <div className="mt-3 text-[11px] leading-5 text-emerald-900/70 dark:text-emerald-100/70">
                  Riscos: {list.risk_labels.join(', ')}
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        {explorer.category_lists.slice(0, 6).map((list) => (
          <article
            key={list.list_id}
            className="rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                {list.label}
              </div>
              <span className="rounded-full border border-gray-300 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300">
                {list.count}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {list.sample_labels.map((label) => (
                <span
                  key={`${list.list_id}-${label}`}
                  className="rounded-full border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:bg-gray-900/70 dark:text-gray-300"
                >
                  {label}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        <FacetBox title="Tipos de produto" items={explorer.product_type_facets} />
        <FacetBox title="Risco" items={explorer.risk_facets} />
        <FacetBox title="Região" items={explorer.region_facets} />
      </div>

      {explorer.product_data_filters?.length || explorer.product_data_screeners?.length ? (
        <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
          <div className="text-sm font-semibold text-emerald-950 dark:text-emerald-100">
            Filtros com dados externos
          </div>
          <div className="mt-3 grid gap-3 xl:grid-cols-2">
            {explorer.product_data_filters?.map((filter) => (
              <article
                key={filter.filter_id}
                className="rounded-xl border border-emerald-200 bg-white p-3 text-xs dark:border-emerald-800 dark:bg-gray-950/30"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-emerald-950 dark:text-emerald-100">
                    {filter.label}
                  </span>
                  <StatusBadge status={filter.status} />
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {filter.options.map((option) => (
                    <span
                      key={`${filter.filter_id}-${option.value}`}
                      className="rounded-full border border-emerald-200 px-2 py-1 text-[11px] text-emerald-800 dark:border-emerald-800 dark:text-emerald-100"
                    >
                      {option.label} · {option.count}
                    </span>
                  ))}
                </div>
              </article>
            ))}
            {explorer.product_data_screeners?.map((screener) => (
              <article
                key={screener.screener_id}
                className="rounded-xl border border-emerald-200 bg-white p-3 text-xs dark:border-emerald-800 dark:bg-gray-950/30"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-emerald-950 dark:text-emerald-100">
                    {screener.label}
                  </span>
                  <StatusBadge status={screener.status} />
                </div>
                <p className="mt-2 leading-5 text-emerald-900/80 dark:text-emerald-100/80">
                  {screener.methodology}
                </p>
                <div className="mt-2 text-[11px] text-emerald-900/70 dark:text-emerald-100/70">
                  {screener.rows.length} ativo(s) com metadados ligados.
                </div>
                <div className="mt-2 space-y-1">
                  {screener.rows.slice(0, 3).map((row) => (
                    <div
                      key={row.instrument_id}
                      className="grid grid-cols-[1fr_auto] gap-3 text-[11px] text-emerald-900 dark:text-emerald-100"
                    >
                      <span>
                        {row.label}
                        {row.income_focus ? ` · ${row.income_focus}` : ''}
                      </span>
                      <span>
                        {typeof row.yield_12m_pct === 'number'
                          ? `${row.yield_12m_pct.toFixed(1)}%`
                          : 'yield n/d'}
                      </span>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
          {explorer.product_data_rankings?.length ? (
            <div className="mt-3 grid gap-3 xl:grid-cols-2">
              {explorer.product_data_rankings.map((ranking) => (
                <article
                  key={ranking.ranking_id}
                  className="rounded-xl border border-emerald-200 bg-white p-3 text-xs dark:border-emerald-800 dark:bg-gray-950/30"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold text-emerald-950 dark:text-emerald-100">
                      {ranking.label}
                    </span>
                    <StatusBadge status={ranking.status} />
                  </div>
                  <p className="mt-2 leading-5 text-emerald-900/80 dark:text-emerald-100/80">
                    {ranking.methodology}
                  </p>
                  <div className="mt-2 space-y-1">
                    {ranking.rows.slice(0, 4).map((row) => (
                      <div key={row.instrument_id} className="flex justify-between gap-3">
                        <span>{row.rank}. {row.label}</span>
                        <span>{row.score.toFixed(1)}</span>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mt-5 rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
        <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
          Rankings de mercado
        </div>
        <p className="mt-2 max-w-4xl text-xs leading-5 text-blue-900/80 dark:text-blue-100/80">
          Estruturas de rankear ativos para inspirar escolha objetiva. Hoje alguns ja sao aplicados nos
          blocos de resultado, e outros seguem em evolucao.
        </p>
        <div className="mt-3 space-y-3">
          {explorer.ranking_backlog.map((item) => (
            <article
              key={item.ranking_id}
              className="rounded-2xl border border-blue-200 bg-white px-3 py-2 text-xs text-blue-900 dark:border-blue-800 dark:bg-gray-950/30 dark:text-blue-100"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">{item.label}</span>
                <StatusBadge status={item.status} />
              </div>
              <p className="mt-1 text-[11px] leading-5 text-blue-900/80 dark:text-blue-100/80">
                {rankingDescription(item)}
              </p>
            </article>
          ))}
        </div>
      </div>

      {snapshotError ? (
        <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-200">
          {snapshotError}
        </div>
      ) : null}

      {snapshot ? (
        <div className="mt-5 space-y-5">
          <InvestmentMarketRankingsPanel rankings={snapshot.market_rankings} />
          <InvestmentMarketScreenersPanel screeners={snapshot.market_screeners} />
        </div>
      ) : null}
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (
    status === 'available_in_result_stories' ||
    status === 'available_in_market_rankings' ||
    status === 'available' ||
    status === 'available_seed'
  ) {
    return (
      <span className="rounded-full border border-emerald-300 bg-emerald-50 px-2 py-1 text-[11px] font-medium text-emerald-700 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-100">
        disponivel
      </span>
    );
  }

  return (
    <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-700 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100">
      planejado
    </span>
  );
}

function rankingDescription(item: { ranking_id: string; status: string; label: string }) {
  if (item.status === 'available_in_market_rankings') {
    return `${item.label}: disponivel nos rankings exportaveis do resultado atual.`;
  }

  if (item.status === 'available_in_result_stories') {
    return `${item.label}: retorno, risco ou renda mostrados nas historias de resultado do estudo atual.`;
  }

  return `${item.label}: previsto no backlog para trazer consistencia de metodo, fonte e periodo de corte.`;
}

function FacetBox({
  title,
  items,
}: {
  title: string;
  items: Array<{ label: string; count: number }>;
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30">
      <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">{title}</div>
      <div className="mt-3 space-y-2">
        {items.slice(0, 6).map((item) => (
          <div
            key={`${title}-${item.label}`}
            className="flex items-center justify-between gap-3 text-sm text-gray-600 dark:text-gray-300"
          >
            <span>{item.label}</span>
            <span className="font-semibold text-gray-900 dark:text-gray-100">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
