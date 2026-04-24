# Active Plans

Last updated: `2026-04-24T00:25:50-03:00`

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

## Highest-Value Next Work

1. Continue splitting `frontend/src/components/InvestmentsWorkspace.tsx`, now using the extracted investment result panels and decision-profile form as the pattern for setup tabs, review, charts, and custom portfolio controls.
2. Continue splitting `src/investing_workbench/application/investments/service.py`, now that narrative outputs live in `src/investing_workbench/application/investments/narratives.py` and profile normalization lives in `decision_profile.py`.
3. Deepen methodology explanations with concrete product-level taxes, fee, liquidity, and investable-product equivalence where data allows.
4. Turn the current decision-profile scoring into a richer fixed-income wizard with horizon, liquidity, tax treatment, real return, and mark-to-market tolerance.
5. Extend the current scenario cards into full portfolio, retirement/pre-retirement, withdrawal, and income-goal simulations.
6. Harden performance and caching for cold fixed-income studies while keeping downloaded datasets out of version control.

## Recently Implemented In This Cycle

- Added backend narrative builders for methodology, fixed-income decision guidance, and portfolio/objective interpretation.
- Added frontend result panels for "Como ler este estudo", "Como decidir em renda fixa", and "Decisao por objetivo".
- Added a decision-profile request layer for objective, horizon, liquidity, mark-to-market tolerance, tax view, and monthly income target.
- Added scenario cards for income capacity, retirement real return, capital preservation, and wealth accumulation.
- Added tests around the new investment narrative contract and result panels.

## Migration Guardrails
- The existing `src/` runtime remains valid until the new architecture is feature-complete.
- Migrate behavior through adapters, not rewrites.
- Preserve YAML config compatibility during the migration.
- Do not expand the asset catalog faster than methodology, assumptions, and validation can explain the results.
- Do not add advanced controls to the default screen unless the user can understand why they matter at first scan.
