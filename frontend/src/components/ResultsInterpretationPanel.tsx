import { BookOpen, ShieldAlert, Sparkles, Target } from 'lucide-react';
import { StrategyResult } from '../types/api';
import { buildResultsInterpretation } from '../lib/resultNarrative';

interface ResultsInterpretationPanelProps {
  results: Record<string, StrategyResult>;
}

const toneStyles = {
  positive:
    'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100',
  caution:
    'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100',
  neutral:
    'border-sky-200 bg-sky-50 text-sky-900 dark:border-sky-800 dark:bg-sky-950/30 dark:text-sky-100',
} as const;

export default function ResultsInterpretationPanel({
  results,
}: ResultsInterpretationPanelProps) {
  const interpretation = buildResultsInterpretation(results);

  if (!interpretation) {
    return null;
  }

  return (
    <div className="card border-slate-200 dark:border-slate-700">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-sky-100 dark:bg-sky-900/40 flex items-center justify-center">
          <BookOpen className="h-5 w-5 text-sky-700 dark:text-sky-300" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Leitura Guiada do Resultado
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Um resumo didático do que este run sugere, com foco em retorno, risco e consistência.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-4 dark:border-sky-800 dark:bg-sky-950/20">
        <div className="flex items-center gap-2 text-sky-800 dark:text-sky-200 text-sm font-semibold">
          <Sparkles className="h-4 w-4" />
          Resumo
        </div>
        <div className="mt-2 text-base font-medium text-gray-900 dark:text-gray-100">
          {interpretation.headline}
        </div>
        <div className="mt-1 text-sm text-gray-700 dark:text-gray-300">
          {interpretation.subheadline}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
            <Target className="h-3.5 w-3.5" />
            Melhor Retorno
          </div>
          <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            {interpretation.bestReturnStrategy}
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
            <Sparkles className="h-3.5 w-3.5" />
            Melhor Sharpe
          </div>
          <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            {interpretation.bestSharpeStrategy}
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
            <ShieldAlert className="h-3.5 w-3.5" />
            Maior Drawdown
          </div>
          <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            {interpretation.highestDrawdownStrategy}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-4">
        {interpretation.insights.map((insight) => (
          <div
            key={`${insight.title}-${insight.body}`}
            className={`rounded-lg border px-4 py-4 ${toneStyles[insight.tone]}`}
          >
            <div className="text-sm font-semibold">{insight.title}</div>
            <div className="mt-1 text-sm leading-relaxed opacity-90">{insight.body}</div>
          </div>
        ))}
      </div>

      <div className="mt-4 rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-4">
        <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 font-semibold">
          Como Ler Este Run
        </div>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
          {interpretation.readingGuide.map((item) => (
            <div
              key={item}
              className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-3 text-sm text-gray-700 dark:text-gray-300"
            >
              {item}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
