import { describe, expect, it } from 'vitest';
import { getSelicAverageAnnualRate } from './helpers';

describe('metrics-cards helpers', () => {
  it('annualizes monthly SELIC rates geometrically', () => {
    const annualized = getSelicAverageAnnualRate({
      metrics: {
        selic_rates_used: [
          { period: '2023-01', rate: 0.01 },
          { period: '2023-02', rate: 0.01 },
          { period: '2023-03', rate: 0.01 },
        ],
      },
    } as any);

    expect(annualized).toBeCloseTo((1.01 ** 12) - 1, 6);
  });
});
