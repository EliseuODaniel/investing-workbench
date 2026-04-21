import { MetricCardProps } from './types';

const trendColors = {
  up: 'text-success-600',
  down: 'text-danger-600',
  neutral: 'text-gray-600',
};

export default function MetricCard({
  title,
  value,
  subtitle,
  trend = 'neutral',
  icon,
  isTopPerformer,
  topPerformerLabel,
}: MetricCardProps) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg border p-6 relative ${
        isTopPerformer
          ? 'border-yellow-300 bg-gradient-to-br from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 dark:border-yellow-600'
          : 'border-gray-200 dark:border-gray-700'
      }`}
    >
      {isTopPerformer && (
        <div className="absolute top-2 right-2">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200">
            🏆 {topPerformerLabel || 'Top'}
          </span>
        </div>
      )}
      <div className="flex items-center justify-between">
        <div className={isTopPerformer ? 'pt-4' : ''}>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
          {subtitle && <p className={`text-sm mt-1 ${trendColors[trend]}`}>{subtitle}</p>}
        </div>
        {icon && (
          <div
            className={`text-gray-400 dark:text-gray-500 ${isTopPerformer ? 'text-yellow-500' : ''}`}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
