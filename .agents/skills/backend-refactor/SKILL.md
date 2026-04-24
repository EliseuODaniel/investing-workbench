---
name: "backend-refactor"
description: "Refactor backend code incrementally toward service-oriented layers while preserving current behavior."
---

# Backend Refactor

## Goals
- Move orchestration out of route handlers and CLIs.
- Keep domain logic decoupled from HTTP and UI concerns.
- Keep new investment-comparison behavior in `src/investing_workbench/application/investments/` and split that package when service files become too broad.
- Shape backend payloads so the frontend can explain results simply: include methodology labels, assumptions, caveats, and beginner-friendly summaries when behavior changes.

## Workflow
1. Identify the smallest unit of business logic to extract.
2. Create or extend `src/investing_workbench/application/`.
3. Keep legacy modules as adapters when needed.
4. Add or update backend tests for behavior changes.
5. Update API models/docs when response contracts or methodology fields change.
6. Check whether the response helps a non-technical user understand what changed without reading backend code.
7. Run backend checks after changes.

## Current Hotspots
- `src/investing_workbench/application/investments/service.py`: split data loading, simulation, fixed-income studies, portfolio studies, summaries, and narratives incrementally.
- `src/investing_workbench/application/investments/narratives.py`: keep methodology, decision, and objective payloads plain-language, data-driven, and covered by investment service tests.
- `src/investing_workbench/application/investments/decision_profile.py`: keep investor profile normalization small, explicit, and stable for frontend forms.
- `src/investing_workbench/application/investments/catalog.py`: keep product catalog growth paired with methodology and assumptions.
- `src/api/main.py` should remain an assembly point; add new route behavior under `src/investing_workbench/interfaces/api/routers/`.

## Suggested Commands
- `uv run pytest -q tests/test_investment_compare_service.py tests/test_api_investments.py`
- `uv run ruff check src/api src/investing_workbench tests`
- `uv run mypy src/investing_workbench`
