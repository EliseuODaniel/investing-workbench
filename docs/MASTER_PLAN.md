# Master Plan

Last updated: `2026-04-20`

## Purpose

This document is the execution guide for the next product cycle.

It translates the current repository state into a practical plan to evolve the system from a strong backtesting application into a complete, reproducible, robust research platform for crypto and benchmark strategies.

It is intentionally more operational than `ROADMAP.md` and more current than older planning notes. Use it as the default planning reference for architecture, product direction, and implementation sequencing.

## Current State

The repository is already in a strong delivery state:

- backend tests, lint, type checks, frontend tests, frontend lint, frontend build, and frontend audit are passing
- persisted runs, optimizations, walk-forward validations, Monte Carlo analyses, and dataset workflows already exist
- the repository has a usable application service layer in `src/bitcoin_martingale/`
- the legacy runtime in `src/` still carries part of the operational surface
- the frontend provides a functional research workspace but still relies on a large application shell

The main gaps are no longer basic feature gaps. They are primarily:

- architectural consolidation
- workflow orchestration maturity
- documentation truthfulness and consistency
- deeper quantitative realism
- more powerful research ergonomics

## North Star

Build a local-first quantitative research platform that is:

- reproducible: every experiment, dataset, config, and artifact can be traced and reopened
- robust: research results are stress-tested and operationally reliable
- useful: the system helps users decide what to trust, not just what performed best
- extensible: new datasets, strategies, analyzers, and workflows can be added cleanly
- practical: the product stays usable for solo research and small teams without cloud dependence

## Product Positioning

The target is not to become a generic broker platform or a clone of QuantConnect.

The target is to become a focused research system for crypto and benchmark strategy evaluation with strong reproducibility, strong experiment lineage, and an unusually good interpretation layer.

The differentiators should be:

- local-first execution with persisted artifacts
- research workflows that are understandable and auditable
- quantitative robustness checks built into the normal workflow
- strong dataset governance and provenance
- didactic reporting for learning and review

## Planning Principles

- Preserve current user-visible behavior unless intentionally changing it.
- Prefer incremental refactors over large rewrites.
- Route new behavior through `src/bitcoin_martingale/`, not deeper into legacy entrypoints.
- Treat datasets, runs, and research jobs as first-class persisted entities.
- Prefer explicit contracts and artifact schemas over implicit conventions.
- Keep API, CLI, and frontend thin. Business logic belongs in application and domain layers.
- Every material behavior change should ship with tests and updated documentation.

## Strategic Workstreams

### 1. Architecture Consolidation

Reduce dependence on legacy runtime modules and complete the migration path into `src/bitcoin_martingale/`.

### 2. Research Kernel

Unify runs, optimization jobs, walk-forward jobs, Monte Carlo jobs, and dataset metadata under a coherent experiment model.

### 3. Quantitative Realism

Improve execution realism, portfolio modeling, transaction cost modeling, and robustness diagnostics.

### 4. Research UX

Turn the current frontend shell into a more navigable research workspace with stronger comparison and interpretation flows.

### 5. Data Governance

Treat datasets as governed assets with provenance, validation, policies, refresh behavior, and quality signals.

### 6. Operational Maturity

Support long-running background jobs, progress updates, and stronger observability.

## Execution Phases

## Phase 0: Truth, Contracts, and Baseline

### Goal

Make the repository self-consistent before major expansion.

### Why this comes first

The codebase is healthier than the docs currently suggest. If the team does not align on reality first, future work will compound confusion.

### Deliverables

- sync `README.md`, `docs/DEVELOPER_GUIDE.md`, `docs/ROADMAP.md`, `docs/FINAL_STATUS.md`, and `docs/EVOLUTION_V2.md`
- document current architecture truthfully, including what is already shipped
- define the official baseline validation matrix
- define stable API, artifact, and service contracts for core workflows
- identify which legacy modules remain transitional and which remain intentionally public

### Acceptance Criteria

- no major docs contradict the current codebase
- Python version requirements are consistent across docs and config
- every primary workflow has an identified owner path and validation command
- a new contributor can understand what is shipped, what is legacy, and what is backlog without reading multiple conflicting docs

