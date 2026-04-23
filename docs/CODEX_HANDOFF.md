# Codex Handoff

Last updated: `2026-04-23T01:05:00-03:00`

## Read This First

This file is the canonical resume point for the current repository state.

If a future Codex session needs to continue from where this session stopped, read this file first, then open:

1. `/home/edann/projects/investing-workbench/README.md`
2. `/home/edann/projects/investing-workbench/docs/ARCHITECTURE.md`
3. `/home/edann/projects/investing-workbench/docs/API_REFERENCE.md`
4. `/home/edann/projects/investing-workbench/frontend/src/App.tsx`
5. `/home/edann/projects/investing-workbench/frontend/src/components/InvestmentsWorkspace.tsx`
6. `/home/edann/projects/investing-workbench/src/investing_workbench/application/investments/service.py`

## Current Identity And Location

- Public product name: **Investing Workbench**
- GitHub repository: `EliseuODaniel/investing-workbench`
- Repository visibility: **private**
- Current local path: `/home/edann/projects/investing-workbench`
- Old local path: `/home/edann/vscode_projects/bitcoin-martingale` (no longer valid)

## What Changed Recently

### Naming and Structure

- The repository was renamed from `bitcoin-martingale` to `investing-workbench`.
- The internal application package was moved from `src/bitcoin_martingale/` to `src/investing_workbench/`.
- A compatibility shim remains in `/home/edann/projects/investing-workbench/src/bitcoin_martingale/__init__.py` so legacy imports still resolve.
- Public docs, API title, frontend title, and package metadata were updated to use **Investing Workbench**.

### Product Direction

The app is no longer just a Bitcoin martingale backtester.

It now acts as a broader **investment comparison and backtesting platform**, with four product spaces:

- `Inicio`
- `Investimentos`
- `Simular`
- `Resultados`
- `Avancado`

The active direction is to keep making the app:

- simpler for non-technical investors
- more didactic about real-world returns
- broader across B3 asset classes
- still powerful enough for advanced quantitative research in the advanced area

## What Is Implemented

### Core Platform

- FastAPI backend with thin API routers under `/home/edann/projects/investing-workbench/src/investing_workbench/interfaces/api/routers/`
- React + Vite frontend under `/home/edann/projects/investing-workbench/frontend/`
- Persisted runs, optimizations, walk-forward validations, Monte Carlo runs, pairs backtests, and saved workspaces
- Compatibility entrypoints still present in `/home/edann/projects/investing-workbench/src/`

### Investment Platform Layer

- New `Investimentos` area in the UI
- Investment comparison API:
  - `GET /investments/catalog`
  - `POST /investments/compare`
- Curated catalog covering:
  - Brazilian stocks
  - Brazilian ETFs
  - international exposure via B3
  - FIIs
  - rate/fixed-income proxies such as Selic
  - historical CDI and IDkA indices for fixed-income duration studies
  - official Tesouro Direto rolling strategies for Tesouro Selic, Prefixado, and IPCA+
- Guided portfolio presets including:
  - `Primeiros passos`
  - `Balanceado B3`
  - `Renda e defensividade`
  - `Global pela B3`
  - `Carteira 40+ (video)`
  - `IPCA+ vs CDI (video)`
  - `Renda fixa por duration`
  - `Tesouro Direto real`

### Fixed-Income Study Layer

- The fixed-income engine now supports two explicit study modes:
  - `index_duration`: CDI + ANBIMA IDkA style duration studies for reproducing the video thesis
  - `retail_treasury`: official Tesouro Direto price history with retail buy/sell prices and estimated taxes
- `POST /investments/compare` now accepts:
  - `fixed_income_study_mode`
  - `fixed_income_tax_treatment`
  - `fixed_income_window_frequency`
- The response payload now exposes:
  - top-level fixed-income summary
  - `studies[]` with one block per methodology
  - gross, net, and real metrics for fixed-income rows
  - rolling-window consistency by horizon
- New backend entry points involved in this layer:
  - `/home/edann/projects/investing-workbench/src/investing_workbench/application/investments/fixed_income.py`
  - `/home/edann/projects/investing-workbench/src/investing_workbench/application/investments/tesouro_direto.py`
  - `/home/edann/projects/investing-workbench/src/investing_workbench/application/investments/service.py`

### Advanced Simulations

- Dedicated WEGE3 comparative scenario in the advanced area
- Long-only strategy comparison with charting, benchmarks, and trade audit
- Pairs trading workspace with guided and research controls
- Optimization, walk-forward, and Monte Carlo visual summaries with interactive charts

## Current Active Focus

The main product direction has shifted from “backtest a strategy” to:

