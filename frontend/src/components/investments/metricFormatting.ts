import { formatCurrency, formatNumber, formatPercent } from '../../lib/utils';

export function formatInvestmentMetric(value?: number | null, kind?: string | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return 'n/a';
  }
  if (kind === 'currency') {
    return formatCurrency(value);
  }
  if (kind === 'percent') {
    return formatPercent(value);
  }
  return formatNumber(value, 2);
}
