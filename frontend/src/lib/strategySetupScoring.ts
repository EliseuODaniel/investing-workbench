import type {
  SavedStrategyRadarItemPayload,
  SavedStrategySetupRunPayload,
  StrategySetupScorePayload,
} from '../types/api';

export type SetupScoreInsight = {
  insight_id: string;
  label: string;
  setup_label: string;
  value_label: string;
  interpretation: string;
};

export function buildSetupScores(
  savedItems: SavedStrategyRadarItemPayload[],
  history: SavedStrategySetupRunPayload[]
): StrategySetupScorePayload[] {
  return savedItems
    .map<StrategySetupScorePayload | null>((item) => {
      const latest = history.find((historyItem) => historyItem.strategy_id === item.strategy_id);
      if (
        !latest ||
        typeof latest.total_return !== 'number' ||
        typeof latest.max_drawdown !== 'number'
      ) {
        return null;
      }
      const tradeCount = latest.trade_count ?? 0;
      const runCount = history.filter(
        (historyItem) =>
          historyItem.strategy_id === item.strategy_id &&
          typeof historyItem.total_return === 'number' &&
          typeof historyItem.max_drawdown === 'number'
      ).length;
      const returnScore = latest.total_return * 100;
      const drawdownPenalty = Math.abs(latest.max_drawdown) * 50;
      const executionScore = Math.min(tradeCount, 20) * 0.25;
      const robustnessScore = Math.min(runCount, 5) * 0.5;
      const dataValidityScore = scoreSetupDataValidity(latest);
      const score =
        returnScore -
        drawdownPenalty +
        executionScore +
        robustnessScore +
        dataValidityScore;
      return {
        strategy_id: item.strategy_id,
        label: item.label,
        score,
        total_return: latest.total_return,
        max_drawdown: latest.max_drawdown,
        trade_count: tradeCount,
        run_count: runCount,
        route_hint: latest.route_hint,
        run_id: latest.run_id ?? null,
        pairs_backtest_id: latest.pairs_backtest_id ?? null,
        return_score: returnScore,
        drawdown_penalty: drawdownPenalty,
        execution_score: executionScore,
        robustness_score: robustnessScore,
        data_validity_score: dataValidityScore,
        ran_at: latest.ran_at,
        methodology:
          'score = retorno_total * 100 - abs(max_drawdown) * 50 + min(trade_count, 20) * 0.25 + min(run_count, 5) * 0.5 + data_validity_score',
      };
    })
    .filter(isSetupScore)
    .sort((left, right) => right.score - left.score);
}

function isSetupScore(value: StrategySetupScorePayload | null): value is StrategySetupScorePayload {
  return value !== null;
}

export function buildSetupScoreInsights(
  scores: StrategySetupScorePayload[]
): SetupScoreInsight[] {
  const candidates = scores.filter(
    (score) =>
      typeof score.score === 'number' &&
      typeof score.total_return === 'number' &&
      typeof score.max_drawdown === 'number'
  );
  if (candidates.length === 0) {
    return [];
  }
  const topScore = candidates.slice().sort((left, right) => right.score - left.score)[0];
  const topReturn = candidates
    .slice()
    .sort((left, right) => right.total_return - left.total_return)[0];
  const lowestDrawdown = candidates
    .slice()
    .sort((left, right) => right.max_drawdown - left.max_drawdown)[0];
  const strongestEvidence = candidates
    .slice()
    .sort(
      (left, right) =>
        (right.run_count ?? 0) - (left.run_count ?? 0) ||
        (right.trade_count ?? 0) - (left.trade_count ?? 0)
    )[0];

  return [
    {
      insight_id: 'top_score',
      label: 'Melhor score',
      setup_label: topScore.label,
      value_label: topScore.score.toFixed(1),
      interpretation: 'Combina retorno, drawdown, execucao, robustez e validade dos dados.',
    },
    {
      insight_id: 'top_return',
      label: 'Maior retorno',
      setup_label: topReturn.label,
      value_label: formatPercent(topReturn.total_return),
      interpretation: 'Olha apenas o retorno total; precisa ser lido junto do drawdown.',
    },
    {
      insight_id: 'lowest_drawdown',
      label: 'Menor drawdown',
      setup_label: lowestDrawdown.label,
      value_label: formatPercent(lowestDrawdown.max_drawdown),
      interpretation: 'Prioriza a queda menos severa entre os setups executados.',
    },
    {
      insight_id: 'strongest_evidence',
      label: 'Mais evidencia',
      setup_label: strongestEvidence.label,
      value_label: `${strongestEvidence.run_count ?? 0} run(s) · ${
        strongestEvidence.trade_count ?? 0
      } trade(s)`,
      interpretation: 'Favorece setups com mais execucoes validas e mais trades observados.',
    },
  ];
}

export type SetupDiversificationSummary = {
  strategyCount: number;
  diversificationScore: number;
  averageReturn: number;
  worstDrawdown: number;
  estimatedBlendedDrawdown: number;
  interpretation: string;
};

export function buildSetupDiversificationSummary(
  scores: StrategySetupScorePayload[]
): SetupDiversificationSummary | null {
  const candidates = scores.filter(
    (score) =>
      typeof score.total_return === 'number' && typeof score.max_drawdown === 'number'
  );
  if (candidates.length < 2) {
    return null;
  }
  const top = candidates.slice(0, 4);
  const avgReturn = top.reduce((sum, s) => sum + s.total_return, 0) / top.length;
  const worstDd = Math.min(...top.map((s) => s.max_drawdown));
  const avgDd = top.reduce((sum, s) => sum + s.max_drawdown, 0) / top.length;
  const blendedDd = avgDd * 0.85;
  const routes = new Set(top.map((s) => s.route_hint));
  const divScore = Math.min(
    100,
    Math.max(
      10,
      (0.5 + Math.min(routes.size * 0.25, 0.5) + Math.min(top.length * 0.1, 0.3)) * 100
    )
  );

  return {
    strategyCount: top.length,
    diversificationScore: Math.round(divScore),
    averageReturn: avgReturn,
    worstDrawdown: worstDd,
    estimatedBlendedDrawdown: blendedDd,
    interpretation: `Combinar os ${top.length} principais setups executados diversifica riscos operacionais e reduz o drawdown maximo estimado para ${(blendedDd * 100).toFixed(1)}%.`,
  };
}

export function buildSetupScoresCsv(scores: StrategySetupScorePayload[]): string {
  const headers = [
    'rank',
    'strategy_id',
    'label',
    'score',
    'total_return',
    'max_drawdown',
    'trade_count',
    'run_count',
    'return_score',
    'drawdown_penalty',
    'execution_score',
    'robustness_score',
    'data_validity_score',
    'route_hint',
    'run_id',
    'pairs_backtest_id',
    'ran_at',
    'methodology',
  ];
  const rows = scores.map((score, index) => [
    index + 1,
    score.strategy_id,
    score.label,
    score.score,
    score.total_return,
    score.max_drawdown,
    score.trade_count ?? 0,
    score.run_count ?? 0,
    score.return_score,
    score.drawdown_penalty,
    score.execution_score,
    score.robustness_score,
    score.data_validity_score,
    score.route_hint,
    score.run_id ?? '',
    score.pairs_backtest_id ?? '',
    score.ran_at,
    score.methodology,
  ]);
  return [headers, ...rows].map((row) => row.map((value) => csvCell(value)).join(',')).join('\n');
}

function scoreSetupDataValidity(item: SavedStrategySetupRunPayload): number {
  let score = 0;
  if (item.run_id || item.pairs_backtest_id) {
    score += 1;
  }
  if (typeof item.total_return === 'number' && typeof item.max_drawdown === 'number') {
    score += 0.75;
  }
  if (['/backtest', '/pairs/backtests'].includes(item.route_hint)) {
    score += 0.25;
  }
  return score;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function csvCell(value: unknown): string {
  const text = String(value ?? '');
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}
