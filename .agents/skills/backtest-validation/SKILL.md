---
name: "backtest-validation"
description: "Validate backtest behavior, metrics, and API outputs after engine or analytics changes."
---

# Backtest Validation

## Checklist
- Trades still serialize correctly
- Equity curves remain well-formed
- Metrics still compute for empty and non-empty runs
- Benchmarks and SELIC flows still work
- API status codes are correct for invalid input

## Suggested Commands
- `./.venv/bin/pytest -q`
- `./.venv/bin/pytest tests/test_api.py -q`
