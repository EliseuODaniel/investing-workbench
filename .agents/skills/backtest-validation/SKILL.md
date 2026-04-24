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
- Investment comparisons preserve cash-flow assumptions, real-return fields, and methodology labels
- Fixed-income studies distinguish index-duration, retail Tesouro, NTN-B ETF, and cash-rate reference behavior
- Investment comparison responses expose usable `methodology_guide`, `fixed_income_decision_guide`, and `portfolio_objective_summary` blocks when applicable
- Decision-profile inputs affect explanatory ranking without changing the underlying historical cash-flow simulation
- Portfolio objective summaries include scenario cards for income capacity, retirement real return, capital preservation, and wealth accumulation
- User-facing summaries remain didactic: clear winner, caveat, risk, horizon, and methodology in plain language
- API status codes are correct for invalid input

## Suggested Commands
- `uv run pytest -q`
- `uv run pytest -q tests/test_api.py tests/test_api_investments.py tests/test_investment_compare_service.py`
- `uv run pytest -q tests/test_data_b3_tickers.py tests/test_selic_daily.py`
- `cd frontend && PATH=/home/edann/.nvm/versions/node/v22.20.0/bin:$PATH npm test -- --run InvestmentDecisionPanels`
- `cd frontend && npm test -- --run`
