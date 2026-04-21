import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import RunHistoryPanel from './RunHistoryPanel';

const baseRun = {
  run_id: 'run_1',
  created_at: '2026-04-21T16:00:00Z',
  config_path: 'configs/martingale.yaml',
  artifact_dir: 'runs/run_1',
  strategy_names: ['Fixed Martingale'],
  benchmark_names: ['Buy & Hold'],
  request_payload: {},
  data_info: {},
  config_snapshot_path: 'runs/run_1/config_resolved.json',
  data_profile_path: 'runs/run_1/data_profile.json',
  data_fingerprint: 'abc123def456',
};

describe('RunHistoryPanel', () => {
  it('shows a legacy badge and disables compare for invalid runs', () => {
    render(
      <RunHistoryPanel
        runs={[
          {
            ...baseRun,
            run_quality: {
              status: 'legacy_invalid',
              code: 'selic_monthly_cache_bug',
              title: 'Run legado invalidado',
              message: 'Run antigo com SELIC inflada.',
            },
          },
        ]}
        isLoading={false}
        onRefresh={vi.fn()}
        onLoadRun={vi.fn()}
        selectedRunIds={[]}
        onToggleCompare={vi.fn()}
      />
    );

    expect(screen.getByText('Legado invalido')).toBeTruthy();
    expect(screen.getByText(/Comparacao desativada para runs legados invalidados/i)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Comparar' })).toBeNull();
  });

  it('keeps compare enabled for valid runs', () => {
    const onToggleCompare = vi.fn();
    render(
      <RunHistoryPanel
        runs={[baseRun]}
        isLoading={false}
        onRefresh={vi.fn()}
        onLoadRun={vi.fn()}
        selectedRunIds={[]}
        onToggleCompare={onToggleCompare}
      />
    );

    const compareButton = screen.getByRole('button', { name: 'Comparar' });
    fireEvent.click(compareButton);
    expect(onToggleCompare).toHaveBeenCalledWith('run_1');
  });
});
