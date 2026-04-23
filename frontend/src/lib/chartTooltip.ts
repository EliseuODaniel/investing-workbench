import type { ScaleFunction } from 'recharts';

export interface ChartTooltipEntry {
  color?: string;
  dataKey?: string | number;
  name?: string | number;
  value?: unknown;
}

export const DEFAULT_TOOLTIP_PROXIMITY_PX = 18;

function toNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

export function pickNearestTooltipPayload(
  payload: readonly ChartTooltipEntry[],
  pointerY: number | undefined,
  yScale: ScaleFunction | undefined,
  thresholdPx = DEFAULT_TOOLTIP_PROXIMITY_PX
): ChartTooltipEntry[] {
  if (payload.length <= 1) {
    return [...payload];
  }

  if (pointerY === undefined || yScale === undefined) {
    return [...payload];
  }

  let nearestEntry: ChartTooltipEntry | null = null;
  let nearestDistance = Number.POSITIVE_INFINITY;

  for (const entry of payload) {
    const value = toNumber(entry.value);
    if (value === null) {
      continue;
    }

    const scaledY = yScale(value);
    if (typeof scaledY !== 'number' || !Number.isFinite(scaledY)) {
      continue;
    }

    const distance = Math.abs(scaledY - pointerY);
    if (distance < nearestDistance) {
      nearestEntry = entry;
      nearestDistance = distance;
    }
  }

  if (nearestEntry === null || nearestDistance > thresholdPx) {
    return [];
  }

  return [nearestEntry];
}
