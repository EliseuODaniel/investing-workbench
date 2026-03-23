import React from 'react';
import { Eye, EyeOff, Filter } from 'lucide-react';

interface VisibilityControlsProps {
  strategies: string[];
  benchmarks: string[];
  visibleStrategies: string[];
  visibleBenchmarks: string[];
  onStrategyToggle: (strategy: string) => void;
  onBenchmarkToggle: (benchmark: string) => void;
  onToggleAllStrategies: (visible: boolean) => void;
  onToggleAllBenchmarks: (visible: boolean) => void;
}

const VisibilityControls: React.FC<VisibilityControlsProps> = ({
  strategies,
  benchmarks,
  visibleStrategies,
  visibleBenchmarks,
  onStrategyToggle,
  onBenchmarkToggle,
  onToggleAllStrategies,
  onToggleAllBenchmarks,
}) => {
  const allStrategiesVisible = strategies.length > 0 && visibleStrategies.length === strategies.length;
  const allBenchmarksVisible = benchmarks.length > 0 && visibleBenchmarks.length === benchmarks.length;

  return (
    <div className="card">
      <div className="flex items-center mb-4">
        <Filter className="h-4 w-4 mr-2" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Controles de Visibilidade
        </h3>
      </div>

      <div className="space-y-4">
        {/* Strategies Visibility */}
        {strategies.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Estratégias ({visibleStrategies.length}/{strategies.length})
              </label>
              <button
                onClick={() => onToggleAllStrategies(!allStrategiesVisible)}
                className="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
              >
                {allStrategiesVisible ? 'Ocultar todas' : 'Mostrar todas'}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {strategies.map((strategy) => (
                <button
                  key={strategy}
                  onClick={() => onStrategyToggle(strategy)}
                  className={`px-3 py-1 text-xs font-medium rounded-full border transition-colors ${
                    visibleStrategies.includes(strategy)
                      ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-800 dark:text-blue-200 dark:border-blue-600'
                      : 'bg-gray-100 text-gray-500 border-gray-300 dark:bg-gray-700 dark:text-gray-400 dark:border-gray-600'
                  }`}
                >
                  <div className="flex items-center">
                    {visibleStrategies.includes(strategy) ? (
                      <Eye className="h-3 w-3 mr-1" />
                    ) : (
                      <EyeOff className="h-3 w-3 mr-1" />
                    )}
                    {strategy}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Benchmarks Visibility */}
        {benchmarks.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Benchmarks ({visibleBenchmarks.length}/{benchmarks.length})
              </label>
              <button
                onClick={() => onToggleAllBenchmarks(!allBenchmarksVisible)}
                className="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
              >
                {allBenchmarksVisible ? 'Ocultar todos' : 'Mostrar todos'}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {benchmarks.map((benchmark) => (
                <button
                  key={benchmark}
                  onClick={() => onBenchmarkToggle(benchmark)}
                  className={`px-3 py-1 text-xs font-medium rounded-full border transition-colors ${
                    visibleBenchmarks.includes(benchmark)
                      ? 'bg-green-100 text-green-800 border-green-300 dark:bg-green-800 dark:text-green-200 dark:border-green-600'
                      : 'bg-gray-100 text-gray-500 border-gray-300 dark:bg-gray-700 dark:text-gray-400 dark:border-gray-600'
                  }`}
                >
                  <div className="flex items-center">
                    {visibleBenchmarks.includes(benchmark) ? (
                      <Eye className="h-3 w-3 mr-1" />
                    ) : (
                      <EyeOff className="h-3 w-3 mr-1" />
                    )}
                    {benchmark}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="border-t pt-4">
          <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-100 border border-blue-300 rounded-full mr-2"></div>
              <span>Estratégias de trading</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-100 border border-green-300 rounded-full mr-2"></div>
              <span>Benchmarks de referência</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisibilityControls;