# Final Status

Last updated: `2026-04-28T00:45:00-03:00`
Reference point: repository state validated locally on `2026-04-28`

## Project State

The project is in a strong handoff state for the current cycle and is no longer scoped only as a Bitcoin martingale backtester.

It is now positioned as **Investing Workbench**, a broader investment comparison and backtesting platform.

Current roadmap implementation estimate: **100% complete** for the planned cycle. Remaining work is post-roadmap evolution: deeper external product data, live integrations, and broader catalogs with explicit source/freshness guarantees.

Delivered areas:
- Codex-ready repository foundation with `AGENTS.md`, skills, project docs, and CI.
- Incremental architecture migration into `src/investing_workbench/`.
- Service-layer backed API with persisted run artifacts.
- Reproducible run manifests, config snapshots, data profiles, and HTML reports.
- New domain-backed engine behind compatibility adapters.
- Analytics extracted into reusable analyzers.
- Frontend workspace for persisted run history, comparison, sharing, and exports.
- PNG export, HTML report download, and CSV trade export flows.
- Unified experiment registry across API, CLI, and frontend.
- Saved research workspaces with persistence, lineage context, and report export.
- Shared report contract for research workspaces across API, CLI, and frontend.
- Frontend performance hardening with lazy loading and manual chunking.
- Frontend dependency and security hardening with `npm audit` clean.
- Guided investment comparison flows across B3 asset classes.
- New `Investimentos` area with curated portfolios, asset catalogs, and simple comparison UX.
- Fixed-income studies with CDI, IDkA, Tesouro Direto rolling strategies, and NTN-B ETFs.
- Investment chart UX with visual date ranges, rebasing, legend focus/hide behavior, and nearest-line tooltips.
- Investment methodology and decision panels that explain evidence types, caveats, fixed-income tradeoffs, and objective-based winners.
- First backend narrative module extracted for investment methodology, fixed-income decisions, and portfolio/objective summaries.
- Decision-profile inputs and scoring for objective, horizon, liquidity, mark-to-market tolerance, tax view, and monthly income target.
- Scenario cards for income capacity, retirement real return, capital preservation, and wealth accumulation.
- Public rename to **Investing Workbench** and internal namespace migration to `src/investing_workbench/`.
- QuantBrasil-inspired market rankings, screeners, cache observability, reusable portfolios, and radar workflows.
- Retail fixed-income equivalence with CDB versus LCI/LCA/incentivized debenture plus taxable examples for Tesouro Selic proxy and DI funds with administration fees.
- Portfolio lifecycle results now include a didactic withdrawal plan with estimated real monthly withdrawal, income-target gap, historical drawdown, and real CAGR by candidate.
- The withdrawal plan now includes base, conservative, and sequence-stress retirement scenarios with drawdown buffers and target-income gaps.
- Catalog coverage now includes additional FIIs, BDRs, a crypto ETF comparison, presets for FIIs/BDRs/risk spectrum, and curated Market Explorer lists for income, FIIs, exterior via B3, NTN-B ETFs, Tesouro Direto, and risk ladder.
- Withdrawal planning now includes a deterministic Monte Carlo preview with approximate P50/P25/P10 income scenarios, real return, volatility, target-income coverage, and an explicit caveat before full monthly resampling exists.
- The Monte Carlo preview now includes a 30-year monthly exhaustion simulation for favorable, base, and adverse sequences, showing withdrawal amount, success rate, final balance, and exhaustion timing.
- Withdrawal planning now includes reproducible stochastic monthly Monte Carlo with 250 trajectories, stable per-asset seed, success rate, final-balance percentiles, median exhaustion timing, and compact frontend rendering.
- Catalog instruments now expose product profiles for investability, liquidity, tax treatment, income policy, fee model, and data quality across real products, proxies, indices, Tesouro Direto, and model portfolios.
- Investment comparison responses now include `study_quality`, a final readiness checklist rendered in the result view with methodology, product realism, rankings, fixed income, cache, retirement/Monte Carlo, warnings, and completion score.
- Investment catalog responses now include `product_data_plan`, the first post-roadmap product-data track with source registry, connector status, expected fields, local source manifest, family coverage, release candidates, market-filter backlog, validation gates, and a setup-tab panel.
- Product-data sources now have the first controlled refresh path with `POST /investments/product-data/refresh` for `b3_fii_listed`, local CSV cache, persisted `manifest.json`, checksum/schema/row-count metadata, and catalog enrichment for cached FII tickers.
- The product-data refresh path now attempts official B3 page collection, records `refresh_history.jsonl`, keeps curated fallback when collection is not structured, exposes selectable source refresh in the setup panel, and adds Market Explorer filters/screeners from cached FII metadata.
- Product-data planning now also includes fixture-backed B3 parser tests, refresh duration/source URL tracking, automatic catalog reload after refresh, first CVM seed refresh, an FII identity map, and FII rankings for cached data quality plus income quality (`fii_data_quality`, `fii_income_quality`).
- The CVM fund-daily-report connector now attempts the official monthly ZIP, parses semicolon CSV files into normalized quota/PL/flow/holder fields, and falls back transparently when the official file is unavailable.
- The catalog product-data plan now exposes `cvm_fund_profile`, giving the setup UI a compact summary of cached CVM row count, latest date, aggregate PL, net flow, holders, and largest fund/class samples.
- The same product-data panel now includes first CVM rankings for largest net worth, highest net flow, and largest holder base, keeping the CNPJ-to-catalog mapping caveat visible.
- `b3_listed_products` now has an operational controlled refresh for ETF/BDR product metadata, feeding `etf_bdr_profile` and the first `b3_lowest_admin_fee` ranking in the setup product-data UI.
- `fii_cvm_bridge` now provides the first explicit ticker-to-CNPJ bridge for FIIs, showing whether each mapped FII is present in the local CVM cache and surfacing latest date, PL, quota, and holder count when matched.
- Product-data planning now closes with `methodology_readiness_ranking`, consolidating FII/B3, CVM bridge, ETF/BDR fees, source ids, score components, and caveats into a single didactic readiness ranking.
- The Investments catalog now includes `investor_easy_parity`, comparing the public Investidor Facil offer against local capabilities and exposing 15 educational calculators plus feature coverage for portfolio organization, goals, contributions, dashboard, reports, alerts, and plan equivalence.
- The Investidor Facil parity panel is now interactive: calculators use editable assumptions, goals and manual positions persist in browser storage, the dashboard summarizes local progress, alerts flag goal/concentration issues, and the monthly report exports as local HTML.
- `Simular` strategy catalog with setup radar, editable setup drafts, backend persistence, execution planning, `/backtest` and `/pairs/backtests` execution, run history, backend score endpoint, compact run-result reopening, and Pairs lab handoff.
- Node 22 frontend runtime alignment through `frontend/.nvmrc`, `.node-version`, and validation under Node `22.20.0`.
- Frontend bundle hardening with route-level lazy loading for `Investimentos`, `Simular`, `Resultados`, and `Avancado`, plus lazy loading per advanced tool.

