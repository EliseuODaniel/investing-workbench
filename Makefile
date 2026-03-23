.PHONY: backend-test backend-lint backend-format backend-type frontend-lint frontend-test frontend-build

backend-test:
	./.venv/bin/pytest -q

backend-lint:
	./.venv/bin/ruff check src/api src/bitcoin_martingale tests/test_api.py

backend-format:
	./.venv/bin/black --check src/api src/bitcoin_martingale tests/test_api.py

backend-type:
	./.venv/bin/mypy src/bitcoin_martingale

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm test -- --run

frontend-build:
	cd frontend && npm run build
