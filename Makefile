.PHONY: backend-sync backend-test backend-lint backend-format backend-type frontend-lint frontend-test frontend-build

backend-sync:
	uv sync --extra dev

backend-test:
	uv run pytest -q

backend-lint:
	uv run ruff check src/api src/investing_workbench tests

backend-format:
	uv run python -m black --check src/api src/investing_workbench tests

backend-type:
	uv run mypy src/investing_workbench

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm test -- --run

frontend-build:
	cd frontend && npm run build
