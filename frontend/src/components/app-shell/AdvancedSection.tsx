import type { ReactNode } from 'react';
import {
  BarChart3,
  Briefcase,
  Crosshair,
  FlaskConical,
  GitBranch,
  Orbit,
  SearchCode,
  TrendingUp,
} from 'lucide-react';
import AllocationSection from './AllocationSection';
import MonteCarloWorkspace from '../MonteCarloWorkspace';
import OptimizationWorkspace from '../OptimizationWorkspace';
import PairsTradingWorkspace from '../PairsTradingWorkspace';
import ResearchDrilldownPanel from '../ResearchDrilldownPanel';
import ResearchOverviewPanel from '../ResearchOverviewPanel';
import Wege3RegraAWorkspace from '../Wege3RegraAWorkspace';
import WalkForwardWorkspace from '../WalkForwardWorkspace';
import { AdvancedTool } from '../../hooks/useAppShellState';
import { ResearchWorkspacePayload } from '../../types/api';

interface AdvancedSectionProps {
  advancedTool: AdvancedTool;
  advancedTools: Array<{ id: AdvancedTool; label: string; badge?: string | number }>;
  onAdvancedToolChange: (tool: AdvancedTool) => void;
  selectedConfigPath?: string;
  defaultStrategies: string[];
  currentRunId?: string;
  onError: (message: string | null) => void;
  onLoadRun: (runId: string) => Promise<void> | void;
  workspaceToOpen: ResearchWorkspacePayload | null;
  onWorkspaceOpened: () => void;
  onWorkspaceSaved: () => void;
}

const TOOL_COPY: Record<
  AdvancedTool,
  {
    icon: ReactNode;
    eyebrow: string;
    description: string;
  }
> = {
  allocation: {
    icon: <Briefcase className="h-5 w-5" />,
    eyebrow: 'Planejamento',
    description: 'Monte um plano de rebalanceamento para a carteira atual.',
  },
  optimization: {
    icon: <TrendingUp className="h-5 w-5" />,
    eyebrow: 'Pesquisa',
    description: 'Varra parametros e veja quais combinacoes sobrevivem melhor.',
  },
  research: {
    icon: <SearchCode className="h-5 w-5" />,
    eyebrow: 'Contexto',
    description: 'Relacione runs, otimizacoes, walk-forward e Monte Carlo num estudo guiado.',
  },
  walkforward: {
    icon: <GitBranch className="h-5 w-5" />,
    eyebrow: 'Validacao',
    description: 'Recalibre janelas e teste se a estrategia sustenta fora da amostra.',
  },
  montecarlo: {
    icon: <Orbit className="h-5 w-5" />,
    eyebrow: 'Risco',
    description: 'Simule cenarios alternativos e distribua incerteza de resultado.',
  },
  pairs: {
    icon: <BarChart3 className="h-5 w-5" />,
    eyebrow: 'Long & Short',
    description: 'Pesquise pairs trading por cointegracao em acoes brasileiras.',
  },
  wege3: {
    icon: <Crosshair className="h-5 w-5" />,
    eyebrow: 'Cenario dedicado',
    description: 'Rode a regra A de grade por preco em WEGE3 com trilha completa.',
  },
  drilldown: {
    icon: <FlaskConical className="h-5 w-5" />,
    eyebrow: 'Diagnostico',
    description: 'Abra detalhes tecnicos mais profundos de runs e experimentos.',
  },
};

function renderAdvancedTool(
  tool: AdvancedTool,
  props: Omit<
    AdvancedSectionProps,
    'advancedTool' | 'advancedTools' | 'onAdvancedToolChange'
  >
) {
  switch (tool) {
    case 'allocation':
      return <AllocationSection onError={props.onError} />;
    case 'optimization':
      return (
        <OptimizationWorkspace
          selectedConfigPath={props.selectedConfigPath}
          defaultStrategies={props.defaultStrategies}
          onError={props.onError}
        />
      );
    case 'research':
      return (
        <ResearchOverviewPanel
          onError={props.onError}
          onLoadRun={props.onLoadRun}
          workspaceToOpen={props.workspaceToOpen}
          onWorkspaceOpened={props.onWorkspaceOpened}
          onWorkspaceSaved={props.onWorkspaceSaved}
        />
      );
    case 'walkforward':
      return (
        <WalkForwardWorkspace
          selectedConfigPath={props.selectedConfigPath}
          defaultStrategies={props.defaultStrategies}
          onError={props.onError}
        />
      );
    case 'montecarlo':
      return (
        <MonteCarloWorkspace
          selectedConfigPath={props.selectedConfigPath}
          currentRunId={props.currentRunId}
          defaultStrategies={props.defaultStrategies}
          onError={props.onError}
        />
      );
    case 'pairs':
      return <PairsTradingWorkspace onError={props.onError} />;
    case 'wege3':
      return <Wege3RegraAWorkspace onError={props.onError} />;
    case 'drilldown':
      return <ResearchDrilldownPanel onError={props.onError} />;
  }
}

export default function AdvancedSection({
  advancedTool,
  advancedTools,
  onAdvancedToolChange,
  selectedConfigPath,
  defaultStrategies,
  currentRunId,
  onError,
  onLoadRun,
  workspaceToOpen,
  onWorkspaceOpened,
  onWorkspaceSaved,
}: AdvancedSectionProps) {
  const activeCopy = TOOL_COPY[advancedTool];

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="max-w-3xl">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Estudos avancados
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Esta area separa o fluxo de pesquisa quantitativa do uso principal. Quem
            quer apenas rodar um backtest nao precisa passar por estes controles.
          </p>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {advancedTools.map((tool) => {
            const copy = TOOL_COPY[tool.id];
            const isActive = tool.id === advancedTool;
            return (
              <button
                key={tool.id}
                type="button"
                onClick={() => onAdvancedToolChange(tool.id)}
                className={`rounded-2xl border p-4 text-left transition ${
                  isActive
                    ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950/20'
                    : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800/70 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`rounded-xl p-3 ${
                      isActive
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-200'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200'
                    }`}
                  >
                    {copy.icon}
                  </div>
                  <div>
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">
                      {copy.eyebrow}
                    </div>
                    <div className="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {tool.label}
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-300">
                  {copy.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="card">
        <div className="mb-5 max-w-3xl">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-300">
            Ferramenta ativa
          </div>
          <h3 className="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {advancedTools.find((tool) => tool.id === advancedTool)?.label}
          </h3>
          <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
            {activeCopy.description}
          </p>
        </div>

        {renderAdvancedTool(advancedTool, {
          selectedConfigPath,
          defaultStrategies,
          currentRunId,
          onError,
          onLoadRun,
          workspaceToOpen,
          onWorkspaceOpened,
          onWorkspaceSaved,
        })}
      </div>
    </div>
  );
}
