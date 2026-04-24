# Project Status And Direction

Last updated: `2026-04-24T00:25:50-03:00`

## Executive Read

Investing Workbench is now past the "make the repo usable" stage. The current codebase is a working local-first investment comparison and research platform with a much stronger foundation than the older docs suggest.

The product center has shifted. The most important surface is now `Investimentos`: a didactic workspace for comparing real B3-oriented investment alternatives, fixed-income studies, guided portfolios, and benchmark outcomes under the same cash-flow assumptions. The original backtesting engine, pairs trading lab, optimization, walk-forward, Monte Carlo, datasets, and research workspaces remain valuable, but they should behave like research labs around the main investor-facing experience.

## Current State

- Git is consolidated on `main`, with `origin/main` as the only remote branch.
- Backend uses Python 3.12, `uv`, FastAPI, and the service-oriented `src/investing_workbench/` architecture.
- Frontend uses React, TypeScript, Vite, typed API hooks, feature components, and shared chart utilities.
- The legacy `src/` runtime still exists for compatibility; new behavior should continue moving into `src/investing_workbench/`.
- The compatibility package `src/bitcoin_martingale/` remains only to avoid breaking legacy imports.
- Downloaded datasets, fixed-income caches, local research workspaces, and pairs artifacts are local runtime artifacts, not product source.

## Shipped Capabilities

- Didactic investment comparisons across B3 stocks, ETFs, FIIs, international exposure through B3, fixed-income proxies, CDI/SELIC, Tesouro Direto studies, IDkA studies, and NTN-B ETFs.
- Fixed-income study modes for index-duration studies and retail Tesouro Direto simulations with gross, net, and real return metrics.
- Interactive investment charts with visual date filtering, rebasing from a selected date, legend focus/hide behavior, and nearest-line tooltips.
- Methodology-aware result panels explaining evidence types, assumptions, caveats, fixed-income decision tradeoffs, and objective-based winners.
- Portfolio/objective interpretation that reframes the same comparison around final wealth, real return, drawdown, volatility, fixed-income role, and allocation comparison.
- Decision-profile scoring for objective, horizon, liquidity, mark-to-market tolerance, tax view, and monthly income target.
- Scenario cards for income capacity, retirement purchasing power, capital preservation, and wealth accumulation.
- Persisted backtests, async jobs, run history, comparison, reports, exports, and reproducibility metadata.
- B3 pairs trading research with universe resolution, screeners, batch backtests, borrow snapshots, diagnostics, and persisted artifacts.
- Optimization, walk-forward validation, Monte Carlo robustness, dataset management, saved research workspaces, and allocation planning.

## Architecture Assessment

The migration to `src/investing_workbench/` is real, not just decorative. API entrypoints are much thinner than before, and the application/domain/infrastructure split is visible across runs, datasets, experiments, pairs trading, allocation, and investments.

The main architecture pressure has moved to two hotspots, with the first extraction now started:

- `frontend/src/components/InvestmentsWorkspace.tsx` is now the product UX hotspot. It is useful and feature-rich, but too large to remain the long-term owner of setup, review, results, chart behavior, fixed-income explanations, and portfolio controls.
- `src/investing_workbench/application/investments/service.py` is now the backend product logic hotspot. It carries too much data loading, simulation, fixed-income methodology, ranking, summary, and narrative work in one file.
- `src/investing_workbench/application/investments/narratives.py` now owns the first slice of methodology, decision, and objective narrative payloads.
- `src/investing_workbench/application/investments/decision_profile.py` normalizes investor profile inputs for didactic guidance.
- `frontend/src/components/investments/` now owns the first extracted result panels for methodology and decision support.

That is a good sign in a way: the pressure has moved from "the app is not wired" to "the flagship feature is important enough to deserve proper internal boundaries."

## Product Direction

The strongest direction is:

**Investing Workbench should help a person understand what they would have earned, why, under which assumptions, and whether that conclusion is robust enough to matter.**

The user experience goal is:

**Keep the main product didactic, simple, and calm: each screen should answer one investor question clearly, hide technical density until needed, and make caveats visible without overwhelming the user.**

This means the next improvements should prioritize:

- explanation quality over adding more tickers
- investable-product comparisons over abstract index winners
- real return, taxes, liquidity, drawdown, and horizon over nominal winner tables
- portfolios and goals over isolated asset rankings
- reproducible research artifacts over one-off screen outputs
- progressive disclosure, readable language, and low-friction chart interaction over dense control panels

## Recommended Near-Term Sequence

1. Continue modularizing the Investments frontend.
   The result methodology/decision panels and decision-profile form are extracted. Next, split setup tabs, review, chart panels, and custom portfolio controls into smaller components and hooks while keeping the default path guided and uncluttered.

2. Continue modularizing the Investments backend.
   Narrative outputs and decision-profile normalization are extracted. Next, separate catalog/data loading, market asset simulation, fixed-income index studies, Tesouro Direto rolling studies, portfolio simulation, and summary generation.

3. Deepen the methodology and assumptions layer.
   The visible layer now exists. Next, improve tax, fee, inflation, liquidity, and investable-product equivalence explanations where data supports them.

4. Build fixed-income decision flows.
   The first profile-scored decision cards exist. Next, make them more interactive around product equivalence, current rates, liquidity need, tax wrapper, real return, and volatility/drawdown.

5. Add portfolio and retirement scenarios.
   Objective-based interpretation and simple income/retirement scenario cards exist. Next, let the user compare allocations, contribution plans, withdrawal paths, and class contribution over time.

6. Harden cold-start performance and cache observability.
   Fixed-income and Tesouro studies should be fast after first load, transparent about cache coverage, and clear when official data could not be refreshed.

## Risks To Watch

- Product sprawl: the app can become hard to read if labs, backtests, investment comparison, and research workflows all compete for primary attention.
- Methodology confusion: IDkA, NTN-B ETFs, Tesouro Direto titles, CDI, SELIC, proxies, and market tickers must be explained as different kinds of evidence.
- Over-ranking: a historical winner should not be framed as an automatic current recommendation.
- File-size drift: the current investment frontend and backend service are already beyond their ideal size.
- Documentation drift: several older docs still describe the repository as a crypto/martingale-first research system.

## What Not To Do Next

- Do not add live trading or broker execution until the research and investment-comparison core is clearer.
- Do not add a large number of new assets without improving assumptions, validation, and methodology labels.
- Do not rewrite the legacy runtime in one pass; keep migration incremental.
- Do not turn `Investimentos` into a dense quant lab. Keep advanced controls available, but tucked away.
- Do not make the user read methodology docs before the UI itself makes the result understandable.

## Practical Next Milestones

- M1: truthful docs, repo-local skills, and active planning aligned with current code.
- M2: modular Investments frontend and backend boundaries.
- M3: methodology-aware fixed-income explanations and product equivalence comparisons.
- M4: portfolio, goal, and retirement scenarios.
- M5: unified research lineage and stronger data-governance diagnostics across investment and strategy workflows.
