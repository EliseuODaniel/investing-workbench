# Bitcoin Martingale Repo Guide

## Mission
- Keep this repository evolving toward a reliable backtesting and research platform for crypto and benchmark comparison.
- Prefer incremental refactors over large rewrites.
- Preserve user-visible behavior unless the task explicitly changes it.

## Repo Layout
- `src/`: current Python application code and API.
- `src/bitcoin_martingale/`: new architecture for application, domain, infrastructure, and interfaces.
- `frontend/`: React + TypeScript + Vite application.
- `configs/`: YAML backtest presets.
- `tests/`: backend tests.
- `docs/`: architecture, workflows, and roadmap.
- `.agents/skills/`: reusable repo-local Codex skills.
- `.codex/`: Codex project configuration.

## Canonical Commands
- Backend setup: `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`
- Backend tests: `./.venv/bin/pytest -q`
- Backend lint: `./.venv/bin/ruff check src/api src/bitcoin_martingale tests/test_api.py`
- Backend format check: `./.venv/bin/black --check src/api src/bitcoin_martingale tests/test_api.py`
- Backend type check: `./.venv/bin/mypy src/bitcoin_martingale`
- Frontend install: `cd frontend && npm install`
- Frontend lint: `cd frontend && npm run lint`
- Frontend tests: `cd frontend && npm test -- --run`
- Frontend build: `cd frontend && npm run build`

## Engineering Rules
- Use `rg` for search and `rg --files` for file discovery.
- Use `apply_patch` for manual file edits.
- Do not rewrite the whole engine in one pass.
- New backend work should go into `src/bitcoin_martingale/` unless the task is explicitly a legacy fix.
- Keep the API thin: business logic belongs in application services, not route handlers.
- Prefer structured logging over `print` for new code.
- Add or update tests when changing behavior.

## Safe Edit Rules
- Treat `data/` and `reports/` as generated artifacts.
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
- Check `docs/code_review.md` before asking for or performing review-style work.
- Check `PLANS.md` for active migration phases before editing architecture-heavy files.