## Current Architecture

Primary code paths:
- Backend compatibility entrypoints remain in `src/`.
- New backend/domain/application code lives in `src/investing_workbench/`.
- FastAPI entrypoint: `src/api/main.py`
- CLI entrypoint: `src/cli.py`
- Frontend entrypoint: `frontend/src/main.tsx`
- Frontend application shell: `frontend/src/App.tsx`

Important supporting areas:
- Persisted runs: `runs/`
- Config presets: `configs/`
- Tests: `tests/`
- Docs: `docs/`
- Codex repo guidance: `AGENTS.md`, `.agents/skills/`, `.codex/config.toml`
- Legacy import compatibility shim: `src/bitcoin_martingale/__init__.py`

## Validation Snapshot

Backend:
- `uv run pytest -q`
- `uv run ruff check ...`
- `uv run mypy ...`

Frontend:
- `cd frontend && npm audit --json`
- `cd frontend && npm run lint`
- `cd frontend && npm test -- --run`
- `cd frontend && npm run build`

Status at handoff:
- Backend test suite passing in the last full validation cycle.
- Frontend lint passing.
- Frontend tests passing.
- Frontend production build passing.
- Frontend `npm audit` reporting `0 vulnerabilities`.

Local verification on `2026-04-23`:
- `uv run pytest tests/test_investment_compare_service.py -q` passing after the narrative payload extraction
- `PATH=/home/edann/.nvm/versions/node/v22.20.0/bin:$PATH npm test -- --run InvestmentDecisionPanels` passing from `frontend/`
- `uv run pytest -q tests/test_data_b3_tickers.py tests/test_investment_compare_service.py tests/test_selic_daily.py` passing
- `uv run ruff check src/data.py src/selic.py src/investing_workbench/application/investments/catalog.py src/investing_workbench/application/investments/service.py tests/test_data_b3_tickers.py tests/test_investment_compare_service.py tests/test_selic_daily.py` passing
- focused frontend tests for Investments, chart date ranges, legend state, tooltip behavior, and WEGE3 comparison passing
- `cd frontend && /tmp/node-v22.22.2-linux-x64/bin/node ./scripts/run-frontend-task.mjs lint` passing
- `cd frontend && /tmp/node-v22.22.2-linux-x64/bin/node ./scripts/run-frontend-task.mjs build` passing

