import { describe, expect, it } from 'vitest';
import {
  applyStrategySetupDraft,
  buildStrategySetupDraft,
  parseCommaList,
  parseLines,
  parseParameterValue,
  parseParameterValues,
  serializeParameterValues,
} from './strategySetupDrafts';
import type { SavedStrategyRadarItem } from '../hooks/useSavedStrategyRadar';

describe('strategySetupDrafts', () => {
  it('builds and applies an editable setup draft', () => {
    const item: SavedStrategyRadarItem = {
      strategy_id: 'pairs_cointegration',
      label: 'Pairs',
      family: 'market_neutral',
      direction: 'long_short',
      parameter_values: { formation_window: 252, entry_zscore: 2 },
      universe: ['PETR4', 'VALE3'],
      timeframe: 'daily',
      setup_notes: ['Revalidar janela.'],
    };

    expect(buildStrategySetupDraft(item)).toEqual({
      universeText: 'PETR4, VALE3',
      timeframe: 'daily',
      parametersText: 'formation_window: 252\nentry_zscore: 2',
      notesText: 'Revalidar janela.',
    });

    expect(
      applyStrategySetupDraft(item, {
        universeText: 'itub4, bbdc4',
        timeframe: ' weekly ',
        parametersText: 'formation_window: 126\nentry_zscore: 1,8\nhedged: true\nmemo:',
        notesText: 'Testar semanalmente.\n\nEvitar feriados.',
      })
    ).toMatchObject({
      universe: ['ITUB4', 'BBDC4'],
      timeframe: 'weekly',
      parameter_values: {
        formation_window: 126,
        entry_zscore: 1.8,
        hedged: true,
        memo: null,
      },
      setup_notes: ['Testar semanalmente.', 'Evitar feriados.'],
    });
  });

  it('parses parameter values conservatively', () => {
    expect(parseParameterValue('true')).toBe(true);
    expect(parseParameterValue('false')).toBe(false);
    expect(parseParameterValue('1,5')).toBe(1.5);
    expect(parseParameterValue('-12')).toBe(-12);
    expect(parseParameterValue('PETR4')).toBe('PETR4');
  });

  it('serializes, parses lists, and parses multi-line notes', () => {
    expect(serializeParameterValues({ enabled: false, threshold: 2.5 })).toBe(
      'enabled: false\nthreshold: 2.5'
    );
    expect(parseParameterValues('entry: 2\nlabel: teste')).toEqual({
      entry: 2,
      label: 'teste',
    });
    expect(parseCommaList(' petr4, , vale3 ')).toEqual(['PETR4', 'VALE3']);
    expect(parseLines('a\n\n b ')).toEqual(['a', 'b']);
  });
});
