import { AlertTriangle, Loader2, PauseCircle, PlayCircle, RefreshCw } from 'lucide-react';
import { BacktestJobPayload } from '../types/api';

interface BacktestJobsPanelProps {
  jobs: BacktestJobPayload[];
  activeJob: BacktestJobPayload | null;
  isLoadingJobs: boolean;
  isCancellingJob: boolean;
  onOpenJob: (jobId: string) => void;
  onResumeJob: (jobId: string) => void;
  onCancelActiveJob: () => void;
  onRefreshJobs: () => void;
}

function statusBadgeClasses(status: BacktestJobPayload['status']): string {
  switch (status) {
    case 'completed':
      return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200';
    case 'failed':
      return 'bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-200';
    case 'cancelled':
      return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
    default:
      return 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-200';
  }
}

function formatStatus(status: BacktestJobPayload['status']): string {
  if (status === 'queued') return 'Na fila';
  if (status === 'running') return 'Executando';
  if (status === 'completed') return 'Concluido';
  if (status === 'failed') return 'Falhou';
  return 'Cancelado';
}

export default function BacktestJobsPanel({
  jobs,
  activeJob,
  isLoadingJobs,
  isCancellingJob,
  onOpenJob,
  onResumeJob,
  onCancelActiveJob,
  onRefreshJobs,
}: BacktestJobsPanelProps) {
  const runningJob = activeJob && ['queued', 'running'].includes(activeJob.status) ? activeJob : null;
  const recentEvents = activeJob ? [...activeJob.events].slice(-8).reverse() : [];

  return (
    <div className="card space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Backtest Jobs
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Execute backtests pesados fora do request principal, acompanhe progresso e retome jobs
            interrompidos.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefreshJobs}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Atualizar
        </button>
      </div>

      {runningJob && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-900/60 dark:bg-amber-950/20">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-amber-900 dark:text-amber-100">
                <Loader2 className="h-4 w-4 animate-spin" />
                Job ativo: {runningJob.job_id}
              </div>
              <p className="text-sm text-amber-800 dark:text-amber-200">
                {runningJob.progress.message}
              </p>
              <div className="h-2 w-full overflow-hidden rounded-full bg-amber-100 dark:bg-amber-900/50">
                <div
                  className="h-full rounded-full bg-amber-500 transition-all"
                  style={{ width: `${Math.max(4, runningJob.progress.percent)}%` }}
                />
              </div>
              <div className="flex flex-wrap gap-3 text-xs text-amber-900/80 dark:text-amber-200/80">
                <span>{runningJob.progress.percent.toFixed(0)}% completo</span>
                {runningJob.progress.total_steps ? (
                  <span>
                    Etapa {runningJob.progress.current_step ?? 0}/{runningJob.progress.total_steps}
                  </span>
                ) : null}
                {runningJob.cancel_requested ? <span>Cancelamento solicitado</span> : null}
              </div>
            </div>
            <button
              type="button"
              onClick={onCancelActiveJob}
              disabled={isCancellingJob || runningJob.cancel_requested}
              className="rounded-lg border border-amber-300 px-3 py-2 text-xs font-medium text-amber-900 transition hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-amber-700 dark:text-amber-100 dark:hover:bg-amber-900/40"
            >
              {runningJob.cancel_requested
                ? 'Cancelamento solicitado'
                : isCancellingJob
                  ? 'Cancelando...'
                  : 'Cancelar'}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {isLoadingJobs && jobs.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Carregando jobs...</p>
        ) : jobs.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Nenhum job assíncrono de backtest foi persistido ainda.
          </p>
        ) : (
          jobs.map((job) => (
            <div
              key={job.job_id}
              className="flex flex-col gap-3 rounded-xl border border-gray-200 p-4 dark:border-gray-700"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {job.job_id}
                    </span>
                    <span
                      className={`rounded-full px-2 py-1 text-[11px] font-medium ${statusBadgeClasses(
                        job.status
                      )}`}
                    >
                      {formatStatus(job.status)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    {job.config_path ?? 'Config nao informado'}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
                    <span>{job.progress.percent.toFixed(0)}%</span>
                    <span>{job.progress.phase}</span>
                    <span>Tentativa {job.attempt_count}</span>
                    {job.worker_id ? <span>Worker: {job.worker_id}</span> : null}
                    {job.run_id ? <span>Run: {job.run_id}</span> : null}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {job.status === 'completed' && job.run_id ? (
                    <button
                      type="button"
                      onClick={() => onOpenJob(job.job_id)}
                      className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 px-3 py-2 text-xs font-medium text-emerald-700 transition hover:bg-emerald-50 dark:border-emerald-900/60 dark:text-emerald-200 dark:hover:bg-emerald-950/30"
                    >
                      <PlayCircle className="h-3.5 w-3.5" />
                      Abrir run
                    </button>
                  ) : null}
                  {(job.status === 'failed' || job.status === 'cancelled') && (
                    <button
                      type="button"
                      onClick={() => onResumeJob(job.job_id)}
                      className="inline-flex items-center gap-2 rounded-lg border border-blue-200 px-3 py-2 text-xs font-medium text-blue-700 transition hover:bg-blue-50 dark:border-blue-900/60 dark:text-blue-200 dark:hover:bg-blue-950/30"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      Retomar
                    </button>
                  )}
                  {(job.status === 'queued' || job.status === 'running') && (
                    <button
                      type="button"
                      onClick={() => onOpenJob(job.job_id)}
                      className="inline-flex items-center gap-2 rounded-lg border border-amber-200 px-3 py-2 text-xs font-medium text-amber-700 transition hover:bg-amber-50 dark:border-amber-900/60 dark:text-amber-200 dark:hover:bg-amber-950/30"
                    >
                      <PauseCircle className="h-3.5 w-3.5" />
                      Acompanhar
                    </button>
                  )}
                </div>
              </div>

              {job.error ? (
                <div className="inline-flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-200">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
                  <span>{job.error}</span>
                </div>
              ) : (
                <p className="text-sm text-gray-600 dark:text-gray-300">{job.progress.message}</p>
              )}
            </div>
          ))
        )}
      </div>

      {activeJob && (
        <div className="rounded-xl border border-gray-200 p-4 dark:border-gray-700">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Job selecionado
              </h4>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{activeJob.job_id}</p>
            </div>
            <span
              className={`rounded-full px-2 py-1 text-[11px] font-medium ${statusBadgeClasses(
                activeJob.status
              )}`}
            >
              {formatStatus(activeJob.status)}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="rounded-lg bg-gray-50 px-3 py-3 text-sm dark:bg-gray-800">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Config
              </div>
              <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                {activeJob.config_path ?? 'n/a'}
              </div>
            </div>
            <div className="rounded-lg bg-gray-50 px-3 py-3 text-sm dark:bg-gray-800">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Estrategias
              </div>
              <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                {activeJob.strategy_names.length > 0
                  ? activeJob.strategy_names.join(', ')
                  : 'Todas do config'}
              </div>
            </div>
            <div className="rounded-lg bg-gray-50 px-3 py-3 text-sm dark:bg-gray-800">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Runtime
              </div>
              <div className="mt-1 font-medium text-gray-900 dark:text-gray-100">
                Tentativa {activeJob.attempt_count}
                {activeJob.run_id ? ` · ${activeJob.run_id}` : ''}
                {activeJob.worker_id ? ` · ${activeJob.worker_id}` : ''}
              </div>
            </div>
          </div>

          <div className="mt-4">
            <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Timeline recente
            </div>
            <div className="mt-2 space-y-2">
              {recentEvents.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Nenhum evento registrado ainda.
                </p>
              ) : (
                recentEvents.map((event) => (
                  <div
                    key={`${event.timestamp}-${event.phase}-${event.message}`}
                    className="rounded-lg border border-gray-200 px-3 py-3 text-sm dark:border-gray-700"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-medium text-gray-900 dark:text-gray-100">
                        {event.phase}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(event.timestamp).toLocaleString('pt-BR')}
                      </div>
                    </div>
                    <div className="mt-1 text-gray-600 dark:text-gray-300">{event.message}</div>
                    {typeof event.percent === 'number' ? (
                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {event.percent.toFixed(0)}%
                      </div>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
