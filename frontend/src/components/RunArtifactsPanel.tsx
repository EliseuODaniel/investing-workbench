import { Database, Fingerprint, Settings2 } from 'lucide-react';
import { RunConfigSnapshot, RunDataProfile } from '../types/api';

interface RunArtifactsPanelProps {
  runId?: string;
  configSnapshot: RunConfigSnapshot | null;
  dataProfile: RunDataProfile | null;
  isLoading: boolean;
}

export default function RunArtifactsPanel({
  runId,
  configSnapshot,
  dataProfile,
  isLoading,
}: RunArtifactsPanelProps) {
  if (!isLoading && !configSnapshot && !dataProfile) {
    return null;
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Database className="h-4 w-4 mr-2" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Run Artifacts
          </h3>
        </div>
        {runId && <span className="text-xs font-mono text-gray-500">{runId}</span>}
      </div>

      {isLoading ? (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Loading persisted artifacts...
        </div>
      ) : (
        <div className="space-y-4">
          {dataProfile && (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
              <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                <Fingerprint className="h-3 w-3 mr-1" />
                Dataset Profile
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Asset</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {dataProfile.asset}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Rows</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {dataProfile.row_count.toLocaleString('pt-BR')}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Range</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {new Date(dataProfile.start_timestamp).toLocaleDateString('pt-BR')} -{' '}
                    {new Date(dataProfile.end_timestamp).toLocaleDateString('pt-BR')}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Cache</div>
                  <div className="font-mono text-xs text-gray-900 dark:text-gray-100">
                    {dataProfile.cache_path}
                  </div>
                </div>
              </div>
              <div className="mt-3">
                <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">Fingerprint</div>
                <div className="font-mono text-xs break-all text-gray-900 dark:text-gray-100">
                  {dataProfile.data_fingerprint}
                </div>
              </div>
            </div>
          )}

          {configSnapshot && (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
              <div className="flex items-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                <Settings2 className="h-3 w-3 mr-1" />
                Resolved Config
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Initial Capital</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    R${' '}
                    {configSnapshot.backtest.initial_capital.toLocaleString('pt-BR', {
                      minimumFractionDigits: 2,
                    })}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Strategies</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {configSnapshot.strategies.length}
                  </div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-1">
                {configSnapshot.strategies.map((strategy) => (
                  <span
                    key={strategy.name}
                    className="px-2 py-1 rounded-full text-xs bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200"
                  >
                    {strategy.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
