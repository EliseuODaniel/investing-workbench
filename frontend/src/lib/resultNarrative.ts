import { StrategyResult } from '../types/api';
import { formatPercent } from './utils';

export interface DidacticInsight {
  tone: 'positive' | 'caution' | 'neutral';
  title: string;
  body: string;
}

export interface ResultsInterpretation {
  headline: string;
  subheadline: string;
  bestReturnStrategy: string;
  bestSharpeStrategy: string;
  highestDrawdownStrategy: string;
  insights: DidacticInsight[];
  readingGuide: string[];
}

function pickStrategy(
  results: Record<string, StrategyResult>,
  selector: (result: StrategyResult) => number,
  mode: 'max' | 'min' = 'max'
): [string, StrategyResult] | null {
  const entries = Object.entries(results);
  if (entries.length === 0) return null;

  return entries.reduce<[string, StrategyResult]>((best, current) => {
    const bestValue = selector(best[1]);
    const currentValue = selector(current[1]);
    if (mode === 'max' ? currentValue > bestValue : currentValue < bestValue) {
      return current;
    }
    return best;
  }, entries[0]);
}

export function buildResultsInterpretation(
  results: Record<string, StrategyResult>
): ResultsInterpretation | null {
  const bestReturn = pickStrategy(results, (result) => result.metrics.total_return, 'max');
  const bestSharpe = pickStrategy(results, (result) => result.metrics.sharpe_ratio, 'max');
  const highestDrawdown = pickStrategy(results, (result) => result.metrics.max_drawdown, 'max');

  if (!bestReturn || !bestSharpe || !highestDrawdown) {
    return null;
  }

  const insights: DidacticInsight[] = [];
  const [bestReturnName, bestReturnResult] = bestReturn;
  const [bestSharpeName, bestSharpeResult] = bestSharpe;
  const [highestDrawdownName, highestDrawdownResult] = highestDrawdown;

  if (bestReturnName === bestSharpeName) {
    insights.push({
      tone: 'positive',
      title: 'Retorno e qualidade caminharam juntos',
      body: `${bestReturnName} liderou tanto em retorno quanto em Sharpe, o que sugere uma combinação melhor de ganho e consistência neste período.`,
    });
  } else {
    insights.push({
      tone: 'neutral',
      title: 'Houve trade-off entre agressividade e consistência',
      body: `${bestReturnName} entregou o maior retorno (${formatPercent(bestReturnResult.metrics.total_return)}), enquanto ${bestSharpeName} teve o melhor Sharpe (${bestSharpeResult.metrics.sharpe_ratio.toFixed(2)}).`,
    });
  }

  if (bestReturnResult.metrics.max_drawdown >= 0.3) {
    insights.push({
      tone: 'caution',
      title: 'A estratégia vencedora exige estômago',
      body: `${bestReturnName} foi a melhor em retorno, mas sofreu drawdown máximo de ${formatPercent(bestReturnResult.metrics.max_drawdown)}. Vale comparar esse risco com a tolerância real do investidor.`,
    });
  }

  if (bestSharpeResult.metrics.total_trades < 5) {
    insights.push({
      tone: 'caution',
      title: 'Amostra pequena pode enganar',
      body: `${bestSharpeName} teve apenas ${bestSharpeResult.metrics.total_trades} trades. Métricas boas com poucas operações merecem leitura mais conservadora.`,
    });
  }

  if (highestDrawdownResult.metrics.max_drawdown >= 0.4) {
    insights.push({
      tone: 'caution',
      title: 'Pior fase muito severa',
      body: `${highestDrawdownName} passou por uma queda máxima de ${formatPercent(highestDrawdownResult.metrics.max_drawdown)}. Isso costuma ser o primeiro sinal de que a estratégia pode ser difícil de sustentar na prática.`,
    });
  }

  const stableCandidates = Object.entries(results).filter(([, result]) => {
    return (
      result.metrics.sharpe_ratio >= 1 &&
      result.metrics.max_drawdown <= 0.2 &&
      result.metrics.profit_factor >= 1.1
    );
  });
  if (stableCandidates.length > 0) {
    const names = stableCandidates.map(([name]) => name).join(', ');
    insights.push({
      tone: 'positive',
      title: 'Há sinais de robustez operacional',
      body: `Estas estratégias combinaram Sharpe acima de 1, drawdown moderado e profit factor saudável: ${names}.`,
    });
  }

  const weakCandidates = Object.entries(results).filter(([, result]) => {
    return result.metrics.sharpe_ratio < 0 || result.metrics.profit_factor < 1;
  });
  if (weakCandidates.length > 0) {
    const names = weakCandidates.map(([name]) => name).join(', ');
    insights.push({
      tone: 'caution',
      title: 'Algumas estratégias destruíram qualidade',
      body: `${names} terminaram com Sharpe negativo ou profit factor abaixo de 1. Isso normalmente indica retorno ruim por unidade de risco ou execução ineficiente.`,
    });
  }

  return {
    headline: `${bestReturnName} foi a líder em retorno no período analisado.`,
    subheadline: `A leitura mais equilibrada aponta ${bestSharpeName} como a referência de consistência ajustada ao risco.`,
    bestReturnStrategy: bestReturnName,
    bestSharpeStrategy: bestSharpeName,
    highestDrawdownStrategy: highestDrawdownName,
    insights,
    readingGuide: [
      'Comece pelo Sharpe e pelo drawdown antes de se apaixonar pelo retorno final.',
      'Confira o número de trades: amostras muito pequenas podem produzir métricas bonitas demais.',
      'Compare a vencedora em retorno com a vencedora em Sharpe para entender o custo do risco.',
      'Se o drawdown parecer desconfortável, use walk-forward e Monte Carlo antes de confiar na estratégia.',
    ],
  };
}
