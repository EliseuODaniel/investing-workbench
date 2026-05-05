interface InvestmentReviewStatsPanelProps {
  selectedAssetCount: number;
  selectedBenchmarkCount: number;
  selectedGuidedPortfolioCount: number;
  entryMode: 'guided' | 'manual';
}

export default function InvestmentReviewStatsPanel({
  selectedAssetCount,
  selectedBenchmarkCount,
  selectedGuidedPortfolioCount,
  entryMode,
}: InvestmentReviewStatsPanelProps) {
  return (
    <div className="mt-5 grid gap-4 xl:grid-cols-4">
      <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700 dark:text-blue-300">
          Comparativos
        </div>
        <div className="mt-2 text-xl font-semibold text-blue-900 dark:text-blue-100">
          {selectedAssetCount}
        </div>
        <div className="mt-1 text-sm text-blue-800 dark:text-blue-200">
          ativos, ETFs ou carteiras entram na disputa
        </div>
      </div>
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
          Benchmarks
        </div>
        <div className="mt-2 text-xl font-semibold text-emerald-900 dark:text-emerald-100">
          {selectedBenchmarkCount}
        </div>
        <div className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
          referências para dizer se o risco valeu a pena
        </div>
      </div>
      <div className="rounded-2xl border border-violet-200 bg-violet-50 p-4 dark:border-violet-900/50 dark:bg-violet-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-700 dark:text-violet-300">
          Carteiras guiadas
        </div>
        <div className="mt-2 text-xl font-semibold text-violet-900 dark:text-violet-100">
          {selectedGuidedPortfolioCount}
        </div>
        <div className="mt-1 text-sm text-violet-800 dark:text-violet-200">
          seleções prontas com rebalanceamento embutido
        </div>
      </div>
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700 dark:text-amber-300">
          Jeito de começar
        </div>
        <div className="mt-2 text-xl font-semibold text-amber-900 dark:text-amber-100">
          {entryMode === 'guided' ? 'Estudo pronto' : 'Manual'}
        </div>
        <div className="mt-1 text-sm text-amber-800 dark:text-amber-200">
          {entryMode === 'guided'
            ? 'você revisa primeiro, depois personaliza se quiser'
            : 'você define os comparativos diretamente'}
        </div>
      </div>
    </div>
  );
}
