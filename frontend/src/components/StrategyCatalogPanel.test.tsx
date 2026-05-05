import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { downloadCSV } from '../lib/utils';
import StrategyCatalogPanel from './StrategyCatalogPanel';

describe('StrategyCatalogPanel', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(apiClient.saveStrategyRadarItem).mockClear();
    vi.mocked(apiClient.deleteStrategyRadarItem).mockClear();
    vi.mocked(downloadCSV).mockClear();
  });

  it('shows strategy catalog metadata from the API', async () => {
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockResolvedValueOnce({
      title: 'Catalogo de estrategias',
      plain_language_summary: 'Explica familias de backtest.',
      generated_at: '2026-04-27T12:00:00Z',
      strategies: [
        {
          strategy_id: 'martingale_v1',
          label: 'Martingale controlado',
          family: 'position_sizing',
          direction: 'long',
          required_inputs: ['base_bet', 'multiplier'],
          supported_timeframes: ['daily'],
          risk_notes: ['Aumenta exposicao quando o preco cai.'],
        },
      ],
      score_dimensions: [
        {
          dimension_id: 'drawdown',
          label: 'Drawdown',
          description: 'Maior perda de pico a vale.',
        },
      ],
      radar_plan: ['Salvar favoritos locais de estrategias e parametros.'],
    });
    render(<StrategyCatalogPanel />);

    await waitFor(() => {
      expect(apiClient.getBacktestStrategyCatalog).toHaveBeenCalledTimes(1);
    });
    expect(await screen.findByText('Martingale controlado')).toBeTruthy();
    expect(screen.getByText('Score planejado')).toBeTruthy();
    expect(screen.getByText('Radar de setups')).toBeTruthy();
  });

  it('saves strategy favorites in the local setup radar', async () => {
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockResolvedValueOnce({
      title: 'Catalogo de estrategias',
      plain_language_summary: 'Explica familias de backtest.',
      generated_at: '2026-04-27T12:00:00Z',
      strategies: [
        {
          strategy_id: 'pairs_cointegration',
          label: 'Pairs por cointegracao',
          family: 'market_neutral',
          direction: 'long_short',
          required_inputs: ['formation_window'],
          parameter_defaults: { formation_window: 252, entry_zscore: 2 },
          universe_defaults: ['PETR4', 'VALE3'],
          supported_timeframes: ['daily'],
          execution_notes: ['Revalidar relacao por janela.'],
          risk_notes: ['Depende da validade temporal da relacao estatistica.'],
        },
      ],
      score_dimensions: [],
      radar_plan: ['Salvar favoritos locais de estrategias e parametros.'],
    });

    render(<StrategyCatalogPanel />);

    expect(await screen.findByText('Pairs por cointegracao')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Favoritar Pairs por cointegracao'));

    expect(screen.getByText('1 favorito(s)')).toBeTruthy();
    expect(screen.getAllByText('formation_window: 252')).toHaveLength(2);
    expect(apiClient.saveStrategyRadarItem).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy_id: 'pairs_cointegration',
        universe: ['PETR4', 'VALE3'],
      })
    );
    expect(window.localStorage.getItem('investing-workbench.strategy-radar.v1')).toContain(
      'pairs_cointegration'
    );

    fireEvent.click(screen.getAllByLabelText('Remover Pairs por cointegracao do radar')[1]);

    expect(screen.getByText('0 favorito(s)')).toBeTruthy();
    expect(apiClient.deleteStrategyRadarItem).toHaveBeenCalledWith('pairs_cointegration');
  });

  it('edits a saved strategy setup draft from the radar', async () => {
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockResolvedValueOnce({
      title: 'Catalogo de estrategias',
      plain_language_summary: 'Explica familias de backtest.',
      generated_at: '2026-04-27T12:00:00Z',
      strategies: [
        {
          strategy_id: 'pairs_cointegration',
          label: 'Pairs por cointegracao',
          family: 'market_neutral',
          direction: 'long_short',
          required_inputs: ['formation_window'],
          parameter_defaults: { formation_window: 252, entry_zscore: 2 },
          universe_defaults: ['PETR4', 'VALE3'],
          supported_timeframes: ['daily'],
          execution_notes: ['Revalidar relacao por janela.'],
          risk_notes: ['Depende da validade temporal da relacao estatistica.'],
        },
      ],
      score_dimensions: [],
      radar_plan: ['Salvar favoritos locais de estrategias e parametros.'],
    });

    render(<StrategyCatalogPanel />);

    expect(await screen.findByText('Pairs por cointegracao')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Favoritar Pairs por cointegracao'));
    fireEvent.click(screen.getByLabelText('Editar setup Pairs por cointegracao'));

    fireEvent.change(screen.getByLabelText('Timeframe'), {
      target: { value: 'weekly' },
    });
    fireEvent.change(screen.getByLabelText('Universo'), {
      target: { value: 'ITUB4, BBDC4' },
    });
    fireEvent.change(screen.getByLabelText('Parametros'), {
      target: { value: 'formation_window: 126\nentry_zscore: 1.8' },
    });
    fireEvent.change(screen.getByLabelText('Notas'), {
      target: { value: 'Testar semanalmente antes de escalar.' },
    });
    fireEvent.click(screen.getByText('Salvar setup'));

    expect(screen.getByText('weekly · ITUB4, BBDC4')).toBeTruthy();
    expect(screen.getByText('formation_window: 126')).toBeTruthy();
    expect(apiClient.saveStrategyRadarItem).toHaveBeenLastCalledWith(
      expect.objectContaining({
        strategy_id: 'pairs_cointegration',
        universe: ['ITUB4', 'BBDC4'],
        timeframe: 'weekly',
        parameter_values: { formation_window: 126, entry_zscore: 1.8 },
      })
    );
  });

  it('prepares an execution plan from a saved setup', async () => {
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockResolvedValueOnce({
      title: 'Catalogo de estrategias',
      plain_language_summary: 'Explica familias de backtest.',
      generated_at: '2026-04-27T12:00:00Z',
      strategies: [
        {
          strategy_id: 'pairs_cointegration',
          label: 'Pairs por cointegracao',
          family: 'market_neutral',
          direction: 'long_short',
          required_inputs: ['formation_window'],
          parameter_defaults: { formation_window: 252, entry_zscore: 2 },
          universe_defaults: ['PETR4', 'VALE3'],
          supported_timeframes: ['daily'],
          execution_notes: ['Revalidar relacao por janela.'],
          risk_notes: ['Depende da validade temporal da relacao estatistica.'],
        },
      ],
      score_dimensions: [],
      radar_plan: ['Salvar favoritos locais de estrategias e parametros.'],
    });
    vi.mocked(apiClient.buildStrategySetupPlan).mockResolvedValueOnce({
      plan_id: 'strategy_setup_plan_pairs_cointegration',
      strategy_id: 'pairs_cointegration',
      label: 'Pairs por cointegracao',
      family: 'market_neutral',
      timeframe: 'daily',
      route_hint: '/pairs/backtests',
      readiness: 'ready_to_review',
      run_request: {
        preset_id: 'custom',
        tickers: ['PETR4', 'VALE3'],
        formation_window: 252,
      },
      assumptions: ['Plano gerado a partir do radar.'],
      warnings: ['Confirmar aluguel.'],
      setup_notes: ['Revalidar relacao por janela.'],
      next_actions: ['Conferir janela de datas e fonte de dados.'],
      generated_at: '2026-04-27T12:00:00Z',
    });
    const navigationListener = vi.fn();
    window.addEventListener('investing-workbench:navigate-advanced-tool', navigationListener);

    render(<StrategyCatalogPanel />);

    expect(await screen.findByText('Pairs por cointegracao')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Favoritar Pairs por cointegracao'));
    fireEvent.click(screen.getByLabelText('Preparar execucao Pairs por cointegracao'));

    expect(await screen.findByText('Plano preparado')).toBeTruthy();
    expect(screen.getByText('/pairs/backtests · ready_to_review')).toBeTruthy();
    expect(screen.getByText(/Confirmar aluguel/)).toBeTruthy();
    fireEvent.click(screen.getByText('Enviar para Pairs'));
    expect(screen.getByText(/Setup enviado para o laboratorio de Pairs/)).toBeTruthy();
    expect(window.localStorage.getItem('investing-workbench.pairs-setup-handoff.v1')).toContain(
      'PETR4, VALE3'
    );
    expect(navigationListener).toHaveBeenCalledTimes(1);
    expect((navigationListener.mock.calls[0][0] as CustomEvent).detail).toEqual({
      tool: 'pairs',
    });
    window.removeEventListener('investing-workbench:navigate-advanced-tool', navigationListener);
    expect(apiClient.buildStrategySetupPlan).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy_id: 'pairs_cointegration',
        universe: ['PETR4', 'VALE3'],
      })
    );
  });

  it('runs a prepared pairs setup directly from the radar', async () => {
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockResolvedValueOnce({
      title: 'Catalogo de estrategias',
      plain_language_summary: 'Explica familias de backtest.',
      generated_at: '2026-04-28T12:00:00Z',
      strategies: [
        {
          strategy_id: 'pairs_cointegration',
          label: 'Pairs por cointegracao',
          family: 'market_neutral',
          direction: 'long_short',
          required_inputs: ['formation_window'],
          parameter_defaults: { formation_window: 252, entry_zscore: 2 },
          universe_defaults: ['PETR4', 'VALE3'],
          supported_timeframes: ['daily'],
          execution_notes: ['Revalidar relacao por janela.'],
          risk_notes: ['Depende da validade temporal da relacao estatistica.'],
        },
      ],
      score_dimensions: [],
      radar_plan: ['Salvar favoritos locais de estrategias e parametros.'],
    });
    vi.mocked(apiClient.buildStrategySetupPlan).mockResolvedValueOnce({
      plan_id: 'strategy_setup_plan_pairs_cointegration',
      strategy_id: 'pairs_cointegration',
      label: 'Pairs por cointegracao',
      family: 'market_neutral',
      timeframe: 'daily',
      route_hint: '/pairs/backtests',
      readiness: 'ready_to_review',
      run_request: {
        preset_id: 'custom',
        tickers: ['PETR4', 'VALE3'],
        formation_window: 252,
        entry_zscore: 2,
        exit_zscore: 0.5,
      },
      assumptions: ['Plano gerado a partir do radar.'],
      warnings: ['Confirmar aluguel.'],
      setup_notes: ['Revalidar relacao por janela.'],
      next_actions: ['Executar o backtest pela rota indicada.'],
      generated_at: '2026-04-28T12:00:00Z',
    });
    vi.mocked(apiClient.runPairsBacktest).mockResolvedValueOnce({
      pairs_backtest_id: 'pairs_123',
      created_at: '2026-04-28T12:01:00Z',
      manifest: {
        pairs_backtest_id: 'pairs_123',
        created_at: '2026-04-28T12:01:00Z',
        preset_id: 'custom',
        preset_label: 'Custom',
        start_date: '2021-01-01',
        requested_tickers: ['PETR4', 'VALE3'],
        available_tickers: ['PETR4', 'VALE3'],
        eligible_tickers: ['PETR4', 'VALE3'],
        scenario_count: 1,
        batch_mode: false,
        benchmark_ids: [],
        candidate_pair_count: 1,
        reconstitution_segment_count: 0,
        warnings: [],
      },
      preset: null,
      universe: {},
      candidate_pairs: [{ pair_label: 'PETR4~VALE3' }],
      benchmarks: [],
      scenarios: [
        {
          scenario_id: 'realistic_cointegration',
          label: 'Realistic cointegration',
          metrics: {
            return_total: 0.12,
            max_drawdown: -0.04,
            trade_count: 3,
          },
          portfolio_summary: {},
          quality_summary: {},
        },
      ],
      robustness_report: { rankings: [], dispersion: {} },
      warnings: [],
    } as any);
    vi.mocked(apiClient.getPairsBacktestResults).mockResolvedValueOnce({
      pairs_backtest_id: 'pairs_123',
      created_at: '2026-04-28T12:01:00Z',
      manifest: {},
      preset: null,
      universe: {},
      candidate_pairs: [{ pair_label: 'PETR4~VALE3' }],
      benchmarks: [],
      scenarios: [
        {
          scenario_id: 'realistic_cointegration',
          label: 'Realistic cointegration',
          metrics: {
            return_total: 0.12,
            max_drawdown: -0.04,
            trade_count: 3,
          },
          portfolio_summary: {},
          quality_summary: {},
        },
      ],
      robustness_report: { rankings: [], dispersion: {} },
      warnings: [],
    } as any);

    render(<StrategyCatalogPanel />);

    expect(await screen.findByText('Pairs por cointegracao')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Favoritar Pairs por cointegracao'));
    fireEvent.click(screen.getByLabelText('Preparar execucao Pairs por cointegracao'));
    expect(await screen.findByText('Plano preparado')).toBeTruthy();

    fireEvent.click(screen.getByText('Rodar Pairs'));

    expect(await screen.findByText(/Pairs concluido: 1/)).toBeTruthy();
    expect(screen.getAllByText(/pairs_123/).length).toBeGreaterThan(0);
    expect(screen.getByText('Historico do setup')).toBeTruthy();
    expect(screen.getByText('Ranking dos setups executados')).toBeTruthy();
    expect(screen.getAllByText(/score 13.3/).length).toBeGreaterThan(0);
    expect(screen.getAllByText('retorno +12.0').length).toBeGreaterThan(0);
    expect(screen.getAllByText('drawdown -2.0').length).toBeGreaterThan(0);
    expect(screen.getAllByText('execucao +0.8').length).toBeGreaterThan(0);
    expect(screen.getAllByText('robustez +0.5').length).toBeGreaterThan(0);
    expect(screen.getAllByText('dados +2.0').length).toBeGreaterThan(0);
    expect(screen.getByText('Melhor score')).toBeTruthy();
    expect(screen.getByText('Maior retorno')).toBeTruthy();
    expect(screen.getByText('Menor drawdown')).toBeTruthy();
    expect(screen.getByText('Mais evidencia')).toBeTruthy();
    fireEvent.click(screen.getByText('Exportar CSV'));
    expect(downloadCSV).toHaveBeenCalledWith(
      expect.stringContaining('strategy_id,label,score'),
      expect.stringMatching(/^strategy_setup_scores_\d{4}-\d{2}-\d{2}\.csv$/)
    );
    expect(vi.mocked(downloadCSV).mock.calls[0][0]).toContain('pairs_cointegration');
    expect(window.localStorage.getItem('investing-workbench.strategy-setup-runs.v1')).toContain(
      'pairs_123'
    );
    expect(apiClient.runPairsBacktest).toHaveBeenCalledWith(
      expect.objectContaining({
        preset_id: 'custom',
        tickers: ['PETR4', 'VALE3'],
      })
    );
    expect(apiClient.saveStrategySetupRun).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy_id: 'pairs_cointegration',
        pairs_backtest_id: 'pairs_123',
        total_return: 0.12,
        max_drawdown: -0.04,
        trade_count: 3,
        route_hint: '/pairs/backtests',
      })
    );
    fireEvent.click(screen.getByText('Ver Pairs'));
    expect(await screen.findByText('trades 3')).toBeTruthy();
    expect(apiClient.getPairsBacktestResults).toHaveBeenCalledWith('pairs_123');
  });

  it('runs a prepared core backtest setup', async () => {
    vi.mocked(apiClient.getBacktestStrategyCatalog).mockResolvedValueOnce({
      title: 'Catalogo de estrategias',
      plain_language_summary: 'Explica familias de backtest.',
      generated_at: '2026-04-27T12:00:00Z',
      strategies: [
        {
          strategy_id: 'buy_and_hold',
          label: 'Buy and hold',
          family: 'benchmark',
          direction: 'long',
          required_inputs: ['initial_capital'],
          parameter_defaults: { initial_capital: 10000 },
          universe_defaults: ['BOVA11'],
          supported_timeframes: ['daily'],
          execution_notes: ['Comparar contra Selic.'],
          risk_notes: ['Nao controla drawdown.'],
        },
      ],
      score_dimensions: [],
      radar_plan: ['Salvar favoritos locais de estrategias e parametros.'],
    });
    vi.mocked(apiClient.buildStrategySetupPlan).mockResolvedValueOnce({
      plan_id: 'strategy_setup_plan_buy_and_hold',
      strategy_id: 'buy_and_hold',
      label: 'Buy and hold',
      family: 'benchmark',
      timeframe: 'daily',
      route_hint: '/backtest',
      readiness: 'ready_to_review',
      run_request: {
        config_path: 'configs/test.yaml',
        strategies: ['Buy & Hold'],
        data_source: 'BOVA11',
      },
      assumptions: ['Plano gerado a partir do radar.'],
      warnings: [],
      setup_notes: ['Comparar contra Selic.'],
      next_actions: ['Executar o backtest pela rota indicada.'],
      generated_at: '2026-04-27T12:00:00Z',
    });
    vi.mocked(apiClient.runBacktest).mockResolvedValueOnce({
      results: {
        'Buy & Hold': {
          strategy_name: 'Buy & Hold',
          equity: [],
          trades: [],
          metrics: {
            total_return: 0.1,
            cagr: 0.1,
            sharpe_ratio: 1,
            sortino_ratio: 1,
            max_drawdown: -0.05,
            hit_rate: 0,
            profit_factor: 0,
            total_trades: 0,
            avg_trade_pnl: 0,
            volatility: 0.15,
            total_interest_earned: 0,
          },
          start_price: 100,
          end_price: 110,
        },
      },
      buy_hold_equity: [],
      run_info: {
        run_id: 'run_123',
        artifact_dir: 'reports/run_123',
      },
      data_info: {
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        total_days: 252,
        initial_price: 100,
        final_price: 110,
      },
    });
    vi.mocked(apiClient.getRunResponse).mockResolvedValueOnce({
      results: {
        'Buy & Hold': {
          strategy_name: 'Buy & Hold',
          equity: [],
          trades: [],
          metrics: {
            total_return: 0.1,
            cagr: 0.1,
            sharpe_ratio: 1,
            sortino_ratio: 1,
            max_drawdown: -0.05,
            hit_rate: 0,
            profit_factor: 0,
            total_trades: 0,
            avg_trade_pnl: 0,
            volatility: 0.15,
            total_interest_earned: 0,
          },
          start_price: 100,
          end_price: 110,
        },
      },
      buy_hold_equity: [],
      data_info: {
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        total_days: 252,
        initial_price: 100,
        final_price: 110,
      },
    });

    render(<StrategyCatalogPanel />);

    expect(await screen.findByText('Buy and hold')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Favoritar Buy and hold'));
    fireEvent.click(screen.getByLabelText('Preparar execucao Buy and hold'));
    expect(await screen.findByText('Plano preparado')).toBeTruthy();

    fireEvent.click(screen.getByText('Rodar backtest'));

    expect(await screen.findByText(/Execucao concluida: 1/)).toBeTruthy();
    expect(screen.getByText(/run run_123/)).toBeTruthy();
    expect(screen.getByText('Historico do setup')).toBeTruthy();
    expect(screen.getByText('Ranking dos setups executados')).toBeTruthy();
    expect(screen.getByText('1 execucao(oes)')).toBeTruthy();
    expect(screen.getAllByText(/score 10.0/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/retorno 10.0%|10.0%/).length).toBeGreaterThan(0);
    expect(window.localStorage.getItem('investing-workbench.strategy-setup-runs.v1')).toContain(
      'run_123'
    );
    fireEvent.click(screen.getByText('Ver resultado'));
    expect(await screen.findByText('trades 0')).toBeTruthy();
    expect(apiClient.getRunResponse).toHaveBeenCalledWith('run_123');
    expect(apiClient.saveStrategySetupRun).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy_id: 'buy_and_hold',
        run_id: 'run_123',
        total_return: 0.1,
        max_drawdown: -0.05,
        trade_count: 0,
      })
    );
    expect(apiClient.runBacktest).toHaveBeenCalledWith(
      expect.objectContaining({
        config_path: 'configs/test.yaml',
        strategies: ['Buy & Hold'],
      })
    );
  });
});