### Target Files

- `README.md`
- `docs/DEVELOPER_GUIDE.md`
- `docs/ROADMAP.md`
- `docs/FINAL_STATUS.md`
- `docs/EVOLUTION_V2.md`
- `docs/API_REFERENCE.md`

## Phase 1: Entry Point Decomposition

### Goal

Reduce the size and responsibility of the current orchestration hotspots.

### Motivation

The current largest coordination points are:

- `src/cli.py`
- `src/api/main.py`
- `frontend/src/App.tsx`

These files are not broken, but they are carrying too much orchestration weight.

### Deliverables

- split FastAPI routes into domain routers
- move API request-to-service translation closer to interface adapters
- replace the placeholder next-generation CLI with a real command surface in `src/bitcoin_martingale/interfaces/cli/`
- reduce `src/cli.py` to compatibility delegation or remove it once safe
- split frontend app orchestration into feature-specific shells and route-like sections
- define a clear frontend module boundary for:
  - backtest execution
  - run history and comparison
  - optimization
  - walk-forward
  - Monte Carlo
  - datasets
  - interpretation

### Acceptance Criteria

- `src/api/main.py` becomes an assembly point, not a dense endpoint file
- `src/cli.py` no longer contains most workflow logic
- `frontend/src/App.tsx` becomes substantially smaller and focused on shell composition
- tests continue to validate all public behavior

## Phase 2: Research Kernel and Experiment Registry

### Goal

Introduce a unified model for persisted research work.

### Desired Capability

A run, optimization job, walk-forward job, and Monte Carlo job should feel like related experiment records, not separate islands.

### Deliverables

- define a shared experiment metadata model
- standardize manifest structure across workflows
- add lineage links between:
  - datasets
  - configs
  - runs
  - optimization trials
  - walk-forward windows
  - Monte Carlo analyses
- support experiment tags, notes, status, and provenance
- build list/filter/query support across experiment types
- normalize artifact directories and machine-readable summaries

### Acceptance Criteria

- users can trace a result from summary back to inputs and artifacts
- related workflows can be compared through shared identifiers and lineage
- artifact layouts are consistent enough for tooling and exports

## Phase 3: Quantitative Realism Upgrade

### Goal

Make research outputs more trustworthy and decision-relevant.

### Deliverables

- pluggable fee and slippage models
- support for partial fills and more realistic order assumptions
- richer benchmark alignment and portfolio-aware comparisons
- regime breakdown analysis
- sensitivity and stability analysis
- stronger risk metrics and warning surfaces
- clearer separation between in-sample excellence and out-of-sample robustness

Status note:

- the core engine already supports configurable fee/slippage inputs and partial-fill execution with liquidity caps
- the remaining work in this phase is now centered on analysis depth, benchmark context, and robustness reporting

### Acceptance Criteria

- execution assumptions are explicit and configurable
- reports explain not just returns, but fragility and sensitivity
- users can tell whether a result is robust or merely curve-fit

## Phase 4: Optimization and Validation Maturity

### Goal

Expand the system from deterministic workflow execution into a more powerful research engine.

### Deliverables

- support more advanced search strategies beyond grid and random
- evaluate Optuna integration for adaptive search and pruning
- add constraint-aware and multi-objective ranking
- add trial early stopping where safe
- improve walk-forward result aggregation and ranking
- improve Monte Carlo result interpretation and warning logic
- support resumable or restartable research jobs

### Acceptance Criteria

- large search spaces remain tractable
- research jobs produce clearer recommendations, not just raw score tables
- long-running jobs can be inspected and resumed safely

## Phase 5: Data Governance and Automation

### Goal

Make datasets reliable enough to serve as durable research inputs.

### Deliverables

- richer dataset quality scoring
- schema validation and anomaly checks
- more explicit provenance and event histories
- scheduled refresh support
- optional background workers for due refresh jobs
- operator-facing refresh diagnostics and notifications
- stronger benchmark and multi-asset dataset support

### Acceptance Criteria

- users can trust what dataset was used and how it was produced
- refreshes are operationally manageable
- dataset quality problems become visible before they damage research conclusions

## Phase 6: Research Workspace UX

### Goal

