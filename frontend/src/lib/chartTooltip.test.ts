import { describe, expect, it } from 'vitest';
import {
  DEFAULT_TOOLTIP_PROXIMITY_PX,
  pickNearestTooltipPayload,
} from './chartTooltip';

describe('pickNearestTooltipPayload', () => {
  it('returns only the closest series to the mouse position', () => {
    const payload = [
      { dataKey: 'cdi_index', name: 'cdi_index', value: 1000 },
      { dataKey: 'ipca_index', name: 'ipca_index', value: 2000 },
      { dataKey: 'stocks', name: 'stocks', value: 3000 },
    ];

    const result = pickNearestTooltipPayload(payload, 98, (value) => Number(value) / 20);

    expect(result).toHaveLength(1);
    expect(result[0]?.dataKey).toBe('ipca_index');
  });

  it('hides the tooltip when the mouse is too far from every visible line', () => {
    const payload = [
      { dataKey: 'cdi_index', name: 'cdi_index', value: 1000 },
      { dataKey: 'ipca_index', name: 'ipca_index', value: 2000 },
    ];

    const result = pickNearestTooltipPayload(
      payload,
      180,
      (value) => Number(value) / 20,
      DEFAULT_TOOLTIP_PROXIMITY_PX
    );

    expect(result).toHaveLength(0);
  });
});
