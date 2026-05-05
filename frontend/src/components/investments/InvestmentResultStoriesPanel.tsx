import type { InvestmentResultStoriesPayload } from '../../types/api';
import { formatCurrency, formatNumber, formatPercent } from '../../lib/utils';

interface InvestmentResultStoriesPanelProps {
  stories?: InvestmentResultStoriesPayload;
}

export default function InvestmentResultStoriesPanel({
  stories,
}: InvestmentResultStoriesPanelProps) {
  if (!stories || stories.stories.length === 0) {
    return null;
  }

  const primaryStories = stories.stories.slice(0, 6);
  const primaryRankings = stories.rankings.slice(0, 2);

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {stories.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {stories.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-gray-300 bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-950/50 dark:text-gray-200">
          {stories.stories.length} leituras
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        {primaryStories.map((story) => (
          <article
            key={story.story_id}
            className="rounded-2xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-950/30"
          >
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400">
              {story.label}
            </div>
            <div className="mt-2 text-sm font-semibold text-gray-950 dark:text-gray-100">
              {story.question}
            </div>
            <div className="mt-3 rounded-xl bg-white px-3 py-3 dark:bg-gray-900/70">
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {story.metric_label}
              </div>
              <div className="mt-1 text-lg font-semibold text-gray-950 dark:text-gray-100">
                {story.winner_label ? `${story.winner_label} · ` : null}
                {formatStoryMetric(story.metric_value, story.metric_kind)}
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-300">
              {story.interpretation}
            </p>
            <p className="mt-2 text-xs leading-5 text-amber-700 dark:text-amber-300">
              {story.caveat}
            </p>
          </article>
        ))}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {primaryRankings.map((ranking) => (
          <div
            key={ranking.ranking_id}
            className="overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800"
          >
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-800 dark:bg-gray-950/50">
              <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
                {ranking.label}
              </div>
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {ranking.metric_label}
              </div>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
              {ranking.rows.slice(0, 5).map((row) => (
                <div
                  key={`${ranking.ranking_id}-${row.instrument_id}`}
                  className="grid grid-cols-[auto_1fr_auto] items-center gap-3 px-4 py-3 text-sm"
                >
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-200">
                    {row.rank}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">
                      {row.label}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {row.category_label}
                    </div>
                  </div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    {formatStoryMetric(row.value, ranking.metric_kind)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 rounded-2xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
        <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
          Próximas perguntas
        </div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-900/90 dark:text-blue-100/90">
          {stories.next_questions.map((question) => (
            <li key={question}>- {question}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function formatStoryMetric(value: number, kind: string) {
  if (kind === 'currency') {
    return formatCurrency(value);
  }
  if (kind === 'percent') {
    return formatPercent(value);
  }
  if (kind === 'count') {
    return formatNumber(value, 0);
  }
  return formatNumber(value, 2);
}
