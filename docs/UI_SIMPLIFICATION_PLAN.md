# UI Simplification Plan

Last updated: `2026-03-24`

## Goal

Reduce cognitive load in the React UI by adopting progressive disclosure:
- keep the default view focused on running and reading one backtest
- move complex research tools behind explicit navigation
- avoid showing multiple advanced panels at the same time

## Main Problems In The Current UI

- too many high-value panels are stacked on the same screen
- research, history, comparison, datasets, and advanced labs compete with the primary backtest flow
- expert-oriented information is visible too early
- the user has to scan too much text before knowing where to click next

## New Information Architecture

### 1. Operacao

Default space for the main journey:
- configure and run a backtest
- inspect the current result
- reopen the core data source tools when needed

Internal navigation:
- `Configurar`
- `Dados`

What stays visible here:
- `BacktestForm`
- current result workspace or empty state

What leaves this first layer:
- run history
- comparison
- research overview
- research labs

### 2. Explorar

Space for persisted artifacts and reopening prior work.

Internal navigation:
- `Historico`
- `Comparacao`
- `Workspaces`
- `Overview`

What lives here:
- `RunHistoryPanel`
- `RunComparisonPanel`
- `SavedResearchWorkspacesPanel`
- `ResearchOverviewPanel`

### 3. Labs

Space for advanced workflows only.

Internal navigation:
- `Optimization`
- `Walk-Forward`
- `Monte Carlo`
- `Drilldown`

What lives here:
- `OptimizationWorkspace`
- `WalkForwardWorkspace`
- `MonteCarloWorkspace`
- `ResearchDrilldownPanel`

## Progressive Disclosure Rules

- only one advanced workspace should be visible at a time
- persisted-history tools should not share the same visual plane as the main backtest form by default
- report, comparison, and drilldown should require an explicit navigation step
- explanatory text should be shortened and moved closer to the action it supports

## Implementation Sequence

### Phase 1

- add a new app shell with top-level navigation
- split the old single stacked page into `Operacao`, `Explorar`, and `Labs`
- move run history out of the default sidebar
- move dataset tools into an internal tab instead of always-visible placement

### Phase 2

- simplify the current results workspace
- keep only the summary and main charts/tables visible by default
- move artifacts, warnings, interpretation, and quick actions into secondary tabs or details sections

### Phase 3

- tighten copywriting throughout the shell
- reduce repeated helper text
- add stronger empty states and clearer next actions

## Acceptance Criteria

- a first-time user can find how to run one backtest without seeing the research labs
- advanced workflows are still available, but only after one intentional click
- the default screen contains fewer competing cards than before
- saved workspaces and research tools remain reachable without breaking existing features
