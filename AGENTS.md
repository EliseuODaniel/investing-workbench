# Investing Workbench Repo Guide

## Mission
- Keep this repository evolving toward a reliable local-first platform for didactic investment comparison, backtesting, and quantitative research.
- Treat `Investimentos` as the main investor-facing product surface, with `Simular`, `Resultados`, and `Avancado` carrying strategy research and deeper analysis.
- Prefer incremental refactors over large rewrites.
- Preserve user-visible behavior unless the task explicitly changes it.

## Repo Layout
- `src/`: current Python application code and API.
- `src/investing_workbench/`: new architecture for application, domain, infrastructure, and interfaces.
- `frontend/`: React + TypeScript + Vite application.
- `configs/`: YAML backtest presets.
- `tests/`: backend tests.
- `docs/`: architecture, workflows, and roadmap.
- `.agents/skills/`: reusable repo-local Codex skills.
- `.codex/`: Codex project configuration.

## Canonical Commands
- Backend setup: `uv sync --extra dev`
- Backend tests: `uv run pytest -q`
- Backend lint: `uv run ruff check src/api src/investing_workbench tests`
- Backend format check: `uv run python -m black --check src/api src/investing_workbench tests`
- Backend type check: `uv run mypy src/investing_workbench`
- Frontend install: `cd frontend && npm install`
- Frontend lint: `cd frontend && npm run lint`
- Frontend tests: `cd frontend && npm test -- --run`
- Frontend build: `cd frontend && npm run build`

## Engineering Rules
- Use `rg` for search and `rg --files` for file discovery.
- Use `apply_patch` for manual file edits.
- Do not rewrite the whole engine in one pass.
- New backend work should go into `src/investing_workbench/` unless the task is explicitly a legacy fix.
- Keep the API thin: business logic belongs in application services, not route handlers.
- Prefer structured logging over `print` for new code.
- Add or update tests when changing behavior.

## Safe Edit Rules
- Treat `data/` and `reports/` as generated artifacts.
- Treat downloaded fixed-income caches, local research workspaces, and pairs backtest outputs as local runtime artifacts unless a task explicitly asks to version fixtures.
- Do not remove legacy modules unless they are fully replaced and validated.
- Keep compatibility with existing config files during the migration.
- If a feature is stubbed, expose that clearly instead of pretending it works.

## Done Means
- Relevant tests and checks were run or an explicit reason was given.
- Public behavior, docs, and commands are aligned.
- New modules have clear ownership and names.
- Changes are reversible and small enough to review comfortably.

## Codex Workflow
- Start broad tasks with a short plan and update it as the work progresses.
- Use repo-local skills in `.agents/skills/` when they match the task.
- Reach for `.agents/skills/software-engineering-guardrails/` on implementation/refactor work.
- Reach for `.agents/skills/git-hygiene/` before staging, committing, or pushing.
- Reach for `.agents/skills/docs-sync/` whenever product direction, commands, endpoints, or user-facing behavior changes.
- Check `docs/code_review.md` before asking for or performing review-style work.
- Check `PLANS.md` for active migration phases before editing architecture-heavy files.
