import { describe, expect, it } from 'vitest';
import {
  buildOptimizationPayload,
  normalizeStrategyList,
  parseJsonObjectInput,
} from './optimizationPayload';

describe('optimizationPayload', () => {
  it('normalizes strategies from commas and new lines', () => {
    expect(normalizeStrategyList('One, Two\nThree')).toEqual(['One', 'Two', 'Three']);
  });

  it('builds an optimization request payload', () => {
    const payload = buildOptimizationPayload('configs/test.yaml', ['Simple Martingale'], {
      strategiesText: '',
      globalSpaceText: '{ "base_bet": { "values": [250, 500] } }',
      strategySpaceText: '{ "Simple Martingale": { "max_layers": { "values": [3, 4] } } }',
      mode: 'grid',
      objective: 'total_return',
      direction: 'maximize',
      maxTrialsText: '5',
      seedText: '42',
    });

    expect(payload.config_path).toBe('configs/test.yaml');
    expect(payload.strategies).toEqual(['Simple Martingale']);
    expect(payload.max_trials).toBe(5);
    expect(payload.random_seed).toBe(42);
  });

  it('rejects invalid json objects', () => {
    expect(() => parseJsonObjectInput('[1,2,3]', 'global search space')).toThrow(
      'Invalid global search space: expected a JSON object'
    );
  });
});