**“show what the investor would really have earned, comparing strategies and real B3 investment alternatives in a didactic way.”**

That means the most relevant ongoing work is:

1. making comparisons across B3 asset classes more complete
2. improving realism of taxes, fees, and income treatment
3. simplifying the UI for a leigo first, while keeping advanced tooling accessible

## Exact Resume Point

If resuming work, the best next-entry files are:

- `/home/edann/projects/investing-workbench/frontend/src/components/InvestmentsWorkspace.tsx`
- `/home/edann/projects/investing-workbench/frontend/src/hooks/useInvestmentsComparison.ts`
- `/home/edann/projects/investing-workbench/frontend/src/lib/api.ts`
- `/home/edann/projects/investing-workbench/frontend/src/types/api.ts`
- `/home/edann/projects/investing-workbench/src/investing_workbench/application/investments/catalog.py`
- `/home/edann/projects/investing-workbench/src/investing_workbench/application/investments/service.py`
- `/home/edann/projects/investing-workbench/src/investing_workbench/interfaces/api/routers/investments.py`

The current product architecture already supports comparison, but the next valuable layer is:

- broader fixed-income coverage beyond Tesouro Direto:
  - LCI/LCA
  - CDBs %CDI
  - debentures incentivadas
- portfolio-level comparison for retirement and income scenarios
- richer didactic explanation of taxes, inflation, and income treatment
- performance optimization for long-window Tesouro Direto studies on cold cache

## Recommended Next Backlog

If a new Codex session continues from here, the highest-value next items are:

1. Expand retail fixed-income coverage:
   - LCI/LCA
   - CDB `% do CDI`
   - debentures incentivadas
   - explicit fee / tax toggles where applicable

2. Improve performance and UX for fixed income:
   - faster cold-start Tesouro Direto preparation
   - clearer side-by-side explanation of `indice` vs `produto real`
   - richer fixed-income charts and leader cards

3. Add portfolio comparison flows:
   - compare one selected asset vs a multi-asset allocation
   - compare user-defined mixes against guided portfolios
   - show contribution by sleeve/class

4. Improve didactic storytelling:
   - “what beat Selic”
   - “what had lower drawdown”
   - “what delivered better real return”
   - “what generated more income”

5. Add scenario presets for investor profiles:
   - conservative
   - balanced
   - growth
   - pre-retirement / retirement

6. Expand B3 comparison coverage:
   - broader FII and ETF catalog
   - clearer treatment of BDRs and international exposure

## Validation Snapshot

The latest fixed-income cycle passed with:

- `uv run pytest -q tests/test_investment_compare_service.py tests/test_api_investments.py`
- `cd frontend && /tmp/node-v22.22.2-linux-x64/bin/node ./scripts/run-frontend-task.mjs test -- --run src/hooks/useInvestmentsComparison.test.tsx`
- `cd frontend && /tmp/node-v22.22.2-linux-x64/bin/node ./scripts/run-frontend-task.mjs lint`

The previous namespace-migration validation also remained green with:

- `uv run ruff check src/api src/investing_workbench tests/test_api.py tests/test_api_investments.py tests/test_investment_compare_service.py tests/test_dataset_service.py`
- `uv run mypy src/investing_workbench`
- `uv run pytest -q tests/test_api.py tests/test_api_investments.py tests/test_investment_compare_service.py tests/test_dataset_service.py`
- `cd frontend && /tmp/node-v22.22.2-linux-x64/bin/node ./scripts/run-frontend-task.mjs build`

Smoke checks also passed:

- `GET http://127.0.0.1:18001/` returned `Investing Workbench API`
- `GET http://127.0.0.1:18001/system/status` returned `status: ok`
- `GET http://127.0.0.1:18001/investments/catalog` returned `200 OK`
- frontend served on `http://127.0.0.1:5173/`

## Suggested Local Startup Commands

Backend:

```bash
cd /home/edann/projects/investing-workbench
uv run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 18001
```

Frontend:

```bash
cd /home/edann/projects/investing-workbench/frontend
/tmp/node-v22.22.2-linux-x64/bin/node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
```

## Worktree Caution

- There is active, unstaged local work in the repository.
- The move from the old path to the new path already happened.
- Do not use the old `vscode_projects/bitcoin-martingale` location.
- Prefer continuing from the current worktree instead of recreating or copying files manually.

## Practical Summary

If the next session only needs the shortest possible handoff:

- the project is now **Investing Workbench**
- local path is `/home/edann/projects/investing-workbench`
- GitHub repo is `EliseuODaniel/investing-workbench`
- internal package is now `src/investing_workbench`
- legacy imports still work through a shim
- the active product focus is a didactic investment platform that compares B3 investment alternatives and strategy results