Turn the current functional UI into a more deliberate research workspace.

### Deliverables

- move from a mostly single-shell composition into feature-led navigation
- unify cross-workflow comparison views
- add saved research views and comparison presets
- add better narrative summaries and interpretation flows
- add richer dashboard storytelling for robustness, ranking, and benchmark context
- improve onboarding and glossary-driven explanation

### Acceptance Criteria

- the UI helps a user decide what to inspect next
- the system explains why a strategy is risky, fragile, or convincing
- users can move naturally from backtest to validation to interpretation

## Phase 7: Operational and Optional Live Layer

### Goal

Prepare the platform for longer-running and more operational usage patterns without forcing a premature live-trading pivot.

### Deliverables

- background job runner abstraction
- progress streaming or polling improvements
- structured job states and failure diagnostics
- observability for long-running workflows
- optional paper-trading and replay architecture investigation
- optional exchange or broker adapter design only after paper-trading foundations are stable

### Acceptance Criteria

- the system handles heavy research jobs without blocking the user experience
- failures are visible, inspectable, and recoverable
- optional live or paper capabilities remain isolated from core research flows

## Phase Gates

Advance only when the following gates hold:

- the baseline validation suite stays green
- public workflow contracts remain stable or intentionally versioned
- docs are updated in the same phase as code changes
- artifacts remain reproducible
- migrations are incremental and reviewable

## Quality Bar By Workstream

### Backend

- new orchestration belongs in application services
- domain models must not become serializer dumping grounds
- persistence formats should be explicit and testable
- all behavior-changing work ships with tests

### Frontend

- features should own their hooks, view logic, and local helpers
- the app shell should coordinate, not implement feature behavior
- comparisons and narratives should be understandable at first scan

### Data and Research

- dataset fingerprints, provenance, and validation signals are mandatory
- no optimization or validation workflow should exist without persisted artifacts
- robustness messaging should surface uncertainty, not overstate confidence

## Metrics For Success

Track the following repository and product health metrics:

- number of workflows routed through `src/bitcoin_martingale/` instead of legacy orchestration
- size reduction in `src/cli.py`, `src/api/main.py`, and `frontend/src/App.tsx`
- time to reproduce a past run from persisted artifacts
- percentage of experiment types with normalized manifests and lineage
- number of dataset quality failures caught before execution
- time to inspect, compare, and interpret a research result
- number of false-positive "winning" strategies rejected by robustness checks

## Risks

- spreading work across too many phases at once
- adding advanced quant features before consolidating current architecture
- increasing feature surface faster than docs and tests can keep up
- moving too aggressively off legacy entrypoints and breaking compatibility
- overbuilding live-trading features before the research kernel is complete

## Explicit Non-Goals For The Next Cycle

- becoming a generic brokerage execution platform
- supporting every asset class before dataset governance is mature
- replacing local-first usage with cloud dependence
- introducing large rewrites without incremental migration paths

## Recommended Immediate Sequence

If execution starts now, use this order:

1. Complete Phase 0 and remove documentation drift.
2. Start Phase 1 with API and frontend decomposition in parallel, then CLI.
3. Begin Phase 2 once the main entrypoints are thinner and contracts are clearer.
4. Start Phase 5 data-governance improvements early where they support Phase 2.
5. Begin Phase 3 and Phase 4 after the research kernel is stable enough to carry richer analytics.
6. Evolve the workspace UX continuously during Phases 2 through 6.
7. Treat Phase 7 as optional until the research platform core is genuinely strong.

## Suggested Milestones

### Milestone M1

Repository truth and stable contracts.

### Milestone M2

Thin entrypoints and cleaner architecture boundaries.

### Milestone M3

Unified experiment registry and lineage.

### Milestone M4

More trustworthy quant realism and robustness scoring.

### Milestone M5

Operationally mature research jobs and stronger data governance.

### Milestone M6

Research workspace with best-in-class interpretation and comparison flows.

## How To Use This Plan

- Use this document to sequence major work.
- Use `PLANS.md` for the active short-horizon slice.
- Update this document only when priorities, phase boundaries, or product direction change.
- Update feature docs and operational docs whenever a phase produces user-visible behavior changes.
