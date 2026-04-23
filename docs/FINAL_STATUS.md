# Final Status

Last updated: `2026-04-22T22:35:00-03:00`
Reference point: repository state validated locally on `2026-04-22`

## Project State

The project is in a strong handoff state for the current cycle and is no longer scoped only as a Bitcoin martingale backtester.

It is now positioned as **Investing Workbench**, a broader investment comparison and backtesting platform.

Delivered areas:
- Codex-ready repository foundation with `AGENTS.md`, skills, project docs, and CI.
- Incremental architecture migration into `src/investing_workbench/`.
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
- Guided investment comparison flows across B3 asset classes.
- New `Investimentos` area with curated portfolios, asset catalogs, and simple comparison UX.
- Public rename to **Investing Workbench** and internal namespace migration to `src/investing_workbench/`.

## Current Architecture

Primary code paths:
- Backend compatibility entrypoints remain in `src/`.
- New backend/domain/application code lives in `src/investing_workbench/`.
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
- Legacy import compatibility shim: `src/bitcoin_martingale/__init__.py`

## Validation Snapshot

Backend:
- `uv run pytest -q`
- `uv run ruff check ...`
- `uv run mypy ...`

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

Local verification on `2026-04-22`:
- `uv run pytest -q tests/test_api.py tests/test_api_investments.py tests/test_investment_compare_service.py tests/test_dataset_service.py` passing
- `uv run ruff check src/api src/investing_workbench tests/test_api.py tests/test_api_investments.py tests/test_investment_compare_service.py tests/test_dataset_service.py` passing
- `uv run mypy src/investing_workbench` passing
- `cd frontend && /tmp/node-v22.22.2-linux-x64/bin/node ./scripts/run-frontend-task.mjs build` passing
- smoke checks for `/`, `/system/status`, and `/investments/catalog` passing

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
- Compare investment alternatives across B3-oriented asset classes.
- Use curated investment presets such as `Primeiros passos`, `Balanceado B3`, and `Carteira 40+ (video)`.
- Compare assets and guided portfolios against Selic and equity proxies in a didactic flow.

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
- The legacy package name `src.bitcoin_martingale` still exists only as a compatibility shim.
- The frontend is much simpler than before, but the `Investimentos` area is still early relative to the long-term platform ambition.
- Fixed-income comparisons still rely partly on proxies rather than full retail bond instrumentation.

## Suggested Next Backlog

If the project continues, the highest-value optional items are:
- richer investment comparison across B3 asset classes and real-return views
- tax/inflation-aware comparison and income-oriented scenarios
- portfolio-level comparison instead of only single-asset or preset comparison
- clearer retirement / pre-retirement planning flows
- visual polish and deeper didactic storytelling for non-technical users
- further thinning of compatibility layers once downstream imports are fully migrated
