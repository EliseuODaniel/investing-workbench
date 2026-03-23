# Evolution V2

## Goal

The next product cycle turns the project from a strong backtesting application into a broader research and learning platform.

Primary outcomes:
- Add parameter optimization workflows.
- Add robustness analysis such as walk-forward, out-of-sample, and Monte Carlo.
- Improve dataset management and research repeatability.
- Expand the frontend from a run workspace into a research workspace.
- Make the product more didactic for learning and interpretation.

## Guiding Principles

- Extend the new `src/bitcoin_martingale/` architecture instead of reintroducing logic into legacy entrypoints.
- Keep CLI, API, and frontend changes thin by routing behavior through application services.
- Prefer persisted, reproducible artifacts over transient in-memory workflows.
- Ship each research feature as a vertical slice with documentation, tests, and artifacts.

## Product Roadmap

### Phase A: Optimization Foundation

Goal:
- Introduce the optimization domain, request/plan/result models, and a planning service.

Deliverables:
- `application/optimizations/` service layer
- `domain/optimizations/` request, search-space, and trial models
- CLI support to preview optimization plans
- docs for search-space format and roadmap

Acceptance:
- A user can define a discrete search space and generate a reproducible trial plan.
- Trial plans are deterministic for the same seed.
- Legacy run flows remain unchanged.

### Phase B: Executable Optimization Runs

Goal:
- Execute trial plans against the current run service and persist optimization manifests.

Deliverables:
- optimization executor service
- persisted optimization artifacts
- summary ranking by chosen objective
- objective metrics such as `sharpe_ratio`, `total_return`, `max_drawdown`, `mar_ratio`

Acceptance:
- A user can run a bounded optimization job and inspect ranked results.
- Optimization artifacts are reproducible and linked to persisted runs.

### Phase C: Robustness Lab

Goal:
- Add validation features beyond single backtest scores.

Deliverables:
- walk-forward planning and execution
- in-sample / out-of-sample splits
- Monte Carlo trade-order resampling
- robustness summary and warning flags

Acceptance:
- Each optimization result can be stress-tested through additional validation workflows.

### Phase D: Dataset and Benchmark Expansion

Goal:
- Make research workflows less dependent on a single cached BTC series.

Deliverables:
- dataset registry and metadata
- richer data validation
- multi-asset datasets and resampling policies
- stronger benchmark selection and alignment

Acceptance:
- Users can manage and inspect datasets as first-class entities.

### Phase E: Didactic Product Layer

Goal:
- Improve interpretation, onboarding, and learning value.

Deliverables:
- glossary and metric explanations
- guided report narrative
- strategy templates and examples
- richer frontend storytelling for comparisons

Acceptance:
- New users can understand not just what won, but why it behaved that way.

## Architecture Plan

### New Backend Areas

```text
src/bitcoin_martingale/
  domain/
    optimizations/
      models.py
  application/
    optimizations/
      dto.py
      service.py
  infrastructure/
    persistence/
      optimization_repo.py        # future
```

### Planned API Surface

Initial future endpoints:
- `POST /optimizations/plan`
- `POST /optimizations`
- `GET /optimizations`
- `GET /optimizations/{optimization_id}`
- `GET /optimizations/{optimization_id}/results`

### Planned Frontend Areas

```text
frontend/src/features/
  optimization/
    components/
    hooks/
    lib/
```

## Search-Space Format

The first implementation targets discrete spaces only.

Supported forms:

```yaml
base_bet:
  values: [250, 500, 750]

multiplier:
  start: 1.5
  stop: 2.5
  step: 0.5
```

Strategy-specific overrides:

```yaml
global:
  take_profit:
    values: [0.1, 0.15, 0.2]

strategies:
  Simple Martingale:
    base_bet:
      values: [250, 500, 1000]
    multiplier:
      values: [1.5, 2.0, 2.5]
```

## Execution Plan

### Sprint V2.1

- Document the evolution roadmap.
- Add optimization planning models and service.
- Add a CLI command to preview trial plans.
- Add deterministic tests for grid and random planning.

### Sprint V2.2

- Execute plans through the existing run service.
- Persist optimization summaries and artifacts.
- Add ranking and filtering logic.

### Sprint V2.3

- Add walk-forward and out-of-sample execution.
- Add Monte Carlo robustness scoring.

### Sprint V2.4

- Add frontend optimization workspace.
- Add dataset manager and research UX.

## Current Status

Started in this cycle:
- roadmap documented
- optimization planning service foundation started
- CLI preview flow started
- optimization execution and persistence started
- optimization API endpoints started
- walk-forward validation and persisted out-of-sample windows started
- Monte Carlo robustness analysis and persisted artifacts started
- frontend optimization workspace started

Remaining backlog:
- dataset manager
- didactic robustness storytelling
- richer cross-workflow research dashboarding
