# Final Status

Last updated: `2026-03-24T19:30:00-03:00`
Reference point: repository state validated locally on `2026-03-24`

## Project State

The project is in a strong handoff state and effectively complete for the refactor and product goals defined in this cycle.

Delivered areas:
- Codex-ready repository foundation with `AGENTS.md`, skills, project docs, and CI.
- Incremental architecture migration into `src/bitcoin_martingale/`.
- Service-layer backed API with persisted run artifacts.
- Reproducible run manifests, config snapshots, data profiles, and HTML reports.
- New domain-backed engine behind compatibility adapters.
- Analytics extracted into reusable analyzers.
- Frontend workspace for persisted run history, comparison, sharing, and exports.
- PNG export, HTML report download, and CSV trade export flows.
- Unified experiment registry across API, CLI, and frontend.
- Saved research workspaces with persistence, lineage context, and report export.
- Shared report contract for research workspaces across API, CLI, and frontend.
- Frontend performance hardening with lazy loading and manual chunking.
- Frontend dependency and security hardening with `npm audit` clean.

## Current Architecture

Primary code paths:
- Backend compatibility entrypoints remain in `src/`.
- New backend/domain/application code lives in `src/bitcoin_martingale/`.
- FastAPI entrypoint: `src/api/main.py`
- CLI entrypoint: `src/cli.py`
- Frontend entrypoint: `frontend/src/main.tsx`
- Frontend application shell: `frontend/src/App.tsx`

Important supporting areas:
- Persisted runs: `runs/`
- Config presets: `configs/`
- Tests: `tests/`
- Docs: `docs/`
- Codex repo guidance: `AGENTS.md`, `.agents/skills/`, `.codex/config.toml`

## Validation Snapshot

Backend:
- `./.venv/bin/pytest -q`
- `./.venv/bin/ruff check ...`
- `./.venv/bin/mypy ...`

Frontend:
- `cd frontend && npm audit --json`
- `cd frontend && npm run lint`
- `cd frontend && npm test -- --run`
- `cd frontend && npm run build`

Status at handoff:
- Backend test suite passing in the last full validation cycle.
- Frontend lint passing.
- Frontend tests passing.
- Frontend production build passing.
- Frontend `npm audit` reporting `0 vulnerabilities`.

Local verification on `2026-03-24`:
- `./.venv/bin/pytest -q` passing
- `./.venv/bin/ruff check src/api src/bitcoin_martingale tests/test_api.py` passing
- `./.venv/bin/mypy src/bitcoin_martingale` passing
- `cd frontend && npm run lint` passing
- `cd frontend && npm test -- --run` passing
- `cd frontend && npm run build` passing
- `cd frontend && npm audit --json` reporting `0 vulnerabilities`

## Key User-Facing Capabilities

- Run backtests through API, CLI, or React UI.
- Persist every run with reproducibility metadata.
- List and reopen historical runs.
- Compare up to three persisted runs in the frontend.
- Share runs through `?run=<run_id>` permalinks.
- Inspect normalized experiments across runs, optimizations, walk-forward validations, and Monte Carlo jobs.
- Save curated research workspaces and reopen them later.
- Export research workspace reports as JSON, Markdown, or HTML through API and CLI.
- Review the same research workspace report contract inside the frontend Report View.
- Export persisted trades as CSV.
- Download persisted HTML reports.
- Export the current frontend results workspace as PNG.

## Known Intentional Limits

- Parameter optimization, walk-forward validation, and Monte Carlo robustness now exist as persisted backend workflows.
- Dataset cataloging and dataset selection now exist across the API, CLI, and frontend.
- Dataset import, supported refresh flows, richer validation diagnostics, and research drilldowns are now available.
- Dataset provenance and event history are now persisted for managed datasets.
- Supported datasets now expose persisted refresh policies, due-state tracking, and manual batch refresh execution.
- The frontend now includes a didactic interpretation layer for reading strategy results with explicit return-vs-risk guidance.
- The frontend quick actions now export a complete JSON project bundle for the current run.
- The frontend now includes saved research workspaces, executive snapshots, report exports, and a server-backed report view.
- The legacy compatibility layer in `src/` still exists to preserve current contracts.
- The frontend is functional and modularized further than before, but not fully replatformed into a page-based app shell.

## Suggested Next Backlog

If the project continues, the highest-value optional items are:
- Parameter optimization with Optuna.
- Monte Carlo robustness storytelling and warnings inside the UI.
- Optional background refresh workers and notifications.
- A fuller user guide focused on interpreting strategy results.
- Visual polish and deeper dashboard storytelling.
- Architectural consolidation of legacy entrypoints into thinner adapters.
- Frontend decomposition beyond the current single-shell composition.
