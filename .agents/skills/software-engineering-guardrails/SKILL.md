---
name: software-engineering-guardrails
description: Use when implementing, refactoring, or reviewing code in this repository and you need a concise workflow for good software engineering practice: inspect context first, keep changes incremental, validate with uv and frontend checks, and align docs with behavior changes.
---

# Software Engineering Guardrails

## Core workflow

- Read `AGENTS.md` and `PLANS.md` before architecture-heavy edits.
- Read `docs/PROJECT_STATUS_AND_DIRECTION.md` before changing product direction.
- Inspect local context before coding: `git status --short`, target modules, and nearby tests.
- Prefer incremental changes in `src/investing_workbench/` unless the task is explicitly legacy.
- Keep route handlers thin and put business logic in application services.
- Preserve user-visible behavior unless the task clearly changes it.
- For investor-facing flows, preserve didactic simplicity and a good user experience as functional requirements, not polish.
- Do not clobber unrelated dirty-worktree changes.

## Implementation rules

- Prefer `rg` and `rg --files` for search.
- Use `apply_patch` for manual edits.
- Add comments only where the intent would otherwise be hard to recover.
- Keep public payloads, docs, and tests aligned when contracts change.
- Before adding a new visible control, ask whether it belongs on the default path or behind progressive disclosure.

## Validation checklist

- Backend setup: `uv sync --extra dev`
- Backend tests: `uv run pytest -q`
- Backend lint: `uv run ruff check src/api src/investing_workbench tests`
- Backend format check: `uv run python -m black --check src/api src/investing_workbench tests`
- Backend type check: `uv run mypy src/investing_workbench`
- Frontend lint: `cd frontend && npm run lint`
- Frontend tests: `cd frontend && npm test -- --run`
- Frontend build: `cd frontend && npm run build`

## Done means

- The changed behavior is covered by tests or an explicit testing gap is called out.
- Docs or handoff notes were updated if the public workflow changed.
- User-facing changes remain simple, understandable, and explicit about assumptions.
- The final summary says what changed, what was validated, and what still carries risk.
