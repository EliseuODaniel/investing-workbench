# Codex Handoff

Last updated: `2026-03-25T00:25:00-03:00`

## Read This First

This file is the canonical resume point for the current uncommitted worktree.

If a future Codex session needs to continue from where this session stopped, read this file first, then open:

1. `docs/MASTER_PLAN.md`
2. `docs/UI_SIMPLIFICATION_PLAN.md`
3. `frontend/src/App.tsx`
4. `frontend/src/components/backtest-results/ResultsTabsPanel.tsx`
5. `frontend/src/hooks/useBacktestWorkspace.ts`

## What Was Delivered In This Cycle

### Product and Architecture

- Documentation was synchronized with the actual repository state.
- The backend API was decomposed into domain routers under `src/bitcoin_martingale/interfaces/api/routers/`.
- The CLI was moved into `src/bitcoin_martingale/interfaces/cli/` and `src/cli.py` became a thin compatibility adapter.
- A unified experiment registry was introduced for `run`, `optimization`, `walkforward`, and `montecarlo`.
- Saved research workspaces were added with persistence, lineage context, report generation, API support, CLI support, and frontend support.
- Research workspace reports now share one contract across API, CLI, and frontend, including `json`, `markdown`, and `html`.

### Frontend Refactor

- `frontend/src/App.tsx` was reshaped into a simpler shell with three primary spaces:
  - `Operacao`
  - `Explorar`
  - `Labs`
- Large frontend hotspots were decomposed into feature folders and hooks:
  - `backtest-form/`
  - `backtest-results/`
  - `charts-tabbed/`
  - `dataset-manager/`
  - `metrics-cards/`
  - `optimization-workspace/`
  - `walkforward-workspace/`
  - `montecarlo-workspace/`
- The backtest setup flow was simplified and gained strategy help:
  - per-strategy `(i)` help
  - quick glossary
  - benchmarks collapsed by default
- Saved research workspaces gained:
  - dedicated list view
  - editing
  - import/export
  - executive snapshot
  - report view
  - server-backed export actions

## Current Active Focus

The original master-plan scope is largely implemented. The active work moved to **UI simplification and usability**.

The most recent user direction was:

- make the first backtest-result experience about the chart, not numbers
- keep advanced interpretation behind secondary tabs or deeper navigation
- reduce text density and cognitive load

## Exact Resume Point

The latest in-progress change is the **chart-first inversion** of the backtest results workspace.

This was already coded in:

- `frontend/src/hooks/useBacktestWorkspace.ts`
- `frontend/src/components/BacktestResultsWorkspace.tsx`
- `frontend/src/components/backtest-results/ResultsTabsPanel.tsx`
- `frontend/src/components/backtest-results/ResultsSummaryHero.tsx`
- `frontend/src/components/backtest-results/ResultsTabsPanel.test.tsx`
- `frontend/src/hooks/useBacktestWorkspace.test.tsx`

What changed in that last step:

- result tabs now place `Graficos` before `Resumo`
- the workspace copy now tells the user to start with charts
- the summary hero was moved inside the `Resumo` tab instead of always sitting above the result
- new backtests and loaded runs now reset to `charts` as the active result tab
- the summary hero was simplified to feel more like context and less like a wall of numbers

## Validation Status

### Verified Earlier In This Cycle

Backend was green before the final UI-only step:

- `./.venv/bin/pytest -q` passed, last known result: `145 passed`
- `./.venv/bin/ruff check src/api src/bitcoin_martingale tests/test_api.py tests/test_research_workspace_reporting.py tests/test_cli_research.py` passed
- `./.venv/bin/mypy src/bitcoin_martingale` passed

Frontend was also green before the final chart-first step:

- `cd frontend && npm run lint` passed
- `cd frontend && npm test -- --run` passed
- `cd frontend && npm run build` passed

### Verified After The Final Chart-First Step

These commands were run after the latest result-UX inversion:

- `cd frontend && npm run lint` passed
- `cd frontend && npm run build` passed

Test status after the last UI step:

- full `vitest` was attempted twice and hit local runner instability
- one run failed with Node/V8 out-of-memory
- a rerun with larger heap did not produce a clean completion in this environment
- targeted tests were added for the chart-first change, but the local test runner still needs a clean rerun

So the **remaining validation gap** is:

- rerun frontend tests cleanly after the chart-first inversion

## What Still Needs To Be Done Next

### Immediate Next Step

1. Reopen the UI in localhost and manually verify the backtest-result flow:
   - run a backtest or reopen a persisted run
   - confirm `Graficos` is the default result tab
   - confirm the summary block only appears inside `Resumo`
   - confirm the chart renders correctly and does not get stuck in a loading state

### After Manual Verification

2. Stabilize and rerun frontend tests:
   - `cd frontend && npm test -- --run`
   - if memory still fails, rerun with `NODE_OPTIONS=--max-old-space-size=8192`
   - if the suite still hangs, narrow down which file or mock is holding the process open

### Then Continue The UI Track

3. Keep simplifying the result reading experience:
   - reduce visual noise in charts and metric sections
   - keep numbers secondary to the main visual story
   - move dense expert detail deeper when possible

## Useful Local Artifacts

Demo persisted run used during this cycle:

- `runs/run_20260325T021512Z_57382ae3/manifest.json`
- `runs/run_20260325T021512Z_57382ae3/response.json`
- `runs/run_20260325T021512Z_57382ae3/report.html`

Demo saved research workspace:

- `research_workspaces/research_ws_20260325T021512Z_466ab5e1/manifest.json`

## Suggested Local Startup Commands

Backend:

```bash
./.venv/bin/uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8765
```

Frontend:

```bash
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

## Worktree Caution

- The repository has a large **uncommitted** refactor and UI simplification worktree.
- Do **not** discard or reset the worktree casually.
- Resume from the existing files instead of recreating the work.

## Practical Summary

If the next session only needs the short version:

- the research-platform master plan was mostly implemented
- the active focus moved to UI simplification
- the latest code change made the result experience chart-first
- lint and build passed after that change
- frontend tests still need a clean rerun because the local runner became unstable
