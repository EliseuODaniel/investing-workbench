# Final Status

Last updated: `2026-03-23T09:32:01-03:00`
Reference commit: `c4b40a2`

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

## Key User-Facing Capabilities

- Run backtests through API, CLI, or React UI.
- Persist every run with reproducibility metadata.
- List and reopen historical runs.
- Compare up to three persisted runs in the frontend.
- Share runs through `?run=<run_id>` permalinks.
- Export persisted trades as CSV.
- Download persisted HTML reports.
- Export the current frontend results workspace as PNG.

## Known Intentional Limits

- Parameter optimization, walk-forward validation, and Monte Carlo robustness now exist as persisted backend workflows.
- Dataset cataloging and dataset selection now exist across the API, CLI, and frontend.
- Dataset import, supported refresh flows, richer validation diagnostics, and research drilldowns are now available.
- Dataset provenance and event history are now persisted for managed datasets.
- The legacy compatibility layer in `src/` still exists to preserve current contracts.
- The frontend is functional and modularized further than before, but not fully replatformed into a page-based app shell.

## Suggested Next Backlog

If the project continues, the highest-value optional items are:
- Parameter optimization with Optuna.
- Frontend views for walk-forward and Monte Carlo workflows.
- Monte Carlo robustness storytelling and warnings inside the UI.
- Dataset import/refresh and stronger quality validation workflows.
- Scheduled dataset refresh and provenance history.
- A user guide focused on interpreting strategy results.
- Visual polish and deeper dashboard storytelling.
