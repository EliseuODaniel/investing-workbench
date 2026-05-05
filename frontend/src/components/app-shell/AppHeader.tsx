import { Activity, AlertTriangle, ChevronDown, DatabaseZap, FolderKanban } from 'lucide-react';
import DarkModeToggle from '../DarkModeToggle';
import { useSystemStatus } from '../../hooks/useSystemStatus';

function statusClasses(isLoading: boolean, isDegraded: boolean, hasError: boolean): string {
  if (isLoading) {
    return 'border-gray-200 bg-white text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300';
  }
  if (hasError || isDegraded) {
    return 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200';
  }
  return 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-200';
}

export default function AppHeader() {
  const { status, isLoading, isStale, error } = useSystemStatus();
  const warningCount = status?.warnings.length ?? 0;
  const activeJobs =
    (status?.job_counts.queued ?? 0) +
    (status?.job_counts.running ?? 0) +
    (status?.pairs_job_counts.queued ?? 0) +
    (status?.pairs_job_counts.running ?? 0);
  const hasError = error !== null;
  const isDegraded = status?.status === 'degraded' || isStale;
  const statusLabel = isLoading
    ? 'Verificando sistema'
    : hasError
      ? 'Diagnostico indisponivel'
      : isStale
        ? 'Diagnostico com atraso'
      : isDegraded
        ? `Atencao: ${warningCount} alerta${warningCount === 1 ? '' : 's'}`
        : 'Sistema pronto';

  return (
    <div className="mb-8 flex items-start justify-between gap-6">
      <div className="max-w-3xl">
        <h1 className="mb-2 text-3xl font-bold text-gray-900 dark:text-gray-100">
          Investing Workbench
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Uma plataforma mais direta para comparar investimentos, testar ideias e so
          entrar em estudos quantitativos quando realmente fizer sentido.
        </p>
      </div>

      <div className="flex items-start gap-3">
        <div
          className={`min-w-[250px] rounded-2xl border px-4 py-3 text-sm ${statusClasses(
            isLoading,
            isDegraded,
            hasError
          )}`}
        >
          <div className="flex items-center gap-2 font-medium">
            {hasError || isDegraded ? (
              <AlertTriangle className="h-4 w-4" />
            ) : (
              <Activity className="h-4 w-4" />
            )}
            {statusLabel}
          </div>

          {hasError ? <p className="mt-2 text-xs opacity-80">Motivo: {error}</p> : null}

          {status && !hasError && (
            <>
              <p className="mt-2 text-xs opacity-80">
                {status.dataset_count} bases, {status.config_count} configuracoes e {activeJobs}{' '}
                tarefa{activeJobs === 1 ? '' : 's'} ativa{activeJobs === 1 ? '' : 's'} agora.
              </p>

              <div className="mt-3 grid grid-cols-4 gap-3 text-xs">
                <div>
                  <div className="flex items-center gap-1 opacity-75">
                    <FolderKanban className="h-3.5 w-3.5" />
                    Configs
                  </div>
                  <div className="mt-1 font-semibold">{status.config_count}</div>
                </div>
                <div>
                  <div className="flex items-center gap-1 opacity-75">
                    <DatabaseZap className="h-3.5 w-3.5" />
                    Datasets
                  </div>
                  <div className="mt-1 font-semibold">
                    {status.dataset_count}
                    {status.due_dataset_count > 0 && (
                      <span className="ml-1 text-[10px] font-medium opacity-75">
                        ({status.due_dataset_count} due)
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <div className="opacity-75">Jobs</div>
                  <div className="mt-1 font-semibold">{activeJobs}</div>
                </div>
                <div>
                  <div className="opacity-75">Warnings</div>
                  <div className="mt-1 font-semibold">{warningCount}</div>
                </div>
              </div>

              <details className="mt-3 rounded-xl border border-current/10 bg-black/5 px-3 py-2 dark:bg-white/5">
                <summary className="flex cursor-pointer list-none items-center gap-2 text-[11px] font-medium opacity-80">
                  <ChevronDown className="h-3.5 w-3.5" />
                  Ver diagnostico tecnico
                </summary>
                <div className="mt-2 space-y-1 text-[11px] opacity-75">
                  <div>Core runtime: {status.job_runtime.execution_mode}</div>
                  <div>Pairs runtime: {status.pairs_job_runtime.execution_mode}</div>
                  {status.latest_backtest_job_id ? <div>Ultimo job core: {status.latest_backtest_job_id}</div> : null}
                  {status.latest_pairs_backtest_job_id ? (
                    <div>Ultimo job pairs: {status.latest_pairs_backtest_job_id}</div>
                  ) : null}
                  {status.latest_run_id ? <div>Ultimo backtest: {status.latest_run_id}</div> : null}
                  {status.latest_pairs_backtest_id ? (
                    <div>Ultimo pairs: {status.latest_pairs_backtest_id}</div>
                  ) : null}
                  {status.latest_research_workspace_id ? (
                    <div>Ultimo estudo salvo: {status.latest_research_workspace_id}</div>
                  ) : null}
                </div>
              </details>
            </>
          )}
        </div>
        <DarkModeToggle />
      </div>
    </div>
  );
}
