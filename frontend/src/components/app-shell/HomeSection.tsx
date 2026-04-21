import type { ReactNode } from 'react';
import {
  ArrowRight,
  BarChart3,
  BookOpenText,
  Briefcase,
  FlaskConical,
  PlayCircle,
} from 'lucide-react';

interface HomeSectionProps {
  runsCount: number;
  workspaceCount: number;
  comparisonCount: number;
  onOpenInvestments: () => void;
  onStartSimulation: () => void;
  onOpenResults: () => void;
  onOpenPlanner: () => void;
  onOpenAdvanced: () => void;
}

interface ActionCardProps {
  title: string;
  description: string;
  eyebrow: string;
  icon: ReactNode;
  cta: string;
  badge?: string;
  onClick: () => void;
}

function ActionCard({
  title,
  description,
  eyebrow,
  icon,
  cta,
  badge,
  onClick,
}: ActionCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex h-full flex-col rounded-2xl border border-gray-200 bg-white p-5 text-left transition hover:-translate-y-0.5 hover:border-gray-300 hover:shadow-sm dark:border-gray-700 dark:bg-gray-800/80 dark:hover:border-gray-600"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="rounded-2xl bg-gray-100 p-3 text-gray-700 dark:bg-gray-700/70 dark:text-gray-100">
          {icon}
        </div>
        {badge ? (
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-200">
            {badge}
          </span>
        ) : null}
      </div>
      <div className="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">
        {eyebrow}
      </div>
      <h3 className="mt-2 text-xl font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
      <p className="mt-2 flex-1 text-sm leading-6 text-gray-600 dark:text-gray-300">
        {description}
      </p>
      <div className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-blue-700 transition group-hover:gap-3 dark:text-blue-300">
        {cta}
        <ArrowRight className="h-4 w-4" />
      </div>
    </button>
  );
}

export default function HomeSection({
  runsCount,
  workspaceCount,
  comparisonCount,
  onOpenInvestments,
  onStartSimulation,
  onOpenResults,
  onOpenPlanner,
  onOpenAdvanced,
}: HomeSectionProps) {
  return (
    <div className="space-y-6">
      <div className="card overflow-hidden">
        <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-300">
              Fluxo principal
            </div>
            <h2 className="mt-3 text-3xl font-semibold text-gray-900 dark:text-gray-100">
              Comece pela tarefa, nao pelo nome do modulo.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-gray-600 dark:text-gray-300">
              A interface agora parte do que uma pessoa quer fazer: testar uma ideia,
              abrir um resultado salvo, montar um plano de carteira ou entrar num estudo
              mais tecnico.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={onOpenInvestments}
                className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-emerald-700"
              >
                Comparar investimentos B3
              </button>
              <button
                type="button"
                onClick={onStartSimulation}
                className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-700"
              >
                Rodar um backtest simples
              </button>
              <button
                type="button"
                onClick={onOpenResults}
                className="rounded-xl border border-gray-200 px-4 py-3 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                Abrir resultados salvos
              </button>
            </div>
          </div>

          <div className="grid gap-3 rounded-2xl border border-gray-200 bg-gray-50/80 p-4 dark:border-gray-700 dark:bg-gray-800/50">
            <div className="rounded-xl bg-white px-4 py-3 dark:bg-gray-900/50">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Resultados recentes
              </div>
              <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {runsCount}
              </div>
            </div>
            <div className="rounded-xl bg-white px-4 py-3 dark:bg-gray-900/50">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Estudos salvos
              </div>
              <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {workspaceCount}
              </div>
            </div>
            <div className="rounded-xl bg-white px-4 py-3 dark:bg-gray-900/50">
              <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Selecionados para comparar
              </div>
              <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {comparisonCount}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-5">
        <ActionCard
          eyebrow="Passo 1"
          title="Investimentos"
          description="Compare acoes, ETFs, FIIs, renda fixa e ativos internacionais pela B3 com o mesmo fluxo de aportes."
          icon={<Briefcase className="h-5 w-5" />}
          cta="Abrir comparador"
          onClick={onOpenInvestments}
        />
        <ActionCard
          eyebrow="Passo 2"
          title="Simular"
          description="Use o fluxo guiado para escolher configuracao, periodo e dados sem abrir areas tecnicas desnecessarias."
          icon={<PlayCircle className="h-5 w-5" />}
          cta="Abrir simulador"
          onClick={onStartSimulation}
        />
        <ActionCard
          eyebrow="Passo 3"
          title="Resultados"
          description="Reabra backtests salvos, compare execucoes e continue de onde parou."
          icon={<BarChart3 className="h-5 w-5" />}
          cta="Ver resultados"
          badge={runsCount > 0 ? `${runsCount} salvos` : undefined}
          onClick={onOpenResults}
        />
        <ActionCard
          eyebrow="Complementar"
          title="Planejar carteira"
          description="Transforme pesos desejados e caixa disponivel em um plano de rebalanceamento mais direto."
          icon={<Briefcase className="h-5 w-5" />}
          cta="Abrir planejador"
          onClick={onOpenPlanner}
        />
        <ActionCard
          eyebrow="Quando precisar"
          title="Estudos avancados"
          description="Optimization, walk-forward, pairs trading e outras analises mais tecnicas ficam aqui, separadas do fluxo simples."
          icon={<FlaskConical className="h-5 w-5" />}
          cta="Explorar avancado"
          onClick={onOpenAdvanced}
        />
      </div>

      <div className="card">
        <div className="flex items-start gap-3">
          <BookOpenText className="mt-1 h-5 w-5 text-blue-600 dark:text-blue-300" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Como usar sem se perder
            </h3>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <div className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:bg-gray-800/70 dark:text-gray-300">
                <strong className="block text-gray-900 dark:text-gray-100">1. Simular</strong>
                Rode um backtest primeiro. Isso gera um resultado concreto para ler.
              </div>
              <div className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:bg-gray-800/70 dark:text-gray-300">
                <strong className="block text-gray-900 dark:text-gray-100">2. Resultados</strong>
                Depois compare runs, revise trades e guarde os estudos que importam.
              </div>
              <div className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:bg-gray-800/70 dark:text-gray-300">
                <strong className="block text-gray-900 dark:text-gray-100">3. Avancado</strong>
                Entre nos labs apenas quando precisar de pesquisa quantitativa mais profunda.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
