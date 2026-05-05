# Active Plans

Last updated: `2026-04-28T00:45:00-03:00`

## Current Cycle: Product Truth And Investment UX

- Keep `main` as the canonical branch unless a task explicitly asks for a review branch.
- Keep the repository synchronized with `origin/main` after coherent delivery slices.
- Make documentation reflect the real product: **Investing Workbench**, not only a martingale backtester.
- Treat `Investimentos` as the flagship didactic workflow for comparing real investment alternatives.
- Make every investor-facing flow simple, didactic, and pleasant to use before adding more depth.
- Keep advanced backtesting, pairs trading, optimization, walk-forward, Monte Carlo, and research workspaces available, but avoid letting them clutter the beginner path.

## Current Product Direction
- Position the app as **Investing Workbench**, not only as a martingale backtester.
- Keep `Investimentos` as the didactic entry point for comparing B3-oriented investments and guided portfolios.
- Keep `Simular` for strategy backtests and `Avancado` for research workflows and labs.
- Prefer simple investor-first UX in the main product and push technical density deeper into advanced areas.
- Optimize for a user who is curious but not technical: plain-language decisions, progressive disclosure, readable charts, and clear caveats.
- Current roadmap implementation estimate: **100% complete** for the planned cycle. Remaining ideas now belong to a post-roadmap evolution track, mainly deeper external product data and richer integrations rather than missing planned foundations.

## Highest-Value Next Work

1. Treat the planned roadmap as concluded and use the new `study_quality` panel as the in-product completion gate for investment studies.
2. Keep future work in a post-roadmap track: deeper external product data, richer live integrations, and broader product catalogs with explicit source/freshness guarantees. The first implementation slice is tracked in `docs/POST_ROADMAP_PRODUCT_DATA_PLAN.md`.
3. Preserve the current validation baseline: full backend tests, full frontend tests under Node 22, backend lint/type checks, and production frontend build.

## Recently Implemented In This Cycle

