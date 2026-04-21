const strategyColors = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
  '#f97316',
];

export function getStrategyColorFactory(strategyNames: string[]) {
  return (strategyName: string) => {
    const strategyIndex = strategyNames.indexOf(strategyName);
    const safeIndex = strategyIndex >= 0 ? strategyIndex : 0;
    return strategyColors[safeIndex % strategyColors.length];
  };
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

export function toNumber(
  value: number | string | readonly (number | string)[] | undefined | null,
) {
  if (Array.isArray(value)) {
    return toNumber(value[0]);
  }
  if (typeof value === 'number') {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}
