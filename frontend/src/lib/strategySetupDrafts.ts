import type { SavedStrategyRadarItem } from '../hooks/useSavedStrategyRadar';
import type { StrategySetupDraft } from '../components/strategy/StrategySetupEditForm';

export function buildStrategySetupDraft(item: SavedStrategyRadarItem): StrategySetupDraft {
  return {
    universeText: (item.universe || []).join(', '),
    timeframe: item.timeframe || 'daily',
    parametersText: serializeParameterValues(item.parameter_values || {}),
    notesText: (item.setup_notes || []).join('\n'),
  };
}

export function applyStrategySetupDraft(
  item: SavedStrategyRadarItem,
  draft: StrategySetupDraft
): SavedStrategyRadarItem {
  return {
    ...item,
    universe: parseCommaList(draft.universeText),
    timeframe: draft.timeframe.trim() || 'daily',
    parameter_values: parseParameterValues(draft.parametersText),
    setup_notes: parseLines(draft.notesText),
  };
}

export function serializeParameterValues(
  values: SavedStrategyRadarItem['parameter_values']
): string {
  return Object.entries(values || {})
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join('\n');
}

export function parseParameterValues(
  text: string
): Record<string, string | number | boolean | null> {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce<Record<string, string | number | boolean | null>>((acc, line) => {
      const [rawKey, ...rawValueParts] = line.split(':');
      const key = rawKey.trim();
      if (!key) {
        return acc;
      }
      const rawValue = rawValueParts.join(':').trim();
      acc[key] = parseParameterValue(rawValue);
      return acc;
    }, {});
}

export function parseParameterValue(value: string): string | number | boolean | null {
  if (value === '') return null;
  if (value.toLowerCase() === 'true') return true;
  if (value.toLowerCase() === 'false') return false;
  const numeric = Number(value.replace(',', '.'));
  return Number.isFinite(numeric) && value.match(/^-?\d+([,.]\d+)?$/) ? numeric : value;
}

export function parseCommaList(text: string): string[] {
  return text
    .split(',')
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}

export function parseLines(text: string): string[] {
  return text
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
}