- Started the next implementation cycle with a `product_realism` response payload and frontend panel that explains tax/IOF, fees/spreads, liquidity, mark-to-market, income/reinvestment, product investability, and retail fixed-income gaps.
- Extracted `InvestmentReviewStatsPanel` from `InvestmentsWorkspace.tsx` as the first review-step component split.
- Added `src/investing_workbench/application/investments/product_realism.py` so the backend service delegates investable-product methodology metadata instead of growing the main service.
- Extracted result highlight cards into `InvestmentHighlightsPanel` and comparison summary builders into `application/investments/summaries.py`.
- Added the first retail fixed-income equivalence layer with `retail_fixed_income_equivalence`, comparing taxable CDB `% CDI` against tax-exempt LCI/LCA after IR and IOF.
- Turned the decision-profile form into a three-step wizard for objective, horizon/liquidity/mark-to-market, and tax/income preferences.
- Added `result_stories` with guided readings and first rankings for SELIC, inflation protection, drawdown, volatility, final value, and real return.
- Added `cache_status` to make listed-asset, fixed-income-index, and Tesouro Direto cache readiness visible in the result; it now also reports latest file, cache age, freshness, and refresh hints.
- Added the first `market_explorer` catalog facets for category lists, product types, risk, region, and ranking backlog inspired by market-list workflows.
- Extracted the fixed-income backtest result section into `InvestmentFixedIncomeBacktestPanel`, reducing `InvestmentsWorkspace.tsx` and giving the renda fixa study UI its own typed component.
- Extracted the final comparison table, quick readings, inflation summary, class summary, and benchmark summary into `InvestmentComparisonSummaryPanel`.
- Extracted portfolio sleeve/category contribution rendering into `InvestmentPortfolioContributionPanel`.
- Extracted result chart controls/rendering into `InvestmentResultChartPanel` and warnings/sources into `InvestmentResultFootnotesPanel`.
- Extracted the result-tab composition into `InvestmentResultsPanel`, leaving `InvestmentsWorkspace.tsx` closer to orchestration-only behavior.
- Extracted the internal backend `SimulationResult` value object into `application/investments/simulation_models.py`.
- Added `market_rankings` with period return, real return, drawdown, volatility, momentum, distance from peak, beta to benchmark, guided factor score, benchmark context, methodology notes, and CSV export in the frontend.
- Added local reusable custom portfolios in `Investimentos`, with save/apply/delete actions backed by browser storage.
- Added `portfolio_lifecycle` scenario cards for withdrawal, retirement target, pre-retirement stability, accumulation, and portfolio-versus-single-asset comparison.
- Added `market_screeners`, a reusable screener layer over the selected universe with first presets for real return, drawdown, volatility, and income candidates.
- Added a local Pairs radar in the Labs surface so relevant cointegration/backtest studies can be favorited and reopened while comparing candidate universes.
- Started backend persistence for investment workspaces so reusable custom portfolios and Pairs radar favorites can move beyond browser-only storage.
- Added `POST /investments/market-rankings` as a compact market-explorer endpoint over presets or explicit universes, reusing the same rankings, screeners, and cache observability as full comparisons.
- Connected the Investment Market Explorer panel to that endpoint so the selected guided study can generate rankings and screeners on demand from the first setup tab.
- Migrated the active Vite dev server and focused frontend validation to Node `22.20.0`.
- Connected `GET /backtests/strategy-catalog` to the `Simular` UI with a strategy catalog panel covering families, risk notes, score dimensions, and the planned radar of setups.
- Added a local strategy setup radar in `Simular`, letting strategies from the catalog be favorited before full parameter/workspace persistence arrives.
- Persisted the `Simular` strategy setup radar through `/investments/workspaces/strategy-radar`, while keeping browser storage as the offline/local fallback.
- Extracted the `Simular` setup-radar persistence into `useSavedStrategyRadar`, reducing visual component state and matching the existing persisted-workspace hook pattern.
- Expanded strategy catalog/radar payloads with initial parameter defaults, suggested universe, timeframe, and setup notes so favorites become reusable setup drafts instead of name-only bookmarks.
- Added inline editing for saved `Simular` setup drafts, allowing timeframe, universe, parameters, and notes to be adjusted and persisted before the future run/compare action.
- Added `POST /backtests/strategy-setup-plan` and a `Preparar execucao` action in the radar, turning a saved setup into a reviewable route/payload plan with assumptions, warnings, and next actions.
- Connected prepared setup plans with `route_hint=/backtest` to real backtest execution from the `Simular` radar, showing completion count and persisted run id when available.
- Added local run history for executed `Simular` setups, showing latest execution count, total return, drawdown, run id, and recent runs per setup.
- Added a first explainable local score/ranking for executed `Simular` setups, balancing return, drawdown, and a capped trade-count execution signal from the latest run history.
- Persisted `Simular` setup execution summaries through `/investments/workspaces/strategy-setup-runs`, keeping browser storage as fallback for history and ranking hydration.
- Added backend setup scoring through `/investments/workspaces/strategy-setup-scores`, with component fields for return score, drawdown penalty, execution score, robustness score, data-validity score, route, run id, and Pairs backtest id; the frontend uses the remote score first and local scoring only as fallback.
- Exposed the setup score decomposition in the `Simular` radar UI, showing return contribution, drawdown penalty, execution contribution, and the formula next to each ranked setup.
- Added quick setup-comparison readings to the `Simular` radar: best score, highest return, lowest drawdown, and strongest evidence.
- Added CSV export for the executed setup ranking in `Simular`, including score components, run ids, Pairs backtest ids, route hints, and methodology.
- Extracted setup scoring, quick insights, and CSV serialization into `frontend/src/lib/strategySetupScoring.ts`, with focused unit coverage separate from the visual radar component.
- Extracted the visual setup ranking/CSV/insights block into `frontend/src/components/strategy/StrategySetupRankingPanel.tsx`, reducing `StrategyCatalogPanel` responsibility while preserving the `Simular` radar flow.
- Extracted prepared-plan execution, Pairs handoff actions, loaded-result summaries, and setup history rendering into `frontend/src/components/strategy/StrategySetupPlanCard.tsx`, reducing `StrategyCatalogPanel.tsx` to about 630 lines.
- Extracted setup draft editing into `frontend/src/components/strategy/StrategySetupEditForm.tsx`, bringing `StrategyCatalogPanel.tsx` below 600 lines while preserving the saved-radar edit flow.
- Extracted each saved setup radar card into `frontend/src/components/strategy/StrategySetupRadarItemCard.tsx`, reducing `StrategyCatalogPanel.tsx` to under 500 lines while keeping the prepare/run/edit/remove flow covered by existing tests.
- Extracted catalog strategy cards and planned-score dimensions into `StrategyCatalogList.tsx` and `StrategyScoreDimensionsPanel.tsx`, bringing `StrategyCatalogPanel.tsx` to about 416 lines.
- Extracted the full saved-setup radar section into `StrategySetupRadarSection.tsx`, bringing `StrategyCatalogPanel.tsx` to about 382 lines while preserving the same tested radar interactions.
- Extracted setup draft serialization/parsing into `frontend/src/lib/strategySetupDrafts.ts`, with focused coverage for parameter parsing, ticker lists, notes, and draft application; `StrategyCatalogPanel.tsx` is now about 328 lines.
- Extracted setup execution state and actions into `frontend/src/hooks/useStrategySetupExecution.ts`, covering plan preparation, `/backtest` and `/pairs/backtests` execution, history hydration, remote scores, loaded results, unsupported routes, and Pairs handoff; `StrategyCatalogPanel.tsx` is now about 199 lines.
- Extracted catalog loading and setup history/score hydration into `frontend/src/hooks/useStrategyCatalogData.ts`, with focused coverage for successful hydration and API error messaging; `StrategyCatalogPanel.tsx` is now about 161 lines.
- Extracted setup draft editing state/actions into `frontend/src/hooks/useStrategySetupDraftEditor.ts`, with focused coverage for start/update/save/cancel; `StrategyCatalogPanel.tsx` is now about 138 lines.
- Extracted setup score selection and insights into `frontend/src/hooks/useStrategySetupScores.ts`, covering remote-first scoring and local fallback; `StrategyCatalogPanel.tsx` is now about 131 lines.
- Extracted setup run-history helpers and Pairs handoff draft construction into `frontend/src/lib/strategySetupHistory.ts`, with focused coverage for history merge, persistence filtering, core backtest summaries, and Pairs summaries.
- Extracted backend setup scoring into `application/investment_workspaces/setup_scoring.py`, keeping `InvestmentWorkspaceService` as a persistence/orchestration facade and adding focused unit coverage for ranking components and data validity.
- Added income-policy examples to `product_realism`, separating how stocks/JCP, FIIs, ETFs, Tesouro Direto, and portfolios should be read for cash flow, tax caveats, reinvestment, and investor decision context; the frontend now renders this as "Politica de renda e reinvestimento".
- Expanded retail fixed-income equivalence with taxable product examples for CDB daily liquidity, Tesouro Selic proxy, and DI funds with administration fees, showing gross `% CDI`, estimated net `% CDI`, IR/IOF, liquidity, and risk notes in the result panel.
- Added a didactic withdrawal plan to portfolio lifecycle results, ranking candidates by estimated real monthly withdrawal, gap versus the user's income target, historical drawdown, and real CAGR.
- Added retirement stress tests to the withdrawal plan, showing base, conservative, and sequence-stress income scenarios with drawdown buffers and income-target gaps.
- Expanded catalog coverage with additional FIIs, BDRs, a crypto ETF comparison, new presets for FIIs/BDRs/risk spectrum, and Market Explorer curated lists for income, FIIs, exterior via B3, NTN-B ETFs, Tesouro Direto, and risk ladder.
- Added a deterministic Monte Carlo preview to the withdrawal plan, using real CAGR, annual volatility, approximate P50/P25/P10 income scenarios, years of target-income coverage, and an explicit caveat before full monthly resampling exists.
- Extended the Monte Carlo preview with a 30-year monthly exhaustion simulation over favorable, base, and adverse sequences, showing withdrawal amount, success rate, final balance, and exhaustion year when applicable.
- Added reproducible stochastic monthly Monte Carlo with 250 trajectories, stable per-asset seed, success rate, final-balance percentiles, median exhaustion timing, and compact frontend rendering inside the withdrawal plan.
- Added `product_data_plan` to the investments catalog, exposing source registry, integration status, family coverage, next release candidates, quality gates, and a setup-tab UI panel for the post-roadmap data track.
- Expanded `product_data_plan` into the 1-9 implementation track with connector status, expected fields, local source manifest, release packages, market-filter backlog, validation gates, and UI readiness summaries.
- Added the first controlled product-data refresh endpoint for `b3_fii_listed`, persisting a local CSV seed plus `manifest.json`, exposing row count/checksum/schema in the catalog manifest, and wiring the setup panel to trigger the refresh.
- Extended product-data refresh with official B3 page collection attempt, curated fallback, refresh history, selectable source refresh in the UI, and Market Explorer filters/screeners for cached FII segment/listing-status metadata.
- Added fixture-backed B3 FII parser coverage, richer refresh timing/URL history, automatic catalog reload after product-data refresh, first CVM seed refresh, FII identity map, and cached FII rankings for data quality plus income quality (`fii_data_quality`, `fii_income_quality`).
- Promoted the CVM daily-fund-report connector from seed-only to official monthly ZIP attempt, with CSV normalization for quota, PL, daily subscriptions/redemptions, holder count, parser tests, and transparent fallback.
- Added `cvm_fund_profile` to the product-data plan and setup UI, summarizing cached CVM row count, latest competence date, aggregate PL, net flow, holder count, and largest fund/class samples.
- Added initial CVM fund/class rankings for largest net worth, highest net flow, and largest holder base, exposed in the setup product-data panel with the CNPJ-to-catalog caveat still explicit.
- Promoted `b3_listed_products` to an operational controlled refresh with ETF/BDR listed-product metadata, then exposed `etf_bdr_profile` and `b3_lowest_admin_fee` in the product-data plan/UI.
- Added `fii_cvm_bridge`, an explicit initial crosswalk from FII tickers to CVM CNPJs, showing mapped instruments, cache matches, latest CVM date, PL, quota, and holder count when available.
- Added `methodology_readiness_ranking`, a final consolidated product-data ranking across FIIs, ETFs and BDRs with score components, source ids, and explicit caveats so it is not mistaken for a buy recommendation.
- Added catalog-level product profiles for assets, portfolios, proxies, fixed-income indices, Tesouro Direto, FIIs, ETFs and BDRs, exposing investability, liquidity, tax treatment, income policy, fee model, and data-quality labels in the setup review UI.
- Added `study_quality`, a final readiness checklist in the comparison payload and frontend result view, consolidating methodology, product realism, rankings, renda fixa, cache, retirement/Monte Carlo, warnings, and completion score.
- Added compact run-result reopening from the `Simular` setup history via `GET /runs/{run_id}/response`, showing return, drawdown, and trades per strategy inside the radar.
- Added a Pairs setup handoff from the `Simular` radar into the Pairs lab, persisting the draft tickers and z-score/formation parameters so the advanced workspace opens prefilled.
- Wired the Pairs setup handoff to app navigation so triggering it from `Simular` opens `Avancado > Pairs B3` directly.
- Added direct execution for prepared `pairs_cointegration` setups from the `Simular` radar through `/pairs/backtests`, persisting `pairs_backtest_id`, reopening Pairs results, and storing scenario metrics/score history alongside regular backtest runs.
- Expanded retail fixed-income equivalence rows to include incentivized debentures alongside LCI/LCA as tax-exempt references against taxable CDB `% CDI`.
- Added `GET /backtests/strategy-catalog` with initial strategy metadata, score dimensions, and radar plan for the `Simular` roadmap.
- Added backend narrative builders for methodology, fixed-income decision guidance, and portfolio/objective interpretation.
- Added frontend result panels for "Como ler este estudo", "Como decidir em renda fixa", and "Decisao por objetivo".
- Reduced frontend cold-start weight by lazy-loading the primary app sections and each advanced workspace; the production build no longer emits the previous Vite large-chunk warning.
- Moved renda fixa study construction out of the main `InvestmentComparisonService` into `application/investments/fixed_income_studies.py` through a dedicated `FixedIncomeStudyService`.
- Added a decision-profile request layer for objective, horizon, liquidity, mark-to-market tolerance, tax view, and monthly income target.
- Added scenario cards for income capacity, retirement real return, capital preservation, and wealth accumulation.
- Added tests around the new investment narrative contract and result panels.

## Migration Guardrails
- The existing `src/` runtime remains valid until the new architecture is feature-complete.
- Migrate behavior through adapters, not rewrites.
- Preserve YAML config compatibility during the migration.
- Do not expand the asset catalog faster than methodology, assumptions, and validation can explain the results.
- Do not add advanced controls to the default screen unless the user can understand why they matter at first scan.
