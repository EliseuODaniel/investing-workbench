import FixedIncomeDecisionGuidePanel from './FixedIncomeDecisionGuidePanel';
import InvestmentCacheStatusPanel from './InvestmentCacheStatusPanel';
import InvestmentComparisonSummaryPanel from './InvestmentComparisonSummaryPanel';
import InvestmentFixedIncomeBacktestPanel from './InvestmentFixedIncomeBacktestPanel';
import InvestmentHighlightsPanel from './InvestmentHighlightsPanel';
import InvestmentMethodologyPanel from './InvestmentMethodologyPanel';
import InvestmentMarketRankingsPanel from './InvestmentMarketRankingsPanel';
import InvestmentMarketScreenersPanel from './InvestmentMarketScreenersPanel';
import InvestmentPortfolioContributionPanel from './InvestmentPortfolioContributionPanel';
import InvestmentPortfolioLifecyclePanel from './InvestmentPortfolioLifecyclePanel';
import InvestmentProductRealismPanel from './InvestmentProductRealismPanel';
import InvestmentResultChartPanel, {
  type InvestmentResultChartMode,
} from './InvestmentResultChartPanel';
import InvestmentResultFootnotesPanel from './InvestmentResultFootnotesPanel';
import InvestmentResultStoriesPanel from './InvestmentResultStoriesPanel';
import InvestmentStudyQualityPanel from './InvestmentStudyQualityPanel';
import PortfolioObjectiveSummaryPanel from './PortfolioObjectiveSummaryPanel';
import RetailFixedIncomeEquivalencePanel from './RetailFixedIncomeEquivalencePanel';
import type {
  InvestmentCatalogPayload,
  InvestmentComparisonResponsePayload,
} from '../../types/api';

interface InvestmentResultsPanelProps {
  comparison?: InvestmentComparisonResponsePayload | null;
  catalog?: InvestmentCatalogPayload | null;
  isLoadingCatalog: boolean;
  chartMode: InvestmentResultChartMode;
  onChartModeChange: (mode: InvestmentResultChartMode) => void;
}

export default function InvestmentResultsPanel({
  comparison,
  catalog,
  isLoadingCatalog,
  chartMode,
  onChartModeChange,
}: InvestmentResultsPanelProps) {
  const portfolioResults =
    comparison?.results.filter((row) => row.component_breakdown.length > 0) ?? [];

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
        Resultado didatico
      </div>
      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
        O objetivo aqui nao e adivinhar o futuro. E mostrar, com um fluxo de aportes consistente,
        qual alternativa teria rendido mais, sofrido menos e preservado melhor o poder de compra.
      </p>

      {!comparison ? (
        <div className="mt-5 rounded-2xl border border-dashed border-gray-300 px-4 py-10 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
          {isLoadingCatalog
            ? 'Carregando catalogo de investimentos...'
            : 'Escolha um objetivo, confirme os ativos e rode a comparacao.'}
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          <InvestmentHighlightsPanel
            highlights={comparison.highlights}
            resultCount={comparison.results.length}
          />

          <InvestmentStudyQualityPanel quality={comparison.study_quality} />

          <InvestmentResultStoriesPanel stories={comparison.result_stories} />

          <InvestmentMarketRankingsPanel rankings={comparison.market_rankings} />

          <InvestmentMarketScreenersPanel screeners={comparison.market_screeners} />

          <InvestmentMethodologyPanel guide={comparison.methodology_guide} />

          <InvestmentProductRealismPanel realism={comparison.product_realism} />

          <RetailFixedIncomeEquivalencePanel
            equivalence={comparison.retail_fixed_income_equivalence}
          />

          <PortfolioObjectiveSummaryPanel summary={comparison.portfolio_objective_summary} />

          <InvestmentPortfolioLifecyclePanel lifecycle={comparison.portfolio_lifecycle} />

          <InvestmentResultChartPanel
            chart={comparison.chart}
            realChart={comparison.real_chart}
            chartMode={chartMode}
            onChartModeChange={onChartModeChange}
          />

          <FixedIncomeDecisionGuidePanel guide={comparison.fixed_income_decision_guide} />

          <InvestmentCacheStatusPanel status={comparison.cache_status} />

          <InvestmentFixedIncomeBacktestPanel backtest={comparison.fixed_income_backtest} />

          <InvestmentComparisonSummaryPanel comparison={comparison} />

          <InvestmentPortfolioContributionPanel portfolioResults={portfolioResults} />

          <InvestmentResultFootnotesPanel
            warnings={comparison.warnings}
            sources={catalog?.sources}
          />
        </div>
      )}
    </section>
  );
}
