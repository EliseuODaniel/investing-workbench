export interface StrategyGuide {
  category: string;
  risk: 'Baixo' | 'Moderado' | 'Moderado/Alto' | 'Alto';
  summary: string;
  bestFor: string;
}

const FALLBACK_GUIDE: StrategyGuide = {
  category: 'Estratégia',
  risk: 'Moderado',
  summary: 'Estratégia disponível no preset atual, sem descrição específica cadastrada.',
  bestFor: 'comparar comportamento com benchmark e outras estratégias do mesmo preset',
};

export function getStrategyGuide(strategyName: string): StrategyGuide {
  const normalized = strategyName.toLowerCase();

  if (normalized.includes('buy & hold')) {
    return {
      category: 'Referência',
      risk: 'Baixo',
      summary: 'Compra uma vez e mantém a posição, sem rebalancear ou fazer novas entradas.',
      bestFor: 'servir de linha de base para comparar se a estratégia ativa realmente agrega valor',
    };
  }

  if (normalized.includes('hybrid')) {
    return {
      category: 'DCA + Martingale',
      risk: normalized.includes('aggressive') ? 'Alto' : 'Moderado/Alto',
      summary:
        'Combina compras periódicas com camadas extras nas quedas para acelerar a recuperação.',
      bestFor: 'quem quer acumular ao longo do tempo, mas ainda capturar quedas mais fortes',
    };
  }

  if (normalized.includes('dca')) {
    return {
      category: 'Acumulação',
      risk: normalized.includes('aggressive') ? 'Moderado/Alto' : 'Baixo',
      summary:
        'Compra em intervalos fixos, reduzindo a dependência de acertar o melhor timing de entrada.',
      bestFor: 'acumulação disciplinada e comparação com abordagens mais ativas',
    };
  }

  if (normalized.includes('mean reversion')) {
    return {
      category: 'Reversão à média',
      risk: 'Moderado',
      summary:
        'Busca comprar depois de exageros de baixa esperando que o preço retorne para a média.',
      bestFor: 'mercados laterais ou ativos que costumam oscilar em torno de uma faixa',
    };
  }

  if (
    normalized.includes('ma cross') ||
    normalized.includes('trend following') ||
    normalized.includes('trend')
  ) {
    return {
      category: 'Seguidor de tendência',
      risk: 'Moderado',
      summary:
        'Entra quando a tendência fica mais clara, normalmente via cruzamento de médias.',
      bestFor: 'mercados com movimentos mais longos e direcionais',
    };
  }

  if (normalized.includes('breakout')) {
    return {
      category: 'Rompimento',
      risk: 'Moderado/Alto',
      summary:
        'Tenta capturar acelerações quando o preço rompe máximas, canais ou faixas importantes.',
      bestFor: 'mercados que entram em tendência forte após consolidações',
    };
  }

  if (normalized.includes('atr')) {
    return {
      category: 'Martingale adaptativo',
      risk: 'Moderado/Alto',
      summary:
        'Usa ATR para ajustar distâncias e agressividade conforme a volatilidade do mercado.',
      bestFor: 'comparar um martingale mais adaptativo contra versões fixas',
    };
  }

  if (normalized.includes('trailing')) {
    return {
      category: 'Martingale com proteção',
      risk: normalized.includes('aggressive') ? 'Alto' : 'Moderado/Alto',
      summary:
        'Aplica trailing take-profit para tentar proteger parte do ganho depois de uma recuperação.',
      bestFor: 'cenários em que a recuperação acontece, mas pode devolver lucro rápido',
    };
  }

  if (normalized.includes('volatility') || normalized.includes('vol ')) {
    return {
      category: 'Martingale adaptativo',
      risk: normalized.includes('hot') ? 'Alto' : 'Moderado/Alto',
      summary:
        'Ajusta a agressividade do martingale com base na volatilidade recente do ativo.',
      bestFor: 'mercados mais instáveis, onde um martingale fixo pode ficar cego ao regime',
    };
  }

  if (normalized.includes('martingale')) {
    return {
      category: 'Martingale',
      risk:
        normalized.includes('aggressive') || normalized.includes('simple')
          ? 'Alto'
          : 'Moderado/Alto',
      summary:
        'Faz compras em camadas nas quedas para reduzir preço médio e buscar recuperação posterior.',
      bestFor: 'estudar reversão com atenção ao risco de exposição crescente',
    };
  }

  return FALLBACK_GUIDE;
}