Earlier local verification:
- `uv run pytest -q tests/test_api.py tests/test_api_investments.py tests/test_investment_compare_service.py tests/test_dataset_service.py` passing
- `uv run ruff check src/api src/investing_workbench tests/test_api.py tests/test_api_investments.py tests/test_investment_compare_service.py tests/test_dataset_service.py` passing
- `uv run mypy src/investing_workbench` passing
- `cd frontend && /tmp/node-v22.22.2-linux-x64/bin/node ./scripts/run-frontend-task.mjs build` passing
- smoke checks for `/`, `/system/status`, and `/investments/catalog` passing

Local verification on `2026-04-24`:
- `uv run pytest tests/test_investment_compare_service.py -q` passing after decision-profile and scenario-card updates
- `uv run ruff check src/api src/investing_workbench tests` passing
- `uv run mypy src/investing_workbench` passing
- `PATH=/home/edann/.nvm/versions/node/v22.20.0/bin:$PATH npm test -- --run InvestmentDecisionPanels` passing from `frontend/`
- `PATH=/home/edann/.nvm/versions/node/v22.20.0/bin:$PATH npm test -- --run InvestmentsWorkspace` passing from `frontend/`
- `PATH=/home/edann/.nvm/versions/node/v22.20.0/bin:$PATH npm run build` passing from `frontend/`

Local verification on `2026-04-28`:
- Full backend test suite passing with `uv run pytest -q` (`267 passed`, with existing NumPy warnings in pairs-service tests).
- Full frontend test suite passing under Node `22.20.0` with `npm test -- --run`.
- Focused backend tests around Investments workspace, strategy catalog, setup plans, and setup-run persistence passing.
- Backend `ruff` over `src/api`, `src/investing_workbench`, and focused tests passing.
- Backend `mypy src/investing_workbench` passing.
- Focused frontend tests for `StrategyCatalogPanel`, `useSavedStrategyRadar`, `usePairsTrading`, and shell navigation passing.
- Frontend lint and production build passing under Node `22.20.0`; the main app chunk was reduced to about `48 kB` and the previous Vite large-chunk warning is no longer emitted.

Local verification on `2026-05-04`:
- Full backend test suite passing with `uv run pytest -q` (`270 passed`, with existing NumPy warnings in pairs-service tests).
- Full frontend test suite passing under Node `22.20.0` with `npm test -- --run`.
- Focused catalog/API contract tests passing for `product_data_plan`.
- Backend `ruff` and `mypy src/investing_workbench` passing.
- Frontend lint and production build passing under Node `22.20.0`.
- Product-data refresh smoke passed on the live API at `http://127.0.0.1:18001/investments/product-data/refresh` for `b3_fii_listed`.
- Focused strategy catalog data, setup execution/draft-editor/draft/scoring-hook/scoring/history, and catalog-panel tests passing after extracting catalog loading, catalog cards, score-dimension panel, setup radar section, setup ranking panel, saved setup card, prepared-plan card, setup edit form, setup execution hook, setup draft editor hook, setup score hook, setup draft helpers, and setup-history helpers.
- Product realism now includes rendered income-policy examples for stocks/JCP, FIIs, ETFs, Tesouro Direto, and portfolios, clarifying cash-flow treatment, tax caveats, reinvestment assumptions, and investor decision context.
- Smoke checks for `http://localhost:3001/`, `/system/status`, `/backtests/strategy-setup-plan`, and setup workspace endpoints passing.

## Key User-Facing Capabilities

