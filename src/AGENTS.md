# Backend Area Guide

## Scope
- Legacy runtime lives in `src/`.
- New architecture starts in `src/investing_workbench/`.

## Rules
- Put new orchestration and use-case logic in `src/investing_workbench/application/`.
- Keep domain concepts separate from FastAPI and CLI concerns.
- Legacy fixes in `src/api/` should be minimal and should route through services where practical.
- Avoid adding new business logic directly to `src/api/main.py`.

## Validation
- Run `./.venv/bin/pytest -q` for backend behavior changes.
- Run `./.venv/bin/ruff check src/api src/investing_workbench tests/test_api.py` for Python linting.
