import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import InvestmentSetupStartTab from './InvestmentSetupStartTab';

const marketExplorer = {
  title: 'Explorador de mercado',
  plain_language_summary: 'Resumo do universo para iniciar comparações.',
  category_lists: [],
  product_type_facets: [],
  risk_facets: [],
  region_facets: [],
  ranking_backlog: [],
};

const productDataPlan = {
  title: 'Plano pos-roadmap de dados de produto',
  plain_language_summary: 'Fontes oficiais e cobertura por familia.',
  status: 'post_roadmap',
  source_count: 1,
  connected_source_count: 0,
  partial_source_count: 1,
  sources: [
    {
      source_id: 'b3_listed_products',
      label: 'B3 - Produtos listados',
      url: 'https://www.b3.com.br/',
      coverage: 'Produtos listados e dados publicos.',
      freshness_policy: 'refresh sob demanda',
      integration_status: 'partial',
      connector_status: 'partial',
      cache_key: 'b3_listed_products',
      families: ['stocks_brazil'],
      expected_fields: ['ticker', 'tipo_produto'],
    },
  ],
  family_coverage: [
    {
      family_id: 'stocks_brazil',
      label: 'Acoes brasileiras',
      instrument_count: 1,
      product_profile_count: 1,
      coverage_score: 1,
      external_data_status: 'partial',
    },
  ],
  source_manifest: {
    title: 'Manifesto local de dados externos',
    plain_language_summary: 'Mostra cache local por fonte.',
    cache_root: 'data/product_sources',
    checked_at: '2026-05-04T12:00:00Z',
    source_count: 1,
    warm_source_count: 0,
    stale_source_count: 0,
    sources: [
      {
        source_id: 'b3_listed_products',
        cache_key: 'b3_listed_products',
        cache_dir: 'data/product_sources/b3_listed_products',
        exists: false,
        file_count: 0,
        total_size_bytes: 0,
        latest_file_name: null,
        latest_file_at: null,
        age_days: null,
        freshness_status: 'empty',
        freshness_label: 'sem cache local',
        connector_status: 'partial',
        expected_fields: ['ticker', 'tipo_produto'],
        row_count: null,
        schema_version: null,
        checksum_sha256: null,
        collection_mode: null,
        refresh_history: [],
      },
    ],
    takeaways: ['Nenhuma fonte nova de produto tem cache local dedicado ainda.'],
  },
  catalog_enrichment: [
    {
      family_id: 'fiis',
      source_id: 'b3_fii_listed',
      matched_instrument_count: 0,
      cached_row_count: 0,
      status: 'waiting_for_cache',
      sample: [],
      next_action: 'Executar refresh de b3_fii_listed para ativar enriquecimento.',
    },
  ],
  implementation_steps: ['Criar inventario de fontes oficiais.'],
  roadmap_steps: [
    {
      step_id: 'dataset_versioning',
      label: 'Persistencia/versionamento dos datasets',
      status: 'manifest_available',
      release_ids: [],
    },
  ],
  next_release_candidates: [
    {
      release_id: 'etf_fee_tracking',
      label: 'ETFs/BDRs: taxa e tracking',
      source_ids: ['b3_listed_products'],
      user_value: 'Mostrar diferenca entre indice e produto investivel.',
      screeners_enabled: ['custo_etf'],
      ranking_candidates: ['taxa_administracao'],
      status: 'specified',
    },
  ],
  market_filter_backlog: [
    {
      filter_id: 'liquidity',
      label: 'Liquidez negociada',
      families: ['stocks_brazil'],
      status: 'needs_external_data',
    },
  ],
  validation_plan: [
    {
      gate_id: 'cache_manifest',
      label: 'Cache e manifesto',
      checks: ['timestamp de coleta', 'idade do cache'],
    },
  ],
  quality_gate: ['Fonte primaria ou secundaria marcada.'],
};