- Run backtests through API, CLI, or React UI.
- Persist every run with reproducibility metadata.
- List and reopen historical runs.
- Compare up to three persisted runs in the frontend.
- Share runs through `?run=<run_id>` permalinks.
- Inspect normalized experiments across runs, optimizations, walk-forward validations, and Monte Carlo jobs.
- Save curated research workspaces and reopen them later.
- Export research workspace reports as JSON, Markdown, or HTML through API and CLI.
- Review the same research workspace report contract inside the frontend Report View.
- Export persisted trades as CSV.
- Download persisted HTML reports.
- Export the current frontend results workspace as PNG.
- Compare investment alternatives across B3-oriented asset classes.
- Use curated investment presets such as `Primeiros passos`, `Balanceado B3`, and `Carteira 40+ (video)`.
- Compare assets and guided portfolios against Selic and equity proxies in a didactic flow.
- Compare CDI/IDkA duration studies, Tesouro Direto rolling strategies, and NTN-B ETFs with gross, net, real, and rolling-window metrics.
- Read "Como ler este estudo", "Como decidir em renda fixa", and "Decisao por objetivo" panels after each investment comparison.
- Tune the result interpretation through a decision profile without changing the historical backtest itself.
- Compare simple income, retirement, preservation, and accumulation scenario cards generated from the same result set.
- Reframe investment charts visually through date sliders while preserving the original simulation.
- Save reusable custom portfolios and radar artifacts through backend-backed investment workspaces with browser-storage fallback.
- Generate market rankings/screeners and compact market-explorer snapshots inspired by QuantBrasil-style list workflows.
- Build, edit, persist, prepare, run, score, decompose, compare, export, and review strategy setups from `Simular`, with scoring logic covered outside both the visual component and the workspace service facade.
- Hand off pairs-cointegration setups from `Simular` directly into `Avancado > Pairs B3` with the Pairs draft prefilled.

## Known Intentional Limits

- Parameter optimization, walk-forward validation, and Monte Carlo robustness now exist as persisted backend workflows.
- Dataset cataloging and dataset selection now exist across the API, CLI, and frontend.
- Dataset import, supported refresh flows, richer validation diagnostics, and research drilldowns are now available.
- Dataset provenance and event history are now persisted for managed datasets.
- Supported datasets now expose persisted refresh policies, due-state tracking, and manual batch refresh execution.
- The frontend now includes a didactic interpretation layer for reading strategy results with explicit return-vs-risk guidance.
- The frontend quick actions now export a complete JSON project bundle for the current run.
- The frontend now includes saved research workspaces, executive snapshots, report exports, and a server-backed report view.
- The legacy compatibility layer in `src/` still exists to preserve current contracts.
- The legacy package name `src.bitcoin_martingale` still exists only as a compatibility shim.
- The frontend is much simpler than before, but the `Investimentos` area is still early relative to the long-term platform ambition.
- Some fixed-income comparisons are intentionally methodology-specific: IDkA is an index-duration study, NTN-B ETFs are investable market products, Tesouro Direto studies are retail rolling simulations, and CDI/SELIC are cash-rate references.
- The Investments frontend and backend service are feature-rich but still need deeper modularization beyond the first extracted result panels and narrative module.
- The setup radar now supports a full local-first workflow, but the setup score is still a first explainable version rather than a statistically complete EV/out-of-sample robustness score.
- Pairs setup handoff and direct Pairs execution are integrated from `Simular`, while deeper diagnostics still belong to the dedicated Pairs lab.
- Product-data roadmap 1-9 now reports 100% completion in the catalog payload: FIIs, CVM,
  Tesouro, ETF/BDR costs, rankings, quality, persistence, explorer UX, and validation are
  represented as operational, cached, gated, or seeded surfaces instead of mapped placeholders.

## Suggested Next Backlog

If the project continues, the highest-value optional items are:
- richer investment comparison across B3 asset classes and real-return views
- deeper tax/inflation-aware comparison and income-oriented scenarios
- richer portfolio-level comparison, using the objective summary and scenario cards as the starting point
- clearer retirement / pre-retirement planning flows
- deeper methodology-aware fixed-income explanations that separate index evidence from investable products
- continued frontend and backend modularization around the Investments workspace
- visual polish and deeper didactic storytelling for non-technical users
- further thinning of compatibility layers once downstream imports are fully migrated
- richer backend setup score dimensions beyond the current return/drawdown/trade-count/run-count/data-validity score: EV, out-of-sample robustness, execution quality, and regime validity
