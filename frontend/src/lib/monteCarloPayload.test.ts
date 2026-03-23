import { describe, expect, it } from 'vitest';
import { buildMonteCarloPayload } from './monteCarloPayload';

describe('monteCarloPayload', () => {
  it('builds a current-run Monte Carlo payload', () => {
    const payload = buildMonteCarloPayload(
      'configs/test.yaml',
      'run_123',
      ['Simple Martingale'],
      {
        sourceMode: 'current-run',
        strategiesText: '',
        simulationsText: '100',
        seedText: '42',
        ruinThresholdText: '0.3',
        method: 'bootstrap',
      }
    );

    expect(payload.run_id).toBe('run_123');
    expect(payload.simulation_count).toBe(100);
    expect(payload.ruin_threshold_pct).toBe(0.3);
  });

  it('rejects missing current run for current-run mode', () => {
    expect(() =>
      buildMonteCarloPayload('configs/test.yaml', undefined, [], {
        sourceMode: 'current-run',
        strategiesText: '',
        simulationsText: '100',
        seedText: '42',
        ruinThresholdText: '0.3',
        method: 'shuffle',
      })
    ).toThrow('Load or run a persisted backtest before using current-run Monte Carlo');
  });
});
