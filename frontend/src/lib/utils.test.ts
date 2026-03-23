import { describe, expect, it } from 'vitest';
import { cn, formatPercent } from './utils';

describe('utils', () => {
  it('joins class names with clsx', () => {
    expect(cn('card', false && 'hidden', 'active')).toBe('card active');
  });

  it('formats percentages with two decimals by default', () => {
    expect(formatPercent(0.1234)).toBe('12.34%');
  });
});