const investorEasyParity = {
  title: 'Paridade Investidor Facil',
  source_url: 'https://investidor-facil-gnje.vercel.app/',
  plain_language_summary: 'Mapa de funcionalidades e calculadoras educativas.',
  observed_at: '2026-05-05',
  calculator_count: 15,
  available_calculator_count: 15,
  feature_coverage: [
    {
      feature_id: 'organized_portfolio',
      label: 'Carteira organizada',
      site_offer: 'Painel simples.',
      local_status: 'available',
      local_surface: 'Carteiras e resultados.',
    },
  ],
  calculator_suite: [
    {
      calculator_id: 'compound_interest',
      label: 'Juros compostos',
      tier: 'basico',
      formula_family: 'future_value',
      status: 'available',
      local_surface: 'Comparador com aportes.',
    },
  ],
  plan_equivalence: [
    {
      plan_label: 'Gratis',
      site_limit: '5 calculadoras basicas.',
      local_equivalent: 'Grupo Basico sem bloqueio local.',
    },
  ],
  remaining_gaps: ['PDF mensal'],
};

const presetGroups = [
  {
    label: 'Renda fixa guiada',
    description: 'Estudos de juros e duration.',
    presets: [
      {
        preset_id: 'fixed_income_ipca_vs_cdi',
        label: 'IPCA+ vs CDI',
        description: 'Compara renda fixa por duration com inflação.',
        asset_ids: ['CDI_INDEX', 'IPCA_INDEX'],
        goal_label: 'Proteger e comparar renda fixa.',
        default_start_date: '2015-01-01',
        default_benchmark_ids: ['selic_cash'],
      },
    ],
  },
];

describe('InvestmentSetupStartTab', () => {
  it('renders guided and manual entry modes and invokes selection callbacks', async () => {
    const user = userEvent.setup();
    const onChooseGuided = vi.fn();
    const onChooseManual = vi.fn();
    const onApplyPreset = vi.fn();
    const onClearManualSelection = vi.fn();
    const onReturnToGuided = vi.fn();

    render(
      <InvestmentSetupStartTab
        entryMode="guided"
        presetGroups={presetGroups}
        selectedPresetId="fixed_income_ipca_vs_cdi"
        investorEasyParity={investorEasyParity}
        marketExplorer={marketExplorer}
        productDataPlan={productDataPlan}
        onChooseGuided={onChooseGuided}
        onChooseManual={onChooseManual}
        onApplyPreset={onApplyPreset}
        onClearManualSelection={onClearManualSelection}
        onReturnToGuided={onReturnToGuided}
      />
    );

    expect(screen.getByText('1. Escolha como quer começar')).toBeTruthy();
    expect(screen.getByText('Plano pos-roadmap de dados de produto')).toBeTruthy();
    expect(screen.getByText('Manifesto local de dados externos')).toBeTruthy();
    expect(screen.getByText('Paridade Investidor Facil')).toBeTruthy();
    expect(screen.getByText('15 calculadoras educativas')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Atualizar fonte/i })).toBeTruthy();
    expect(screen.getByText('Enriquecimento do catálogo')).toBeTruthy();
    expect(screen.getByText('Roadmap 1-9')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Quero um estudo pronto/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Quero montar manualmente/i })).toBeTruthy();

    await user.click(screen.getByRole('button', { name: /Quero montar manualmente/i }));
    expect(onChooseManual).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: /Quero um estudo pronto/i }));
    expect(onChooseGuided).toHaveBeenCalledTimes(1);

    const presetButton = screen.getByText('IPCA+ vs CDI').closest('button');
    expect(presetButton).not.toBeNull();
    await user.click(presetButton!);
    expect(onApplyPreset).toHaveBeenCalledTimes(1);
  });

  it('invokes apply preset and manual reset callbacks', async () => {
    const user = userEvent.setup();
    const onApplyPreset = vi.fn();
    const onClearManualSelection = vi.fn();
    const onReturnToGuided = vi.fn();

    render(
      <InvestmentSetupStartTab
        entryMode="manual"
        presetGroups={presetGroups}
        selectedPresetId="fixed_income_ipca_vs_cdi"
        investorEasyParity={investorEasyParity}
        marketExplorer={marketExplorer}
        productDataPlan={productDataPlan}
        onChooseGuided={vi.fn()}
        onChooseManual={vi.fn()}
        onApplyPreset={onApplyPreset}
        onClearManualSelection={onClearManualSelection}
        onReturnToGuided={onReturnToGuided}
      />
    );

    await user.click(screen.getByRole('button', { name: 'Limpar seleção atual' }));
    expect(onClearManualSelection).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: 'Voltar para estudos prontos' }));
    expect(onReturnToGuided).toHaveBeenCalledTimes(1);
  });
});
