import ChartsTabbed from '../ChartsTabbed';
import MetricsCards from '../MetricsCards';
import { ResultsOverviewTabProps } from './types';

export default function ResultsOverviewTab({
  backtestResponse,
  visibleStrategies,
  visibleBenchmarks,
  mode = 'summary',
}: ResultsOverviewTabProps) {
  if (mode === 'charts') {
    return (
      <ChartsTabbed
        results={backtestResponse.results}
        buyHoldEquity={backtestResponse.buy_hold_equity}
        visibleStrategies={visibleStrategies}
        visibleBenchmarks={visibleBenchmarks}
        benchmarks={backtestResponse.benchmarks}
      />
    );
  }

  return (
    <div className="space-y-6">
      <MetricsCards results={backtestResponse.results} benchmarks={backtestResponse.benchmarks} />
    </div>
  );
}
