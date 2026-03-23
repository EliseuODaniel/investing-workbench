import { describe, expect, it } from 'vitest';
import { buildWalkForwardPayload } from './walkForwardPayload';

describe('walkForwardPayload', () => {
  it('builds a walk-forward request payload', () => {
    const payload = buildWalkForwardPayload('configs/test.yaml', ['Simple Martingale'], {
      strategiesText: '',
      trainDaysText: '90',
      testDaysText: '30',
      stepDaysText: '30',
    });

    expect(payload.config_path).toBe('configs/test.yaml');
    expect(payload.strategies).toEqual(['Simple Martingale']);
    expect(payload.train_window_days).toBe(90);
  });

  it('rejects invalid numeric fields', () => {
    expect(() =>
      buildWalkForwardPayload('configs/test.yaml', [], {
        strategiesText: '',
        trainDaysText: '0',
        testDaysText: '30',
        stepDaysText: '30',
      })
    ).toThrow('Invalid train window: expected a positive integer');
  });
});
