import AllocationWorkspace from '../AllocationWorkspace';

interface AllocationSectionProps {
  onError: (message: string | null) => void;
}

export default function AllocationSection({ onError }: AllocationSectionProps) {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Planejamento de Alocacao
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Esta area transforma carteira atual, pesos-alvo e restricoes de caixa em um plano
          reutilizavel de rebalanceamento.
        </p>
      </div>
      <AllocationWorkspace onError={onError} />
    </div>
  );
}
