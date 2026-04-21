import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { useWege3RegraA } from './useWege3RegraA';

describe('useWege3RegraA', () => {
  it('runs the dedicated WEGE3 scenario and stores the payload', async () => {
    const onError = vi.fn();
    vi.mocked(apiClient.runWege3RegraAScenario).mockResolvedValue({
      scenario_id: 'wege3_regra_a',
      scenario_label: 'WEGE3 Regra A',
      generated_at: '2026-04-21T03:30:00Z',
      request: {
        start_date: '2021-01-01',
        end_date: null,
        force_download: false,
      },
      assumptions: {},
      dataset: {
        start_session: '2021-01-04',
        end_session: '2026-04-20',
      },
      result: {
        saldo_final_total: 84951.82,
      },
      statistics: {},
      benchmarks: {},
      audit: {},
      comparison_variants: [],
      best_strategy: {},
      parameter_search: {},
      strategy_context: {},
      comparison_chart: {
        series: [],
        points: [],
        reference_series_id: 'selic_cash',
      },
      trades: [],
      artifacts: {
        summary_output_path: 'reports/wege3_summary.json',
        trades_output_path: 'reports/wege3_trades.csv',
        comparison_output_path: 'reports/wege3_comparison.csv',
        comparison_trades_output_path: 'reports/wege3_comparison_trades.csv',
        search_output_path: 'reports/wege3_search.csv',
      },
      reproduction_command: 'python -m scenario',
    });

    const { result } = renderHook(() => useWege3RegraA(onError));

    await act(async () => {
      await result.current.runScenario();
    });

    await waitFor(() => {
      expect(result.current.isRunning).toBe(false);
    });

    expect(apiClient.runWege3RegraAScenario).toHaveBeenCalledWith({
      start_date: '2021-01-01',
      end_date: null,
      force_download: false,
    });
    expect(result.current.result?.scenario_id).toBe('wege3_regra_a');
    expect(onError).toHaveBeenLastCalledWith(null);
  });
});
